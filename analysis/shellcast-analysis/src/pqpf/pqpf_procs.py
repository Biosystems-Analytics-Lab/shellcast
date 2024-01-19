"""
Common PQPF data processing
Steps:
1. Listing today's PQPF file names for download.

"""
import sys
import os
import logging.config
import pygrib
import warnings
import constants as ct
from shapely.errors import ShapelyDeprecationWarning
from datetime import datetime
from typing import List
from pqpf import utils
from pqpf.pqpf_proc_dirs import ProcDirs
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

logger = logging.getLogger(__name__)


# Prerequisites
# Lease point layer having lease_id and rainfall threshold

class PQPFProcs:
    def __init__(self, state, db):
        self.state = state.upper()
        pdirs = ProcDirs(self.state, db)
        self.os_type = pdirs.os_type
        self.config = pdirs.config
        self.grb_raw_dir = pdirs.grb_raw_dir
        self.tiffs_dir = pdirs.tiffs_dir
        self.grb_subsets_dir = pdirs.grb_subsets_dir
        self.outfile_date = None

    def get_files_to_download(self) -> List[str]:
        """
        List today's PQPF GRB files.
        Returns:
            object: list of today's PQPF GRB files
        """
        logger.info('[PQPF GRB files to download]')
        try:
            files = []
            files_to_download = []
            today = datetime.today().strftime('%Y%m%d')
            # Get GRB names for today
            for hour in ct.VALID_HOURS:
                fname = f'{ct.GRB_PREFIX}_{today}{ct.Z_RUN}{hour}.grb'
                files.append(fname)
            # Check today's GRB files are already in directory
            if len(files) > 0:
                for f in files:
                    if f not in os.listdir(self.grb_raw_dir):
                        files_to_download.append(f)
                if len(files_to_download) > 0:
                    for f in files_to_download:
                        logger.info(f)
                    return files_to_download
                else:
                    logger.info('Data exists in the directory.')
                logger.info(utils.done_str)
            else:
                msg = ' Having a problem listing PQPF GRB files.'
                logger.error(msg)
                utils.send_email(msg, self.state)
                sys.exit(1)
        except Exception as e:
            msg = 'Files to download failed.'
            utils.error_process(msg, e)

    def check_grb_files(self):
        """
        Check downloaded PQPF data is current. Sometimes
        TODO - Make analysis done with downloaded files. For instance, one day, there is no f030 PQPF data then run analysis with rest of PQPF files.

        """
        logger.info('[Check GRB files dates]')
        grb_file_dates = []
        to_db_bool = False
        grb_files = os.listdir(self.grb_raw_dir)
        today_dt = datetime.today()
        today_str = datetime.strftime(today_dt, '%Y-%m-%d')
        for f in grb_files:
            if f.endswith('.grb'):
                date = f.split('_')[-1][:8]
                grb_file_dates.append(date)
        unique_dates = list(set(grb_file_dates))
        if len(unique_dates) == 1:
            dt = datetime.strptime(unique_dates[0], '%Y%m%d')
            self.outfile_date = datetime.strftime(dt, '%Y-%m-%d')
            if self.outfile_date == today_str:
                to_db_bool = True
            logger.info(f'Date of data: {self.outfile_date}')
            logger.info(utils.done_str)
            return to_db_bool
        else:
            msg = 'All GRB files need to have the same date.'
            logger.error(msg)
            sys.exit(0)

    def wgrib2_small_grib(self, grb_fpath):
        grb_fname = os.path.basename(grb_fpath)
        try:
            wgrib2 = 'wgrib2'
            if self.os_type == 'Other':
                wgrib2 = '/usr/local/bin/wgrib2'

            out_grb_path = os.path.join(self.grb_subsets_dir, f'sbs_{grb_fname}')
            cmd = [wgrib2, grb_fpath, '-small_grib', self.config[self.state]['LON_WE'],
                   self.config[self.state]['LAT_SN'], out_grb_path]
            utils.cmd_subprocess(cmd)
            logger.info(f'{grb_fname} --- cropped')

        except Exception as e:
            msg = f'{grb_fname} --- subset GRIB file failed.'
            utils.error_process(msg, e)

    def small_grb(self) -> None:
        """
        Crop GRB files in small area.
        """
        logger.info('[Subset GRB file for small area]')
        try:
            utils.delete_files(self.grb_subsets_dir)
            grbs = utils.get_raw_grb_list(self.grb_raw_dir)
            if grbs and len(grbs) > 0:
                if self.state == 'FL':
                    for grb in grbs:
                        if grb.endswith('f030.grb'):
                            self.wgrib2_small_grib(grb)
                else:
                    for grb in grbs:
                        self.wgrib2_small_grib(grb)
            logger.info(utils.done_str)

        except Exception as e:
            msg = 'Subset GRIB file failed.'
            utils.error_process(msg, e)

    def grb_to_tiff(self, thresholds) -> None:
        """
        Transform GRB to Tiff for each threshold.
        Args:
            thresholds (List[float]): List of unique rainfall thresholds
        """
        logger.info('[Transform GRB to Tiff for each threshold]')
        try:
            utils.delete_files(self.tiffs_dir)
            dst_srs = 'EPSG:4326' if self.state == 'FL' else None

            for grb_fpath in [os.path.join(self.grb_subsets_dir, f) for f in os.listdir(self.grb_subsets_dir) if
                              f.endswith('grb')]:
                grbs = pygrib.open(grb_fpath)
                fname = grb_fpath.split('_')[-1].split('.')[0]

                for idx, grb in enumerate(grbs):
                    if 'upperLimit' in grb.keys():
                        # upper_limit = grb.upperLimit
                        # inches = round((upper_limit / 1000) / 25.4, 1)
                        inches = round(grb.upperLimit / 25.4, 1)
                        for threshold in thresholds:
                            if float(threshold) == inches:
                                rainfall_str = str(threshold).replace('.', 'p')
                                tiff_path = os.path.join(self.tiffs_dir, f'{ct.TIFF_PREFIX}_{fname}_{rainfall_str}.tif')
                                utils.run_gdal_to_tiff(grb_fpath, tiff_path, {idx + 1}, dst_srs)
                                # cmd = [gdal_translate, '-b', f'{idx + 1}', '-of', 'GTiff', grb_fpath, tiff_path]
                                # utils.cmd_subprocess(cmd)
            logger.info(utils.done_str)
        except Exception as e:
            msg = 'GRB to TIFF transformation failed.'
            utils.error_process(msg, e)

    def grb_to_tiff_all(self) -> None:
        """
        Transform GRB thresholds to TIFF.
        Args:
            thresholds (List[float]): List of unique rainfall thresholds
        """
        logger.info('[Transform all GRB thresholds to TIFF]')
        try:
            utils.delete_files(self.tiffs_dir)
            dst_srs = 'EPSG:4326' if self.state == 'FL' else None
            for grb_fpath in [os.path.join(self.grb_subsets_dir, f) for f in os.listdir(self.grb_subsets_dir) if
                              f.endswith('grb')]:
                grbs = pygrib.open(grb_fpath)
                fname = grb_fpath.split('_')[-1].split('.')[0]

                for idx, grb in enumerate(grbs):
                    if 'upperLimit' in grb.keys():
                        # upper_limit = grb.upperLimit
                        # inches = round((upper_limit / 1000) / 25.4, 1)
                        inches = float(round(grb.upperLimit / 25.4, 1))
                        rainfall_str = str(inches).replace('.', 'p')
                        tiff_path = os.path.join(self.tiffs_dir, f'{ct.TIFF_PREFIX}_{fname}_{rainfall_str}.tif')
                        utils.run_gdal_to_tiff(grb_fpath, tiff_path, {idx + 1}, dst_srs)
            logger.info(utils.done_str)
        except Exception as e:
            msg = 'GRB to TIFF transformation failed.'
            utils.error_process(msg, e)

import configparser
import sys
import os
import gc
import logging.config
import functools as ft
import pygrib
import warnings
import rasterio
import pandas as pd
import geopandas as gpd
import sqlalchemy.engine
import numpy as np
import constants as ct
from ftplib import FTP
from shapely.geometry import Point
from shapely.errors import ShapelyDeprecationWarning
from datetime import datetime
from typing import List, Type
from rasterstats import zonal_stats
from sqlalchemy import create_engine
from . import utils

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

logger = logging.getLogger(__name__)


# Prerequisites
# Lease point layer having lease_id and rainfall threshold


class PQPF:
    def __init__(self, state, db: str):
        """
        Args:
            state (str): State abbreviation
        """
        self.outfile_date = None
        self.config = configparser.ConfigParser()
        self.config.read(ct.CONFIG_INI)
        self.state = state.upper()
        self.data_root = os.path.join(ct.PQPF_DATA_DIR, state.lower())
        self.connect_str = utils.get_connection_string(self.config[db], self.config[self.state]['DB_NAME'])
        # Data directories
        self.inputs_dir = os.path.join(self.data_root, 'inputs')
        self.outputs_dir = utils.create_directory(os.path.join(self.data_root, 'outputs'), delete=True)
        self.grb_raw_dir = utils.create_directory(os.path.join(ct.PQPF_DATA_DIR, 'raw'))
        self.intermediate_outputs_dir = utils.create_directory(os.path.join(self.data_root, 'intermediate'),
                                                               delete=True)
        self.grb_subsets_dir = utils.create_directory(os.path.join(self.intermediate_outputs_dir, 'subsets'),
                                                      delete=True)
        self.tiffs_dir = utils.create_directory(os.path.join(self.intermediate_outputs_dir, 'tiffs'), delete=True)

        self.lease_shp = os.path.join(self.inputs_dir, self.config[self.state]['LEASE_SHP'])
        if self.state == 'NC':
            self.cmu_shp = os.path.join(self.inputs_dir, self.config[self.state]['CMU_SHP'])
            self.use_cols = [
                self.config[self.state]['LEASE_SHP_COL_LEASE_ID'],
                self.config[self.state]['LEASE_SHP_COL_CMU_NAME'],
                self.config[self.state]['LEASE_SHP_COL_RAIN_IN'],
                'geometry'
            ]
            self.cmu_use_cols = [
                self.config[self.state]['CMU_SHP_COL_CMU_NAME'],
                self.config[self.state]['CMU_SHP_COL_RAIN_IN'],
                'geometry'
            ]
        elif self.state == 'SC':
            self.use_cols = [
                self.config[self.state]['LEASE_SHP_COL_LEASE_ID'],
                'geometry'
            ]

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
                utils.send_email(self.state, msg)
                sys.exit(1)
        except Exception as e:
            msg = 'Files to download failed.'
            utils.error_process(self.state, msg, e)

    def download_grbs(self, files: List[str]) -> None:
        """
        Download PQPF GRB files from FTP.
        Args:
            files (List[str]): List of GRB files
        """
        logger.info('[Download PQPF GRBs from FTP]')
        try:
            if files:
                ftp = FTP(ct.FTP_URL)
                ftp.login()
                ftp.encoding = 'utf-8'
                ftp.cwd(ct.FTP_CWD)
                for fname in files:
                    grb_path = os.path.join(self.grb_raw_dir, fname)
                    with open(grb_path, 'wb') as f:
                        ftp.retrbinary("RETR " + fname, f.write)
                    logger.info(f'{fname} downloaded.')
                ftp.quit()
            else:
                logger.info('Skip download')
            logger.info(utils.done_str)
        except Exception as e:
            msg = 'GRB file download failed.'
            utils.error_process(self.state, msg, e)

    def small_grb(self) -> None:
        """
        Crop GRB files in small area.
        """
        logger.info('[Subset GRB file for small area]')
        try:
            utils.delete_files(self.grb_subsets_dir)
            for grb in [os.path.join(self.grb_raw_dir, f) for f in os.listdir(self.grb_raw_dir) if f.endswith('.grb')]:
                out_grb_path = os.path.join(self.grb_subsets_dir, f'sbs_{os.path.basename(grb)}')
                cmd = ['wgrib2', grb, '-small_grib', self.config[self.state]['LON_WE'],
                       self.config[self.state]['LAT_SN'], out_grb_path]
                logger.info(cmd)
                utils.cmd_subprocess(cmd)
            logger.info(utils.done_str)
        except Exception as e:
            msg = 'Subset GRIB file failed.'
            utils.error_process(self.state, msg, e)

    def grb_to_tiff(self, thresholds: List[float]) -> None:
        """
        Transform GRB to Tiff for each threshold.
        Args:
            thresholds (List[float]): List of unique rainfall thresholds
        """
        logger.info('[Transform GRB to Tiff for each threshold]')
        try:
            # Delete previous outputs
            utils.delete_files(self.tiffs_dir)

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
                            if threshold == inches:
                                rainfall_str = str(threshold).replace('.', 'p')
                                tiff_path = os.path.join(self.tiffs_dir, f'{ct.TIFF_PREFIX}_{fname}_{rainfall_str}.tif')
                                cmd = ['gdal_translate', '-b', f'{idx + 1}', '-of', 'GTiff', grb_fpath, tiff_path]
                                utils.cmd_subprocess(cmd)
            logger.info(utils.done_str)
        except Exception as e:
            msg = 'GRB to TIFF transformation failed.'
            utils.error_process(self.state, msg, e)

    def get_thresholds(self) -> List[float]:
        """
        Get unique rain_in values.

        Args
            lease_shp (str): The lease shp name
        Returns (List[float]): A list of unique rainfall thresholds
        """
        logger.info('[Get unique rainfall thresholds]')
        try:
            gdf = gpd.read_file(self.lease_shp)
            gdf = gdf[self.use_cols]
            thresholds = sorted(gdf.rain_in.unique())  # Returns list of class numpy.float64
            if len(thresholds) > 0:
                thresholds_num = [float(threshold) for threshold in thresholds]
                thresholds_str = ', '.join([str(threshold) for threshold in thresholds])
                logger.info(f'Thresholds: {thresholds_str}')
                logger.info(utils.done_str)
                return thresholds_num
            else:
                raise
        except Exception as e:
            msg = 'Failed to get rainfall thresholds.'
            utils.error_process(self.state, msg, e)
        else:
            del gdf
            gc.collect()

    def ras_values_to_pts(self, pts_shp, what_lyr) -> Type:
        """
        Assign PQPF raster values to leases.

        Returns (gpd.GeoDataFrame): DataFrame containing each lease's lease_id, cmu_name, rain_in,
            pqpf_24h, pqpf_48h, pqpf_72h columns with values.
        """
        logger.info('[Get PQPF raster value]')
        logger.info(f'{"-"*5} {what_lyr.upper()} {"-"*5}')
        try:
            gdf = gpd.read_file(pts_shp)
            result_gdf = gpd.GeoDataFrame()
            if what_lyr == 'cmu':
                gdf = gdf[self.cmu_use_cols]
            elif what_lyr == 'lease':
                gdf = gdf[self.use_cols]
            tiffs = utils.list_files(self.tiffs_dir, '.tif')

            for tiff in tiffs:
                tiff_fname = os.path.basename(tiff)

                logger.info(f'Process: {tiff_fname}')
                src = rasterio.open(tiff)
                fname = os.path.basename(tiff)
                match = utils.regex_find(ct.REG_PATTERN_GRB_HOURS, fname)
                if match and len(match) > 0:
                    file_hour = f'{match[0][2:]}'
                    hour = str(int(file_hour) + ct.TO_HOUR) + 'h'
                    rainfall_str = fname.split('_')[-1].split('.')[0]
                    rainfall_in = float(rainfall_str.replace('p', '.'))
                    gdf_q = gdf.query(f'rain_in == {rainfall_in}').copy()
                    coords = [(Point(i).x, Point(i).y) for i in gdf_q.geometry]
                    gdf_q[f'pqpf_{hour}'] = [x for x in src.sample(coords)]
                    result_gdf = pd.concat([result_gdf, gdf_q])
                    logger.info(f'pqpf_{hour}: {rainfall_in} in ---> Done')
            logger.info(utils.done_str)
            return result_gdf

        except Exception as e:
            msg = 'Raster values to points failed.'
            utils.error_process(self.state, msg, e)
        else:
            del gdf
            gc.collect()

    def cmu_mean(self, df, group_col, what_lyr) -> str:
        """
        Calculate each CMU mean value for qppf_24h, pqpf_48h, and pqpf_72h and saves the data in CSV.
            # mean >= 0.9	Very High	5
            # mean >= 0.75	High	    4
            # mean >= 0.5	Moderate	3
            # mean >= 0.25	Low	        2
            # mean < 0.25	Very Low    1
        Args:
            df (DataFrame): Each lease having cmu_name, rain_in, and probabilities.
            group_col (str): CMU name field (e.g. 'cmu_name')
            what_lyr (str): 'cmu' or 'lease'
        Returns (str): CMU probability CSV file path
        """
        logger.info('[Calculate CMU mean values]')
        logger.info(f'{"-"*5} {what_lyr.upper()} {"-"*5}')
        try:
            cat_labels = [5, 4, 3, 2, 1]
            rename_cols = {'pqpf_24h': 'prob_1d_perc', 'pqpf_48h': 'prob_2d_perc', 'pqpf_72h': 'prob_3d_perc'}
            # Delete previous outputs
            utils.delete_files(self.outputs_dir)
            out_csv_path = os.path.join(self.intermediate_outputs_dir, f'pqpf_{what_lyr}_{self.outfile_date}.csv')
            # group_col = [self.config[self.state]['LEASE_SHP_COL_CMU_NAME']]
            metric_cols = ['pqpf_24h', 'pqpf_48h', 'pqpf_72h']
            aggs = df.groupby(group_col)[metric_cols].mean()  # Aggregate by CMU
            aggs.to_csv(os.path.join(self.intermediate_outputs_dir, 'aggs.csv'))

            for key in rename_cols.keys():
                prob_col = aggs[key]
                cond_lst = [prob_col >= 0.9, prob_col >= 0.75, prob_col >= 0.5, prob_col >= 0.25, prob_col < 0.25]
                aggs[key] = np.select(cond_lst, cat_labels)
                aggs = aggs.rename({key: rename_cols[key]}, axis=1)
            aggs.to_csv(out_csv_path)
            logger.info(utils.done_str)
            return out_csv_path

        except Exception as e:
            msg = 'CMU mean process failed.'
            utils.error_process(self.state, msg, e)
        else:
            del aggs
            gc.collect()

    def tiff_resample(self) -> None:
        """
        Resample TIFF file (approximately 25 meters).
        """
        logger.info('[Resample TIFF files]')
        try:
            resample_dir = os.path.join(self.data_root, 'intermediate/resample')
            utils.create_directory(resample_dir, delete=True)
            tiffs = utils.list_files(self.tiffs_dir, '.tif')
            for tiff in tiffs:
                out_fpath = os.path.join(resample_dir, os.path.basename(tiff))
                cmd = ['gdalwarp', '-tr', f'{ct.GRB_RES_X / 100}', f'{ct.GRB_RES_Y / 100}', '-r', 'bilinear',
                       '-dstnodata',
                       '-999', '-overwrite', tiff, out_fpath]
                utils.cmd_subprocess(cmd)
            logger.info(utils.done_str)
        except Exception as e:
            msg = 'Resampling failed.'
            utils.error_process(self.state, msg, e)

    def zonal_statis_to_df(self, shp, tiff) -> Type:
        """
        Args:
            shp (str): Polygon shapefile path
            tiff (str): TIFF raster file path

        Returns (gpd.GeoDataFrame):
        """
        logger.info('[Zonal Stats]')
        try:
            stats = zonal_stats(shp, tiff, geojson_out=True, all_touched=True)
            df = gpd.GeoDataFrame.from_features(stats)
            df = df[[self.config[self.state]['LEASE_SHP_COL_LEASE_ID'], 'mean']]
            return df
        except Exception as e:
            msg = 'Zonal Statistics to DataFrame failed.'
            utils.error_process(self.state, msg, e)

    def zonal_stats_to_csv(self) -> str:
        """
        Save calculated zonal statistics to CSV file. The mean values of zonal statistics are categorized as below.
            # mean >= 0.9	Very High	5
            # mean >= 0.75	High	    4
            # mean >= 0.5	Moderate	3
            # mean >= 0.25	Low	        2
            # mean < 0.25	Very Low    1
        Returns (str): Output CSV file path
        """
        logger.info('[Zonal Statistics to CSV]')
        try:
            resample_dir = os.path.join(self.data_root, 'intermediate/resample')
            tiffs = utils.list_files(resample_dir, '.tif')
            columns = {'24': 'prob_1d_perc', '48': 'prob_2d_perc', '72': 'prob_3d_perc'}
            out_csv_path = os.path.join(self.outputs_dir, f'pqpf_cmu_{self.outfile_date}.csv')
            lease_id_field = self.config[self.state]['LEASE_SHP_COL_LEASE_ID']
            rename_field = self.config[self.state]['LEASE_SHP_COL_CMU_NAME']
            cat_labels = [5, 4, 3, 2, 1]
            dfs = []

            for tiff in tiffs:
                fname = os.path.basename(tiff).split('.')[0]
                match = utils.regex_find(ct.REG_PATTERN_GRB_HOURS, fname)
                if match and len(match) > 0:
                    file_hour = f'{match[0][2:]}'  # e.g. ['f024]
                    hour = str(int(file_hour) + ct.TO_HOUR)
                    probs = columns[hour]
                    logger.info(f'{"-"*10} {hour}-hours {"-"*10}')
                    df = self.zonal_statis_to_df(self.lease_shp, tiff)
                    mean_col = df['mean']
                    cond_lst = [mean_col >= 0.9, mean_col >= 0.75, mean_col >= 0.5, mean_col >= 0.25, mean_col < 0.25]
                    df['mean'] = np.select(cond_lst, cat_labels)
                    df['mean'] = df['mean'].round(0).astype(int)
                    df = df.rename(columns={'mean': probs})
                    dfs.append(df)

            if len(dfs) > 0:
                df_merge = ft.reduce(lambda left, right: pd.merge(left, right, on=lease_id_field), dfs)
                df_merge = df_merge.rename(columns={lease_id_field: rename_field})
                # df_merge = df_merge.sort_values(by=[rename_field], ascending=True)
                df_merge = df_merge.sort_values(rename_field, ascending=True)
                df_merge.to_csv(out_csv_path, index=False)
                logger.info(utils.done_str)
                return out_csv_path
        except Exception as e:
            msg = 'Zonal Statistics to CSV failed.'
            utils.error_process(self.state, msg, e)

    def save_to_db(self, csv_path: str) -> None:
        """
        Saves the data to DB.
        Args:
            csv_path (str): CMU probabilities CSV file path
        """
        logger.info('[Save to DB]')
        try:
            engine = create_engine(self.connect_str)
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, index_col=False)
                if len(df.index) > 0:
                    with engine.connect() as conn:
                        conn.execute('CALL DeleteCmuProbsToday()')
                        df.to_sql('cmu_probabilities', con=conn, if_exists='append', index=False)
                        queryset = conn.execute('CALL SelectCmuProbsToday()')
                        if queryset.rowcount == len(df.index):
                            logger.info(f'{queryset.rowcount} rows added to DB.')
            logger.info(utils.done_str)
        except Exception as e:
            msg = 'Save to DB failed.'
            utils.error_process(self.state, msg, e)

    def db_connection_test(self):
        logger.info('[DB connection test]')
        try:
            engine = sqlalchemy.create_engine(self.connect_str)
            conn = engine.connect()
            tables = conn.execute('SHOW TABLES;')
            # print(tables.all())
            conn.close()
            engine.dispose()
            logger.info(f'{"*"*10} Connected {"*"*10}\n')
        except Exception as e:
            msg = 'DB connection failed.'
            utils.error_process(self.state, msg, e)

    @staticmethod
    def csv_concat(lease_csv_fpath, cmu_csv_fpath, csv_out_fpath):
        """
        Merge lease points' probabilities and the CMU centroid point probabilities where the CMUs
        don't have lease points.
        Args:
            lease_csv_fpath (str): lease probabilities CSV file path
            cmu_csv_fpath (str): CMU probabilities CSV file path
            csv_out_fpath (str): Resulting CSV file path
        """
        logger.info('[Concatenate CSV files]')
        column = 'cmu_name'
        df1 = pd.read_csv(lease_csv_fpath)
        df2 = pd.read_csv(cmu_csv_fpath)
        df3 = df2[~df2.cmu_name.isin(df1.cmu_name)]
        df4 = pd.concat([df1, df3])
        df4 = df4.sort_values(by=[column])
        df4.to_csv(csv_out_fpath, index=False)
        logger.info(utils.done_str)

    def check_grb_files(self):
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

    def nc_main(self) -> None:
        """
        Runs NC PQPF data extraction and save the results in database.
        """
        start = datetime.now()
        self.db_connection_test()
        lyrs = {'lease': [self.lease_shp, self.config[self.state]['LEASE_SHP_COL_CMU_NAME']],
                'cmu': [self.cmu_shp, self.config[self.state]['CMU_SHP_COL_CMU_NAME']]
                }
        csv_fpaths = []

        # Get data
        utils.delete_grbs(self.grb_raw_dir)
        files = self.get_files_to_download()
        self.download_grbs(files)
        to_db_bool = self.check_grb_files()
        csv_out_fpath = os.path.join(self.outputs_dir, f'pqpf_cmu_probs_{self.outfile_date}.csv')
        # Process data
        self.small_grb()
        thresholds = self.get_thresholds()
        self.grb_to_tiff(thresholds)
        for key, vals in lyrs.items():
            df = self.ras_values_to_pts(vals[0], key)
            csv_path = self.cmu_mean(df, vals[1], key)
            csv_fpaths.append(csv_path)
        self.csv_concat(csv_fpaths[0], csv_fpaths[1], csv_out_fpath)

        # Save data to DB
        if to_db_bool:
            self.save_to_db(csv_out_fpath)
        else:
            logger.info(f'Raw GRB files date is not today. {"!"*5} DATA NOT SAVED IN DATABASE {"!"*5}')

        stop = datetime.now()
        utils.calculate_duration(start, stop)

    def sc_main(self) -> None:
        """
        Runs NC PQPF data extraction and save the results in database.
        """
        start = datetime.now()
        self.db_connection_test()
        # Get threshold
        thresholds = [float(self.config[self.state]['THRESHOLD'])]

        # Get data
        utils.delete_grbs(self.grb_raw_dir)
        files = self.get_files_to_download()
        self.download_grbs(files)
        to_db_bool = self.check_grb_files()

        # Process data
        self.small_grb()
        self.grb_to_tiff(thresholds)
        self.tiff_resample()

        # Save data to DB
        csv_path = self.zonal_stats_to_csv()
        if to_db_bool:
            self.save_to_db(csv_path)
        else:
            logger.info(f'Raw GRB files date is not today. {"!"*5} DATA NOT SAVED IN DATABASE {"!"*5}')
        stop = datetime.now()
        utils.calculate_duration(start, stop)

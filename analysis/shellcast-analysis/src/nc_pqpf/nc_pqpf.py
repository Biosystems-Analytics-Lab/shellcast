import os
import logging.config
import warnings
import rasterio
import pandas as pd
import geopandas as gpd
import numpy as np
import constants as ct
from shapely.geometry import Point
from shapely.errors import ShapelyDeprecationWarning
from datetime import datetime
from typing import List, Type
import utils
from pqpf_procs import ProcDirs, PQPFProcs

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

logger = logging.getLogger(__name__)


class NCPQPF:
    def __init__(self, db, save=True):
        self.state = 'NC'
        pqpf_dirs = ProcDirs(self.state, db)
        self.config = pqpf_dirs.config
        self.connect_str = pqpf_dirs.connect_str
        self.inputs_dir = pqpf_dirs.inputs_dir
        self.grb_raw_dir = pqpf_dirs.grb_raw_dir
        self.tiffs_dir = pqpf_dirs.tiffs_dir
        self.lease_shp = pqpf_dirs.lease_shp
        self.outputs_dir = pqpf_dirs.outputs_dir
        self.outfile_date = pqpf_dirs.outfile_date
        self.intermediate_dir = pqpf_dirs.intermediate_dir
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

        self.procs = PQPFProcs(self.state, db)
        self.save = save

    def nc_get_thresholds(self) -> List[float]:
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
            utils.error_process(msg, e)

    def ras_values_to_pts(self, pts_shp, what_lyr):
        """
        --- [ NC ] ---
        Assign PQPF raster values to leases.

        Returns (gpd.GeoDataFrame): DataFrame containing each lease's lease_id, cmu_name, rain_in,
            pqpf_24h, pqpf_48h, pqpf_72h columns with values.
        """
        logger.info('[Get PQPF raster value]')
        logger.info(f'{"-" * 5} {what_lyr.upper()} {"-" * 5}')
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
            utils.error_process(msg, e)

    def cmu_mean(self, df, group_col, what_lyr) -> str:
        """
        --- [ NC ] ---
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
        logger.info(f'{"-" * 5} {what_lyr.upper()} {"-" * 5}')
        try:
            cat_labels = [5, 4, 3, 2, 1]
            rename_cols = {'pqpf_24h': 'prob_1d_perc', 'pqpf_48h': 'prob_2d_perc', 'pqpf_72h': 'prob_3d_perc'}
            # Delete previous outputs
            utils.delete_files(self.outputs_dir)
            out_csv_path = os.path.join(self.intermediate_dir, f'pqpf_{what_lyr}_{self.outfile_date}.csv')
            # group_col = [self.config[self.state]['LEASE_SHP_COL_CMU_NAME']]
            metric_cols = ['pqpf_24h', 'pqpf_48h', 'pqpf_72h']
            aggs = df.groupby(group_col)[metric_cols].mean()  # Aggregate by CMU
            aggs.to_csv(os.path.join(self.intermediate_dir, 'aggs.csv'))

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
            utils.error_process(msg, e)

    @staticmethod
    def csv_concat(lease_csv_fpath, cmu_csv_fpath, csv_out_fpath):
        """
        --- [ NC ] ---
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

    def main(self) -> None:
        """
        Runs NC PQPF data extraction and save the results in database.
        """
        start = datetime.now()
        utils.db_connection_test(self.connect_str)
        lyrs = {'lease': [self.lease_shp, self.config[self.state]['LEASE_SHP_COL_CMU_NAME']],
                'cmu': [self.cmu_shp, self.config[self.state]['CMU_SHP_COL_CMU_NAME']]
                }
        csv_fpaths = []

        # Get data
        utils.delete_outdated_grbs(self.grb_raw_dir)
        files = self.procs.get_files_to_download()
        utils.download_grbs(self.grb_raw_dir, files, ct.PQPF_FTP_URL, ct.PQPF_FTP_CWD)
        to_db_bool = self.procs.check_grb_files()

        # Save data to DB
        if to_db_bool:
            csv_out_fpath = os.path.join(self.outputs_dir, f'pqpf_cmu_probs_{self.outfile_date}.csv')
            # Process data
            self.procs.small_grb()
            thresholds = self.nc_get_thresholds()
            self.procs.grb_to_tiff(thresholds)
            for key, vals in lyrs.items():
                df = self.ras_values_to_pts(vals[0], key)
                csv_path = self.cmu_mean(df, vals[1], key)
                csv_fpaths.append(csv_path)
            self.csv_concat(csv_fpaths[0], csv_fpaths[1], csv_out_fpath)
            if self.save:
                utils.save_to_db(self.connect_str, csv_out_fpath)
        else:
            logger.info(f'Raw GRB files date is not today. {"!" * 5} DATA NOT SAVED IN DATABASE {"!" * 5}')

        stop = datetime.now()
        utils.calculate_duration(start, stop)

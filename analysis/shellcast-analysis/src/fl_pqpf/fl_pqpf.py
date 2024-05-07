import os
import logging.config
import warnings
import rasterio
import pandas as pd
import geopandas as gpd
import numpy as np
import math
from shapely.geometry import Point
from shapely.errors import ShapelyDeprecationWarning
from datetime import datetime
import utils
from pqpf_procs import ProcDirs, PQPFProcs
import constants as ct

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

logger = logging.getLogger(__name__)

# FL Field names
TP_ACCUM = 'tp_accum'  # Total precipitation accumulation in hours (e.g. 1 day = 24 hours, 2 days = 48 hours etc.)
TP_CALC = 'dth_minus_tpa'  # Days rainfall threshold in inches - tp_accum
PQPF_TH = 'pqpf_threshold'  # Find applicable PQPF threshold based on TP_CALC
PQPF_PROC = 'pqpf_proc_val'  # PQPF probability
PQPF_CAT = 'prob_1d_perc'


def fl_qppf_threshold_generator(tp_accum):
    if tp_accum == 0:
        return 0
    elif 0 < tp_accum <= 0.2:
        return 0.2
    elif 0.2 < tp_accum <= 0.5:
        return 0.5
    elif 0.5 < tp_accum <= 1:
        return 1
    elif 1 < tp_accum <= 1.5:
        return 1.5
    elif 1.5 < tp_accum <= 2:
        return 2.0
    elif 2 < tp_accum <= 2.5:
        return 2.5
    elif 2.5 < tp_accum <= 3:
        return 3
    elif 3 < tp_accum <= 4:
        return 4
    elif 4 < tp_accum <= 5:
        return 5
    elif 5 < tp_accum <= 6:
        return 6
    elif 6 < tp_accum <= 8:
        return 8
    elif 8 < tp_accum:
        return 16


def pqpf_threshold_stringify(num):
    # if not Decimal(str(num)).as_integer_ratio()[1] == 1:
    if float(num):
        str_pqpf_threshold = str(num).replace('.', 'p')
        return str_pqpf_threshold


class FLPQPF:
    def __init__(self, db, save=True):
        self.state = 'FL'
        pqpf_dirs = ProcDirs(self.state, db)
        self.config = pqpf_dirs.config
        self.fl_config = self.config[self.state]
        self.connect_str = pqpf_dirs.connect_str
        self.grb_raw_dir = pqpf_dirs.grb_raw_dir
        self.tiffs_dir = pqpf_dirs.tiffs_dir
        self.lease_shp = pqpf_dirs.lease_shp
        self.outputs_dir = pqpf_dirs.outputs_dir
        self.outfile_date = pqpf_dirs.outfile_date

        # ----- Total precipitation 1 hour accumulation directories -----
        self.tp_data_dir = os.path.join(ct.TP_DATA_DIR, self.state.lower())
        self.tp_raw_dir = os.path.join(self.tp_data_dir, 'raw')
        self.tp_intermediate_dir = utils.create_directory(os.path.join(self.tp_data_dir, 'intermediate'), delete=True)
        self.convert_to_grib2_dir = utils.create_directory(os.path.join(self.tp_intermediate_dir, 'cnvgrib2'),
                                                           delete=True)
        self.tp_procs_dir = utils.create_directory(os.path.join(self.tp_intermediate_dir, 'procs'), delete=True)
        self.tp_outputs_dir = utils.create_directory(os.path.join(self.tp_data_dir, 'outputs'))

        self.procs = PQPFProcs(self.state, db)
        self.save = save

    def tp_accum_ras_values_to_pts(self):
        """
        Steps:
        1. Get TP accumulation value from tp_{hours}h.tif.
        2. Calculate SHA rainfall threshold minus Step 1.
        3. Get PQPF threshold based on Step 2.

        Returns:
        """
        logger.info('[Process A]')
        gdf = gpd.read_file(self.lease_shp)
        gdf['days'] = gdf['days'].astype('int')  # Convert to int
        gdf['rain_in'] = gdf['rain_in'].astype('float')  # Convert to float
        # df = pd.read_csv(os.path.join(os.path.dirname(self.lease_shp), 'fl_individual_leases_and_auz_pts.csv'))
        uni_days = sorted(gdf['days'].unique())  # List[int]
        tp_tiffs = utils.list_files(self.tp_outputs_dir, 'tif')  # [path to tp_24h.tif, path to tp_48h.tif, ...]

        result_gdf = gpd.GeoDataFrame()
        for day in uni_days:
            gdf_q = gdf.query(f'days == {day}').copy()
            coords = [(Point(i).x, Point(i).y) for i in gdf_q.geometry]

            if day == 1:  # Day 1 means we need only pqpf forecasting value
                gdf_q[TP_ACCUM] = 0
            if 1 < day < 8:
                # Subtract one for pqpf forecasting value to obtain later
                hours = (day - 1) * 24
                logger.info(f'{day} - {hours}')
                for tp_tiff in tp_tiffs:
                    if tp_tiff.endswith(f'_{hours}h.tif'):
                        tp_tiff_fname = os.path.basename(tp_tiff)
                        src = rasterio.open(tp_tiff)
                        gdf_q[TP_ACCUM] = [x[0] for x in src.sample(coords)]
                        logger.info(f'{tp_tiff_fname} --- raster values to points')

            result_gdf = pd.concat([result_gdf, gdf_q])
        # result_gdf[TP_CALC] = round(result_gdf[self.fl_config['LEASE_SHP_COL_RAIN_IN']].astype('float') - result_gdf[
        #     TP_ACCUM], 1)
        result_gdf[TP_CALC] = result_gdf[self.fl_config['LEASE_SHP_COL_RAIN_IN']].astype('float') - result_gdf[
            TP_ACCUM]
        logger.info(f'[rain_in - raster value at point] --- calculated')
        result_gdf[PQPF_TH] = result_gdf[TP_CALC].apply(fl_qppf_threshold_generator)
        logger.info(f'PQPF threshold --- assigned')
        # result_gdf.dropna(subset=[TP_CALC], inplace=True)
        logger.info(utils.done_str)
        return result_gdf

    def pqpf_ras_values_to_pts(self, df):
        """
        Steps:
        1. Set PQPF value to 1 where Process A's TP_CALC is negative.
        2. Get rest of PQPF values of Process A's PQPF_TH
        Args:
            df:

        Returns:

        """
        logger.info('[Process B]')
        # gdf = gpd.read_file(self.lease_shp)
        # result_gdf = gpd.GeoDataFrame()
        thresholds = sorted(list(df[PQPF_TH].drop_duplicates()))
        # thresholds = sorted(list(df[PQPF_TH].unique()))
        pqpf_tiffs = utils.list_files(self.tiffs_dir, 'tif')
        df_to_concat = []

        # Step 1
        df.loc[df[TP_CALC] < 0, PQPF_PROC] = 1
        dfq = df.query(f'{TP_CALC} < 0').copy()
        if len(dfq.index) > 0:
            df_to_concat.append(dfq)
        logger.info(f'{len(dfq.index)} has negative value --- set to 1')

        # Step 2
        for threshold in thresholds:
            if not math.isnan(threshold):
                str_num = pqpf_threshold_stringify(threshold)
                for pqpf_tiff in pqpf_tiffs:
                    if pqpf_tiff.endswith(f'{str_num}.tif'):
                        src = rasterio.open(pqpf_tiff)
                        gdf_q = df.query(f'{PQPF_TH} == {threshold}').copy()
                        coords = [(Point(i).x, Point(i).y) for i in gdf_q.geometry]
                        gdf_q[PQPF_PROC] = [x[0] for x in src.sample(coords)]
                        if len(gdf_q.index) > 0:
                            df_to_concat.append(gdf_q)
                            logger.info(f'{len(gdf_q.index)} rows from {os.path.basename(pqpf_tiff)}({threshold})')
                        # result_gdf = pd.concat([result_gdf, gdf_q])
        if len(df_to_concat) > 0:
            result_gdf = gpd.GeoDataFrame(pd.concat(df_to_concat, ignore_index=True))
            # result_gdf.loc[result_gdf[TP_CALC] < 0, PQPF_PROC] = 1
            logger.info(utils.done_str)
            return result_gdf

    def cmu_mean(self, df, csv_out_fpath):
        logger.info('[Categorize PQPF value group by CMU]')
        s_arr = df.groupby(['cmu_name'])['pqpf_proc_val'].mean()
        new_df = pd.DataFrame(s_arr).reset_index()
        vals = new_df[PQPF_PROC]
        condition_lst = [vals >= 0.9, vals >= 0.75, vals >= 0.5, vals >= 0.25, vals < 0.25]
        cat_labels = [5, 4, 3, 2, 1]
        new_df[PQPF_CAT] = np.select(condition_lst, cat_labels)
        new_df[PQPF_CAT] = new_df[PQPF_CAT].round(0).astype(int)
        new_df = new_df.drop([PQPF_PROC], axis=1)
        new_df.to_csv(csv_out_fpath, index=False)

    def pqpf_probability_into_category(self, df, out_csv_path):
        """
        #  >= 0.9	Very High	5
        #  >= 0.75	High	    4
        #  >= 0.5	Moderate	3
        #  >= 0.25	Low	        2
        #  < 0.25	Very Low    1

        Returns:

        """
        logger.info('[Categorize PQPF value group by lease]')
        del df['geometry']
        vals = df[PQPF_PROC]
        condition_lst = [vals >= 0.9, vals >= 0.75, vals >= 0.5, vals >= 0.25, vals < 0.25]
        cat_labels = [5, 4, 3, 2, 1]
        df[PQPF_CAT] = np.select(condition_lst, cat_labels)
        df[PQPF_CAT] = df[PQPF_CAT].round(0).astype(int)
        df.to_csv(out_csv_path, index=False)
        logger.info(f'{os.path.basename(out_csv_path)} --- created')
        logger.info(utils.done_str)

    def main(self):
        start = datetime.now()
        utils.db_connection_test(self.connect_str)
        utils.delete_outdated_grbs(self.grb_raw_dir)
        files = self.procs.get_files_to_download()
        utils.download_grbs(self.grb_raw_dir, files, ct.PQPF_FTP_URL, ct.PQPF_FTP_CWD)
        to_db_bool = self.procs.check_grb_files()

        if to_db_bool:
            csv_lease_fpath = os.path.join(self.outputs_dir, f'pqpf_lease_probs_{self.outfile_date}.csv')
            csv_cmu_fpath = os.path.join(self.outputs_dir, f'pqpf_cmu_probs_{self.outfile_date}.csv')

            # Process data
            self.procs.small_grb()
            self.procs.grb_to_tiff_all()
            accum_df = self.tp_accum_ras_values_to_pts()
            pqpf_df = self.pqpf_ras_values_to_pts(accum_df)
            self.pqpf_probability_into_category(pqpf_df, csv_lease_fpath)
            self.cmu_mean(pqpf_df, csv_cmu_fpath)

            if self.save:
                utils.save_to_db(self.connect_str, csv_cmu_fpath)

        stop = datetime.now()
        utils.calculate_duration(start, stop)

# if __name__ == '__main__':
#     db = 'gcp.mysql'
#     pqpf = FLPQPF(db)
#     pqpf.main()

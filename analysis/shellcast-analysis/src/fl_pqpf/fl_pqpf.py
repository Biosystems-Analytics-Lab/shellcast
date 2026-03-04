import csv
import logging.config
import math
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path

import constants as ct
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import utils
from pqpf_procs import PQPFProcs
from shapely.errors import ShapelyDeprecationWarning
from shapely.geometry import Point

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

logger = logging.getLogger(__name__)

# FL Field names
TP_ACCUM = "tp_accum"  # Total precipitation accumulation in hours (e.g., 1 day = 24 hours, 2 days = 48 hours etc.)
TP_CALC = "dth_minus_tpa"  # Days rainfall threshold in inches - tp_accum
PQPF_TH = "pqpf_threshold"  # Find the applicable PQPF threshold based on TP_CALC
PQPF_PROC = "pqpf_proc_val"  # PQPF probability
PQPF_CAT = "prob_1d_perc"


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
        str_pqpf_threshold = str(num).replace(".", "p")
        return str_pqpf_threshold


class FLPQPF:
    def __init__(self, config_dirs):
        self.state = "FL"
        self.config = config_dirs.config
        self.fl_config = self.config[self.state]
        self.connect_str = config_dirs.connect_str
        self.grb_raw_dir = config_dirs.grb_raw_dir
        self.tiffs_dir = config_dirs.tiffs_dir
        self.lease_shp = config_dirs.lease_shp
        self.intermediate_dir = config_dirs.intermediate_dir
        self.outputs_dir = config_dirs.outputs_dir
        self.date_today = config_dirs.date_today

        # ----- Total precipitation 1 hour accumulation directories -----
        logger.info(f"TP_DATA_DIR: {ct.TP_DATA_DIR}")
        self.tp_data_dir = os.path.join(ct.TP_DATA_DIR, self.state.lower())
        logger.info(f"tp_data_dir: {self.tp_data_dir}")
        self.tp_raw_dir = os.path.join(ct.TP_DATA_DIR, "raw")
        logger.info(f"tp_raw_dir: {self.tp_raw_dir}")
        self.tp_intermediate_dir = utils.create_directory(
            os.path.join(ct.TP_DATA_DIR, self.state.lower(), "intermediate"),
            delete=True,
        )
        logger.info(f"tp_intermediate_dir: {self.tp_intermediate_dir}")
        self.convert_to_grib2_dir = utils.create_directory(
            os.path.join(self.tp_intermediate_dir, "cnvgrib2"), delete=True
        )
        logger.info(f"convert_to_grib2_dir: {self.convert_to_grib2_dir}")
        self.tp_procs_dir = utils.create_directory(
            os.path.join(self.tp_intermediate_dir, "procs"), delete=True
        )
        logger.info(f"tp_procs_dir: {self.tp_procs_dir}")
        self.tp_outputs_dir = utils.create_directory(
            os.path.join(ct.TP_DATA_DIR, self.state.lower(), "outputs")
        )
        logger.info(f"tp_outputs_dir: {self.tp_outputs_dir}")

        self.procs = PQPFProcs(config_dirs)
        # Use config value if save parameter is None, otherwise use the provided value
        self.save = self.config[f"{self.state}.SaveToDB"].getboolean("SAVE_TO_DB")

    def tp_accum_ras_values_to_pts(self):
        """
        Steps:
        1. Get TP accumulation value from tp_{hours}h.tif.
        2. Calculate SHA rainfall thresholds minus Step 1.
        3. Get a PQPF threshold based on Step 2.

        Returns:
        """
        logger.info("[Process A]")
        gdf = gpd.read_file(self.lease_shp)
        gdf["days"] = gdf["days"].astype("int")  # Convert to int
        gdf["rain_in"] = gdf["rain_in"].astype("float")  # Convert to float
        # df = pd.read_csv(os.path.join(os.path.dirname(self.lease_shp), 'fl_individual_leases_and_auz_pts.csv'))
        uni_days = sorted(gdf["days"].unique())  # List[int]
        tp_tiffs = utils.list_files(
            self.tp_outputs_dir, "tif"
        )  # [path to tp_24h.tif, path to tp_48h.tif, ...]

        result_gdf = gpd.GeoDataFrame()
        for day in uni_days:
            gdf_q = gdf.query(f"days == {day}").copy()
            coords = [(Point(i).x, Point(i).y) for i in gdf_q.geometry]

            if day == 1:  # Day 1 means we need only pqpf forecasting value
                gdf_q[TP_ACCUM] = 0
            if 1 < day < 8:
                # Subtract one for pqpf forecasting value to obtain later
                hours = (day - 1) * 24
                logger.info(f"{day} - {hours}")
                for tp_tiff in tp_tiffs:
                    if tp_tiff.endswith(f"_{hours}h.tif"):
                        tp_tiff_fname = os.path.basename(tp_tiff)
                        src = rasterio.open(tp_tiff)
                        gdf_q[TP_ACCUM] = [x[0] for x in src.sample(coords)]
                        logger.info(f"{tp_tiff_fname} --- raster values to points")

            result_gdf = pd.concat([result_gdf, gdf_q])
        # result_gdf[TP_CALC] = round(result_gdf[self.fl_config['LEASE_SHP_COL_RAIN_IN']].astype('float') - result_gdf[
        #     TP_ACCUM], 1)
        result_gdf[TP_CALC] = (
            result_gdf[self.fl_config["LEASE_SHP_COL_RAIN_IN"]].astype("float")
            - result_gdf[TP_ACCUM]
        )
        logger.info("[rain_in - raster value at point] --- calculated")
        result_gdf[PQPF_TH] = result_gdf[TP_CALC].apply(fl_qppf_threshold_generator)
        logger.info("PQPF threshold --- assigned")
        logger.info(utils.done_str)
        return result_gdf

    def pqpf_ras_values_to_pts(self, df):
        """
        Steps:
        1. Set PQPF value to 1 where Process A's TP_CALC is negative.
        2. Get the rest of PQPF values of Process A's PQPF_TH
        Args:
            df (DataFrame): DataFrame from Process A

        Returns:
            DataFrame:

        """
        logger.info("[Process B]")
        # gdf = gpd.read_file(self.lease_shp)
        # result_gdf = gpd.GeoDataFrame()
        thresholds = sorted(list(df[PQPF_TH].drop_duplicates()))
        # thresholds = sorted(list(df[PQPF_TH].unique()))
        pqpf_tiffs = utils.list_files(self.tiffs_dir, "tif")
        df_to_concat = []

        # Step 1
        df.loc[df[TP_CALC] < 0, PQPF_PROC] = 1
        dfq = df.query(f"{TP_CALC} < 0").copy()
        if len(dfq.index) > 0:
            df_to_concat.append(dfq)
        logger.info(f"{len(dfq.index)} has negative value --- set to 1")

        # Step 2
        for threshold in thresholds:
            if not math.isnan(threshold):
                str_num = pqpf_threshold_stringify(threshold)
                for pqpf_tiff in pqpf_tiffs:
                    if pqpf_tiff.endswith(f"{str_num}.tif"):
                        src = rasterio.open(pqpf_tiff)
                        gdf_q = df.query(f"{PQPF_TH} == {threshold}").copy()
                        coords = [(Point(i).x, Point(i).y) for i in gdf_q.geometry]
                        gdf_q[PQPF_PROC] = [x[0] for x in src.sample(coords)]
                        if len(gdf_q.index) > 0:
                            df_to_concat.append(gdf_q)
                            logger.info(
                                f"{len(gdf_q.index)} rows from {os.path.basename(pqpf_tiff)}({threshold})"
                            )
                        # result_gdf = pd.concat([result_gdf, gdf_q])
        if len(df_to_concat) > 0:
            result_gdf = gpd.GeoDataFrame(pd.concat(df_to_concat, ignore_index=True))
            # result_gdf.loc[result_gdf[TP_CALC] < 0, PQPF_PROC] = 1
            logger.info(utils.done_str)
            return result_gdf

    @staticmethod
    def pqpf_probability_into_category(df, out_csv_path):
        """
        >= 0.9     Very High	5
        >= 0.75	High	    4
        >= 0.5	    Moderate	3
        >= 0.25    Low	        2
        < 0.25	    Very Low    1

        """
        logger.info("[Categorize PQPF value group by lease]")
        del df["geometry"]
        condition_lst = utils.set_conditions_list(df[PQPF_PROC])
        df[PQPF_CAT] = np.select(condition_lst, ct.CATEGORY_LABELS)
        df[PQPF_CAT] = df[PQPF_CAT].round(0).astype(int)
        df.to_csv(out_csv_path, index=False)
        logger.info(f"{os.path.basename(out_csv_path)} --- created")
        logger.info(utils.done_str)

    def cmu_mean(self, df, csv_out_fpath):
        logger.info("[Categorize PQPF value group by CMU]")
        df = df.rename(columns={self.fl_config["LEASE_SHP_COL_CMU_NAME"]: "cmu_id"})
        s_arr = df.groupby(["cmu_id"])[PQPF_PROC].mean()
        new_df = pd.DataFrame(s_arr).reset_index()
        condition_lst = utils.set_conditions_list(new_df[PQPF_PROC])
        new_df[PQPF_CAT] = np.select(condition_lst, ct.CATEGORY_LABELS)
        new_df[PQPF_CAT] = new_df[PQPF_CAT].round(0).astype(int)
        new_df = new_df.drop([PQPF_PROC], axis=1)
        season_df = df[["cmu_id", "season"]].drop_duplicates()
        joined_df = new_df.join(season_df.set_index("cmu_id"), on="cmu_id")
        joined_df.to_csv(csv_out_fpath, index=False)

    def check_tp_outputs(self):
        logger.info(f"Checking TP outputs in: {self.tp_outputs_dir}")
        if os.path.exists(self.tp_outputs_dir):
            logger.info(f"Contents of directory: {os.listdir(self.tp_outputs_dir)}")
        tiffs = list(map(str, Path(self.tp_outputs_dir).glob("*.tif")))
        logger.info(f"Found TIFF files: {len(tiffs)}")
        if len(tiffs) == 0:
            logger.error("No TP outputs found")
            sys.exit(1)
        else:
            logger.info(f"Found {len(tiffs)} TIFF files")
        return True

    def get_season_now(self, in_csv_fpath, out_csv_fpath):
        """
        Create CSV file that contains cmu_id and prob_1d_perc columns based on the
        season.
        Args:
            in_csv_fpath (str): Input CSV file path (all)
            out_csv_fpath (str): Output CSV file path (only in season)-this is the
                final output file, and this data will be saved to the database.

        """
        columns = ["cmu_id", "prob_1d_perc"]
        with open(in_csv_fpath, "r") as rf:
            reader = csv.reader(rf)
            next(reader)
            with open(out_csv_fpath, "w", newline="") as wf:
                writer = csv.writer(wf)
                writer.writerow(columns)
                for row in reader:
                    flag = False
                    # e.g 1/1-12/31 or multiple like 4/1-6/30, 9/1-11/30
                    dt_str_lst = row[2].strip("[]").split(", ")
                    if dt_str_lst and len(dt_str_lst) > 0:
                        for dt_str in dt_str_lst:
                            dates = utils.convert_date_string(dt_str)
                            if utils.is_season(
                                self.date_today, dates["start"], dates["end"]
                            ):
                                flag = True
                                break
                    # cmu_id, prob_1d_perc, if not in season, assign 100
                    writer.writerow([row[0], row[1]] if flag else [row[0], 100])

    def main(self):
        start = datetime.now()
        has_data = self.check_tp_outputs()
        if not has_data:
            logger.error("No TP outputs found")
            sys.exit(1)
        utils.db_connection_test(self.connect_str)
        self.procs.get_input_files()
        utils.delete_outdated_grbs(self.grb_raw_dir)
        file_list = self.procs.get_files_to_download()
        utils.download_grbs(
            self.grb_raw_dir, file_list, ct.PQPF_FTP_URL, ct.PQPF_FTP_CWD
        )
        to_db_bool = self.procs.check_grb_files()

        if to_db_bool:
            date_str = self.date_today.strftime("%Y-%m-%d")
            csv_lease_fpath = os.path.join(
                self.outputs_dir, f"pqpf_lease_probs_season{date_str}.csv"
            )
            csv_cmu_tmp_fpath = os.path.join(
                self.outputs_dir, f"pqpf_cmu_probs_tmp_{date_str}.csv"
            )
            csv_cmu_fpath = os.path.join(
                self.outputs_dir, f"pqpf_cmu_probs_{date_str}.csv"
            )

            # Process data
            self.procs.small_grb()
            self.procs.grb_to_tiff_all()
            accum_df = self.tp_accum_ras_values_to_pts()
            pqpf_df = self.pqpf_ras_values_to_pts(accum_df)
            self.pqpf_probability_into_category(pqpf_df, csv_lease_fpath)
            self.cmu_mean(pqpf_df, csv_cmu_tmp_fpath)
            self.get_season_now(csv_cmu_tmp_fpath, csv_cmu_fpath)
            if self.save:
                utils.save_to_db(self.connect_str, csv_cmu_fpath)

        stop = datetime.now()
        utils.calculate_duration(start, stop)


# if __name__ == '__main__':
#     db = 'gcp.mysql'
#     pqpf = FLPQPF(db, save=False)
#     pqpf.main()

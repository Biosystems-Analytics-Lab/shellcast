import functools as ft
import logging.config
import os
import warnings
from datetime import datetime

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterstats import zonal_stats
from shapely.errors import ShapelyDeprecationWarning

import constants as ct
import utils
from pqpf_procs import PQPFProcs

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

logger = logging.getLogger(__name__)


class SCPQPF:
    def __init__(self, config_dirs, save=True):
        self.state = "SC"
        self.config = config_dirs.config
        self.connect_str = config_dirs.connect_str
        self.outfile_date = config_dirs.outfile_date
        self.data_root = config_dirs.data_root
        self.grb_raw_dir = config_dirs.grb_raw_dir
        self.tiffs_dir = config_dirs.tiffs_dir
        self.lease_shp = config_dirs.lease_shp
        self.outputs_dir = config_dirs.outputs_dir
        self.outfile_date = config_dirs.date_today.strftime("%Y-%m-%d")
        self.use_cols = [self.config[self.state]["LEASE_SHP_COL_LEASE_ID"], "geometry"]
        self.procs = PQPFProcs(config_dirs)
        self.save = save

    def tiff_resample(self) -> None:
        """
        --- [ SC ] ---
        Resample TIFF file (approximately 25 meters).
        """
        logger.info("[Resample TIFF files]")
        try:
            resample_dir = os.path.join(self.data_root, "intermediate/resample")
            utils.create_directory(resample_dir, delete=True)
            tiffs = utils.list_files(self.tiffs_dir, ".tif")
            for tiff in tiffs:
                out_fpath = os.path.join(resample_dir, f"rs_{os.path.basename(tiff)}")
                xres = ct.GRB_RES_X / 100
                yres = ct.GRB_RES_Y / 100
                utils.run_gdal_resample(tiff, out_fpath, xres, yres, "-999")
                # cmd = [gdalwarp, '-tr', f'{ct.GRB_RES_X / 100}', f'{ct.GRB_RES_Y / 100}', '-r', 'bilinear',
                #        '-dstnodata',
                #        '-999', '-overwrite', tiff, out_fpath]
                # utils.cmd_subprocess(cmd)
            logger.info(utils.done_str)
        except Exception as e:
            msg = "Resampling failed."
            utils.error_process(msg, e)

    def zonal_statis_to_df(self, shp, tiff):
        """
        --- [ SC ] ---
        Args:
            shp (str): Polygon shapefile path
            tiff (str): TIFF raster file path

        Returns (gpd.GeoDataFrame):
        """
        logger.info("[Zonal Stats]")
        try:
            stats = zonal_stats(shp, tiff, geojson_out=True, all_touched=True)
            df = gpd.GeoDataFrame.from_features(stats)
            df = df[[self.config[self.state]["LEASE_SHP_COL_LEASE_ID"], "mean"]]
            return df
        except Exception as e:
            msg = "Zonal Statistics to DataFrame failed."
            utils.error_process(msg, e)

    def zonal_stats_to_csv(self):
        """
        --- [ SC ] ---
        Save calculated zonal statistics to CSV file. The mean values of zonal statistics are categorized as below.
            # mean >= 0.9	Very High	5
            # mean >= 0.75	High	    4
            # mean >= 0.5	Moderate	3
            # mean >= 0.25	Low	        2
            # mean < 0.25	Very Low    1
        Returns (str): Output CSV file path
        """
        logger.info("[Zonal Statistics to CSV]")
        try:
            resample_dir = os.path.join(self.data_root, "intermediate/resample")
            tiffs = utils.list_files(resample_dir, ".tif")
            columns = {"24": "prob_1d_perc", "48": "prob_2d_perc", "72": "prob_3d_perc"}
            out_csv_path = os.path.join(
                self.outputs_dir, f"pqpf_cmu_{self.outfile_date}.csv"
            )
            lease_id_field = self.config[self.state]["LEASE_SHP_COL_LEASE_ID"]
            rename_field = self.config[self.state]["LEASE_SHP_COL_CMU_NAME"]
            cat_labels = [5, 4, 3, 2, 1]
            dfs = []

            for tiff in tiffs:
                fname = os.path.basename(tiff).split(".")[0]
                match = utils.regex_find(ct.REG_PATTERN_GRB_HOURS, fname)
                if match and len(match) > 0:
                    file_hour = f"{match[0][2:]}"  # e.g. ['f024]
                    hour = str(int(file_hour) + ct.TO_HOUR)
                    probs = columns[hour]
                    logger.info(f"{'-' * 10} {hour}-hours {'-' * 10}")
                    df = self.zonal_statis_to_df(self.lease_shp, tiff)
                    mean_col = df["mean"]
                    cond_lst = [
                        mean_col >= 0.9,
                        mean_col >= 0.75,
                        mean_col >= 0.5,
                        mean_col >= 0.25,
                        mean_col < 0.25,
                    ]
                    df["mean"] = np.select(cond_lst, cat_labels)
                    df["mean"] = df["mean"].round(0).astype(int)
                    df = df.rename(columns={"mean": probs})
                    dfs.append(df)

            if len(dfs) > 0:
                df_merge = ft.reduce(
                    lambda left, right: pd.merge(left, right, on=lease_id_field), dfs
                )
                df_merge = df_merge.rename(columns={lease_id_field: rename_field})
                # df_merge = df_merge.sort_values(by=[rename_field], ascending=True)
                df_merge = df_merge.sort_values(rename_field, ascending=True)
                df_merge.to_csv(out_csv_path, index=False)
                logger.info(utils.done_str)
                return out_csv_path
        except Exception as e:
            msg = "Zonal Statistics to CSV failed."
            utils.error_process(msg, e)

    def main(self) -> None:
        """
        Runs SC PQPF data extraction and save the results in a database.
        """
        start = datetime.now()
        utils.db_connection_test(self.connect_str)
        # Get hresholds
        thresholds = [float(self.config[self.state]["THRESHOLD"])]

        # Get data
        utils.delete_outdated_grbs(self.grb_raw_dir)
        files = self.procs.get_files_to_download()
        utils.download_grbs(self.grb_raw_dir, files, ct.PQPF_FTP_URL, ct.PQPF_FTP_CWD)
        to_db_bool = self.procs.check_grb_files()

        if to_db_bool:
            # Process data
            self.procs.small_grb()
            self.procs.grb_to_tiff(thresholds)
            self.tiff_resample()
            csv_path = self.zonal_stats_to_csv()
            if self.save:
                utils.save_to_db(self.connect_str, csv_path)
        else:
            logger.info(
                f"Raw GRB files date is not today. {'!' * 5} DATA NOT SAVED IN DATABASE {'!' * 5}"
            )
        stop = datetime.now()
        utils.calculate_duration(start, stop)

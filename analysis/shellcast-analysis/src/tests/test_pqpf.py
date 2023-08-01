

import unittest
import os
from tempfile import TemporaryDirectory
from pqpf import pqpf
from ..constants import TODAY, REG_PATTERN_TODAY, REG_PATTERN_GRB_HOURS
from datetime import datetime

class TestPqpf(unittest.TestCase):
    def setUp(self) -> None:
        self.pqpf_obj = pqpf.PQPF('NC', 'docker.mysql')

    def test_regex_find(self):
        fname = f'pqpf_p24i_conus_12f024.grb'
        print(pqpf.regex_find(REG_PATTERN_TODAY, fname))
        match_today = pqpf.regex_find(REG_PATTERN_TODAY, fname)[0]
        match_hours = pqpf.regex_find(REG_PATTERN_GRB_HOURS, fname)[0]

        self.assertEqual(match_today, TODAY)
        self.assertEqual(match_hours, 'f024')

    def test_list_grbs_today(self):
        """Test all files are today's GRB files """
        grbs = ['pqpf_p24i_conus_2022120112f024.grb', 'pqpf_p24i_conus_2022120112f048.grb', 'pqpf_p24i_conus_2022120112f072.grb']
        with TemporaryDirectory() as temp_dir:
            for grb in grbs:
                open(os.path.join(temp_dir, grb), 'w').close()
            # print(os.listdir(temp_dir))
            results = pqpf.list_grbs_not_today(temp_dir)
            # print(results)
            self.assertEqual(len(results), 0)

    def test_list_grbs_not_today_no_grb(self):
        """Test old files and other extensions """
        grbs = [
            'pqpf_p24i_conus_2022113012f024.grb',
            'pqpf_p24i_conus_2022113012f048.grb',
            'pqpf_p24i_conus_2022113012f072.grb',
            'pqpf_p24i_conus_2022113012f072.xml',
            'pqpf_p24i_conus_2022113012f072.txt',
            'pqpf_p24i_conus_2022120112f024.grb',
            'pqpf_p24i_conus_2022120112f048.grb',
            'pqpf_p24i_conus_2022120112f072.grb'
        ]
        with TemporaryDirectory() as temp_dir:
            # Create directory
            for grb in grbs:
                open(os.path.join(temp_dir, grb), 'w').close()
            # print(os.listdir(temp_dir))
            results = pqpf.list_grbs_not_today(temp_dir)
            # print(results)
            self.assertEqual(len(results), 5)

    def test_files_to_download(self):
        files = self.pqpf_obj.files_to_download()
        self.assertEqual(len(files), 3)

    def test_download_grbs(self):
        grbs_to_download = self.pqpf_obj.files_to_download()
        self.pqpf_obj.download_grbs(grbs_to_download)
        files = os.listdir(self.pqpf_obj.grb_raw_dir)
        downloaded = []
        for f in files:
            if f.endswith('grb'):
                downloaded.append(f)
        self.assertEqual(grbs_to_download, downloaded)

    def test_small_grb(self):
        self.pqpf_obj.small_grb()
        self.assertEqual(len(os.listdir(self.pqpf_obj.grb_subsets_dir)), 3)

    def test_get_thresholds(self):
        thresholds = self.pqpf_obj.get_thresholds()
        self.assertTrue(len(thresholds) > 0)

    def test_grb_to_tiff(self):
        thresholds = self.pqpf_obj.get_thresholds()
        thresholds.remove(0)
        self.pqpf_obj.grb_to_tiff(thresholds)
        tiff_cnt = 3 * len(thresholds)
        tiffs = len(os.listdir(self.pqpf_obj.tiffs_dir))
        self.assertEqual(tiff_cnt, tiffs)

    def test_ras_values_to_pts(self):
        df = self.pqpf_obj.ras_values_to_pts()
        print(df.head())

    def test_cmu_mean(self):
        df = self.pqpf_obj.ras_values_to_pts()
        csv_path = self.pqpf_obj.cmu_mean(df)
        self.assertTrue(os.path.exists(csv_path))

    def test_save_to_db(self):
        out_csv_path = os.path.join(self.pqpf_obj.outputs_dir, f'pqpf_cmu_{datetime.today().date()}.csv')
        self.pqpf_obj.save_to_db(out_csv_path)


if __name__ == '__main__':
    unittest.main()

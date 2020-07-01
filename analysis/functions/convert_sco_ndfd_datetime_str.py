"""
# ---- script header ----
script name: convert_sco_ndfd_datetime_str.py
purpose of script: reformats string in datetime format to different time formats
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200427

required librariess: none
required functions: none

"""
def convert_sco_ndfd_datetime_str(datetime_str):
    """
    Description: Takes string of format "%Y-%m-%d %H:%M" and converts it to the "%Y%m%d%H", "%Y%m%d", and "%Y%m" formats
    Parameters:
        datetime_str (str): A string in "%Y-%m-%d %H:%M" format (e.g., "2016-01-01 00:00")
    Returns:
        datetime_ym_str (str): A string in "%Y%m" format (e.g, "201601")
        datetime_ymd_str (str): A string in "%Y%m%d" format (e.g, "20160101")
        datetime_ymdh_str (str): A string in "%Y%m%d%H" format (e.g, "2016010100")

    """
    date_str, time_str = datetime_str.split()
    year_str, month_str, day_str = date_str.split("-")
    hour_str, sec_str = time_str.split(":")

    # define datetime combinations
    datetime_ym_str = year_str + month_str
    datetime_ymd_str = year_str + month_str + day_str
    datetime_ymdh_str = year_str + month_str + day_str + hour_str

    return datetime_ym_str, datetime_ymd_str, datetime_ymdh_str

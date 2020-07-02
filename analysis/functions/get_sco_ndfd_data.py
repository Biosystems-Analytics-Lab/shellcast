"""
# ---- script header ----
script name: get_sco_ndfd_data.py
purpose of script: returns a dataframe of sco ndfd data for a specified datetime
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200427

required libraries & functions: pydap, requests
required functions: convert_sco_ndfd_datetime_str.py

"""

# %% get ndfd data function

def get_sco_ndfd_data(base_server_url, datetime_uct_str):
    """
    Description: Returns a dataframe of NC State Climate office (SCO) National Digital Forecast Dataset (NDFD) data for a specified datetime,
                 if url does not exist then will give empty dataset
    Parameters:
        base_server_url (str): Base URL (string) for the SCO NDFD TDS server
        datetime_uct_str (str): A string in "%Y-%m-%d %H:%M" format (e.g., "2016-01-01 00:00") with timezone = UCT
    Returns:
        ndfd_data (pydap Dataset): Pydap dataset object for specified datetime,
        if url does not exist then will give empty dataset
    Required:
        import open_url from pydap.client
        import requests
        must load and run convert_sco_ndfd_datetime_str() function
    """
    # convert datetime string
    year_month, year_month_day, year_month_day_hour = convert_sco_ndfd_datetime_str(datetime_uct_str)

    # define data url
    date_str_url = year_month + "/" + year_month_day + "/" + year_month_day_hour
    data_url = base_server_url + date_str_url + "ds.midatlan.oper.bin"
    data_url_to_check = data_url + ".html" # check with requests is working unless it has .html on end
    # needs to be in format https://tds.climate.ncsu.edu/thredds/dodsC/nws/ndfd/YYYYMM/YYYYMMDD/YYYYMMDDHHds.midatlan.oper.bin.html

    # check if url exisits
    url_check = requests.get(data_url_to_check)
    url_status = url_check.status_code

    if url_status == 200: # 200 means that everything is ok
        # get data from SCO server url and store it on pc
        ndfd_data = open_url(data_url)

    else: # 404 or any other number means that url is not ok
        ndfd_data = []

    return ndfd_data #, url_status, data_url_to_check

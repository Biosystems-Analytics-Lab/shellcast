# -*- coding: utf-8 -*-
"""
ndfd_get_latest_sco_data_script.py

This script grabs latest National Digital Forecast Dataset (NDFD) data from the NC State Climate Office (SCO) TDS server, reformats it, and stores it in a local directory.

To see the catalog website: https://tds.climate.ncsu.edu/thredds/catalog/nws/ndfd/catalog.html

Last Updated: 20200527
Created By: Sheila (ssaia@ncsu.edu)
"""

# %% to do list

# TODO check in with John about qpf noon 72 hr forecast (not currently available)


# %% help

# pydap help: https://pydap.readthedocs.io/en/latest/developer_data_model.html
# thredds help (with python code): https://oceanobservatories.org/thredds-quick-start/#python
# to see the nc sco catalog website: https://tds.climate.ncsu.edu/thredds/catalog/nws/ndfd/catalog.html

# %% load libraries

import pandas # for data mgmt
import numpy # for data mgmt
import datetime as dt # for datetime mgmt
from pydap.client import open_url # to convert bin file
import requests # to check if website exists

# %% set paths

# define data directory path (for export)
data_dir = '/Users/sheila/Documents/bae_shellcast_project/shellcast_analysis/data/tabular/ndfd_sco_latest_raw/'

# %% datetime format conversion function

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

# %% get latest ndfd data function

#def get_latest_sco_ndfd_data():
#    """
#    Description: Returns the latest dataframe of SCO NDFD data,
#                 if url does not exist then will give empty dataset
#    Parameters:
#        none
#    Returns:
#        ndfd_data (pydap Dataset): Pydap dataset object for specified datetime,
#        if url does not exist then will give empty dataset
#    Required:
#        import open_url from pydap.client
#        import requests
#    """
#    # data url (always the same link to data...but data itself will change with time)
#    data_url = "https://tds.climate.ncsu.edu/thredds/dodsC/nws/ndfd/ndfd_latest.midatlan.oper.bin"
#    data_url_to_check = data_url + ".html"
#
#    # check if url exisits
#    url_check = requests.get(data_url_to_check)
#    url_status = url_check.status_code
#
#    if url_status == 200: # 200 means that everything is ok
#        # get data from SCO server url and store it on pc
#        ndfd_data = open_url(data_url)
#
#    else: # 404 or any other number means that url is not ok
#        ndfd_data = []
#
#    return ndfd_data #, url_status, data_url_to_check

# works but not sure how to pull the date time out of this

# %% get ndfd data function

def get_sco_ndfd_data(base_server_url, datetime_uct_str):
    """
    Description: Returns a dataframe of SCO NDFD data for a specified datetime,
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

# %% tidy either pop12 or qpf data function

def tidy_sco_ndfd_data(ndfd_data, datetime_uct_str, ndfd_var):
    """
    Description: Returns a tidy dataframe of qpf SCO NDFD data for a specified date
    Parameters:
        ndfd_data (pydap Dataset): Pydap dataset object for specified datetime, from get_sco_ndfd_data() function
        datetime_uct_str (str): A string in "%Y-%m-%d %H:%M" format (e.g., "2016-01-01 00:00") with timezone = UCT
        ndfd_var (str): either "qpf" or "pop12", the SCO NDFD variable of interest
    Returns:
        var_data_pd (data frame): A pandas dataframe with SCO NDFD variable data
        datetime_ymdh_str (str): A string in "%Y%m%d%H" format (e.g, "2016010100")
    Required:
        import numpy, import pandas, import datatime, must load and run convert_sco_ndfd_datetime_str() and get_sco_ndfd_data() functions before this
    """
    # ndfd_data.values # to see all possible variables

    # convert datetime str so can append to file name
    datetime_ym, datetime_ymd_str, datetime_ymdh_str = convert_sco_ndfd_datetime_str(datetime_uct_str)

    # if data exists
    if (len(ndfd_data) > 0):
        # make ndfd_data children into string for later search check
        ndfd_children_str = str(ndfd_data.children)

        # find variable of interest, if -1 then it does not exist
        qpf_var_check = ndfd_children_str.find('Total_precipitation_surface_6_Hour_Accumulation')
        pop12_var_check = ndfd_children_str.find('Total_precipitation_surface_12_Hour_Accumulation_probability_above_0p254')

        # if requestig qpf data
        if ((ndfd_var == "qpf") and (qpf_var_check != -1)):
            # save variable data
            var_data = ndfd_data['Total_precipitation_surface_6_Hour_Accumulation'] # qpf
            #var_data.dimensions # to see dimensions of variable

            # save variable dimentions
            var_data_dims = var_data.dimensions # get all dimentions

            # check number of dimensions and find 'time' dimensions
            # when there are more than three (i.e., when 'refime' dimension exisits) there's
            # no available list of pop12 or qpf for 24, 36, etc. hours out (which i need)
            # so skip entries with 4 dimensions
            if (len(var_data_dims) == 3): # when dimensions are (time, y, x)
                var_data_time_dim = var_data_dims[0] # get time dimention


                # save list of variable time dimentions
                var_time_np = numpy.array(var_data[var_data_time_dim][:])
                # we want 24 hr (1-day), 48 hr (2-day), and 72 hr (3-day) data

                # make list of desired times
                #var_times_sel = [24, 48, 72]

                # loop through desired times and get indeces
                #var_times_sel_index = []
                #for time in var_times_sel:
                #    var_times_sel_index.append(int(numpy.where(var_time_np == time)[0][0]))

                # check that desired times are available
                var_times_sel = numpy.array([24.0, 48.0, 72.0])
                var_comparison = numpy.intersect1d(var_time_np, var_times_sel)

                # if all desired times are available
                if (len(var_comparison) == 3):
                    # create indeces for hrs of interest
                    hr24_index = int(numpy.where(var_time_np == 24)[0][0]) # 1-day forecast
                    hr48_index = int(numpy.where(var_time_np == 48)[0][0]) # 2-day forecast
                    hr72_index = int(numpy.where(var_time_np == 72)[0][0]) # 3-day forecast

                    # for four loop will need if statement for each if length is zero
                    # len(numpy.where(temp_pop12_time_np == 24)[0])

                    # convert data to array (200 x 194)
                    var_24hr_np = numpy.array(var_data.data[0][hr24_index][0])
                    var_48hr_np = numpy.array(var_data.data[0][hr48_index][0])
                    var_72hr_np = numpy.array(var_data.data[0][hr72_index][0])

                    # convert data to dataframe (3 x 38800)
                    var_24hr_pd_raw = pandas.DataFrame(var_24hr_np).stack(dropna = False).reset_index()
                    var_48hr_pd_raw = pandas.DataFrame(var_48hr_np).stack(dropna = False).reset_index()
                    var_72hr_pd_raw = pandas.DataFrame(var_72hr_np).stack(dropna = False).reset_index()

                    # add valid period column
                    var_24hr_pd_raw['valid_period_hrs'] = numpy.repeat("24", len(var_24hr_pd_raw), axis=0)
                    var_48hr_pd_raw['valid_period_hrs'] = numpy.repeat("48", len(var_48hr_pd_raw), axis=0)
                    var_72hr_pd_raw['valid_period_hrs'] = numpy.repeat("72", len(var_72hr_pd_raw), axis=0)

                    # merge rows of data frames
                    var_data_pd_raw = var_24hr_pd_raw.append([var_48hr_pd_raw, var_72hr_pd_raw]).reset_index()

                    # rename columns
                    var_data_pd = var_data_pd_raw.rename(columns={"level_0": "y_index", "level_1": "x_index", 0: "qpf_value_kgperm2"})

                                    # save x and y data
                    x_data = ndfd_data['x'][:] # x coordinate
                    y_data = ndfd_data['y'][:] # y coordinate

                    # create latitude and longitude columns
                    longitude = []
                    latitude = []
                    for row in range(0, var_data_pd.shape[0]):
                        x_index_val = var_data_pd['x_index'][row]
                        y_index_val = var_data_pd['y_index'][row]
                        longitude.append(x_data.data[x_index_val]) # x is longitude
                        latitude.append(y_data.data[y_index_val]) # y is latitude

                    # add longitude and latitude to data frame
                    var_data_pd['longitude_km'] = longitude
                    var_data_pd['latitude_km']  = latitude

                    # create and wrangle time columns
                    # server time is in UCT but changing it to something that's local for NC (use NYC timezone)
                    var_data_pd['time'] = pandas.to_datetime(numpy.repeat(datetime_uct_str, len(var_data_pd), axis=0), format = "%Y-%m-%d %H:%M")
                    var_data_pd['time_uct_long'] = var_data_pd.time.dt.tz_localize(tz = 'UCT')
                    var_data_pd['time_uct'] = var_data_pd.time_uct_long.dt.strftime("%Y-%m-%d %H:%M")
                    var_data_pd['time_nyc_long'] = var_data_pd.time_uct_long.dt.tz_convert(tz = 'America/New_York')
                    var_data_pd['time_nyc'] = var_data_pd.time_nyc_long.dt.strftime("%Y-%m-%d %H:%M")

                    # print status
                    print("tidied " + ndfd_var + " data on " + datetime_ymdh_str)

                    return var_data_pd, datetime_ymdh_str

                # when not all desired times are available
                else:
                    # empty dataframe
                    var_data_pd = pandas.DataFrame()

                    # print status
                    print("desired times for " + ndfd_var + " data on " + datetime_ymdh_str + " are not available")

                    return var_data_pd, datetime_ymdh_str


            # if number of dimensions is more than 3 i.e. when they are: (reftime, time, y, x)
            else:
                # empty dataframe
                var_data_pd = pandas.DataFrame()

                # print status
                print("desired times for " + ndfd_var + " data on " + datetime_ymdh_str + " are not available")

                return var_data_pd, datetime_ymdh_str


        # if requesting pop12 data
        elif ((ndfd_var == "pop12") and (pop12_var_check != -1)):
            # save variable data
            var_data = ndfd_data['Total_precipitation_surface_12_Hour_Accumulation_probability_above_0p254'] # pop12

            # save variable dimentions
            var_data_dims = var_data.dimensions # get all dimentions

            # check number of dimensions and find 'time' dimensions
            # when there are more than three (i.e., when 'refime' dimension exisits) there's
            # no available list of pop12 and qpf for 24, 36, etc. hours out (which i need)
            # so skip entries with 4 dimensions
            if (len(var_data_dims) == 3): # when dimensions are (time, y, x)
                var_data_time_dim = var_data_dims[0] # get time dimention

                # save list of variable time dimentions
                var_time_np = numpy.array(var_data[var_data_time_dim][:])
                # we want 24 hr (1-day), 48 hr (2-day), and 72 hr (3-day) data

                # check that desired times are available
                var_times_sel = numpy.array([24.0, 48.0, 72.0])
                var_comparison = numpy.intersect1d(var_time_np, var_times_sel)

                # if all desired times are available
                if (len(var_comparison) == 3):
                    # create indeces for hrs of interest
                    hr24_index = int(numpy.where(var_time_np == 24)[0][0]) # 1-day forecast
                    hr48_index = int(numpy.where(var_time_np == 48)[0][0]) # 2-day forecast
                    hr72_index = int(numpy.where(var_time_np == 72)[0][0]) # 3-day forecast

                    # for four loop will need if statement for each if length is zero
                    # len(numpy.where(temp_pop12_time_np == 24)[0])

                    # convert data to array (200 x 194)
                    var_24hr_np = numpy.array(var_data.data[0][hr24_index][0])
                    var_48hr_np = numpy.array(var_data.data[0][hr48_index][0])
                    var_72hr_np = numpy.array(var_data.data[0][hr72_index][0])

                    # convert data to dataframe (3 x 38800)
                    var_24hr_pd_raw = pandas.DataFrame(var_24hr_np).stack(dropna = False).reset_index()
                    var_48hr_pd_raw = pandas.DataFrame(var_48hr_np).stack(dropna = False).reset_index()
                    var_72hr_pd_raw = pandas.DataFrame(var_72hr_np).stack(dropna = False).reset_index()

                    # add valid period column
                    var_24hr_pd_raw['valid_period_hrs'] = numpy.repeat("24", len(var_24hr_pd_raw), axis=0)
                    var_48hr_pd_raw['valid_period_hrs'] = numpy.repeat("48", len(var_48hr_pd_raw), axis=0)
                    var_72hr_pd_raw['valid_period_hrs'] = numpy.repeat("72", len(var_72hr_pd_raw), axis=0)

                    # merge rows of data frames
                    var_data_pd_raw = var_24hr_pd_raw.append([var_48hr_pd_raw, var_72hr_pd_raw]).reset_index()

                    # make final pd dataframe with renamed columns
                    var_data_pd = var_data_pd_raw.rename(columns={"level_0": "y_index", "level_1": "x_index", 0: "pop12_value_perc"})

                    # save x and y data
                    x_data = ndfd_data['x'][:] # x coordinate
                    y_data = ndfd_data['y'][:] # y coordinate

                    # create latitude and longitude columns
                    longitude = []
                    latitude = []
                    for row in range(0, var_data_pd.shape[0]):
                        x_index_val = var_data_pd['x_index'][row]
                        y_index_val = var_data_pd['y_index'][row]
                        longitude.append(x_data.data[x_index_val]) # x is longitude
                        latitude.append(y_data.data[y_index_val]) # y is latitude

                    # add longitude and latitude to data frame
                    var_data_pd['longitude_km'] = longitude
                    var_data_pd['latitude_km']  = latitude
                    # create and wrangle time columns
                    # server time is in UCT but changing it to something that's local for NC (use NYC timezone)
                    var_data_pd['time'] = pandas.to_datetime(numpy.repeat(datetime_uct_str, len(var_data_pd), axis=0), format = "%Y-%m-%d %H:%M")
                    var_data_pd['time_uct_long'] = var_data_pd.time.dt.tz_localize(tz = 'UCT')
                    var_data_pd['time_uct'] = var_data_pd.time_uct_long.dt.strftime("%Y-%m-%d %H:%M")
                    var_data_pd['time_nyc_long'] = var_data_pd.time_uct_long.dt.tz_convert(tz = 'America/New_York')
                    var_data_pd['time_nyc'] = var_data_pd.time_nyc_long.dt.strftime("%Y-%m-%d %H:%M")

                    # print status
                    print("tidied " + ndfd_var + " data on " + datetime_ymdh_str)

                    return var_data_pd, datetime_ymdh_str

                # if not all desired times are available
                else:
                    # empty dataframe
                    var_data_pd = pandas.DataFrame()

                    # print status
                    print("desired times for " + ndfd_var + " data on " + datetime_ymdh_str + " are not available")

                    return var_data_pd, datetime_ymdh_str


            # if number of dimensions is more than 3 i.e. when they are: (reftime, time, y, x)
            else:
                # empty dataframe
                var_data_pd = pandas.DataFrame()

                # print status
                print("desired times for " + ndfd_var + " data on " + datetime_ymdh_str + " are not available")

                return var_data_pd, datetime_ymdh_str

        # if qpf or pop12 are wanted to but not available
        elif(((ndfd_var == "qpf") and (qpf_var_check == -1)) or ((ndfd_var == "pop12") and (pop12_var_check == -1))):
            # empty dataframe
            var_data_pd = pandas.DataFrame()

            # print status
            print("desired vars for " + ndfd_var + " data on " + datetime_ymdh_str + " are not available")

            return var_data_pd, datetime_ymdh_str


        # if requesting something other than qpf or pop12 data
        else:
            return print("Not a valid ndfd_var option.")

    # if data doesn't exist
    else:
        # print status
        print("data on " + datetime_ymdh_str + " are not available")

        # return empty dataframe
        var_data_pd = pandas.DataFrame()

        return var_data_pd, datetime_ymdh_str

# %% test functions

# get latest data
# ndfd_data = get_latest_sco_ndfd_data()
# not sure how to pull the date time out of this

# date now
datetime_now = pandas.to_datetime(dt.datetime.now(), format = "%Y-%m-%d %H:%M") # this is local time (ET) but server is in UCT
datetime_now_nyc = datetime_now.tz_localize(tz = "America/New_York")
datetime_now_uct = datetime_now_nyc.tz_convert(tz = "UCT")
datetime_now_uct_str_full = datetime_now_uct.strftime("%Y-%m-%d %H:%M")
datetime_now_uct_str_short = datetime_now_uct.strftime("%Y-%m-%d")

# date now (midnight)
test_midnight_datetime_str = datetime_now_uct_str_short + " 00:00"

# test function
test_midnight_ym_str, test_midnight_ymd_str, test_midnight_ymdh_str = convert_sco_ndfd_datetime_str(datetime_str = test_midnight_datetime_str)

# define serve path
ndfd_sco_server_url = 'https://tds.climate.ncsu.edu/thredds/dodsC/nws/ndfd/'
# this is the server path for latest ndfd forecasts
# to see the catalog website: https://tds.climate.ncsu.edu/thredds/catalog/nws/ndfd/catalog.html

# get today's midnitght data
test_midnight_data = get_sco_ndfd_data(base_server_url = ndfd_sco_server_url, datetime_uct_str = test_midnight_datetime_str)

# tidy today's midnight qpf data
test_midnight_qpf_data_pd, test_midnight_qpf_datetime_ymdh_str = tidy_sco_ndfd_data(ndfd_data = test_midnight_data, datetime_uct_str = test_midnight_datetime_str, ndfd_var = "qpf")

# tidy today's midnight pop12 data
test_midnight_pop12_data_pd, test_midnight_pop12_datetime_ymdh_str = tidy_sco_ndfd_data(ndfd_data = test_midnight_data, datetime_uct_str = test_midnight_datetime_str, ndfd_var = "pop12")



# date now (noon)
test_noon_datetime_str = datetime_now_uct_str_short + " 12:00"

# test function
test_noon_ym_str, test_noon_ymd_str, test_noon_ymdh_str = convert_sco_ndfd_datetime_str(datetime_str = test_noon_datetime_str)

# define serve path
ndfd_sco_server_url = 'https://tds.climate.ncsu.edu/thredds/dodsC/nws/ndfd/'
# this is the server path for latest ndfd forecasts
# to see the catalog website: https://tds.climate.ncsu.edu/thredds/catalog/nws/ndfd/catalog.html

# get today's noon data
test_noon_data = get_sco_ndfd_data(base_server_url = ndfd_sco_server_url, datetime_uct_str = test_noon_datetime_str)

# tidy today's noon qpf data
test_noon_qpf_data_pd, test_noon_qpf_datetime_ymdh_str = tidy_sco_ndfd_data(ndfd_data = test_noon_data, datetime_uct_str = test_noon_datetime_str, ndfd_var = "qpf")

# tidy today's noon pop12 data
test_noon_pop12_data_pd, test_noon_pop12_datetime_ymdh_str = tidy_sco_ndfd_data(ndfd_data = test_noon_data, datetime_uct_str = test_noon_datetime_str, ndfd_var = "pop12")

# %% real deal

# define serve path
ndfd_sco_server_url = 'https://tds.climate.ncsu.edu/thredds/dodsC/nws/ndfd/'
# this is the server path for historic ndfd forecasts
# to see the catalog website: https://tds.climate.ncsu.edu/thredds/catalog/nws/ndfd/catalog.html

# keep track of available dates
data_available_pd = pandas.DataFrame(columns = ['datetime_uct_str', 'status'])

# get time now
#datetime_now_nyc = pandas.to_datetime(dt.datetime.now(), format = "%Y-%m-%d %H:%M").tz_localize(tz = "America/New_York") # this is local time (ET) but server is in UCT
datetime_now_nyc = pandas.to_datetime("2020-06-17 07:00", format = "%Y-%m-%d %H:%M").tz_localize(tz = "America/New_York") # force midnight uct grab at 8am et
#datetime_now_nyc = pandas.to_datetime("2020-05-28 15:00", format = "%Y-%m-%d %H:%M").tz_localize(tz = "America/New_York") # force noon uct grab at 8pm et

# convert to uct
datetime_now_uct = datetime_now_nyc.tz_convert(tz = "UCT")

# round up to nearest hour in uct
datetime_now_uct_td = dt.timedelta(hours = datetime_now_uct.hour, minutes = datetime_now_uct.minute, seconds=datetime_now_uct.second, microseconds = datetime_now_uct.microsecond)
to_hour = dt.timedelta(hours=round(datetime_now_uct_td.total_seconds()/3600))
datetime_now_round_uct = pandas.to_datetime((dt.datetime.combine(datetime_now_uct, dt.time(0)) + to_hour), format = "%Y-%m-%d %H:%M").tz_localize(tz = "UCT")

# calc other bounds
datetime_midnighttoday_uct = pandas.to_datetime((datetime_now_round_uct.strftime("%Y-%m-%d") + " 00:00")).tz_localize("UCT")
datetime_noontoday_uct = pandas.to_datetime((datetime_now_round_uct.strftime("%Y-%m-%d") + " 12:00")).tz_localize("UCT")
datetime_midnightnextd_uct = datetime_midnighttoday_uct + pandas.DateOffset(days = 1)

# determine datetime string to use for query using bounds
if (datetime_now_round_uct >= datetime_midnighttoday_uct) & (datetime_now_round_uct < datetime_noontoday_uct): # between midnight and noon
    temp_datetime_uct_str = datetime_midnighttoday_uct.strftime("%Y-%m-%d %H:%M")
elif (datetime_now_round_uct >= datetime_noontoday_uct) & (datetime_now_round_uct < datetime_midnightnextd_uct): # between noon and midnight
    temp_datetime_uct_str = datetime_noontoday_uct.strftime("%Y-%m-%d %H:%M")

# convert datetime to simple string for later data export
temp_datetime_ymdh_str = convert_sco_ndfd_datetime_str(temp_datetime_uct_str)[2]
temp_datetime_ymdh_str

# %% 

# get data
temp_data = get_sco_ndfd_data(base_server_url = ndfd_sco_server_url, datetime_uct_str = temp_datetime_uct_str)

# only append data when it exists
if (len(temp_data) > 0):
    # tidy qpf and pop12 data
    temp_qpf_data_pd, temp_qpf_datetime_ymdh_str = tidy_sco_ndfd_data(ndfd_data = temp_data, datetime_uct_str = temp_datetime_uct_str, ndfd_var = "qpf")
    temp_pop12_data_pd, temp_pop12_datetime_ymdh_str = tidy_sco_ndfd_data(ndfd_data = temp_data, datetime_uct_str = temp_datetime_uct_str, ndfd_var = "pop12")

    # check if desired times were available, only keep when we have both
    if ((len(temp_qpf_data_pd) > 0) and (len(temp_pop12_data_pd) > 0)):

        # define export path
        temp_qpf_data_path = data_dir + "qpf_" + temp_datetime_ymdh_str +  ".csv" # data_dir definited at top of script
        temp_pop12_data_path = data_dir + "pop12_" + temp_datetime_ymdh_str + ".csv" # data_dir definited at top of script

        # export results
        temp_qpf_data_pd.to_csv(temp_qpf_data_path, index = False)
        temp_pop12_data_pd.to_csv(temp_pop12_data_path, index = False)

        # keep track of available data
        temp_data_available_pd = pandas.DataFrame({'datetime_uct_str':[temp_datetime_uct_str], 'status':["available"]})
        data_available_pd = data_available_pd.append(temp_data_available_pd, ignore_index = True)
        
        # export data availability
        data_availability_path = data_dir + "data_available_" + temp_datetime_ymdh_str +  ".csv"
        data_available_pd.to_csv(data_availability_path, index = False)

        # print status
        print("exported " + temp_datetime_uct_str + " data")

    else:
        # keep track of available data
        temp_data_available_pd = pandas.DataFrame({'datetime_uct_str':[temp_datetime_uct_str], 'status':["not_available"]})
        data_available_pd = data_available_pd.append(temp_data_available_pd, ignore_index = True)
        
        # export data availability
        data_availability_path = data_dir + "data_available_" + temp_datetime_ymdh_str +  ".csv"
        data_available_pd.to_csv(data_availability_path, index = False)

        # print status
        print("did not append " + temp_datetime_uct_str + " data")

else:
    # keep track of available data
    temp_data_available_pd = pandas.DataFrame({'datetime_uct_str':[temp_datetime_uct_str], 'status':["not_available"]})
    data_available_pd = data_available_pd.append(temp_data_available_pd, ignore_index = True)
    
    # export data availability
    data_availability_path = data_dir + "data_available_" + temp_datetime_ymdh_str +  ".csv"
    data_available_pd.to_csv(data_availability_path, index = False)

    # print status
    print("did not append " + temp_datetime_uct_str + " data")


# %% testing times
base_server_url = 'https://tds.climate.ncsu.edu/thredds/dodsC/nws/ndfd/'
datetime_uct_str = '2020-05-27 12:00'
ndfd_var = "qpf"
#ndfd_var = "pop12"
ndfd_data = get_sco_ndfd_data(base_server_url = base_server_url, datetime_uct_str = datetime_uct_str)
ndfd_children_str = str(ndfd_data.children)
qpf_var_check = ndfd_children_str.find('Total_precipitation_surface_6_Hour_Accumulation')
#pop12_var_check = ndfd_children_str.find('Total_precipitation_surface_12_Hour_Accumulation_probability_above_0p254')
var_data = ndfd_data['Total_precipitation_surface_6_Hour_Accumulation']
#var_data = ndfd_data['Total_precipitation_surface_12_Hour_Accumulation_probability_above_0p254']
var_data_dims = var_data.dimensions
var_data_time_dim = var_data_dims[0]
var_time_np = numpy.array(var_data[var_data_time_dim][:])
var_time_np

# looks like pop12 is available at 00:00 and 12:00 for 24, 48, and 72 hr forecasts
# looks like qpf is available at 00:00 for all three forecasts but 12:00 72 hr forecast is missing

# 00:00 UCT = 8pm the day before ET
# 12:00 UCT = 8am that day ET

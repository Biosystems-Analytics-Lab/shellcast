"""
# ---- script header ----
script name: functions.py
purpose of script: python fuctions required for running shellcast analysis
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200923
"""

import pandas # for data mgmt
import numpy # for data mgmt
import datetime as dt # for datetime mgmt
from pydap.client import open_url # to convert bin file
import requests # to check if website exists
from csv import writer

def aggregate_sco_ndfd_var_data(ndfd_var_data, var_period_index, var_period_vals, ndfd_var) :
    """
    Description: Returns a tidy dataframe of qpf SCO NDFD data for a specified date
    Parameters:
        ndfd_var_data (pydap Dataset): Pydap dataset object for specified datetime, from get_sco_ndfd_data() function and need to select a specific variable within this raw dataset
        var_period_index (integer): Integer value that represents where in ndfd_var_data the subperiod of interest is (e.g. 6 hr, 12hr)
        var_period_vals (array): An array of subperiod values (e.g., 6hr, 12hr) for the full period of interest (e.g., 24hr)
        ndfd_var (str): either "qpf" or "pop12", the SCO NDFD variable of interest
    Returns:
        var_agg_data_pd (data frame): A pandas dataframe with variable data aggregated to the full period of interest (e.g., 24hr)
      Required:
        import pandas
        ndfd_var_data requires loading and running convert_sco_ndfd_datetime_str() and get_sco_ndfd_data() functions before this
    Source: none, custom function

    Note: Subperiods and periods are described as follows. For example, qpf data is reported in subperiods of 6 hours so to calculate qpf for 24 hours, you will have to sum 6, 12, 18, and 24 hour subperiods to get a full 24 hour period.
    """
    # all data for 1-day forecast (24 hrs)
    var_period_raw_data = ndfd_var_data.data[0][var_period_index[0]:(var_period_index[-1]+1)]
    # now have to loop through and bind each of these 4 arrays together into one for 24hrs

    # 24 hrs (compile dataframe from all subperiods)
    var_period_full_df = pandas.DataFrame()
    for subperiod in range(0, var_period_raw_data.shape[0]):
        temp_subperiod_pd_raw = pandas.DataFrame(var_period_raw_data[subperiod]).stack(dropna = False).reset_index()
        # temp_subperiod_pd_raw['subperiod_hrs'] = numpy.repeat(str(var_period_vals[subperiod]), len(temp_subperiod_pd_raw), axis=0)
        var_period_full_df = var_period_full_df.append(temp_subperiod_pd_raw)

    # reset index
    var_period_full_df.reset_index()

    if ndfd_var == "qpf":
        # aggregate all subperiods and reset (take summation)
        var_period_agg_df = var_period_full_df.groupby(['level_0', 'level_1']).agg(
                qpf_value_kgperm2 = pandas.NamedAgg(column = 0, aggfunc = sum)).reset_index()

        # print response
        print(ndfd_var + " " + str(int(var_period_vals[-1])) + " hr period aggregated")

    else: # ndfd_var == "pop12"
        # aggregate all subperiods and reset (take maximum)
        var_period_agg_df = var_period_full_df.groupby(['level_0', 'level_1']).agg(
                pop12_value_perc = pandas.NamedAgg(column = 0, aggfunc = max)).reset_index()

        # print response
        print(ndfd_var + " " + str(int(var_period_vals[-1])) + " hr period aggregated")

    return var_period_agg_df


def append_list_as_row(file_name, list_of_elem):
    """
    Description: opens existing file and appends row to it
    Parameters:
        file_name (str): a string defining the file path
        list_of_elem (list): the list of elements to be added to the file
    Returns:
        path with list_of_elements appended to it (i.e., row appended)
    Required:
        import writer from the csv library
    Source: https://thispointer.com/python-how-to-append-a-new-row-to-an-existing-csv-file/
    """
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)


def convert_sco_ndfd_datetime_str(datetime_str):
    """
    Description: takes string of format "%Y-%m-%d %H:%M" and converts it to the "%Y%m%d%H", "%Y%m%d", and "%Y%m" formats
    Parameters:
        datetime_str (str): A string in "%Y-%m-%d %H:%M" format (e.g., "2016-01-01 00:00")
    Returns:
        datetime_ym_str (str): A string in "%Y%m" format (e.g, "201601")
        datetime_ymd_str (str): A string in "%Y%m%d" format (e.g, "20160101")
        datetime_ymdh_str (str): A string in "%Y%m%d%H" format (e.g, "2016010100")
    Required: none
    Source: none, custom function
    """
    # strings
    date_str, time_str = datetime_str.split(" ")
    year_str, month_str, day_str = date_str.split("-")
    hour_str, sec_str = time_str.split(":")

    # define datetime combinations
    datetime_ym_str = year_str + month_str
    datetime_ymd_str = year_str + month_str + day_str
    datetime_ymdh_str = year_str + month_str + day_str + hour_str

    return datetime_ym_str, datetime_ymd_str, datetime_ymdh_str


def get_sco_ndfd_data(base_server_url, datetime_uct_str):
    """
    Description: returns a dataframe of NC State Climate office (SCO) National Digital Forecast Dataset (NDFD) data for a specified datetime, if url does not exist then will give empty dataset
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
    Source: none, custom function
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


def get_var_col_name(ndfd_data, ndfd_var):
    """
    Description: returns the full column name of the variable of interest and SCO NDFD dataset of interest
    Parameters:
        ndfd_data (pydap Dataset): Pydap dataset object for specified datetime, from get_sco_ndfd_data() function
        ndfd_var (str): either "qpf" or "pop12", the SCO NDFD variable of interest
    Returns:
        var_col_name (str): A string with the full SCO NDFD variable column name means data is available)
    Required: none
    Source: none, custom function
    """
    # get children string
    ndfd_children_str = str(ndfd_data.children)

    # split string
    ndfd_cols = ndfd_children_str.split(",")

    # create empty variable
    var_col_name = []

    # look through each row of data for variable of interest
    if (ndfd_var == "qpf"):
        for row in range(0, len(ndfd_cols)):
            row_to_check = ndfd_cols[row]
            row_result = row_to_check.find('Total_precipitation_surface_6_Hour_Accumulation')

            if row_result > 0:
                row_to_check_final = row_to_check.replace(" ", "").replace("'","")
                var_col_name.append(row_to_check_final)

    elif (ndfd_var == "pop12"):
        for row in range(0, len(ndfd_cols)):
            row_to_check = ndfd_cols[row]
            row_result = row_to_check.find('Total_precipitation_surface_12_Hour_Accumulation_probability_above_0p254')

            if row_result > 0:
                row_to_check_final = row_to_check.replace(" ", "").replace("'","")
                var_col_name.append(row_to_check_final)

    return var_col_name[0]


def make_lease_sql_query(data):
    """
    Description: opens existing file and appends row to it
    Parameters:
        data (pandas df): a pandas dataframe that includes ncdmf lease information to be added to the shellcast mysql database,
        this dataframe must have the following columns: ncdmf_lease_id, grow_area_name, rainfall_thresh_in, longitude, latitude
    Returns:
        sql query (string) to insert new ncdmf leases into the shellcast mysql database
    Requred: need to import pandas, data going into this function needs to be at least 1 row or longer
    Source: none, custom function

    """
    # if there's only one lease to add
    if (len(data) == 1):
        # get data for the only row
        temp_row = data.iloc[0]

        # initial string
        initial_str = "INSERT INTO `ncdmf_leases` (`ncdmf_lease_id`, `grow_area_name`, `rainfall_thresh_in`, `geometry`) VALUES "

        # define temp row string
        temp_row_str = '(\'{ncdmf_lease_id}\', \'{grow_area_name}\', {rainfall_thresh_in}, ST_PointFromText(\'POINT({longitude} {latitude})\'));'.format(
                ncdmf_lease_id = temp_row.ncdmf_lease_id,
                grow_area_name = temp_row.grow_area_name,
                rainfall_thresh_in = temp_row.rainfall_thresh_in,
                longitude = round(temp_row.longitude, ndigits = 6),
                latitude = round(temp_row.latitude, ndigits = 6))

        # concatinate strings
        full_str = initial_str + temp_row_str

    # if greater than 1 (doesn't go into this function if it's not > 0)
    else:
        # define first and last rows
        first_row = 0
        last_row = len(data) - 1

        # full string
        full_str = ""

        for row in range(0, len(data)):
            # temp row string
            if (row == first_row):
                # get data for one row
                temp_row = data.iloc[row]

                # initial string
                initial_str = "INSERT INTO `ncdmf_leases` (`ncdmf_lease_id`, `grow_area_name`, `rainfall_thresh_in`, `geometry`) VALUES "

                # define temp row string
                temp_row_str = '(\'{ncdmf_lease_id}\', \'{grow_area_name}\', {rainfall_thresh_in}, ST_PointFromText(\'POINT({longitude} {latitude})\')), '.format(
                        ncdmf_lease_id = temp_row.ncdmf_lease_id,
                        grow_area_name = temp_row.grow_area_name,
                        rainfall_thresh_in = temp_row.rainfall_thresh_in,
                        longitude = round(temp_row.longitude, ndigits = 6),
                        latitude = round(temp_row.latitude, ndigits = 6))

                # concatinate strings
                full_str = full_str + initial_str + temp_row_str

            elif ((row > first_row) and (row < last_row)):
                # get data for one row
                temp_row = data.iloc[row]

                # define temp row string, note comma at end
                temp_row_str = '(\'{ncdmf_lease_id}\', \'{grow_area_name}\', {rainfall_thresh_in}, ST_PointFromText(\'POINT({longitude} {latitude})\')), '.format(
                        ncdmf_lease_id = temp_row.ncdmf_lease_id,
                        grow_area_name = temp_row.grow_area_name,
                        rainfall_thresh_in = temp_row.rainfall_thresh_in,
                        longitude = round(temp_row.longitude, ndigits = 6),
                        latitude = round(temp_row.latitude, ndigits = 6))

                # concatinate strings
                full_str = full_str + temp_row_str

            else: #if (row == last_row):
                # get data for one row
                temp_row = data.iloc[row]

                # define temp row string, note semi-colon
                temp_row_str = '(\'{ncdmf_lease_id}\', \'{grow_area_name}\', {rainfall_thresh_in}, ST_PointFromText(\'POINT({longitude} {latitude})\'));'.format(
                        ncdmf_lease_id = temp_row.ncdmf_lease_id,
                        grow_area_name = temp_row.grow_area_name,
                        rainfall_thresh_in = temp_row.rainfall_thresh_in,
                        longitude = round(temp_row.longitude, ndigits = 6),
                        latitude = round(temp_row.latitude, ndigits = 6))

                # concatinate strings
                full_str = full_str + temp_row_str

    # return string
    return full_str


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
        import numpy, import pandas, import datatime, must load and run convert_sco_ndfd_datetime_str(), get_sco_ndfd_data(), and aggregate_sco_ndfd_var_data() functions before this
    Source: none, custom function
    """
    # ndfd_data.values # to see all possible variables

    # convert datetime str so can append to file name
    datetime_ym, datetime_ymd_str, datetime_ymdh_str = convert_sco_ndfd_datetime_str(datetime_uct_str)

    # if data exists
    if (len(ndfd_data) > 0):
        # get actual column name in SCO NDFD data and check code
        # there was an issue where the column name had some other padded information (see 2015/09/16 data)
        qpf_var_col_name = get_var_col_name(ndfd_data = ndfd_data, ndfd_var = "qpf")
        pop12_var_col_name = get_var_col_name(ndfd_data = ndfd_data, ndfd_var = "pop12")

        # check that column name is exact
        qpf_var_check = qpf_var_col_name == 'Total_precipitation_surface_6_Hour_Accumulation'
        pop12_var_check = pop12_var_col_name == 'Total_precipitation_surface_12_Hour_Accumulation_probability_above_0p254'

        # if requestig qpf data
        if ((ndfd_var == "qpf") and (qpf_var_check == True)):
            # save variable data
            var_data = ndfd_data[qpf_var_col_name] # qpf
            #var_data.dimensions # to see dimensions of variable

            # save variable dimentions
            var_data_dims = var_data.dimensions # get all dimentions

            # check number of dimensions and find 'time' dimensions
            # when there are more than three (i.e., when 'refime' dimension exisits) there's
            # no available list of pop12 or qpf for 24, 36, etc. hours out (which i need)
            # so skip entries with 4 dimensions
            if (len(var_data_dims) == 3): # when dimensions are (time, y, x)
                # get time dimention
                var_data_time_dim = var_data_dims[0]

                # save list of variable time dimentions
                var_time_np = numpy.array(var_data[var_data_time_dim][:])
                # we want 24 hr (1-day), 48 hr (2-day), and 72 hr (3-day) data

                # select subperiods
                var_times_sel = numpy.array([6., 12., 18., 24., 30., 36., 42., 48., 54., 60., 66., 72.])

                # check that subperiods are available
                var_comparison = numpy.intersect1d(var_time_np, var_times_sel) # has to be 12 long

                # all subperiods are available
                if(len(var_comparison) == 12):
                    # get subperiod values
                    var_24hr_vals = var_times_sel[0:4]
                    var_48hr_vals = var_times_sel[4:8]
                    var_72hr_vals = var_times_sel[8:12]

                    # get index for pulling data
                    var_24hr_index = numpy.where(numpy.isin(var_times_sel, var_24hr_vals))[0] # 1-day forecast
                    var_48hr_index = numpy.where(numpy.isin(var_times_sel, var_48hr_vals))[0] # 2-day forecast
                    var_72hr_index = numpy.where(numpy.isin(var_times_sel, var_72hr_vals))[0] # 3-day forecast

                    # aggregate qpf data
                    var_24hr_pd_raw = aggregate_sco_ndfd_var_data(var_data, var_24hr_index, var_24hr_vals, ndfd_var)
                    var_48hr_pd_raw = aggregate_sco_ndfd_var_data(var_data, var_48hr_index, var_48hr_vals, ndfd_var)
                    var_72hr_pd_raw = aggregate_sco_ndfd_var_data(var_data, var_72hr_index, var_72hr_vals, ndfd_var)

                    # add valid period column
                    var_24hr_pd_raw['valid_period_hrs'] = numpy.repeat("24", len(var_24hr_pd_raw), axis=0)
                    var_48hr_pd_raw['valid_period_hrs'] = numpy.repeat("48", len(var_48hr_pd_raw), axis=0)
                    var_72hr_pd_raw['valid_period_hrs'] = numpy.repeat("72", len(var_72hr_pd_raw), axis=0)

                    # merge rows of data frames
                    var_data_pd_raw = var_24hr_pd_raw.append([var_48hr_pd_raw, var_72hr_pd_raw]).reset_index()

                    # rename columns
                    var_data_pd = var_data_pd_raw.rename(columns={"level_0": "y_index", "level_1": "x_index", "qpf_value_kgperm2": "qpf_value_kgperm2"})

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

                # not all subperiods are available for this analysis so don't run
                else:
                    # empty dataframe
                    var_data_pd = pandas.DataFrame()

                    # print status
                    print("desired subperiods for " + ndfd_var + " data on " + datetime_ymdh_str + " are not available")

                    return var_data_pd, datetime_ymdh_str

            # if number of dimensions is more than 3 i.e. when they are: (reftime, time, y, x)
            else:
                # empty dataframe
                var_data_pd = pandas.DataFrame()

                # print status
                print("desired data dimensions for " + ndfd_var + " data on " + datetime_ymdh_str + " are not available")

                return var_data_pd, datetime_ymdh_str


        # if requesting pop12 data
        elif ((ndfd_var == "pop12") and (pop12_var_check == True)):
            # save variable data
            var_data = ndfd_data[pop12_var_col_name] # pop12

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

                # select subperiods
                var_times_sel = numpy.array([12.,  24.,  36.,  48.,  60.,  72.])

                # check that subperiods are available
                var_comparison = numpy.intersect1d(var_time_np, var_times_sel) # has to be 6 long

                # all subperiods are available
                if(len(var_comparison) == 6):
                    # get subperiod values
                    var_24hr_vals = var_times_sel[0:2]
                    var_48hr_vals = var_times_sel[2:4]
                    var_72hr_vals = var_times_sel[4:6]

                    # get index for pulling data
                    var_24hr_index = numpy.where(numpy.isin(var_times_sel, var_24hr_vals))[0] # 1-day forecast
                    var_48hr_index = numpy.where(numpy.isin(var_times_sel, var_48hr_vals))[0] # 2-day forecast
                    var_72hr_index = numpy.where(numpy.isin(var_times_sel, var_72hr_vals))[0] # 3-day forecast

                    # aggregate qpf data
                    var_24hr_pd_raw = aggregate_sco_ndfd_var_data(var_data, var_24hr_index, var_24hr_vals, ndfd_var)
                    var_48hr_pd_raw = aggregate_sco_ndfd_var_data(var_data, var_48hr_index, var_48hr_vals, ndfd_var)
                    var_72hr_pd_raw = aggregate_sco_ndfd_var_data(var_data, var_72hr_index, var_72hr_vals, ndfd_var)

                    # add valid period column
                    var_24hr_pd_raw['valid_period_hrs'] = numpy.repeat("24", len(var_24hr_pd_raw), axis=0)
                    var_48hr_pd_raw['valid_period_hrs'] = numpy.repeat("48", len(var_48hr_pd_raw), axis=0)
                    var_72hr_pd_raw['valid_period_hrs'] = numpy.repeat("72", len(var_72hr_pd_raw), axis=0)

                    # merge rows of data frames
                    var_data_pd_raw = var_24hr_pd_raw.append([var_48hr_pd_raw, var_72hr_pd_raw]).reset_index()

                    # rename columns
                    var_data_pd = var_data_pd_raw.rename(columns={"level_0": "y_index", "level_1": "x_index", "pop12_value_perc": "pop12_value_perc"})

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

                # not all subperiods are available for this analysis so don't run
                else:
                    # empty dataframe
                    var_data_pd = pandas.DataFrame()

                    # print status
                    print("desired subperiods for " + ndfd_var + " data on " + datetime_ymdh_str + " are not available")

                    return var_data_pd, datetime_ymdh_str

            # if number of dimensions is more than 3 i.e. when they are: (reftime, time, y, x)
            else:
                # empty dataframe
                var_data_pd = pandas.DataFrame()

                # print status
                print("desired times for " + ndfd_var + " data on " + datetime_ymdh_str + " are not available")

                return var_data_pd, datetime_ymdh_str


        # if qpf or pop12 are wanted to but not available
        elif(((ndfd_var == "qpf") and (qpf_var_check == False)) or ((ndfd_var == "pop12") and (pop12_var_check == False))):
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

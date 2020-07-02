"""
# ---- script header ----
script name: tidy_sco_ndfd_data.py
purpose of script: returns a tidy dataframe of nc sco data for a specified datetime
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200427

required libraries: pydap, requests, numpy, pandas, datetime
required functions: convert_sco_ndfd_datetime_str.py, get_sco_ndfd_data.py

"""
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

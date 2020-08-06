"""
# ---- script header ----
script name: aggregate_sco_ndfd_var_data.py
purpose of script: returns a pandas dataframe dataframe of nc sco data aggregated for a specified variable and time period
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200806

required libraries: pydap, requests, numpy, pandas, datetime
required functions: convert_sco_ndfd_datetime_str.py, get_sco_ndfd_data.py

"""
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
        import numpy, import pandas, ndfd_var_data requires loading and running convert_sco_ndfd_datetime_str() and get_sco_ndfd_data() functions before this
        
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
    
    return(var_period_agg_df)
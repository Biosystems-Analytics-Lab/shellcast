"""
# ---- script header ----
script name: get_var_col_name.py
purpose of script: returns the full column name and check code of the variable of interest and SCO NDFD dataset of interest
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200820

required libraries: pydap, requests
required functions: get_sco_ndfd_data.py

"""
def get_var_col_name(ndfd_data, ndfd_var):
    """
    Description: Returns the full column name of the variable of interest and SCO NDFD dataset of interest
    Parameters:
        ndfd_data (pydap Dataset): Pydap dataset object for specified datetime, from get_sco_ndfd_data() function
        ndfd_var (str): either "qpf" or "pop12", the SCO NDFD variable of interest
    Returns:
        var_col_name (str): A string with the full SCO NDFD variable column name means data is available)
    Required:
        import pydap and requests, must load and run the get_sco_ndfd_data() function before this
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
    
    return(var_col_name[0])
        
    
"""
# ---- script header ----
script name: make_lease_sql_query.py
purpose of script: makes sql (string) query to add new leases to mysql database
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200731

required libraries: pandas
required functions: none

source: none, custom function

"""
def make_lease_sql_query(data):
    """
    Description: opens existing file and appends row to it
    Parameters:
        data (pandas df): a pandas dataframe that includes ncdmf lease information to be added to the shellcast mysql database,
        this dataframe must have the following columns: ncdmf_lease_id, grow_area_name, rainfall_thresh_in, longitude, latitude
    Returns:
        sql quere (string) to insert new ncdmf leases into the shellcast mysql database
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
    return(full_str)
"""
# ---- script header ----
script name: append_list_as_row.py
purpose of script: appends a row to an exisiting csv file
author: sheila saia
email: ssaia@ncsu.edu
date created: 20200622

required libraries: csv (writer)
required functions: none

source: https://thispointer.com/python-how-to-append-a-new-row-to-an-existing-csv-file/

"""
def append_list_as_row(file_name, list_of_elem):
    """
    Description: opens existing file and appends row to it
    Parameters:
        file_name (str): a string defining the file path
        list_of_elem (list): the list of elements to be added to the file
    Returns:
        path with list_of_elements appended to it (i.e., row appended)
    Requred: need to import writer from the csv library
    Source: https://thispointer.com/python-how-to-append-a-new-row-to-an-existing-csv-file/
    
    """
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)
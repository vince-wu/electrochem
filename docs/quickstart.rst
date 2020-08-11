============
Quick Start
============

First, import the ``electrochem`` module, along the the ``pandas`` module (we need ``pandas`` to read 
and manipulate dataframe objects)::

    >>> import electrochem as echem
    >>> import pandas as pd

To open an Arbin .res file and output a readable .csv file, define a raw data path and 
a path for the .csv file to be saved to::

    >>> file_path  = "d:/data/cycling_data.res"
    >>> save_path = "d:/data/cycling_data.csv"

Then, simply use the ``parseArbin`` function to convert your data into a .csv file.::

    >>> echem.parseArbin(file_path, save_path)

In this example, the file will be saved into **cycling_data.csv**.
To further manipulate your data, you can create an easily workable data object from the .csv file by using the 
``toDataFrame`` function. This function takes in a .csv or .xlsx file containing raw cycling
data along with your electrode material's mass, in mg::

    >>> mass = 10 # electrode mass is in mg units
    >>> partitioned_data = echem.toDataFrame(save_path, mass)

Here, ``partitioned_data`` is a data object where dataframes are sorted by both cycle index and 
charge/ discharge cycles. It is meant to facilitate data extraction and analysis. 
For example, to get the data for the first charge and discharge, simply do:: 

    >>> first_charge_df = partitioned_data[1]['charge'] # data table for first charge
    >>> first_discharge_df = partitioned_data[1]['discharge'] # data table for first discharge

To extract column data such as voltage and capacity, simply call the corresponding keys,
which are the column names in the .csv file. Note that specific capacity was automatically calculated and 
added to the table by the ``toDataFrame`` function based off the mass you inputted.

    >>> first_charge_voltage = first_charge_df['Voltage'].tolist()
    >>> first_charge_capacity = first_charge_df['Charge_Capacity'].tolist()
    >>> first_discharge_voltage = first_discharge_df['Voltage'].tolist()
    >>> first_discharge_capacity = first_discharge_df['Discharge_Capacity'].tolist()

Then, you can plot the voltage-capacity curves:

    >>> import matplotlib.pyplot as plt
    >>> plt.plot(first_charge_capacity, first_charge_voltage, '-', label='First Charge')
    >>> plt.plot(first_discharge_capacity, first_discharge_voltage, '-', label='First Discharge')
    >>> plt.xlabel('Capacity [mAh/g]')
    >>> plt.ylabel('Voltage [V]')
    >>> plt.legend()
    >>> plt.show()

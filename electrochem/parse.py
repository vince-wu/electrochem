import pandas as pd
try:
    import pyodbc
except Exception:
    pass
import numpy as np
if __name__ == "__main__":
    import matplotlib.pyplot as plt
else:
    import matplotlib
    matplotlib.use('Qt5Agg')
    
import os.path
import tkinter as tk
from tkinter import filedialog
import csv
import re
from pkg_resources import parse_version
import requests
from requests.exceptions import HTTPError
import json
import os

from modules.utils import safeRound, compareVersion, getActiveMass
import modules.errors as errors


class EchemData:
    def __init__(self, dischargeCapacity, chargeCapacity, power, avgVoltage, efficiency):
        self.dischargeCapacity = dischargeCapacity
        self.chargeCapacity = chargeCapacity
        self.power = power
        self.avgVoltage = avgVoltage
        self.efficiency = efficiency
    def __repr__(self):
        string = 'dischargeCapacity: %s\ncharge capacity: %s\npower: %s\naverage voltage: %s\nefficiency: \
%s\n'%(self.dischargeCapacity, self.chargeCapacity, self.power, self.avgVoltage, self.efficiency)
        return string

class DataSet:
    def __init__(self, name, mass, indexed_dfs):
        self.name = name
        self.mass = mass
        self.echem_df = indexed_dfs 
        self.properties = {}
    def addProperty(self, name, value):
        self.properties[name] = value

class ExtractedData:
    def __init__(self, firstCycleData, averageData, voltageRange):
        self.firstCycleData = firstCycleData
        self.averageData = averageData
        self.voltageRange = voltageRange

def parseArbin(source_path, save_path=None, table_name='Channel_Normal_Table'):
    #table_name = 'Channel_Normal_Table'
    # set up some constants
    MDB = source_path
    DRV = '{Microsoft Access Driver (*.mdb)}'
    PWD = 'pw'

    # connect to db
    con = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format(DRV,MDB,PWD))
    cur = con.cursor()
    header_row = []
    for r in cur.columns(table=table_name):
        header_row.append(r.column_name)
        
    # run a query and get the results 
    SQL = 'SELECT * FROM %s;'%(table_name) # your query goes here
    rows = cur.execute(SQL).fetchall()
    rows.insert(0, header_row)
    cur.close()
    con.close()

    if save_path:
        with open(save_path, 'w', newline='') as f:
            csv_writer = csv.writer(f)
            csv_writer.writerows(rows)

# Description: parsed the excel file for Arbin cycler and extracts raw data into a Pandas dataframe
# Charge capacity data for cycle 'i' can be retrieved by:
# indexedData[i]['charge']['Charge_Capacity']
# Discharge capacity data for cycle 'i' can be retrieved by: 
# indexedData[i]['discharge']['Discharge_Capacity']
# Charge voltage data for cycle 'i' can be retrieved by: indexedData[i]['charge']['Voltage']
# Discharge voltage data for cycle 'i' can be retrieved by: indexedData[i]['discharge']['Voltage']
def toDataframe(path, active_mass):
    try:
        extension = os.path.splitext(path)[1]
        if extension == '.csv':
            echem_df = pd.read_csv(path)
        elif extension == '.xls':
            # Read excel file
            echem_df = pd.read_excel(path, sheet_name=1)
            # change column names for excel
            echem_df = echem_df.rename(columns={
                'Current(A)': 'Current', 
                'Charge_Capacity(Ah)': 'Charge_Capacity', 
                'Discharge_Capacity(Ah)': 'Discharge_Capacity',
                'Voltage(V)': 'Voltage',
                'Charge_Energy(Wh)': 'Charge_Energy',
                'Discharge_Energy(Wh)': 'Discharge_Energy',
                'dV/dt(V/s)': 'dV/dt',
                'Internal_Resistance(Ohm)': 'Internal_Resistance',
                'AC_Impedance(Ohm)': 'AC_Impedance',
                'ACI_Phase_Angle(Deg)': 'ACI_Phase_Angle',
                })
        echem_df = echem_df.sort_values(by=['Data_Point'])
        # Convert capacities into mAh/g
        echem_df['Charge_Capacity'] = echem_df['Charge_Capacity']*1000*1000/active_mass
        echem_df['Discharge_Capacity'] = echem_df['Discharge_Capacity']*1000*1000/active_mass
        # Parse data
        maxIndex = echem_df['Cycle_Index'].iloc[-1]
        indexedData = []
        for i in range(1, maxIndex+1):
            # Split data by Cycle Index
            df = echem_df[echem_df['Cycle_Index'] == i]
            # Remove soaking data
            df = df[df['Step_Index'] != 1] 
            # Remove tail data
            df = df[df['Step_Index'] != 4] 
            # Split data by charge
            charge_df = df[df['Current'] >= 0]
            # Split data by discharge
            discharge_df = df[df['Current'] < 0] 
            # Add data to list as a dictionary specifying charge/discharge  
            indexedData.append({'charge':charge_df, 'discharge':discharge_df})
    except OSError:
        raise errors.rawDataError()
    return indexedData

# Description: calculates electrochemical data on the first charge/ discharge curve.
def extractCycleEchem(indexedData, cycleIndex):
    chargeCapacities = indexedData[cycleIndex-1]['charge']['Charge_Capacity'].to_numpy()
    dischargeCapacities = indexedData[cycleIndex-1]['discharge']['Discharge_Capacity'].to_numpy()
    dischargeVoltages = indexedData[cycleIndex-1]['discharge']['Voltage'].to_numpy()
    if not dischargeCapacities.size == 0:
        dischargeCap = dischargeCapacities[-1]
        power = np.trapz(dischargeVoltages, dischargeCapacities, dx=0.01)
        avgVoltage = power/dischargeCap
    else:
        dischargeCap = None
        power = None
        avgVoltage = None
    if not chargeCapacities.size == 0:
        chargeCap = chargeCapacities[-1]
    else:
        chargeCap = None
    if chargeCap and dischargeCap:
        efficiency = dischargeCap/chargeCap*100
    else:
        efficiency = None
    echemData = EchemData(dischargeCap, chargeCap, power, avgVoltage, efficiency)
    return echemData

# Description: extracts the cycling voltage range
def extractVoltageRange(indexedData, cycleIndex):
    chargeVoltages = indexedData[cycleIndex-1]['charge']['Voltage'].to_numpy()
    dischargeVoltages = indexedData[cycleIndex-1]['discharge']['Voltage'].to_numpy()
    if not chargeVoltages.size == 0 and not dischargeVoltages.size == 0:
        min = dischargeVoltages[-1]
        max = chargeVoltages[-1]
    else:
        min = 'n/a'
        max = 'n/a'
    return [min, max]

def extractEchem(indexedData):
    avgVoltage = []
    avgDischargeCap = []
    avgChargeCap = []
    avgPower = []
    # Calculate single curve echem data for each cycle, then average out
    for i in range(len(indexedData)):
        data = extractCycleEchem(indexedData, i)
        if data.avgVoltage: 
            avgVoltage.append(data.avgVoltage)
        if data.dischargeCapacity:
            avgDischargeCap.append(data.dischargeCapacity)
        if data.chargeCapacity:
            avgChargeCap.append(data.chargeCapacity)
        if data.power:
            avgPower.append(data.power)
    avgEfficiency = np.mean(avgDischargeCap)/np.mean(avgChargeCap)*100
    avgData = EchemData(np.mean(avgDischargeCap), np.mean(avgChargeCap), np.mean(avgPower), 
    np.mean(avgVoltage), avgEfficiency)
    if __name__ == "__main__":
        print('--------------------------------------------------------------------')
        print('***Average Electrochemical Data: ***')
        print('Charge Capacity [mAh/g]: %s'%(safeRound(avgData.chargeCapacity,2)))
        print('Discharge Capacity [mAh/g]: %s'%(safeRound(avgData.dischargeCapacity,2)))
        print('Average Discharge Voltage [V]: %s'%(safeRound(avgData.avgVoltage,2)))
        print('Discharge Power [Wh/kg]: %s'%(safeRound(avgData.power,2)))
        print('Coulombic Efficiency: %s%%'%(safeRound(avgData.efficiency,4)))
        print('--------------------------------------------------------------------')
    return avgData

def plotEchem(indexedData, figurePath, system, cycleList, show=True, molar_mass=0,  type='cap', style='standard'):
    option = 0
    plt.rcParams.update({'font.size': 25})
    plt.rcParams.update({'font.family':'Arial'})
    plt.figure(figsize=(8,6.5))
    fsize = 25  
    if not __name__ == "__main__":
        #TODO: write case for package
        return
    ax = plt.gca()
    # For each cycle, plot both charge and discharge curves with the same color
    for index in cycleList:
        if index < len(indexedData) and index >= 0:
            if option == 0:
                x1_data = indexedData[index]['charge']['Charge_Capacity']
                x2_data = indexedData[index]['discharge']['Discharge_Capacity']
            elif option == 1:
                cap1_data = indexedData[index]['charge']['Charge_Capacity']
                cap2_data = indexedData[index]['discharge']['Discharge_Capacity']
                full_capacity = 2/molar_mass*96500*0.2777
                x1_data = 2 - cap1_data / full_capacity
                x2_data = 2 - cap1_data.iloc[-1]/full_capacity + cap2_data / full_capacity
            y1_data = indexedData[index]['charge']['Voltage']
            y2_data = indexedData[index]['discharge']['Voltage']
            color = next(ax._get_lines.prop_cycler)['color']
            plt.plot(x1_data, y1_data, '-', color=color,  linewidth=4, label='Cycle %s'%(index+1))
            plt.plot(x2_data, y2_data, '-', color=color, linewidth=4)
    # plt.ylim(1.3, 4.3)
    # plt.xlim(-2.7, 61)
    plt.xlabel('$x$ in Na$_{2-x}$Mn$_3$(VO$_4$)$_2$PO$_4$', fontsize=fsize)
    plt.ylabel('Voltage [V]', fontsize=fsize)
    #plt.title('Cycling Data for ' + system)
    #plt.title('Cycling Data for ' + 'Cathode A')
    # if molar_mass != 0:
    #     full_capacity = 1/molar_mass*96500*0.2777
    #     ax2 = ax.secondary_xaxis('top')
    #     xticks = ax.get_xticks()
    #     ax2.set_xticks(xticks)
    #     ticklabels = [np.round(x/full_capacity, 1) for x in xticks]
    #     # ticklabels = [-0.01, 0, 0.02, 0.04, 0.06, 0.08]
    #     ax2.set_xticks([x*full_capacity for x in ticklabels])
    #     ax2.set_xticklabels(ticklabels)
    #     print([x*full_capacity for x in ticklabels])
    #     ax2.set_xlabel('Na$^+$ ions inserted/ extracted')
    plt.legend(prop={'size': 22}).set_draggable(True)
    plt.tight_layout()
    # Save matplotlib figure as png
    try:
        if figurePath:
            plt.savefig(figurePath + system + '.png')
            if __name__ == "__main__":
                print('Plot saved to ', figurePath + system + '.png')
                print('--------------------------------------------------------------------')
    except PermissionError:
        raise errors.figurePermissionError
    if __name__ == "__main__":
        if show:
            plt.show()

def generateSummary(data, name, tablePath):
    with open(tablePath + '/' + name + '.csv', mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for key, value in data.items():
            csv_writer.writerow([key, value])
    return

def generateEchemSummary(system, tablePath, indexedData, suppData):
    acc = 3
    data = {}
    voltageRange = extractVoltageRange(indexedData, 1)
    echemData = extractEchem(indexedData)
    cycleEchemData = extractCycleEchem(indexedData, 1)
    roundedRange = [safeRound(voltageRange[0], 3), safeRound(voltageRange[1], 3)]
    data['System'] = system
    data['Voltage Range [V]'] = str(roundedRange[0]) + '-' + str(roundedRange[1])
    data['Avg. Charge Cap. [mAh/g]'] = safeRound(echemData.chargeCapacity, acc)
    data['Avg. Discharge Cap. [mAh/g]'] = safeRound(echemData.dischargeCapacity, acc)
    data['Avg. Voltage [V]'] = safeRound(echemData.avgVoltage, acc)
    data['Avg. Power [Wh/kg]'] = safeRound(echemData.power, acc)
    data['Avg. Coulombic Efficiency'] = str(safeRound(echemData.efficiency, acc))+'%'
    data['First Charge Cap. [mAh/g]'] = safeRound(cycleEchemData.chargeCapacity, acc)
    data['First Discharge Cap. [mAh/g]'] = safeRound(cycleEchemData.dischargeCapacity,acc)
    data['First Discharge Volt. [V]'] = safeRound(cycleEchemData.avgVoltage, acc)
    data['First Discharge Power [Wh/kg]'] = safeRound(cycleEchemData.power, acc)
    data['First Discharge Efficiency'] = str(safeRound(cycleEchemData.efficiency, acc))+'%'
    data.update(suppData)
    generateSummary(data, system, tablePath)
    if __name__ == "__main__":
        print('Successfully saved data table!')

# Description: main function 
def runTasks(filepath, choosefile, figurePath, tablePath, cycleList, mass, 
    ACBratio, rate, cellType, anode, comments, molar_mass=0, active_ions=2):
    # Get system name
    filename = os.path.splitext(os.path.basename(filepath))[0]
    system = filename.replace('.xls', '').replace('VW-', '')
    # Get path
    if choosefile:
        # Prompt File Selection
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename()
    else:
        path = filepath
    extension = os.path.splitext(filepath)[1]
    if extension == '.res':
        parseArbin(path, 'data.csv', 'Channel_Normal_Table')
        path = 'data.csv'
    elif extension == '.csv' or '.xls':
        pass
    # Get active mass
    activeMass = getActiveMass(mass, ACBratio)
    # Parse data from excel file
    indexedData = toDataframe(path, activeMass)
    suppData = {
        'Mass': mass,
        'Active:Carbon:Binder Ratio': ACBratio,
        'Rate': rate,
        'Cell Type': cellType,
        'Anode': anode,
        'Comments': comments
    }
    # Generate CSV summary file
    generateEchemSummary(system, tablePath, indexedData, suppData)
    # Plot data
    plotEchem(indexedData, figurePath, system, cycleList, True, molar_mass)

if __name__ == "__main__":
    runTasks(
        # filepath = 'd:/Clement Research/Electrochem/VW-MnMn-B06-S02-E1.xls',
        # filepath = 'd:/Clement Research/Electrochem/VW-MnAl-B01-S01-B-E1.xls',
        # filepath = 'd:/Clement Research/Electrochem/VW-PMnMn-B02-S01-E1-01.xls',
        # filepath = 'd:/Clement Research/Electrochem/VW-PMnAl-B01-S01-B-E1.xls',
        filepath = 'd:/Clement Research/Electrochem/VW-PVMnMn-B01-S01-E1.xls',
        choosefile = False, # whether or not to choose your file directly (will ignore filepath, filename if true)
        figurePath = 'd:/Clement Research/Electrochem/Figures/', # the directory to save your plot in
        tablePath = 'd:/Clement Research/Electrochem/Summaries/', # the directory to save your table in
        cycleList = range(100),
        # mass = 28.5, # mass of entire cathode (do not multiply by active mass ratio)
        # mass = 17.6,
        # mass = 13.7,
        # mass = 14,
        mass = 12.3,
        ACBratio = '70:20:10', # active:carbon:binder ratio
        rate = 'C/20', # rate
        cellType = 'Swagelok', # cell type
        anode = 'Na', # anode material
        comments = None, # comments
        # molar_mass = 555.61, #Na2Mn3(VO4)3
        # molar_mass = 527.65, #Na2Mn2Al(VO4)3
        # molar_mass = 495.71, #Na2Mn3(PO4)3
        # molar_mass = 467.75, #Na2Mn2Al(PO4)3
        molar_mass = 535.64 #Na2Mn3(VO4)2PO4
        )

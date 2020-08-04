import os
import sys

import matplotlib
import requests
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from pkg_resources import parse_version
from PyQt5.QtWidgets import QApplication, QFileDialog
from requests.exceptions import HTTPError

import errors
from utils import getActiveMass
from display import displayError, setUpGraph
from parse import toDataframe, readArbin, generateEchemSummary, extractEchem

matplotlib.use('Qt5Agg')


class InputData():
    def __init__(self, dataPath, figurePath, tablePath, initCycle, numCycles, system, mass, ratio, 
    rate, type, anode, comments):
        self.dataPath = dataPath
        self.figurePath = figurePath
        self.tablePath = tablePath
        self.initCycle = initCycle
        self.numCycles = numCycles
        self.mass = mass
        self.ratio = ratio
        self. rate = rate
        self.type = type
        self.anode = anode
        self.comments = comments
        if system:
            self.system = system
        else:
            self.system = os.path.basename(dataPath).replace('.xls', '').replace('VW-', '')

# Reads the inputs in the GUI and assigns them to variables
def getInputs(self):
    system = self.system_input.text()
    initCycle = self.first_cycle_spinBox.value()
    numCycles = self.num_cycles_spinBox.value()
    mass = self.mass_doubleSpinBox.value()
    ratio = self.ratio_input.text()
    rate = self.rate_comboBox.currentText()
    type = self.type_input.text()
    anode = self.anode_input.text() 
    comments = self.comments_input.toPlainText()
    dataPath = self.raw_inputfile.text() 
    figurePath = self.figure_path.text() 
    tablePath = self.table_path.text() 
    inputs = InputData(dataPath, figurePath, tablePath, initCycle, numCycles, system, mass, ratio, 
    rate, type, anode, comments)
    return inputs

def saveInputs(self, inputs):
    f = open('savefile.txt', 'w')
    f.write('initCycle, %s\n'%(inputs.initCycle))
    f.write('numCycles, %s\n'%(inputs.numCycles))
    f.write('mass, %s\n'%(inputs.mass))
    f.write('ratio, %s\n'%(inputs.ratio))
    f.write('rate, %s\n'%(inputs.rate))
    f.write('type, %s\n'%(inputs.type))
    f.write('anode, %s\n'%(inputs.anode))
    f.write('dataPath, %s\n'%(inputs.dataPath))
    f.write('figurePath, %s\n'%(inputs.figurePath))
    f.write('tablePath, %s'%(inputs.tablePath))
    f.close()

def getRawDataPath(self):
    path = QFileDialog.getOpenFileName(self, 'Choose Raw Data File', '',"(*.xls *.csv *.res)")[0]
    if path:
        self.raw_inputfile.setText(path)

def getFigurePath(self):
    path = QFileDialog.getExistingDirectory(self, 'Select Directory for Plot Figure')
    if path:
        self.figure_path.setText(path)

def getTablePath(self):
    path = QFileDialog.getExistingDirectory(self, 'Select Directory for Data Table')
    if path:
        self.table_path.setText(path)

def plotData(self, partitioned_data, figurePath, system, initCycle, numCycles, show=True):
    if self.display_exists:
        setUpGraph(self)
    else:
        self.graphWindow.axes.cla()
        self.graphWindow.axes.clear()
        self.graphWindow.draw()
    fsize=14
    # Set the max cycle limit based on inputs
    maxCycle = initCycle + numCycles
    if maxCycle-1 > len(partitioned_data):
        maxCycle = len(partitioned_data) + 1
    if initCycle > len(partitioned_data):
        return
    # For each cycle, plot both charge and discharge curves with the same color
    for index in range(initCycle, maxCycle):
        x1_data = partitioned_data[index-1]['charge']['Charge_Capacity']
        y1_data = partitioned_data[index-1]['charge']['Voltage']
        x2_data = partitioned_data[index-1]['discharge']['Discharge_Capacity']
        y2_data = partitioned_data[index-1]['discharge']['Voltage']
        ax = self.graphWindow.gca
        color = next(ax._get_lines.prop_cycler)['color']
        self.graphWindow.axes.plot(x1_data, y1_data, '-', color=color, label='Cycle %s'%(index))
        self.graphWindow.axes.plot(x2_data, y2_data, '-', color=color)
    self.graphWindow.axes.tick_params(axis='both', which='major', labelsize=fsize)
    self.graphWindow.axes.set_xlabel('Capacity [mAh/g]', fontsize=fsize)
    self.graphWindow.axes.set_ylabel('Voltage [V]', fontsize=fsize)
    self.graphWindow.axes.set_title('Cycling Data for ' + system, fontsize=fsize)
    self.graphWindow.axes.legend(prop={'size': fsize})
    self.graphWindow.draw()
    # Save matplotlib figure as png
    if figurePath:
        self.graphWindow.fig.savefig(figurePath + '/' + system + '.png')
    if __name__ == "__main__":
        if show:
            self.graphWindow.axes.plot.show()
    QApplication.processEvents()

def runTasks(self):
    try:
        # Read inputs
        inputs = getInputs(self)
        # Get active mass
        activeMass = getActiveMass(inputs.mass, inputs.ratio)
        # Parse data from excel file
        self.statusbar.showMessage('Parsing raw data file...')
        QApplication.processEvents()
        extension = os.path.splitext(inputs.dataPath)[1]
        if extension == '.res':
            readArbin(inputs.dataPath, 'data.csv', 'Channel_Normal_Table')
            path = 'data.csv'
        else:
            path = inputs.dataPath
        partitioned_data = toDataframe(path, activeMass)
        # Extract electrochem data
        extractedData = extractEchem(partitioned_data)
        self.statusbar.showMessage('Parsing complete.', 2000)
        QApplication.processEvents()
        # Plot data
        plotData(self, partitioned_data, inputs.figurePath, inputs.system, inputs.initCycle, inputs.numCycles)
        # Generate CSV summary file
        generateEchemSummary(inputs.system, inputs.tablePath, extractedData.firstCycleData, extractedData.averageData, 
        extractedData.voltageRange, inputs.mass, inputs.ratio, inputs.rate, 
        inputs.type, inputs.anode, inputs.comments)
        # Save inputs
        saveInputs(self, inputs)
        self.statusbar.showMessage('Plot and data table saved successfully.', 3000)
    except Exception as e:
        if self.debug:
            raise e
        else:
            displayError(self, str(e))

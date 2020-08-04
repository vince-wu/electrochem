import sys
from PyQt5 import QtWidgets, uic, Qt
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from modules.MainWindow import Ui_MainWindow
import modules.gui_interact as gui_interact
import modules.display as display


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setvariables()
        self.setWindowTitle("Electrochemistry Parser v{}".format(self.version))
        self.connectEvents()
        display.initDisplay(self)
        display.readInputFromSave(self)

    # set global class variables
    def setvariables(self):
        self.version = '0.1.0'
        self.display_exists = True
        self.debug = False

    # Connect keystrokes and clicks to event functions
    def connectEvents(self):
        self.run_button.clicked.connect(self.runButtonClicked)
        self.table_button.clicked.connect(self.tableButtomClicked)
        self.plot_button.clicked.connect(self.plotButtonClicked)
        self.raw_button.clicked.connect(self.rawButtonClicked)

    def keyPressEvent(self,event): 
        if event.key()== Qt.Key_Return: 
            self.runButtonClicked()

    # Connection Functions 
    def runButtonClicked(self):
        gui_interact.runTasks(self)
    
    def tableButtomClicked(self):
        gui_interact.getTablePath(self)

    def plotButtonClicked(self):
        gui_interact.getFigurePath(self)
    
    def rawButtonClicked(self):
        gui_interact.getRawDataPath(self)
        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
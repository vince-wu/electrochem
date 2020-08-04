"""Top-level package for Arbin Electrochemical Tools."""
import electrochem._version

__author__ = """Vincent Wu"""
__email__ = 'vincentwu@ucsb.edu'
__version__ = __version__ = electrochem._version.__version__
from electrochem.parse import (parseArbin, toDataframe, extractEchem, 
extractCycleEchem, generateSummary, generateEchemSummary, plotEchem)


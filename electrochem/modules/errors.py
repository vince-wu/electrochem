class rawDataError(Exception):
    def __init__(self):
        self.message = 'Please choose a valid raw data file!'
        super().__init__(self.message)

class ratioError(Exception):
    def __init__(self):
        self.message = 'Could not read Active:Carbon:Binder ratio input.'
        super().__init__(self.message)

class tablePermissionError(Exception):
    def __init__(self):
        self.message = 'Cannot save data table because the file is currently in use by another program.'
        super().__init__(self.message)

class figurePermissionError(Exception):
    def __init__(self):
        self.message = 'Cannot save figure because the file is currently in use by another program.'
        super().__init__(self.message)
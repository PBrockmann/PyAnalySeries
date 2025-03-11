import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt

#=========================================================================================
class myplot:

    #---------------------------------------------------------------------------------------------
    def __init__(self, rows=1, cols=1):

        self.fig, self.ax = plt.subplots(rows, cols)



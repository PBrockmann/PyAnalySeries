import matplotlib.pyplot as plt
from matplotlib.axis import XAxis, YAxis
from matplotlib.lines import Line2D

import numpy as np

#=========================================================================================
def is_axvline(line):
    xdata = line.get_xdata()
    ydata = line.get_ydata()

    x_is_constant = (
        len(xdata) == 1 or 
        (len(xdata) == 2 and xdata[0] == xdata[1])
    )

    y_covers_full_axis = (
        len(ydata) == 2 and ydata[0] == 0 and ydata[1] == 1
    )

    return x_is_constant and y_covers_full_axis

#=========================================================================================
class interactivePlot:

    #---------------------------------------------------------------------------------------------
    def __init__(self, rows=1, cols=1):

        self.fig, self.axs = plt.subplots(rows, cols)

        self.left_margin = 100              # in pixels
        self.right_margin = 50
        self.top_margin = 50
        self.bottom_margin = 50

        # flat axes
        self.axs = np.ravel(self.axs)

        # Set pickradius for XAxis and YAxis for easier selection
        for ax in self.axs:
            ax.xaxis.set_pickradius(50)
            ax.yaxis.set_pickradius(50)
            ax.pan_start = None
            ax.line_points_pairs = []
            ax.map_legend_to_line = {}

        # Connect events to methods
        self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.fig.canvas.mpl_connect("resize_event", self.on_resize)

    #---------------------------------------------------------------------------------------------
    def plot(self, n, x, y, label=None):

        ax = self.axs[n]

        line, = ax.plot(x, y, picker=5, label=label)  # Make the plot pickable with tolerance 5 pixels
        points = ax.scatter(x, y, s=5, marker='o', visible=False)
        ax.line_points_pairs.append((line, points))

        legend = ax.legend()
        if label:
            for legend_line, ax_line in zip(legend.get_lines(), ax.get_lines()):
                legend_line.set_picker(5)
                ax.map_legend_to_line[legend_line] = ax_line

        ax.figure.canvas.draw()  # Redraw the canvas

    #---------------------------------------------------------------------------------------------
    def detect_artist(self, event):
        for ax in self.axs:
            # First check if the event occurred on the X or Y axis ticks
            if ax.xaxis.contains(event)[0]:
                return ax.xaxis  # Detected XAxis
            if ax.yaxis.contains(event)[0]:
                return ax.yaxis  # Detected YAxis

            # Now check if the event occurred inside the Axes itself
            if ax.contains(event)[0]:
                return ax  # Detected Axes itself
        return None

    #---------------------------------------------------------------------------------------------
    def on_scroll(self, event):
        """Zoom in and out based on mouse scroll."""
        if event.button == 'up':
            scale_factor = 0.9  # Zoom in
        elif event.button == 'down':
            scale_factor = 1.1  # Zoom out

        artist = self.detect_artist(event)  # Detect the Artist element under the mouse
        #print(artist)

        if artist is None:
            #print("No artist detected under the scroll event.")
            return

        if isinstance(artist, XAxis):
            ax = artist.axes
            # Zoom on the X axis
            cur_xlim = ax.get_xlim()
            xdata = event.xdata if event.xdata is not None else (cur_xlim[0] + cur_xlim[1]) / 2
            new_xlim = [xdata - (xdata - cur_xlim[0]) * scale_factor,
                        xdata + (cur_xlim[1] - xdata) * scale_factor]
            ax.set_xlim(new_xlim)
            #print("Zooming in on the X axis (ticks or labels)")

        elif isinstance(artist, YAxis):
            ax = artist.axes
            # Zoom on the Y axis
            cur_ylim = ax.get_ylim()
            ydata = event.ydata if event.ydata is not None else (cur_ylim[0] + cur_ylim[1]) / 2
            new_ylim = [ydata - (ydata - cur_ylim[0]) * scale_factor,
                        ydata + (cur_ylim[1] - ydata) * scale_factor]
            ax.set_ylim(new_ylim)
            #print("Zooming in on the Y axis (ticks or labels)")

        elif isinstance(artist, plt.Axes):
            ax = artist
            # Zoom on both axes
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()

            xdata = event.xdata
            ydata = event.ydata
            if xdata is None or ydata is None:
                return  # Prevent NoneType error

            new_xlim = [xdata - (xdata - cur_xlim[0]) * scale_factor,
                        xdata + (cur_xlim[1] - xdata) * scale_factor]
            new_ylim = [ydata - (ydata - cur_ylim[0]) * scale_factor,
                        ydata + (cur_ylim[1] - ydata) * scale_factor]

            ax.set_xlim(new_xlim)
            ax.set_ylim(new_ylim)
            #print("Zooming in on both axes (plot area)")

        ax.figure.canvas.draw()  # Redraw the canvas

    #---------------------------------------------------------------------------------------------
    def on_press(self, event):
        if event.button != 1: return            # Only left button

        """Store the starting point for panning."""
        if event.inaxes:
            event.inaxes.pan_start = event.xdata, event.ydata  # Store the starting point for panning

    #---------------------------------------------------------------------------------------------
    def on_motion(self, event):
        """Handle panning when the mouse is moved."""
        if event.inaxes and event.inaxes.pan_start:
            xstart, ystart = event.inaxes.pan_start

            dx = xstart - event.xdata
            dy = ystart - event.ydata

            cur_xlim = event.inaxes.get_xlim()
            cur_ylim = event.inaxes.get_ylim()

            event.inaxes.set_xlim(cur_xlim[0] + dx, cur_xlim[1] + dx)  # Update limits for panning
            event.inaxes.set_ylim(cur_ylim[0] + dy, cur_ylim[1] + dy)

            event.inaxes.figure.canvas.draw()  # Redraw the canvas

    #---------------------------------------------------------------------------------------------
    def on_release(self, event):
        """Remove the starting point for panning."""
        for ax in self.axs:
            ax.pan_start = None

    #---------------------------------------------------------------------------------------------
    def on_key_press(self, event):

        if not event.inaxes:
            return

        if event.key == 'control':
            for line, points in event.inaxes.line_points_pairs:
                if line.get_visible():
                    points.set_visible(True)
            event.inaxes.figure.canvas.draw()  # Redraw the canvas

        elif event.key == 'a':
            visible_lines = [line for line in event.inaxes.lines if (line.get_visible() and not is_axvline(line))]
            if visible_lines:
                x_min = min(line.get_xdata().min() for line in visible_lines)
                x_max = max(line.get_xdata().max() for line in visible_lines)

                y_min = min(line.get_ydata().min() for line in visible_lines)
                y_max = max(line.get_ydata().max() for line in visible_lines)

                x_margin = (x_max - x_min) * 0.05
                y_margin = (y_max - y_min) * 0.05

                event.inaxes.set_xlim(x_min - x_margin, x_max + x_margin)
                event.inaxes.set_ylim(y_min - y_margin, y_max + y_margin)

            event.inaxes.figure.canvas.draw()  # Redraw the canvas

    #---------------------------------------------------------------------------------------------
    def on_key_release(self, event):

        if not event.inaxes:
            return
        
        if event.key == 'control':
            for line, points in event.inaxes.line_points_pairs:
                if line.get_visible():
                    points.set_visible(False)
            event.inaxes.figure.canvas.draw()  # Redraw the canvas

    #---------------------------------------------------------------------------------------------
    def on_pick(self, event):

        legend_line = event.artist
       
        if not isinstance(legend_line, Line2D): return

        if legend_line in legend_line.axes.map_legend_to_line:
            ax_line = legend_line.axes.map_legend_to_line[legend_line]
            visible = not ax_line.get_visible()
            ax_line.set_visible(visible)
            legend_line.set_alpha(1.0 if visible else 0.2)
            for line, points in legend_line.axes.line_points_pairs:
                points.set_visible(False)
            legend_line.axes.figure.canvas.draw()  # Redraw the canvas

    #---------------------------------------------------------------------------------------------
    def on_resize(self, event):
        width, height = self.fig.get_size_inches() * self.fig.dpi

        self.fig.subplots_adjust(
            left = self.left_margin / width,
            right = 1 - self.right_margin / width,
            top = 1 - self.top_margin / height,
            bottom = self.bottom_margin / height,
            wspace = None,
            hspace = 0.5
        )

        self.fig.canvas.draw()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    x1 = np.linspace(0, 10, 100)
    y1 = np.sin(x1)
    x2 = np.linspace(5, 15, 100)
    y2 = np.cos(x2)

    interactive_plot = interactivePlot(rows=2, cols=1)

    interactive_plot.plot(0, x1, y1, label='sin')
    interactive_plot.plot(0, x2, y2, label='cos')

    interactive_plot.plot(1, x2, y2, label='cos')

    #interactive_plot.axs[1].sharex(interactive_plot.axs[0])

    plt.show()

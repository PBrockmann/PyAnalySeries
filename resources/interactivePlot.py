
import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.axis import XAxis, YAxis
from matplotlib.lines import Line2D

import numpy as np

from shapely.geometry import LineString, Point

#=========================================================================================
plt.rcParams["toolbar"] = "None" 

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
        self.axs = list(np.ravel(self.axs))

        for ax in self.axs:
            ax.pan_start = None
            ax.line_points_pairs = []
            ax.map_legend_to_line = {}
            ax.spine_left_position = 0
            ax.spine_bottom_position = 0
            ax.twins = []
            ax.twins_orientation = None

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
    def reset(self, num=0):

        self.axs[num].line_points_pairs = []
        self.axs[num].map_legend_to_line = {}
   
    #---------------------------------------------------------------------------------------------
    def reset_tooltip(self):

        if not hasattr(self, "tooltip") or self.tooltip.figure is None:
            #print("Tooltip does not exist. Creating a new one.")
            self.tooltip = plt.annotate(
                "", xy=(0, 0), xytext=(20, 30),
                xycoords="figure pixels",
                textcoords="offset pixels",
                arrowprops=dict(arrowstyle="->", color='black'),
                zorder=10
            )
        
        elif self.tooltip not in self.fig.texts:
            #print("Tooltip exists but is no longer attached. Reattaching")
            self.fig.texts.append(self.tooltip)
       
        self.tooltip.set_visible(False)

    #---------------------------------------------------------------------------------------------
    def plot(self, n, x, y, label=None):

        ax = self.axs[n]

        line, = ax.plot(x, y, picker=5, label=label)
        points = ax.scatter(x, y, s=5, marker='o', picker=5, visible=False)
        ax.line_points_pairs.append((line, points))

        if label:
            legend = ax.legend()
            for legend_line, ax_line in zip(legend.get_lines(), ax.get_lines()):
                legend_line.set_picker(5)
                ax.map_legend_to_line[legend_line] = ax_line

        ax.figure.canvas.draw()  # Redraw the canvas

    #---------------------------------------------------------------------------------------------
    def detect_artist(self, event):
    
        #------------------------------------------------------------------
        closest_axis = None
        axis_type = None
        distance_min = float('inf')

        #------------------------------------------------------------------
        #print('-----------------')
        #print(f'Mouse: {event.x}, {event.y}')
        
        for ax_current in self.axs:

            if ax_current.contains(event)[0]:  
                return ax_current, ax_current  # If cursor is inside the main axis, return it
    
            mouse = Point((event.x, event.y))

            spine = ax_current.spines['left']
            path = spine.get_path().transformed(spine.get_transform())
            spine_left = LineString(path.vertices)

            spine = ax_current.spines['bottom']
            path = spine.get_path().transformed(spine.get_transform())
            spine_bottom = LineString(path.vertices)

            distance_left = mouse.distance(spine_left)
            distance_bottom = mouse.distance(spine_bottom)
            #print(f"Distance : {distance_left}, {distance_bottom}")
            
            if min(distance_left, distance_bottom) < distance_min:
                distance_min = min(distance_left, distance_bottom)
                closest_axis = ax_current
                axis_type = ax_current.yaxis if distance_left < distance_bottom else ax_current.xaxis

        return closest_axis, axis_type

    #---------------------------------------------------------------------------------------------
    def on_scroll(self, event):
        """Zoom in and out based on mouse scroll."""
        if event.button == 'up':
            scale_factor = 0.9  # Zoom in
        elif event.button == 'down':
            scale_factor = 1.1  # Zoom out

        ax, artist = self.detect_artist(event)  # Detect the Artist element under the mouse

        if artist is None:
            #print("No artist detected under the scroll event.")
            return
        
        #------------------------------
        if isinstance(artist, XAxis):
            # Zoom on the X axis
            cur_xlim = ax.get_xlim()
            xdata = event.xdata if event.xdata is not None else (cur_xlim[0] + cur_xlim[1]) / 2
            new_xlim = [xdata - (xdata - cur_xlim[0]) * scale_factor,
                        xdata + (cur_xlim[1] - xdata) * scale_factor]
            ax.set_xlim(new_xlim)
            #print("Zooming in on the X axis (ticks or labels)")

        #------------------------------
        elif isinstance(artist, YAxis):
            # Zoom on the Y axis
            cur_ylim = ax.get_ylim()
            ydata = event.ydata if event.ydata is not None else (cur_ylim[0] + cur_ylim[1]) / 2
            new_ylim = [ydata - (ydata - cur_ylim[0]) * scale_factor,
                        ydata + (cur_ylim[1] - ydata) * scale_factor]
            ax.set_ylim(new_ylim)
            #print("Zooming in on the Y axis (ticks or labels)")

        #------------------------------
        elif isinstance(artist, plt.Axes):
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
        """Store the starting point for panning."""

        if event.button != 1: return            # Only left button

        ax, artist = self.detect_artist(event)  # Detect the Artist element under the mouse
        #print("press", ax, artist, type(artist))

        if artist is None: return

        display_coord = (event.x, event.y)
        coordx, coordy = ax.transData.inverted().transform(display_coord)

        ax.pan_start = coordx, coordy   # Store the starting point for panning

    #---------------------------------------------------------------------------------------------
    def on_motion(self, event):
        """Handle panning when the mouse is moved."""

        self.fig.canvas.setFocus()

        ax, artist = self.detect_artist(event)  # Detect the Artist element under the mouse
        #print("motion", ax, artist, event.inaxes)

        if artist is None: return

        #-------------------------
        if hasattr(ax, "pan_start") and ax.pan_start:
            xstart, ystart = ax.pan_start

            display_coord = (event.x, event.y)
            coordx, coordy = ax.transData.inverted().transform(display_coord)

            dx = xstart - coordx
            dy = ystart - coordy

            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()

            # Update limits for panning
            if isinstance(artist, XAxis):
                ax.set_xlim(cur_xlim[0] + dx, cur_xlim[1] + dx)
            elif isinstance(artist, YAxis):
                ax.set_ylim(cur_ylim[0] + dy, cur_ylim[1] + dy)
            else:
                ax.set_xlim(cur_xlim[0] + dx, cur_xlim[1] + dx)
                ax.set_ylim(cur_ylim[0] + dy, cur_ylim[1] + dy)

            ax.figure.canvas.draw()  # Redraw the canvas

        #-------------------------
        for ax in self.axs:
            for line, points in ax.line_points_pairs:
                if line.get_visible():
                    contains, info = points.contains(event)
                    if contains:
                        ind = info['ind'][0]
                        x_data, y_data = points.get_offsets().T
                        color = points.get_facecolors()[0]

                        position_xy = ax.transData.transform((x_data[ind], y_data[ind]))
   
                        self.reset_tooltip()
                        self.tooltip.xy = (position_xy)
                        self.tooltip.set_text(f"({x_data[ind]:.6f}, {y_data[ind]:.6f})")
                        self.tooltip.set_bbox(dict(boxstyle="round,pad=0.3", fc=color, alpha=0.2))
                        self.tooltip.set_visible(True)
                        #print('here', x_data[ind], y_data[ind], position_xy)

                        ax.figure.canvas.draw_idle()
                        return

    #---------------------------------------------------------------------------------------------
    def on_release(self, event):
        """Remove the starting point for panning."""
        for ax in self.axs:
            ax.pan_start = None

    #---------------------------------------------------------------------------------------------
    def on_key_press(self, event):

        ax, artist = self.detect_artist(event)  # Detect the Artist element under the mouse

        #------------------------------
        if isinstance(artist, plt.Axes):
            if event.key == 'control':
                for ax in self.axs:
                    for line, points in ax.line_points_pairs:
                        if line.get_visible():
                            points.set_visible(True)
                self.fig.canvas.draw()

            elif event.key == 'a':
                #print("key a on Axe")

                #---------------------------------------
                # No twin axis
                if len(ax.twins) == 0:
                    visible_lines = [line for line in ax.lines if (line.get_visible() and not is_axvline(line))]
                    if visible_lines:
                        x_min = min(line.get_xdata().min() for line in visible_lines)
                        x_max = max(line.get_xdata().max() for line in visible_lines)
                        y_min = min(np.nanmin(line.get_ydata()) for line in visible_lines)  # np.nanmin to ignore nan
                        y_max = max(np.nanmax(line.get_ydata()) for line in visible_lines)
                        x_margin = (x_max - x_min) * 0.05
                        y_margin = (y_max - y_min) * 0.05
                        is_inverted = ax.yaxis.get_inverted()             # keep inverted

                        ax.set_xlim(x_min - x_margin, x_max + x_margin)
                        ax.set_ylim(y_min - y_margin, y_max + y_margin)
                        ax.yaxis.set_inverted(is_inverted)                # set back to state

                #---------------------------------------
                else:

                    #---------------------------------------
                    if ax.twins_orientation == 'vertical':
                        # Set vertical range
                        all_visible_lines = []
                        for ax_current in ax.twins + [ax]:
                            visible_lines = [line for line in ax_current.lines if (line.get_visible() and not is_axvline(line))]
                            if visible_lines:
                                y_min = min(np.nanmin(line.get_ydata()) for line in visible_lines)
                                y_max = max(np.nanmax(line.get_ydata()) for line in visible_lines)
                                y_margin = (y_max - y_min) * 0.05
                                is_inverted = ax_current.yaxis.get_inverted()             # keep inverted
                                ax_current.set_ylim(y_min - y_margin, y_max + y_margin)
                                ax_current.yaxis.set_inverted(is_inverted)                # set back to state
                                all_visible_lines += visible_lines

                        # Set horizontal range
                        if all_visible_lines:
                            x_min = min(line.get_xdata().min() for line in all_visible_lines)
                            x_max = max(line.get_xdata().max() for line in all_visible_lines)
                            x_margin = (x_max - x_min) * 0.05
                            ax.set_xlim(x_min - x_margin, x_max + x_margin)

                    #---------------------------------------
                    elif ax.twins_orientation == 'horizontal':
                        # Set horizontal range
                        all_visible_lines = []
                        for ax_current in ax.twins + [ax]:
                            visible_lines = [line for line in ax_current.lines if (line.get_visible() and not is_axvline(line))]
                            if visible_lines:
                                x_min = min(line.get_xdata().min() for line in visible_lines)
                                x_max = max(line.get_xdata().max() for line in visible_lines)
                                x_margin = (x_max - x_min) * 0.05
                                ax_current.set_xlim(x_min - x_margin, x_max + x_margin)
                                all_visible_lines += visible_lines

                        # Set vertical range
                        if all_visible_lines:
                            y_min = min(np.nanmin(line.get_ydata()) for line in all_visible_lines)
                            y_max = max(np.nanmax(line.get_ydata()) for line in all_visible_lines)
                            y_margin = (y_max - y_min) * 0.05
                            is_inverted = ax.yaxis.get_inverted()             # keep inverted
                            ax.set_ylim(y_min - y_margin, y_max + y_margin)
                            ax.yaxis.set_inverted(is_inverted)                # set back to state

                self.fig.canvas.draw()

        #------------------------------
        elif isinstance(artist, XAxis):
            if event.key == 'a':
                #print("key a on xaxis")
                visible_lines = [line for line in ax.lines if (line.get_visible() and not is_axvline(line))]
                if visible_lines:
                    x_min = min(line.get_xdata().min() for line in visible_lines)
                    x_max = max(line.get_xdata().max() for line in visible_lines)
                    x_margin = (x_max - x_min) * 0.05
                    ax.set_xlim(x_min - x_margin, x_max + x_margin)
                    ax.figure.canvas.draw()  # Redraw the canvas
            
        #------------------------------
        elif isinstance(artist, YAxis):
            if event.key == 'a':
                #print("key a on yaxis")
                visible_lines = [line for line in ax.lines if (line.get_visible() and not is_axvline(line))]
                if visible_lines:
                    y_min = min(np.nanmin(line.get_ydata()) for line in visible_lines)
                    y_max = max(np.nanmax(line.get_ydata()) for line in visible_lines)
                    y_margin = (y_max - y_min) * 0.05
                    is_inverted = ax.yaxis.get_inverted()             # keep inverted
                    ax.set_ylim(y_min - y_margin, y_max + y_margin)
                    ax.yaxis.set_inverted(is_inverted)                # set back to state
                    ax.figure.canvas.draw()  # Redraw the canvas

    #---------------------------------------------------------------------------------------------
    def on_key_release(self, event):

        if event.key == 'control':

            if hasattr(self, "tooltip"):
                self.tooltip.set_visible(False)
            for ax in self.axs:
                for line, points in ax.line_points_pairs:
                    if line.get_visible():
                     points.set_visible(False)
            self.fig.canvas.draw()

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
        fig_width, fig_height = self.fig.canvas.get_width_height()

        self.fig.subplots_adjust(
            left = self.left_margin / fig_width,
            right = 1 - self.right_margin / fig_width,
            top = 1 - self.top_margin / fig_height,
            bottom = self.bottom_margin / fig_height,
            wspace = None,
            hspace = 0.5
        )

        for ax in self.axs:
            bbox = ax.get_position()
            ax_width = bbox.width * fig_width
            ax_height = bbox.height * fig_height
            if hasattr(ax, "spine_left_position") and ax.spine_left_position != 0:
                position = ax.spine_left_position / ax_width
                ax.spines["left"].set_position(("axes", position))
            if hasattr(ax, "spine_bottom_position") and ax.spine_bottom_position != 0:
                position = ax.spine_bottom_position / ax_height
                ax.spines["bottom"].set_position(("axes", position))

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
   
    # Test reset
    #interactive_plot.axs[0].clear()
    #interactive_plot.reset(0)
    #interactive_plot.plot(0, x2, y2, label='cos')

    plt.show()

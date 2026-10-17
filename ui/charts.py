"""Matplotlib chart containers embedded in the Tkinter dashboards."""
import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ui import theme


def create_bar_chart(parent, labels, values, title):
	"""Create a stable chart area, including a useful empty-data state."""
	container = tk.Frame(parent, bg=theme.WHITE, highlightbackground=theme.BORDER, highlightthickness=1)
	figure = Figure(figsize=(5.2, 2.5), dpi=100, facecolor=theme.WHITE, constrained_layout=True)
	axes = figure.add_subplot(111)
	axes.set_title(title, loc="left", fontsize=11, color=theme.TEXT)
	axes.tick_params(axis="x", labelrotation=20, labelsize=8, colors=theme.MUTED)
	axes.tick_params(axis="y", labelsize=8, colors=theme.MUTED)
	axes.spines[["top", "right"]].set_visible(False)
	axes.spines[["left", "bottom"]].set_color(theme.BORDER)
	if labels and values:
		axes.bar(labels, values, color=theme.PRIMARY, width=0.62)
		axes.set_ylim(0, max(values) * 1.15 if max(values) else 1)
	else:
		axes.text(0.5, 0.5, "No data yet", ha="center", va="center", color=theme.MUTED,
				  transform=axes.transAxes)
		axes.set_xticks([])
		axes.set_yticks([])
	canvas = FigureCanvasTkAgg(figure, master=container)
	canvas.get_tk_widget().pack(fill="both", expand=True)
	container.canvas = canvas
	return container

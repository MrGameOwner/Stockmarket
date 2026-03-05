"""
chart_widget.py

Reusable PyQt6 widget embedding a matplotlib chart canvas.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class StockChartWidget(QWidget):
    """Widget to display a stock line chart."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.figure = Figure(facecolor="#1e1e1e")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self._style_axes()

    def _style_axes(self) -> None:
        """Apply dark-theme styling."""
        self.ax.set_facecolor("#252526")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")
        for spine in self.ax.spines.values():
            spine.set_color("#888888")

    def plot_prices(self, symbol: str, points: List[Tuple[datetime, float]], range_label: str) -> None:
        """Plot list of (datetime, price) points."""
        self.ax.clear()
        self._style_axes()

        if not points:
            self.ax.set_title(f"{symbol} - No data available")
            self.canvas.draw()
            return

        x_vals = [p[0] for p in points]
        y_vals = [p[1] for p in points]

        self.ax.plot(x_vals, y_vals, color="#4FC3F7", linewidth=2)
        self.ax.set_title(f"{symbol} Price Chart ({range_label})")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Price (USD)")
        self.ax.grid(True, alpha=0.2, color="white")

        self.figure.autofmt_xdate()
        self.canvas.draw()

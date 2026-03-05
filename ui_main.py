"""
ui_main.py

Main PyQt6 UI for the Stock Market Overview Dashboard.
"""

from __future__ import annotations

import sys
from typing import List

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from chart_widget import StockChartWidget
from stock_api import AlphaVantageClient, Quote, fetch_top_quotes


# Embedded API key as requested
API_KEY = "5O2JQ6K9B1KU1IIT"

DEFAULT_TOP_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK.B", "JPM", "V",
]


class StockDashboardWindow(QMainWindow):
    """Main dashboard window with table, search, and chart panel."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Stock Market Overview Dashboard")
        self.resize(1200, 760)

        if not API_KEY:
            QMessageBox.warning(self, "Missing API Key", "API key is not configured in ui_main.py")

        self.client = AlphaVantageClient(api_key=API_KEY)
        self.current_symbols: List[str] = DEFAULT_TOP_SYMBOLS.copy()
        self.current_selected_symbol: str | None = None
        self.current_range = "1D"

        self._build_ui()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_table_data)
        self.refresh_timer.start(60_000)

        self.refresh_table_data()

    def _build_ui(self) -> None:
        """Create and connect all UI components."""
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        title = QLabel("📈 Stock Market Overview Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        root_layout.addWidget(title)

        top_controls = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search ticker (e.g., AAPL)")
        self.search_input.returnPressed.connect(self.on_search_symbol)

        search_button = QPushButton("Search")
        search_button.clicked.connect(self.on_search_symbol)

        refresh_button = QPushButton("Refresh Now")
        refresh_button.clicked.connect(self.refresh_table_data)

        top_controls.addWidget(self.search_input)
        top_controls.addWidget(search_button)
        top_controls.addWidget(refresh_button)
        root_layout.addLayout(top_controls)

        content_row = QHBoxLayout()
        content_row.setSpacing(12)
        root_layout.addLayout(content_row, stretch=1)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Symbol", "Company Name", "Current Price", "Daily Change %", "Volume"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self.on_table_row_clicked)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        content_row.addWidget(self.table, stretch=3)

        # Right panel: range + chart
        right_panel = QVBoxLayout()

        range_buttons_layout = QHBoxLayout()
        self.range_group = QButtonGroup(self)

        self.btn_1d = QPushButton("1 Day")
        self.btn_1w = QPushButton("1 Week")
        self.btn_1m = QPushButton("1 Month")

        for b, key in [(self.btn_1d, "1D"), (self.btn_1w, "1W"), (self.btn_1m, "1M")]:
            b.setCheckable(True)
            b.clicked.connect(lambda _checked, k=key: self.on_change_range(k))
            self.range_group.addButton(b)
            range_buttons_layout.addWidget(b)

        self.btn_1d.setChecked(True)

        self.chart = StockChartWidget()
        right_panel.addLayout(range_buttons_layout)
        right_panel.addWidget(self.chart, stretch=1)

        content_row.addLayout(right_panel, stretch=4)

        # Dark, modern-ish style
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #1e1e1e; color: #f0f0f0; }
            QLineEdit, QTableWidget {
                background-color: #252526; color: #f0f0f0; border: 1px solid #3a3a3a;
                border-radius: 6px; padding: 6px;
            }
            QPushButton {
                background-color: #0e639c; color: white; border: none; border-radius: 6px; padding: 8px 12px;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:checked { background-color: #2d8fce; }
            QHeaderView::section {
                background-color: #333333; color: #ffffff; padding: 6px; border: 1px solid #444;
            }
            """
        )

    def refresh_table_data(self) -> None:
        """Refresh stock rows."""
        try:
            quotes, errors = fetch_top_quotes(self.client, self.current_symbols, sleep_seconds=12.0)
            self._populate_table(quotes)

            if errors:
                self._show_status_message(
                    "Some symbols failed to load:\n" + "\n".join(errors[:4]) +
                    ("\n..." if len(errors) > 4 else "")
                )
        except Exception as exc:
            self._show_status_message(f"Failed to refresh data: {exc}")

    def _populate_table(self, quotes: List[Quote]) -> None:
        """Fill table with quote data."""
        self.table.setRowCount(0)

        for row_idx, quote in enumerate(quotes):
            self.table.insertRow(row_idx)

            symbol_item = QTableWidgetItem(quote.symbol)
            name_item = QTableWidgetItem(quote.company_name)
            price_item = QTableWidgetItem(f"${quote.current_price:,.2f}")
            change_item = QTableWidgetItem(f"{quote.daily_change_percent:+.2f}%")
            volume_item = QTableWidgetItem(f"{quote.volume:,}")

            change_item.setForeground(
                Qt.GlobalColor.green if quote.daily_change_percent >= 0 else Qt.GlobalColor.red
            )

            self.table.setItem(row_idx, 0, symbol_item)
            self.table.setItem(row_idx, 1, name_item)
            self.table.setItem(row_idx, 2, price_item)
            self.table.setItem(row_idx, 3, change_item)
            self.table.setItem(row_idx, 4, volume_item)

        if quotes and not self.current_selected_symbol:
            self.current_selected_symbol = quotes[0].symbol
            self.load_chart_for_symbol(self.current_selected_symbol)

    def on_table_row_clicked(self, row: int, _column: int) -> None:
        """Handle table selection."""
        symbol_item = self.table.item(row, 0)
        if not symbol_item:
            return
        self.current_selected_symbol = symbol_item.text().strip().upper()
        self.load_chart_for_symbol(self.current_selected_symbol)

    def on_change_range(self, range_key: str) -> None:
        """Change graph range."""
        self.current_range = range_key
        if self.current_selected_symbol:
            self.load_chart_for_symbol(self.current_selected_symbol)

    def load_chart_for_symbol(self, symbol: str) -> None:
        """Load and plot chart for selected symbol."""
        try:
            points = self.client.get_history_for_range(symbol, self.current_range)
            self.chart.plot_prices(symbol, points, self.current_range)
        except Exception as exc:
            self._show_status_message(f"Chart load failed for {symbol}: {exc}")
            self.chart.plot_prices(symbol, [], self.current_range)

    def on_search_symbol(self) -> None:
        """Search and add ticker to table list."""
        symbol = self.search_input.text().strip().upper()
        if not symbol:
            return

        if symbol in self.current_symbols:
            self.current_selected_symbol = symbol
            self.load_chart_for_symbol(symbol)
            return

        self.current_symbols.insert(0, symbol)
        self.current_symbols = self.current_symbols[:20]
        self.refresh_table_data()
        self.current_selected_symbol = symbol
        self.load_chart_for_symbol(symbol)

    def _show_status_message(self, msg: str) -> None:
        """Show temporary status message."""
        self.statusBar().showMessage(msg, 8000)


def run_app() -> None:
    """App bootstrap."""
    app = QApplication(sys.argv)
    win = StockDashboardWindow()
    win.show()
    sys.exit(app.exec())

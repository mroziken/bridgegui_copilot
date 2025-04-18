"""Copilot widgets for bridge frontend

Thi module contains widgets for displaying copilot advices.

Classes:
Copilot -- Text box for displaying copilot advices
"""

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt

import bridgegui.messaging as messaging
import bridgegui.positions as positions
import bridgegui.cards as cards

SCORE_TAG = "score"
PARTNERSHIP_TAG = "partnership"


class Copilot(QTableWidget):
    """Text box for displaying copilot advices"""

    def __init__(self, parent=None):
        """Initialize copilot text box"""
        super().__init__(parent)
        self.setColumnCount(1)
        self.setHorizontalHeaderLabels(["Copilot Messages"])
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setWordWrap(True)  # Enable word wrapping for the table

        # Set row height and visible row count
        self.setRowHeight(0, 20)  # Set the height of each row (20 pixels as an example)
        self.setMinimumHeight(10 * 20 + 2)  # Ensure the widget can display 10 rows
        self.setMaximumHeight(10 * 20 + 2)  # Fix the height to exactly 10 rows
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().Fixed)

        # Adjust column width to match the text box width
        self.horizontalHeader().setStretchLastSection(True)  # Stretch the last column
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def resizeEvent(self, event):
        """Adjust column width when the widget is resized"""
        super().resizeEvent(event)
        self.setColumnWidth(0, self.viewport().width())  # Set column width to match the widget width

    def append_message(self, message):
        """Append a message to the copilot text box"""
        row = self.rowCount()
        self.insertRow(row)
        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)  # Align text to the top-left
        item.setFlags(Qt.ItemIsEnabled)  # Make the item non-editable
        self.setItem(row, 0, item)
        self.resizeRowToContents(row)  # Adjust row height to fit the content

"""Game label widgets for bridge frontend

Thi module contains widgets for displaying game id.

Classes:
GameLabel -- Text box for displaying copilot advices
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt



SCORE_TAG = "score"
PARTNERSHIP_TAG = "partnership"


class GameLabel(QLabel):
    """Text box for displaying game id"""

    def __init__(self, parent=None):
        """Initialize game label box"""
        super().__init__(parent)
        self.setText("Game ID: ")
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setWordWrap(True)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().Fixed)
        # Set row height and visible row count
        self.setMinimumHeight(20)
        self.setMaximumHeight(20)
        # Adjust column width to match the text box width
        self.setStyleSheet("QLabel { background-color: white; }")
        # Set the label to be non-editable
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.setOpenExternalLinks(True)
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)



    def resizeEvent(self, event):
        """Adjust column width when the widget is resized"""
        super().resizeEvent(event)
        self.setFixedWidth(self.parent().width())
        # Set column width to match the widget width

    def append_message(self, message):
        """Append a message to the game label text box"""
        self.setText(message)

    def set_text(self, text):
        """Set the game label text"""
        self.setText(text)

    def set_text_color(self, color):
        """Set the game label text color"""
        self.setStyleSheet(f"QLabel {{ color: {color}; }}")

    def set_background_color(self, color):
        """Set the game label background color"""
        self.setStyleSheet(f"QLabel {{ background-color: {color}; }}")

    def set_text_alignment(self, alignment):
        """Set the game label text alignment"""
        self.setAlignment(alignment)

    def set_text_interaction_flags(self, flags):
        """Set the game label text interaction flags"""
        self.setTextInteractionFlags(flags)

    def set_open_external_links(self, open_external_links):
        """Set the game label open external links"""
        self.setOpenExternalLinks(open_external_links)

    def set_text_format(self, text_format):
        """Set the game label text format"""
        self.setTextFormat(text_format)


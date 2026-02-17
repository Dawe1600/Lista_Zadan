# styles.py

MAIN_STYLE = """
    QWidget {
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }
    #MainWindow {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 15px;
    }
    QLabel {
        color: #FFFFFF;
        font-size: 18px;
        font-weight: bold;
        padding: 5px;
    }
    QPushButton {
        background-color: #2D2D2D;
        border: 1px solid #3E3E3E;
        border-radius: 8px;
        color: #E0E0E0;
        padding: 6px 12px;
        font-size: 16px;
        font-family: "Segoe UI Emoji";
    }
    QPushButton:hover {
        background-color: #3E3E3E;
        border-color: #4E4E4E;
    }
    QListWidget {
        background-color: transparent;
        border: none;
        outline: none;
        font-family: "Consolas", monospace;
        font-size: 15px;
    }
    QListWidget::item {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border-radius: 8px;
        margin-bottom: 4px;
        padding: 8px;
    }
    QListWidget::item:hover {
        background-color: #383838;
    }
    QListWidget::item:selected {
        background-color: #404040;
        border: 1px solid #555;
    }
    QScrollBar:vertical {
        border: none;
        background: transparent;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #3E3E3E;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background: #4E4E4E;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    QMenu {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #3E3E3E;
    }
    QMenu::item {
        padding: 5px 20px;
    }
    QMenu::item:selected {
        background-color: #3E3E3E;
    }
"""

DIALOG_STYLE = """
    QDialog {
        background-color: #1E1E1E;
        color: #E0E0E0;
        border: 1px solid #333;
        border-radius: 15px;
    }
    QLabel {
        font-size: 16px;
        font-weight: bold;
        color: #FFFFFF;
        margin-bottom: 5px;
    }
    QLineEdit, QPlainTextEdit {
        background-color: #2D2D2D;
        border: 1px solid #3E3E3E;
        border-radius: 8px;
        padding: 10px;
        color: #E0E0E0;
        font-size: 14px;
    }
    QPushButton {
        background-color: #3A3A3A;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        color: white;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #4A4A4A;
    }
    QPushButton:disabled {
        background-color: #2A2A2A;
        color: #555;
    }
"""
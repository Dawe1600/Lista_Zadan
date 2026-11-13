# styles.py
from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAbstractButton,
    QApplication,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

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
    QLabel#TaskCountBadge {
        background-color: #2D2D2D;
        color: #94A3B8;
        font-size: 12px;
        font-weight: 600;
        border-radius: 10px;
        padding: 2px 8px;
    }
    QLabel#TaskTitleLabel {
        color: #E0E0E0;
        font-family: "Consolas", monospace;
        font-size: 14px;
        font-weight: normal;
        padding: 0px;
    }
    QLabel#TaskDescLabel {
        color: #94A3B8;
        font-family: 'Segoe UI', sans-serif;
        font-size: 12px;
        font-weight: normal;
        padding: 0px;
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
    QPushButton[rowAction="true"] {
        background-color: #1F1F1F;
        border: 1px solid #353535;
        border-radius: 6px;
        color: #CBD5E1;
        padding: 0px;
        font-size: 12px;
    }
    QPushButton[rowAction="true"]:hover {
        background-color: #333333;
        border-color: #4E4E4E;
    }
    QPushButton[rowAction="true"]:disabled {
        color: #525252;
        border-color: #2A2A2A;
    }
    QPushButton#AiBtn {
        background-color: rgba(168, 85, 247, 0.16);
        border-color: rgba(168, 85, 247, 0.45);
        color: #E9D5FF;
    }
    QPushButton#DeleteBtn:hover {
        background-color: rgba(255, 85, 85, 0.22);
        border-color: rgba(255, 85, 85, 0.55);
        color: #FECACA;
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
    QLabel#DetailsTitle {
        font-size: 16px;
        font-weight: bold;
        color: #FFF;
        border: none;
    }
    QLabel#FieldLabel {
        color: #CCC;
        font-size: 13px;
        font-weight: bold;
        margin-top: 10px;
    }
    QLabel#AITitle {
        font-size: 16px;
        font-weight: bold;
        color: #a29bfe;
        border: none;
    }
    QLineEdit, QPlainTextEdit {
        background-color: #2D2D2D;
        border: 1px solid #3E3E3E;
        border-radius: 8px;
        padding: 10px;
        color: #E0E0E0;
        font-size: 14px;
    }
    QPlainTextEdit#AIResponseArea {
        background-color: #252526;
        color: #dcdcdc;
        font-size: 14px;
        border: 1px solid #3E3E3E;
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
    QPushButton#DialogCloseBtn {
        background: transparent;
        color: #AAA;
        border: none;
        font-size: 16px;
        padding: 0px;
    }
    QPushButton#DialogCloseBtn:hover {
        color: #FFF;
        background: transparent;
    }
    QCheckBox {
        color: #E0E0E0;
        font-size: 13px;
        spacing: 8px;
        margin-top: 4px;
    }
"""

_INTERACTIVE_WIDGETS = (QLineEdit, QPushButton, QListWidget, QAbstractButton, QPlainTextEdit)


class _FramelessDragFilter(QObject):
    """Event filter enabling drag-to-move on non-interactive areas of frameless windows."""

    def __init__(self, target: QWidget):
        super().__init__(target)
        self._target = target
        self._drag_active = False
        self._drag_offset = None

    def eventFilter(self, obj, event):
        if obj is not self._target:
            return False

        etype = event.type()
        if etype == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            child = self._target.childAt(event.pos())
            if child is None or not isinstance(child, _INTERACTIVE_WIDGETS):
                self._drag_active = True
                self._drag_offset = event.globalPos() - self._target.frameGeometry().topLeft()
                event.accept()
                return True
        elif etype == QEvent.MouseMove and self._drag_active and (event.buttons() & Qt.LeftButton):
            if self._drag_offset is not None:
                self._target.move(event.globalPos() - self._drag_offset)
                event.accept()
                return True
        elif etype == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self._drag_active = False
            self._drag_offset = None

        return False


def install_drag(widget: QWidget) -> None:
    """Attach frameless drag behavior to a widget without inheritance."""
    drag_filter = _FramelessDragFilter(widget)
    widget.installEventFilter(drag_filter)


def center_on_screen(widget: QWidget, parent: QWidget | None = None) -> None:
    """Center a widget on the screen containing parent (or the primary screen)."""
    geo = widget.frameGeometry()
    desktop = QApplication.desktop()
    screen_geo = desktop.availableGeometry(parent) if parent else desktop.availableGeometry()
    geo.moveCenter(screen_geo.center())
    widget.move(geo.topLeft())


def apply_task_item_style(item: QListWidgetItem, done: bool) -> None:
    """Apply active or completed visual styling to a QListWidgetItem."""
    font = item.font()
    font.setStrikeOut(done)
    item.setFont(font)
    item.setForeground(QColor(100, 100, 100) if done else QColor(224, 224, 224))

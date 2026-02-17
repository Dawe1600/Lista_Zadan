from PyQt5.QtCore import Qt

class DraggableMixin:
    _drag_active = False
    _drag_offset = None

    def _is_interactive_child(self, child):
        from PyQt5.QtWidgets import QLineEdit, QPushButton, QListWidget, QAbstractButton, QPlainTextEdit
        return isinstance(child, (QLineEdit, QPushButton, QListWidget, QAbstractButton, QPlainTextEdit))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.pos())
            if child is None or not self._is_interactive_child(child):
                self._drag_active = True
                self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.LeftButton and self._drag_offset is not None:
            self.move(event.globalPos() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = False
            self._drag_offset = None
        super().mouseReleaseEvent(event)
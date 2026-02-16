import sys
import os
import json
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout,
    QListWidget, QListWidgetItem, QInputDialog, QDialog, QDialogButtonBox, QLineEdit,
    QPlainTextEdit
)
from PyQt5.QtCore import Qt


class DraggableMixin:
    """
    Dodaje możliwość przeciągania okna bez ramek.
    Domyślnie NIE zaczyna przeciągania, jeśli kliknięto w kontrolki interaktywne.
    """
    _drag_active = False
    _drag_offset = None

    def _is_interactive_child(self, child):
        # Importy typów lokalnie, żeby nie robić cykli / problemów z kolejnością
        from PyQt5.QtWidgets import QLineEdit, QPushButton, QListWidget, QAbstractButton, QPlainTextEdit

        return isinstance(child, (QLineEdit, QPushButton, QListWidget, QAbstractButton, QPlainTextEdit))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.pos())
            # Przeciąganie tylko gdy nie klikamy w interaktywne kontrolki
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

class AddTaskDialog(DraggableMixin, QDialog):
    def __init__(self, parent=None, text="", description=""):
        super().__init__(parent)

        self.setWindowTitle("Zadanie")
        

        # Frameless + na wierzchu (opcjonalnie)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)

        # Jeśli chcesz prawdziwą przezroczystość okna, odkomentuj:
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setModal(True)

        layout = QVBoxLayout(self)

        title = QLabel("Dodaj zadanie:")
        title.setAlignment(Qt.AlignLeft)

        self.input = QLineEdit()
        self.input.setPlaceholderText("np. Zrobić backup, wysłać maila...")
        self.input.setText(text)
        self.input.textChanged.connect(self._validate)

        self.desc_input = QPlainTextEdit()
        self.desc_input.setPlaceholderText("Opis (opcjonalnie)...")
        self.desc_input.setPlainText(description)

        # Przyciski OK/Anuluj
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(title)
        layout.addWidget(self.input)
        layout.addWidget(self.desc_input)
        layout.addWidget(self.buttons)

        # Styl — dopasuj do swojego
        self.setStyleSheet("""
            QDialog {
                color: white;
                font-size: 16px;
                background-color: rgba(0, 0, 0, 170);
                border-radius: 10px;
                padding: 12px;
            }
            QLabel { font-size: 18px; }
            QLineEdit {
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 8px;
                padding: 8px;
                color: white;
            }
            QPlainTextEdit {
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 8px;
                padding: 8px;
                color: white;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 25);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 8px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)

        # Startowo OK zablokowany, dopóki coś nie wpiszesz
        self._validate(self.input.text())

        # Fokus od razu na polu + Enter zatwierdza (domyślnie)
        self.input.setFocus()

        # Centrowanie na ekranie
        self.adjustSize()
        geo = self.frameGeometry()
        screen_geo = QApplication.desktop().availableGeometry(parent) if parent else QApplication.desktop().availableGeometry()
        geo.moveCenter(screen_geo.center())
        self.move(geo.topLeft())

    def _validate(self, text: str):
        ok_btn = self.buttons.button(QDialogButtonBox.Ok)
        ok_btn.setEnabled(bool(text.strip()))

    def get_data(self):
        return self.input.text().strip(), self.desc_input.toPlainText().strip()

class ListaZadan(DraggableMixin, QWidget):
    # Plik z danymi — zapis obok skryptu
    DATA_FILE = os.path.join(os.path.dirname(__file__), 'tasks.json')

    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_tasks_into_list()  # wczytaj zapisane zadania przy starcie

        

    def initUI(self):
        self.setWindowTitle('Lista Zadań')
        self.setGeometry(1500, 750, 400, 300)

        # Bez ramek + zawsze na wierzchu
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint)
        # Jeśli chcesz przezroczyste tło, odkomentuj:
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.root = QVBoxLayout()
        self.header = QHBoxLayout()

        title = QLabel("Zadania:")
        self.header.addWidget(title, alignment=Qt.AlignLeft)

        # przycisk usuń zaznaczone
        self.del_btn = QPushButton("🗑")
        self.del_btn.clicked.connect(self.usun_zaznaczone)
        self.header.addWidget(self.del_btn, alignment=Qt.AlignRight)

        # przycisk dodaj
        self.add_btn = QPushButton('✏️')
        self.add_btn.clicked.connect(self.dodaj_zadanie)
        self.header.addWidget(self.add_btn, alignment=Qt.AlignRight)

        # Lista zadań z checkboxami
        self.list = QListWidget()
        self.list.setWordWrap(True)
        # Każda zmiana (odhaczenie/edycja tekstu) -> zapis do JSON
        self.list.itemChanged.connect(self.on_item_changed)
        # Podwójne kliknięcie -> edycja (opis)
        self.list.itemDoubleClicked.connect(self.edytuj_zadanie)

        self.root.addLayout(self.header)
        self.root.addWidget(self.list)
        self.setLayout(self.root)

        self.setStyleSheet("""
            color: white; font-size: 16px;
            background-color: rgba(0, 0, 0, 100);
            border-radius: 10px; padding: 10px;
        """)

    # Tworzy element listy z checkboxem (i możliwością edycji tekstu)
    def create_item(self, text, done=False, description=""):
        item = QListWidgetItem(text)
        # Usunięto Qt.ItemIsEditable, aby podwójne kliknięcie otwierało dialog edycji zamiast edycji in-line
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setCheckState(Qt.Checked if done else Qt.Unchecked)
        item.setData(Qt.UserRole, description)
        if description:
            item.setToolTip(description)

        self.apply_done_style(item)
        return item

    # Dodawanie nowego zadania
    def dodaj_zadanie(self):
        dlg = AddTaskDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            text, desc = dlg.get_data()
            if text:
                self.list.blockSignals(True)
                self.list.addItem(self.create_item(text, done=False, description=desc))
                self.list.blockSignals(False)
                self.save_tasks()

    def edytuj_zadanie(self, item):
        text = item.text()
        description = item.data(Qt.UserRole) or ""
        dlg = AddTaskDialog(self, text, description)
        if dlg.exec_() == QDialog.Accepted:
            new_text, new_desc = dlg.get_data()
            if new_text:
                self.list.blockSignals(True)
                item.setText(new_text)
                item.setData(Qt.UserRole, new_desc)
                item.setToolTip(new_desc)
                self.list.blockSignals(False)
                self.save_tasks()

    def usun_zaznaczone(self):
    # usuwamy od końca, żeby indeksy się nie rozjechały
        self.list.blockSignals(True)
        for i in range(self.list.count() - 1, -1, -1):
            item = self.list.item(i)
            if item.checkState() == Qt.Checked:
                self.list.takeItem(i)
        self.list.blockSignals(False)

        self.save_tasks()



    # Reaguj na odhaczenie/edytowanie elementu -> zapisz
    def on_item_changed(self, item):
        # zablokuj sygnały, bo ustawianie fontu/koloru też może triggerować itemChanged
        self.list.blockSignals(True)
        self.apply_done_style(item)
        self.list.blockSignals(False)

        self.save_tasks()

    # Wczytanie z JSON -> odtworzenie listy
    def load_tasks_into_list(self):
        tasks = []
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                    if not isinstance(tasks, list):
                        tasks = []
            except (json.JSONDecodeError, OSError):
                tasks = []

        self.list.blockSignals(True)
        self.list.clear()
        for t in tasks:
            text = t.get('text', '')
            done = bool(t.get('done', False))
            desc = t.get('description', '')
            if text:
                self.list.addItem(self.create_item(text, done, desc))
        self.list.blockSignals(False)

    # Zbierz dane z listy -> zapisz do JSON
    def save_tasks(self):
        tasks = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            tasks.append({
                'text': it.text(),
                'done': (it.checkState() == Qt.Checked),
                'description': it.data(Qt.UserRole) or ""
            })
        try:
            with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f'Błąd zapisu: {e}')

    def apply_done_style(self, item: QListWidgetItem):
        done = (item.checkState() == Qt.Checked)

        f = item.font()
        f.setStrikeOut(done)
        item.setFont(f)

        # opcjonalnie: wyszarz ukończone
        item.setForeground(QColor(170, 170, 170) if done else QColor(255, 255, 255))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ListaZadan()
    w.show()
    sys.exit(app.exec_())
import os
import json
import sys
from styles import MAIN_STYLE
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QMenu, QAction, QDialog, QStyledItemDelegate)
from PyQt5.QtCore import Qt, QStandardPaths, QSettings
from PyQt5.QtGui import QColor, QIcon, QPixmap, QPainter, QFont, QPen

from mixins import DraggableMixin
from dialogs import AddTaskDialog, TaskDetailsDialog, CompletedTasksDialog

class TaskDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.data(Qt.UserRole + 1): # is_problem
            painter.save()
            painter.setPen(QPen(QColor("#FF5555"), 2))
            painter.setBrush(Qt.NoBrush)
            rect = option.rect.adjusted(1, 1, -1, -1)
            painter.drawRoundedRect(rect, 8, 8)
            painter.restore()

class ListaZadan(DraggableMixin, QWidget):
    def __init__(self):
        super().__init__()
        self.DATA_FILE = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation), 'tasks.json')
        self.completed_tasks = []
        self.initUI()
        self.load_tasks_into_list()

    def initUI(self):
        self.setWindowTitle('Lista Zadań')
        self.setGeometry(1500, 750, 400, 300)
        self.setObjectName("MainWindow") # Dodane, żeby styl działał na konkretny widget
        self.setStyleSheet(MAIN_STYLE)

        # Ikona aplikacji (zielony ptaszek)
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Fallback: rysowanie dynamiczne, jeśli brak pliku
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setFont(QFont("Segoe UI Emoji", 32))
            painter.setPen(QColor("#55ff55"))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "✔")
            painter.end()
            self.setWindowIcon(QIcon(pixmap))

        # Bez ramek + zawsze na wierzchu
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint)
        # Jeśli chcesz przezroczyste tło, odkomentuj:
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.root = QVBoxLayout()
        self.header = QHBoxLayout()

        title = QLabel("Zadania:")
        self.header.addWidget(title, alignment=Qt.AlignLeft)

        self.header.addStretch()

        # przycisk ustawienia (zębatka)
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.clicked.connect(self.show_settings_menu)
        self.header.addWidget(self.settings_btn)

        # przycisk pokaż zakończone (zamiast kosza)
        self.history_btn = QPushButton("\u2714\uFE0F") # Checkmark emoji
        self.history_btn.clicked.connect(self.pokaz_zakonczone)
        self.header.addWidget(self.history_btn)

        # przycisk dodaj
        self.add_btn = QPushButton("\u270F\uFE0F")
        self.add_btn.clicked.connect(self.dodaj_zadanie)
        self.header.addWidget(self.add_btn)

        # Lista zadań z checkboxami
        self.list = QListWidget()
        self.list.setWordWrap(True)
        # Każda zmiana (odhaczenie/edycja tekstu) -> zapis do JSON
        self.list.itemChanged.connect(self.on_item_changed)
        # Podwójne kliknięcie -> edycja (opis)
        self.list.itemDoubleClicked.connect(self.edytuj_zadanie)
        
        # Menu kontekstowe i delegat (obramówka problemu)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_context_menu)
        self.list.setItemDelegate(TaskDelegate(self.list))

        self.root.addLayout(self.header)
        self.root.addWidget(self.list)
        self.setLayout(self.root)

    # Tworzy element listy z checkboxem (i możliwością edycji tekstu)
    def create_item(self, text, done=False, description="", is_problem=False):
        item = QListWidgetItem(text)
        
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setCheckState(Qt.Checked if done else Qt.Unchecked)
        item.setData(Qt.UserRole, description)
        item.setData(Qt.UserRole + 1, is_problem)
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

    def pokaz_zakonczone(self):
        dlg = CompletedTasksDialog(self, main_app=self)
        dlg.exec_()

    # Reaguj na odhaczenie/edytowanie elementu -> zapisz
    def on_item_changed(self, item):
        # Jeśli zadanie zostało zaznaczone (wykonane) -> przenieś do completed_tasks
        if item.checkState() == Qt.Checked:
            self.list.blockSignals(True)
            
            # Dodaj do listy pamięci
            self.completed_tasks.append({
                'text': item.text(),
                'done': True,
                'description': item.data(Qt.UserRole) or ""
            })
            
            # Usuń z widoku
            row = self.list.row(item)
            self.list.takeItem(row)
            
            self.list.blockSignals(False)
        
        self.save_tasks()

    def restore_task(self, text, description):
        # Metoda wywoływana przez okno historii, aby przywrócić zadanie
        # Usuwamy z completed_tasks (szukamy po treści - uproszczenie)
        self.completed_tasks = [t for t in self.completed_tasks if t['text'] != text]
        
        self.list.blockSignals(True)
        self.list.addItem(self.create_item(text, done=False, description=description))
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
        self.completed_tasks = []
        
        for t in tasks:
            text = t.get('text', '')
            done = bool(t.get('done', False))
            desc = t.get('description', '')
            is_problem = bool(t.get('is_problem', False))
            if text:
                if done:
                    self.completed_tasks.append(t)
                else:
                    self.list.addItem(self.create_item(text, done, desc, is_problem))
        self.list.blockSignals(False)

    # Zbierz dane z listy -> zapisz do JSON
    def save_tasks(self):
        # Zbieramy aktywne zadania z UI
        active_tasks = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            active_tasks.append({
                'text': it.text(),
                'done': (it.checkState() == Qt.Checked),
                'description': it.data(Qt.UserRole) or "",
                'is_problem': bool(it.data(Qt.UserRole + 1))
            })
            
        # Łączymy z zadaniami zakończonymi
        all_tasks = active_tasks + self.completed_tasks
        
        try:
            with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_tasks, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f'Błąd zapisu: {e}')

    def apply_done_style(self, item: QListWidgetItem):
        done = (item.checkState() == Qt.Checked)

        f = item.font()
        f.setStrikeOut(done)
        item.setFont(f)

        
        item.setForeground(QColor(100, 100, 100) if done else QColor(224, 224, 224))

    def show_settings_menu(self):
        menu = QMenu(self)
        
        autostart_action = QAction("Uruchamiaj przy starcie systemu", self)
        autostart_action.setCheckable(True)
        autostart_action.setChecked(self.check_autostart_status())
        autostart_action.triggered.connect(self.toggle_autostart)
        
        menu.addAction(autostart_action)
        menu.exec_(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft()))

    def check_autostart_status(self):
        settings = QSettings("HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", QSettings.NativeFormat)
        return settings.contains("ListaZadan")

    def toggle_autostart(self, checked):
        settings = QSettings("HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", QSettings.NativeFormat)
        if checked:
            app_path = sys.executable.replace('/', '\\')
            settings.setValue("ListaZadan", f'"{app_path}"')
        else:
            settings.remove("ListaZadan")

    def show_context_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        is_problem = bool(item.data(Qt.UserRole + 1))
        action = QAction("Usuń oznaczenie problemu" if is_problem else "Oznacz jako problem", self)
        action.triggered.connect(lambda: self.toggle_problem(item))
        menu.addAction(action)
        menu.exec_(self.list.mapToGlobal(pos))

    def toggle_problem(self, item):
        current = bool(item.data(Qt.UserRole + 1))
        item.setData(Qt.UserRole + 1, not current)
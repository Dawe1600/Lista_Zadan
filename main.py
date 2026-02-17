import sys
import os
import json
from PyQt5.QtGui import QColor, QIcon, QPixmap, QPainter, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout,
    QListWidget, QListWidgetItem, QInputDialog, QDialog, QDialogButtonBox, QLineEdit,
    QPlainTextEdit, QMenu, QAction
)
from PyQt5.QtCore import Qt, QStandardPaths, QSettings


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

        # Styl
        self.setStyleSheet("""
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
            QLineEdit {
                background-color: #2D2D2D;
                border: 1px solid #3E3E3E;
                border-radius: 8px;
                padding: 10px;
                color: #E0E0E0;
                font-size: 14px;
            }
            QPlainTextEdit {
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

class TaskDetailsDialog(DraggableMixin, QDialog):
    def __init__(self, parent=None, text="", description=""):
        super().__init__(parent)
        self.setWindowTitle("Szczegóły zadania")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Nagłówek
        header = QHBoxLayout()
        title_lbl = QLabel("Szczegóły zadania")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFF; border: none;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background: transparent; color: #AAA; border: none; font-size: 16px;")
        
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(close_btn)

        # Pola
        lbl_task = QLabel("Zadanie:")
        lbl_task.setStyleSheet("color: #CCC; font-size: 13px; font-weight: bold; margin-top: 10px;")
        
        self.task_view = QLineEdit(text)
        self.task_view.setReadOnly(True)
        
        lbl_desc = QLabel("Opis:")
        lbl_desc.setStyleSheet("color: #CCC; font-size: 13px; font-weight: bold; margin-top: 10px;")
        
        self.desc_view = QPlainTextEdit()
        self.desc_view.setPlainText(description if description else "(Brak opisu)")
        self.desc_view.setReadOnly(True)

        # Przycisk Zamknij na dole
        ok_btn = QPushButton("Zamknij")
        ok_btn.clicked.connect(self.accept)

        layout.addLayout(header)
        layout.addWidget(lbl_task)
        layout.addWidget(self.task_view)
        layout.addWidget(lbl_desc)
        layout.addWidget(self.desc_view)
        layout.addWidget(ok_btn)

        self.resize(350, 400)
        
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; border: 1px solid #333; border-radius: 15px; }
            QLabel { color: #FFFFFF; }
            QLineEdit, QPlainTextEdit {
                background-color: #252525; border: 1px solid #3E3E3E;
                border-radius: 8px; padding: 10px; color: #FFFFFF; font-size: 15px;
            }
            QPushButton { background-color: #3A3A3A; border: none; border-radius: 8px; padding: 8px 16px; color: white; font-weight: bold; }
            QPushButton:hover { background-color: #4A4A4A; }
        """)

        # Centrowanie na ekranie
        geo = self.frameGeometry()
        screen_geo = QApplication.desktop().availableGeometry(parent) if parent else QApplication.desktop().availableGeometry()
        geo.moveCenter(screen_geo.center())
        self.move(geo.topLeft())

class CompletedTasksDialog(DraggableMixin, QDialog):
    def __init__(self, parent=None, main_app=None):
        super().__init__(parent)
        self.main_app = main_app
        self.setWindowTitle("Zakończone zadania")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        title = QLabel("Wykonane zadania:")
        
        # Przycisk usuwania wszystkich zakończonych
        clear_btn = QPushButton("🗑")
        clear_btn.setToolTip("Usuń wszystkie zakończone")
        clear_btn.clicked.connect(self.clear_all_tasks)

        close_btn = QPushButton("✕")
        close_btn.clicked.connect(self.accept)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)
        header.addWidget(close_btn)

        self.list = QListWidget()
        self.list.itemChanged.connect(self.on_item_changed)
        self.list.itemDoubleClicked.connect(self.show_task_details)
        
        # Menu kontekstowe (Prawy Przycisk Myszy)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_context_menu)

        layout.addLayout(header)
        layout.addWidget(self.list)

        # Wczytaj zadania z listy completed_tasks głównej aplikacji
        self.load_items()

        self.resize(400, 500)
        # Styl (taki sam jak w głównej aplikacji)
        self.setStyleSheet(parent.styleSheet())

    def load_items(self):
        self.list.blockSignals(True)
        self.list.clear()
        for task in self.main_app.completed_tasks:
            item = QListWidgetItem(task['text'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, task.get('description', ''))
            
            # Styl przekreślony
            f = item.font()
            f.setStrikeOut(True)
            item.setFont(f)
            item.setForeground(QColor(100, 100, 100))
            
            self.list.addItem(item)
        self.list.blockSignals(False)

    def on_item_changed(self, item):
        # Jeśli użytkownik odznaczy zadanie w historii -> przywróć do głównych
        if item.checkState() == Qt.Unchecked:
            text = item.text()
            desc = item.data(Qt.UserRole)
            
            # Usuń z listy completed_tasks i dodaj do głównej listy
            self.main_app.restore_task(text, desc)
            
            # Usuń z tego widoku
            self.list.takeItem(self.list.row(item))

    def show_task_details(self, item):
        text = item.text()
        desc = item.data(Qt.UserRole) or ""
        
        # Otwieramy okno tylko do odczytu
        dlg = TaskDetailsDialog(self, text, desc)
        dlg.exec_()

    def show_context_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return
            
        menu = QMenu(self)
        restore_action = QAction("Przywróć", self)
        delete_action = QAction("Usuń", self)
        
        # Przywracanie: wystarczy odznaczyć checkbox, co wywoła on_item_changed
        restore_action.triggered.connect(lambda: item.setCheckState(Qt.Unchecked))
        delete_action.triggered.connect(lambda: self.delete_item(item))
        
        menu.addAction(restore_action)
        menu.addAction(delete_action)
        
        menu.exec_(self.list.mapToGlobal(pos))

    def delete_item(self, item):
        text = item.text()
        self.main_app.completed_tasks = [t for t in self.main_app.completed_tasks if t['text'] != text]
        self.list.takeItem(self.list.row(item))
        self.main_app.save_tasks()

    def clear_all_tasks(self):
        self.main_app.completed_tasks = []
        self.list.clear()
        self.main_app.save_tasks()

class ListaZadan(DraggableMixin, QWidget):
    def __init__(self):
        super().__init__()
        # Plik z danymi — zapis w Dokumentach
        self.DATA_FILE = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation), 'tasks.json')
        self.completed_tasks = [] # Lista słowników dla zadań wykonanych
        self.initUI()
        self.load_tasks_into_list()  # wczytaj zapisane zadania przy starcie

        

    def initUI(self):
        self.setWindowTitle('Lista Zadań')
        self.setGeometry(1500, 750, 400, 300)

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

        self.root.addLayout(self.header)
        self.root.addWidget(self.list)
        self.setLayout(self.root)

        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            ListaZadan {
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
        """)

    # Tworzy element listy z checkboxem (i możliwością edycji tekstu)
    def create_item(self, text, done=False, description=""):
        item = QListWidgetItem(text)
        
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
            if text:
                if done:
                    self.completed_tasks.append(t)
                else:
                    self.list.addItem(self.create_item(text, done, desc))
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
                'description': it.data(Qt.UserRole) or ""
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ListaZadan()
    w.show()
    sys.exit(app.exec_())
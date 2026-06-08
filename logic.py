import os
import json
import sys
from dialogs import AddTaskDialog, CompletedTasksDialog, AIDialog
from styles import MAIN_STYLE
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QMenu, QAction, QDialog, QStyledItemDelegate, QAbstractItemView, QMessageBox)
from PyQt5.QtCore import Qt, QStandardPaths, QSettings, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QPixmap, QPainter, QFont, QPen

from mixins import DraggableMixin
from dialogs import AddTaskDialog, CompletedTasksDialog, AIDialog
from planner_api import PlannerSync

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

class PlannerSyncWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            sync = PlannerSync()
            tasks = sync.get_my_planner_tasks()
            self.finished.emit(tasks)
        except Exception as e:
            self.error.emit(str(e))

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
        self.setObjectName("MainWindow")
        self.setStyleSheet(MAIN_STYLE)

        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setFont(QFont("Segoe UI Emoji", 32))
            painter.setPen(QColor("#55ff55"))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "✔")
            painter.end()
            self.setWindowIcon(QIcon(pixmap))

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.root = QVBoxLayout()
        self.header = QHBoxLayout()

        title = QLabel("Zadania:")
        self.header.addWidget(title, alignment=Qt.AlignLeft)

        self.header.addStretch()

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.clicked.connect(self.show_settings_menu)
        self.header.addWidget(self.settings_btn)

        self.sync_btn = QPushButton("🔄")
        self.sync_btn.clicked.connect(self.sync_planner_tasks)
        self.sync_btn.setToolTip("Synchronizuj z MS Planner")
        self.header.addWidget(self.sync_btn)

        self.history_btn = QPushButton("\u2714\uFE0F")
        self.history_btn.clicked.connect(self.show_completed_tasks)
        self.header.addWidget(self.history_btn)

        self.add_btn = QPushButton("\u270F\uFE0F")
        self.add_btn.clicked.connect(self.add_task)
        self.header.addWidget(self.add_btn)

        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.itemChanged.connect(self.on_item_changed)
        self.list.itemDoubleClicked.connect(self.edit_task)
        
        # Drag & Drop
        self.list.setDragDropMode(QAbstractItemView.InternalMove)
        self.list.setDefaultDropAction(Qt.MoveAction)
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.model().rowsMoved.connect(lambda: self.save_tasks())

        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_context_menu)
        self.list.setItemDelegate(TaskDelegate(self.list))

        self.root.addLayout(self.header)
        self.root.addWidget(self.list)
        self.setLayout(self.root)

        self.ai_enabled = self.check_ai_status()
    
    def check_ai_status(self):
        # Odczytujemy z tego samego miejsca co instalator
        settings = QSettings("ToDoList", "ToDoWidgetApp")
        # Zwraca 1 (True) lub 0 (False). Domyślnie 0 (False) jeśli brak wpisu.
        return bool(settings.value("EnableAI", 0, type=int))

    # Tworzy element listy z checkboxem (i możliwością edycji tekstu)
    def create_item(self, text, done=False, description="", is_problem=False, planner_id=None):
        item = QListWidgetItem(text)
        
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if not planner_id:
            flags |= Qt.ItemIsUserCheckable
        item.setFlags(flags)
        
        if not planner_id:
            item.setCheckState(Qt.Checked if done else Qt.Unchecked)
            
        item.setData(Qt.UserRole, description)
        item.setData(Qt.UserRole + 1, is_problem)
        item.setData(Qt.UserRole + 2, planner_id)
        
        tt = description
        if planner_id:
            tt = f"[Planner] {tt}" if tt else "[Zadanie z MS Planner]"
        if tt:
            item.setToolTip(tt)

        self.apply_done_style(item)
        
        if planner_id:
            item.setForeground(QColor("#a29bfe"))
            if done:
                f = item.font()
                f.setStrikeOut(True)
                item.setFont(f)
                item.setForeground(QColor("#635e9c"))
        
        return item

    # Dodawanie nowego zadania
    def add_task(self):
        dlg = AddTaskDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            text, desc = dlg.get_data()
            if text:
                self.list.blockSignals(True)
                self.list.addItem(self.create_item(text, done=False, description=desc))
                self.list.blockSignals(False)
                self.save_tasks()

    def edit_task(self, item):
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

    def show_completed_tasks(self):
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
            planner_id = t.get('planner_id')
            if text:
                if done and not planner_id:
                    self.completed_tasks.append(t)
                else:
                    self.list.addItem(self.create_item(text, done, desc, is_problem, planner_id))
        self.list.blockSignals(False)

    # Zbierz dane z listy -> zapisz do JSON
    def save_tasks(self):
        # Zbieramy aktywne zadania z UI
        active_tasks = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            active_tasks.append({
                'text': it.text(),
                'done': (it.checkState() == Qt.Checked) if not it.data(Qt.UserRole + 2) else False,
                'description': it.data(Qt.UserRole) or "",
                'is_problem': bool(it.data(Qt.UserRole + 1)),
                'planner_id': it.data(Qt.UserRole + 2)
            })
            
        # Łączymy z zadaniami zakończonymi
        all_tasks = active_tasks + self.completed_tasks
        
        try:
            with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_tasks, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f'Błąd zapisu: {e}')

    def apply_done_style(self, item: QListWidgetItem):
        if item.data(Qt.UserRole + 2):
            return # Styl zadań plannera nakładany jest w create_item
            
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
        
        #   Opcja: Zapytaj AI (tylko jeśli to problem)
        # 1. Czy zadanie jest problemem
        # 2. Czy użytkownik włączył AI w instalatorze (self.ai_enabled)
        if is_problem and self.ai_enabled:
            ai_action = QAction("🧠 Zapytaj AI jak to rozwiązać", self)
            ai_action.triggered.connect(lambda: self.ask_ai_solution(item))
            menu.addAction(ai_action)
            menu.addSeparator()

        # 2. Opcja: Oznaczanie jako problem
        problem_text = "Usuń oznaczenie problemu" if is_problem else "Oznacz jako problem"
        toggle_action = QAction(problem_text, self)
        toggle_action.triggered.connect(lambda: self.toggle_problem(item))
        menu.addAction(toggle_action)
        
        # 3. Opcja: Usuń zadanie (opcjonalnie, skoro to menu kontekstowe)
        delete_action = QAction("Usuń zadanie", self)
        delete_action.triggered.connect(lambda: self.delete_task_from_context(item))
        menu.addAction(delete_action)

        menu.exec_(self.list.mapToGlobal(pos))

    def toggle_problem(self, item):
        current = bool(item.data(Qt.UserRole + 1))
        item.setData(Qt.UserRole + 1, not current)

    def ask_ai_solution(self, item):
        text = item.text()
        desc = item.data(Qt.UserRole) or ""
        
        # Otwieramy okno AI
        dlg = AIDialog(self, text, desc)
        dlg.exec_()

    def delete_task_from_context(self, item):
        row = self.list.row(item)
        self.list.takeItem(row)
        self.save_tasks()

    def sync_planner_tasks(self):
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("⏳")
        self.worker = PlannerSyncWorker()
        self.worker.finished.connect(self.on_sync_finished)
        self.worker.error.connect(self.on_sync_error)
        self.worker.start()

    def on_sync_finished(self, planner_tasks):
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("🔄")
        
        # Oczyszczamy obecne zadania z Plannera, zachowując lokalne
        local_tasks = []
        for i in range(self.list.count()):
            it = self.list.item(i)
            if not it.data(Qt.UserRole + 2):
                local_tasks.append({
                    'text': it.text(),
                    'done': it.checkState() == Qt.Checked,
                    'description': it.data(Qt.UserRole) or "",
                    'is_problem': bool(it.data(Qt.UserRole + 1))
                })

        self.list.blockSignals(True)
        self.list.clear()
        
        # Przywracamy lokalne
        for t in local_tasks:
            self.list.addItem(self.create_item(t['text'], t['done'], t['description'], t['is_problem']))
            
        # Dodajemy pobrane z Plannera
        for pt in planner_tasks:
            title = pt.get('title', 'Bez nazwy')
            planner_id = pt.get('id')
            percent = pt.get('percentComplete', 0)
            done = (percent == 100)
            
            # W Plannerze często brak rozbudowanego opisu bez dodatkowego żądania, ale bierzemy co jest
            # Lub można nie dodawać ukończonych zadań do widoku
            if not done:
                self.list.addItem(self.create_item(title, done=done, description="", is_problem=False, planner_id=planner_id))
            
        self.list.blockSignals(False)
        self.save_tasks()
        QMessageBox.information(self, "Synchronizacja", "Zadania z MS Planner zostały zsynchronizowane.")

    def on_sync_error(self, err):
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("🔄")
        QMessageBox.warning(self, "Błąd synchronizacji", f"Wystąpił błąd:\n{err}")
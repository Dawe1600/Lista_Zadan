import os

from PyQt5.QtCore import Qt, QStandardPaths
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from app_settings import AppSettings
from dialogs import AIDialog, AddTaskDialog, CompletedTasksDialog
from styles import MAIN_STYLE, apply_task_item_style, install_drag
from task_store import JsonTaskRepository, Task, TaskStore


class TaskDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.data(Qt.UserRole + 1):  # is_important
            painter.save()
            painter.setPen(QPen(QColor("#FF5555"), 2))
            painter.setBrush(Qt.NoBrush)
            rect = option.rect.adjusted(1, 1, -1, -1)
            painter.drawRoundedRect(rect, 8, 8)
            painter.restore()


class ListaZadan(QWidget):
    def __init__(self, store: TaskStore | None = None, settings: AppSettings | None = None):
        super().__init__()
        if store is None:
            data_file = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
                "tasks.json",
            )
            store = TaskStore(JsonTaskRepository(data_file))
        self.store = store
        self.settings = settings or AppSettings()
        self.initUI()
        self.render_active_tasks()

    def initUI(self):
        self.setWindowTitle("Lista Zadań")
        self.setGeometry(1500, 750, 400, 300)
        self.setObjectName("MainWindow")
        self.setStyleSheet(MAIN_STYLE)

        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
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
        install_drag(self)

        self.root = QVBoxLayout()
        self.header = QHBoxLayout()

        title = QLabel("Zadania:")
        self.header.addWidget(title, alignment=Qt.AlignLeft)
        self.header.addStretch()

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.clicked.connect(self.show_settings_menu)
        self.header.addWidget(self.settings_btn)

        self.history_btn = QPushButton("\u2714\uFE0F")
        self.history_btn.clicked.connect(self.pokaz_zakonczone)
        self.header.addWidget(self.history_btn)

        self.add_btn = QPushButton("\u270F\uFE0F")
        self.add_btn.clicked.connect(self.dodaj_zadanie)
        self.header.addWidget(self.add_btn)

        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.itemChanged.connect(self.on_item_changed)
        self.list.itemDoubleClicked.connect(self.edytuj_zadanie)

        self.list.setDragDropMode(QAbstractItemView.InternalMove)
        self.list.setDefaultDropAction(Qt.MoveAction)
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list.model().rowsMoved.connect(self.on_rows_moved)

        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_context_menu)
        self.list.setItemDelegate(TaskDelegate(self.list))

        self.root.addLayout(self.header)
        self.root.addWidget(self.list)
        self.setLayout(self.root)

        self.ai_enabled = self.settings.is_ai_enabled()

    def create_item(self, task: Task) -> QListWidgetItem:
        item = QListWidgetItem(task.text)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setCheckState(Qt.Checked if task.done else Qt.Unchecked)
        item.setData(Qt.UserRole, task.id)
        item.setData(Qt.UserRole + 1, task.is_important)
        if task.description:
            item.setToolTip(task.description)
        apply_task_item_style(item, task.done)
        return item

    def render_active_tasks(self):
        self.list.blockSignals(True)
        self.list.clear()
        for task in self.store.active_tasks():
            self.list.addItem(self.create_item(task))
        self.list.blockSignals(False)

    def dodaj_zadanie(self):
        dlg = AddTaskDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            text, desc = dlg.get_data()
            if text:
                self.store.add(text, desc)
                self.render_active_tasks()

    def edytuj_zadanie(self, item: QListWidgetItem):
        task_id = item.data(Qt.UserRole)
        task = self.store.get(task_id)
        if task is None:
            return
        dlg = AddTaskDialog(self, task.text, task.description)
        if dlg.exec_() == QDialog.Accepted:
            new_text, new_desc = dlg.get_data()
            if new_text:
                self.store.update(task_id, new_text, new_desc)
                self.render_active_tasks()

    def pokaz_zakonczone(self):
        dlg = CompletedTasksDialog(self, store=self.store, on_changed=self.render_active_tasks)
        dlg.exec_()

    def on_item_changed(self, item: QListWidgetItem):
        if item.checkState() == Qt.Checked:
            task_id = item.data(Qt.UserRole)
            self.store.complete(task_id)
            self.render_active_tasks()

    def on_rows_moved(self):
        ordered_ids = [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]
        self.store.reorder_active(ordered_ids)

    def show_settings_menu(self):
        menu = QMenu(self)

        autostart_action = QAction("Uruchamiaj przy starcie systemu", self)
        autostart_action.setCheckable(True)
        autostart_action.setChecked(self.settings.is_autostart_enabled())
        autostart_action.triggered.connect(self.settings.set_autostart)

        menu.addAction(autostart_action)
        menu.exec_(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft()))

    def show_context_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return

        task = self.store.get(item.data(Qt.UserRole))
        if task is None:
            return

        menu = QMenu(self)

        if task.is_important and self.ai_enabled:
            ai_action = QAction("🧠 Zapytaj AI jak to rozwiązać", self)
            ai_action.triggered.connect(lambda: self.ask_ai_solution(task))
            menu.addAction(ai_action)
            menu.addSeparator()

        important_text = "Usuń oznaczenie ważności" if task.is_important else "Oznacz jako ważne"
        toggle_action = QAction(important_text, self)
        toggle_action.triggered.connect(lambda: self.toggle_important(task.id))
        menu.addAction(toggle_action)

        delete_action = QAction("Usuń zadanie", self)
        delete_action.triggered.connect(lambda: self.delete_task_from_context(task.id))
        menu.addAction(delete_action)

        menu.exec_(self.list.mapToGlobal(pos))

    def toggle_important(self, task_id: str):
        self.store.toggle_important(task_id)
        self.render_active_tasks()

    def ask_ai_solution(self, task: Task):
        dlg = AIDialog(self, task.text, task.description, settings=self.settings)
        dlg.exec_()

    def delete_task_from_context(self, task_id: str):
        self.store.delete(task_id)
        self.render_active_tasks()

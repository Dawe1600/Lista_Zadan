import os

from PyQt5.QtCore import QSize, Qt, QStandardPaths
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from .app_settings import AppSettings
from .dialogs import AIDialog, AddTaskDialog, CompletedTasksDialog
from .styles import MAIN_STYLE, install_drag
from .task_store import JsonTaskRepository, Task, TaskStore


def _resolve_icon_path() -> str:
    package_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(package_dir, "icon.ico"),
        os.path.abspath(os.path.join(package_dir, "..", "..", "icon.ico")),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[-1]


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
        self.setGeometry(1500, 750, 420, 340)
        self.setObjectName("MainWindow")
        self.setStyleSheet(MAIN_STYLE)

        icon_path = _resolve_icon_path()
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

        self.count_label = QLabel("0")
        self.count_label.setObjectName("TaskCountBadge")
        self.header.addWidget(self.count_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
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
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.setResizeMode(QListWidget.Adjust)
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
        item = QListWidgetItem()
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
        item.setData(Qt.UserRole, task.id)
        item.setData(Qt.UserRole + 1, task.is_important)
        if task.description:
            item.setToolTip(task.description)
        return item

    def _make_row_btn(
        self,
        label: str,
        object_name: str,
        tooltip: str,
        callback,
        enabled: bool = True,
    ) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName(object_name)
        btn.setProperty("rowAction", True)
        btn.setToolTip(tooltip)
        btn.setEnabled(enabled)
        btn.setFixedSize(24, 24)
        btn.clicked.connect(callback)
        return btn

    def _create_row_widget(self, task: Task, index: int, total: int) -> QWidget:
        row = QWidget()
        row.setObjectName("TaskRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(6)

        checkbox = QCheckBox()
        checkbox.setObjectName("TaskCompleteCheckbox")
        checkbox.setChecked(task.done)
        checkbox.stateChanged.connect(lambda state, tid=task.id: state == Qt.Checked and self.complete_task(tid))
        row_layout.addWidget(checkbox, alignment=Qt.AlignTop)

        body = QVBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(2)

        title_lbl = QLabel(task.text)
        title_lbl.setObjectName("TaskTitleLabel")
        title_lbl.setWordWrap(True)
        title_lbl.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        body.addWidget(title_lbl)

        if task.description:
            non_empty_lines = [line.strip() for line in task.description.splitlines() if line.strip()]
            if non_empty_lines:
                first_line = non_empty_lines[0]
                preview = first_line[:60] + ("…" if len(first_line) > 60 else "")
                desc_lbl = QLabel(preview)
                desc_lbl.setObjectName("TaskDescLabel")
                desc_lbl.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
                desc_lbl.setToolTip(task.description)
                body.addWidget(desc_lbl)

        row_layout.addLayout(body, stretch=1)

        tools = QHBoxLayout()
        tools.setContentsMargins(0, 0, 0, 0)
        tools.setSpacing(3)

        move_up_btn = self._make_row_btn(
            "↑",
            "MoveUpBtn",
            "Przesuń w górę",
            lambda _checked=False, tid=task.id: self.move_task(tid, -1),
            enabled=index > 0,
        )
        move_down_btn = self._make_row_btn(
            "↓",
            "MoveDownBtn",
            "Przesuń w dół",
            lambda _checked=False, tid=task.id: self.move_task(tid, 1),
            enabled=index < total - 1,
        )
        ai_btn = self._make_row_btn(
            "🧠",
            "AiBtn",
            "Zapytaj AI jak to rozwiązać",
            lambda _checked=False, t=task: self.ask_ai_solution(t),
        )
        ai_btn.setVisible(bool(task.is_important and self.ai_enabled))

        important_btn = self._make_row_btn(
            "★" if task.is_important else "☆",
            "ImportantBtn",
            "Usuń oznaczenie ważności" if task.is_important else "Oznacz jako ważne",
            lambda _checked=False, tid=task.id: self.toggle_important(tid),
        )
        delete_btn = self._make_row_btn(
            "✕",
            "DeleteBtn",
            "Usuń zadanie",
            lambda _checked=False, tid=task.id: self.delete_task(tid),
        )

        for btn in (move_up_btn, move_down_btn, ai_btn, important_btn, delete_btn):
            tools.addWidget(btn)

        row_layout.addLayout(tools)
        return row

    def move_task(self, task_id: str, delta: int):
        ids = [t.id for t in self.store.active_tasks()]
        if task_id not in ids:
            return
        idx = ids.index(task_id)
        target = idx + delta
        if target < 0 or target >= len(ids):
            return
        ids[idx], ids[target] = ids[target], ids[idx]
        self.store.reorder_active(ids)
        self.render_active_tasks()

    def complete_task(self, task_id: str):
        self.store.complete(task_id)
        self.render_active_tasks()

    def render_active_tasks(self):
        active = self.store.active_tasks()
        self.count_label.setText(str(len(active)))
        self.list.blockSignals(True)
        self.list.clear()
        total = len(active)
        vp_width = self.list.viewport().width()
        if vp_width <= 0:
            vp_width = max(self.width() - 32, 200)
        for index, task in enumerate(active):
            item = self.create_item(task)
            row_widget = self._create_row_widget(task, index, total)
            row_widget.setFixedWidth(vp_width)
            row_widget.adjustSize()
            item.setSizeHint(QSize(vp_width, row_widget.sizeHint().height() + 4))
            self.list.addItem(item)
            self.list.setItemWidget(item, row_widget)
        self.list.blockSignals(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_row_sizes()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_row_sizes()

    def _sync_row_sizes(self):
        vp_width = self.list.viewport().width()
        if vp_width <= 0:
            return
        for i in range(self.list.count()):
            item = self.list.item(i)
            row_widget = self.list.itemWidget(item)
            if row_widget is not None:
                row_widget.setFixedWidth(vp_width)
                row_widget.adjustSize()
                item.setSizeHint(QSize(vp_width, row_widget.sizeHint().height() + 4))

    def dodaj_zadanie(self):
        dlg = AddTaskDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            text, desc, is_important = dlg.get_data()
            if text:
                self.store.add(text, desc, is_important=is_important)
                self.render_active_tasks()

    def edytuj_zadanie(self, item: QListWidgetItem):
        task_id = item.data(Qt.UserRole)
        task = self.store.get(task_id)
        if task is None:
            return
        dlg = AddTaskDialog(self, task.text, task.description, is_important=task.is_important)
        if dlg.exec_() == QDialog.Accepted:
            new_text, new_desc, new_important = dlg.get_data()
            if new_text:
                self.store.update(task_id, new_text, new_desc, is_important=new_important)
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
        self.render_active_tasks()

    def set_ai_enabled(self, enabled: bool):
        self.settings.set_ai_enabled(enabled)
        self.ai_enabled = self.settings.is_ai_enabled()
        self.render_active_tasks()

    def build_settings_menu(self) -> QMenu:
        menu = QMenu(self)

        autostart_action = QAction("Uruchamiaj przy starcie systemu", self)
        autostart_action.setCheckable(True)
        autostart_action.setChecked(self.settings.is_autostart_enabled())
        autostart_action.triggered.connect(self.settings.set_autostart)

        ai_action = QAction("Asystent AI", self)
        ai_action.setCheckable(True)
        ai_action.setChecked(self.settings.is_ai_enabled())
        ai_action.triggered.connect(self.set_ai_enabled)

        menu.addAction(autostart_action)
        menu.addAction(ai_action)
        return menu

    def show_settings_menu(self):
        menu = self.build_settings_menu()
        menu.exec_(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomLeft()))

    def build_context_menu(self, task: Task) -> QMenu:
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
        delete_action.triggered.connect(lambda: self.delete_task(task.id))
        menu.addAction(delete_action)

        return menu

    def show_context_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return

        task = self.store.get(item.data(Qt.UserRole))
        if task is None:
            return

        menu = self.build_context_menu(task)
        menu.exec_(self.list.mapToGlobal(pos))

    def toggle_important(self, task_id: str):
        self.store.toggle_important(task_id)
        self.render_active_tasks()

    def ask_ai_solution(self, task: Task):
        dlg = AIDialog(self, task.text, task.description, settings=self.settings)
        dlg.exec_()

    def delete_task(self, task_id: str):
        self.store.delete(task_id)
        self.render_active_tasks()

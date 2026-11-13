import google.generativeai as genai
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QAction,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from .app_settings import AppSettings
from .styles import DIALOG_STYLE, apply_task_item_style, center_on_screen, install_drag
from .task_store import TaskStore


class FramelessDialog(QDialog):
    """Shared base for frameless, draggable, translucent dialogs."""

    def __init__(self, parent=None, stay_on_top: bool = False):
        super().__init__(parent)
        self.setStyleSheet(DIALOG_STYLE)
        flags = Qt.FramelessWindowHint | Qt.Dialog
        if stay_on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        install_drag(self)


class AddTaskDialog(FramelessDialog):
    def __init__(self, parent=None, text="", description="", is_important: bool = False):
        super().__init__(parent, stay_on_top=True)
        self.setWindowTitle("Zadanie")

        layout = QVBoxLayout(self)

        title = QLabel("Edytuj zadanie:" if text else "Dodaj zadanie:")
        title.setAlignment(Qt.AlignLeft)

        self.input = QLineEdit()
        self.input.setPlaceholderText("np. Zrobić backup, wysłać maila...")
        self.input.setText(text)
        self.input.textChanged.connect(self._validate)

        self.desc_input = QPlainTextEdit()
        self.desc_input.setPlaceholderText("Opis (opcjonalnie)...")
        self.desc_input.setPlainText(description)

        self.important_checkbox = QCheckBox("Oznacz jako ważne")
        self.important_checkbox.setChecked(bool(is_important))

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(title)
        layout.addWidget(self.input)
        layout.addWidget(self.desc_input)
        layout.addWidget(self.important_checkbox)
        layout.addWidget(self.buttons)

        self._validate(self.input.text())
        self.input.setFocus()

        self.adjustSize()
        center_on_screen(self, parent)

    def _validate(self, text: str):
        ok_btn = self.buttons.button(QDialogButtonBox.Ok)
        ok_btn.setEnabled(bool(text.strip()))

    def get_data(self):
        return (
            self.input.text().strip(),
            self.desc_input.toPlainText().strip(),
            self.important_checkbox.isChecked(),
        )


class TaskDetailsDialog(FramelessDialog):
    def __init__(self, parent=None, text="", description=""):
        super().__init__(parent)
        self.setWindowTitle("Szczegóły zadania")

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title_lbl = QLabel("Szczegóły zadania")
        title_lbl.setObjectName("DetailsTitle")

        close_btn = QPushButton("✕")
        close_btn.setObjectName("DialogCloseBtn")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.accept)

        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(close_btn)

        lbl_task = QLabel("Zadanie:")
        lbl_task.setObjectName("FieldLabel")

        self.task_view = QLineEdit(text)
        self.task_view.setReadOnly(True)

        lbl_desc = QLabel("Opis:")
        lbl_desc.setObjectName("FieldLabel")

        self.desc_view = QPlainTextEdit()
        self.desc_view.setPlainText(description if description else "(Brak opisu)")
        self.desc_view.setReadOnly(True)

        ok_btn = QPushButton("Zamknij")
        ok_btn.clicked.connect(self.accept)

        layout.addLayout(header)
        layout.addWidget(lbl_task)
        layout.addWidget(self.task_view)
        layout.addWidget(lbl_desc)
        layout.addWidget(self.desc_view)
        layout.addWidget(ok_btn)

        self.resize(350, 400)
        center_on_screen(self, parent)


class CompletedTasksDialog(FramelessDialog):
    def __init__(self, parent=None, store: TaskStore | None = None, on_changed=None):
        super().__init__(parent)
        self.store = store
        self._on_changed = on_changed
        self.setWindowTitle("Zakończone zadania")

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Wykonane zadania:")

        clear_btn = QPushButton("🗑")
        clear_btn.setToolTip("Usuń wszystkie zakończone")
        clear_btn.clicked.connect(self.clear_all_tasks)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("DialogCloseBtn")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.accept)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)
        header.addWidget(close_btn)

        self.list = QListWidget()
        self.list.itemChanged.connect(self.on_item_changed)
        self.list.itemDoubleClicked.connect(self.show_task_details)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_context_menu)

        layout.addLayout(header)
        layout.addWidget(self.list)

        self.load_items()
        self.resize(400, 500)
        center_on_screen(self, parent)

    def load_items(self):
        self.list.blockSignals(True)
        self.list.clear()
        if self.store is not None:
            for task in self.store.completed_tasks():
                item = QListWidgetItem(task.text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, task.id)
                apply_task_item_style(item, done=True)
                self.list.addItem(item)
        self.list.blockSignals(False)

    def on_item_changed(self, item):
        if item.checkState() == Qt.Unchecked and self.store is not None:
            task_id = item.data(Qt.UserRole)
            self.store.restore(task_id)
            self.list.takeItem(self.list.row(item))
            if self._on_changed:
                self._on_changed()

    def show_task_details(self, item):
        task_id = item.data(Qt.UserRole)
        task = self.store.get(task_id) if self.store is not None else None
        text = task.text if task else item.text()
        desc = task.description if task else ""
        dlg = TaskDetailsDialog(self, text, desc)
        dlg.exec_()

    def show_context_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        restore_action = QAction("Przywróć", self)
        delete_action = QAction("Usuń", self)

        restore_action.triggered.connect(lambda: item.setCheckState(Qt.Unchecked))
        delete_action.triggered.connect(lambda: self.delete_item(item))

        menu.addAction(restore_action)
        menu.addAction(delete_action)
        menu.exec_(self.list.mapToGlobal(pos))

    def delete_item(self, item):
        if self.store is not None:
            self.store.delete(item.data(Qt.UserRole))
        self.list.takeItem(self.list.row(item))

    def clear_all_tasks(self):
        if self.store is not None:
            self.store.clear_completed()
        self.list.clear()


class AIWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, task_text, task_desc, settings: AppSettings | None = None):
        super().__init__()
        self.task_text = task_text
        self.task_desc = task_desc
        self.settings = settings or AppSettings()

    def run(self):
        klucz = self.settings.get_gemini_api_key()

        if not klucz:
            self.error.emit(
                "Brak klucza API! Aplikacja nie została skonfigurowana.\n"
                "Uruchom instalator ponownie i podaj klucz."
            )
            return

        try:
            genai.configure(api_key=klucz)
            model = genai.GenerativeModel("gemini-2.5-flash")

            prompt = (
                f"Jesteś asystentem produktywności. Użytkownik ma problem z następującym zadaniem: '{self.task_text}'. "
                f"Opis zadania: '{self.task_desc}'. "
                "Podaj 3 konkretne, krótkie kroki, jak rozwiązać ten problem lub jak zacząć. "
                "Odpowiedź sformatuj w czytelnych punktach, bez zbędnego wstępu."
            )

            response = model.generate_content(prompt)

            if response and response.text:
                self.finished.emit(response.text)
            else:
                self.error.emit("Model AI nie zwrócił odpowiedzi (pusta treść).")

        except Exception as e:
            self.error.emit(f"Błąd połączenia z AI:\n{str(e)}")


class AIDialog(FramelessDialog):
    def __init__(self, parent=None, task_text="", task_desc="", settings: AppSettings | None = None):
        super().__init__(parent)
        self.settings = settings or AppSettings()
        self.setWindowTitle("Asystent AI")
        self.resize(400, 450)

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title_lbl = QLabel("🧠 Sugestie AI")
        title_lbl.setObjectName("AITitle")

        close_btn = QPushButton("✕")
        close_btn.setObjectName("DialogCloseBtn")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.reject)

        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(close_btn)

        self.response_area = QPlainTextEdit()
        self.response_area.setObjectName("AIResponseArea")
        self.response_area.setReadOnly(True)
        self.response_area.setPlaceholderText("Łączenie z AI...")

        ok_btn = QPushButton("Dzięki, rozumiem")
        ok_btn.clicked.connect(self.accept)

        layout.addLayout(header)
        layout.addWidget(self.response_area)
        layout.addWidget(ok_btn)

        center_on_screen(self, parent)
        self.start_ai_query(task_text, task_desc)

    def start_ai_query(self, text, desc):
        self.response_area.setPlainText("🤖 Analizuję problem...\nProszę czekać.")

        self.worker = AIWorker(text, desc, settings=self.settings)
        self.worker.finished.connect(self.display_result)
        self.worker.error.connect(self.display_error)
        self.worker.start()

    def display_result(self, text):
        self.response_area.setPlainText(text)

    def display_error(self, error_msg):
        self.response_area.setPlainText(f"Wystąpił błąd połączenia:\n{error_msg}")

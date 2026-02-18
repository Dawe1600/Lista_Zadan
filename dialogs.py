from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPlainTextEdit, QDialogButtonBox, QHBoxLayout, 
                             QPushButton, QListWidget, QListWidgetItem, QMenu, QAction, QApplication)
from PyQt5.QtCore import Qt
from styles import DIALOG_STYLE
from PyQt5.QtGui import QColor
from mixins import DraggableMixin
from PyQt5.QtCore import QThread, pyqtSignal, QSettings
import google.generativeai as genai

def get_api_key():
    settings = QSettings("ToDoList", "ToDoWidgetApp")
    
    # 1. Najpierw sprawdzamy, czy AI jest w ogóle włączone (z instalatora)
    # Domyślnie zwracamy 0 (False), jeśli wpisu nie ma
    ai_enabled = bool(settings.value("EnableAI", 0, type=int))
    
    if not ai_enabled:
        return None  # Jeśli użytkownik wyłączył AI, udajemy, że nie ma klucza

    # 2. Jeśli włączone, pobieramy klucz
    api_key = settings.value("GeminiApiKey", type=str)
    
    # Zwracamy klucz tylko jeśli nie jest pusty
    if api_key and api_key.strip():
        return api_key
    
    return None

class AddTaskDialog(DraggableMixin, QDialog):
    def __init__(self, parent=None, text="", description=""):
        super().__init__(parent)

        self.setStyleSheet(DIALOG_STYLE)
        self.setWindowTitle("Zadanie")
        

        # Frameless + na wierzchu
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)

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

        self.setStyleSheet(DIALOG_STYLE)
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
        

        # Centrowanie na ekranie
        geo = self.frameGeometry()
        screen_geo = QApplication.desktop().availableGeometry(parent) if parent else QApplication.desktop().availableGeometry()
        geo.moveCenter(screen_geo.center())
        self.move(geo.topLeft())

class CompletedTasksDialog(DraggableMixin, QDialog):
    def __init__(self, parent=None, main_app=None):
        super().__init__(parent)
        self.main_app = main_app
        self.setStyleSheet(DIALOG_STYLE)
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


class AIWorker(QThread):

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, task_text, task_desc):
        super().__init__()
        self.task_text = task_text
        self.task_desc = task_desc

    def run(self):
        # 1. Pobieramy klucz z rejestru/ustawień
        klucz = get_api_key()

        # 2. Sprawdzamy czy klucz istnieje PRZED próbą połączenia
        if not klucz:
            self.error.emit(
                "Brak klucza API! Aplikacja nie została skonfigurowana.\n"
                "Uruchom instalator ponownie i podaj klucz."
            )
            return  # <--- Ważne: przerywamy, żeby nie spowodować crasha

        try:
            # 3. Konfiguracja biblioteki
            genai.configure(api_key=klucz)
            
            # 4. Twój sprawdzony model
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = (
                f"Jesteś asystentem produktywności. Użytkownik ma problem z następującym zadaniem: '{self.task_text}'. "
                f"Opis zadania: '{self.task_desc}'. "
                "Podaj 3 konkretne, krótkie kroki, jak rozwiązać ten problem lub jak zacząć. "
                "Odpowiedź sformatuj w czytelnych punktach, bez zbędnego wstępu."
            )
            
            # Generowanie odpowiedzi
            response = model.generate_content(prompt)
            
            if response and response.text:
                self.finished.emit(response.text)
            else:
                self.error.emit("Model AI nie zwrócił odpowiedzi (pusta treść).")
            
        except Exception as e:
            # Łapiemy błędy (np. brak internetu, błąd 404 modelu, limit tokenów)
            self.error.emit(f"Błąd połączenia z AI:\n{str(e)}")

class AIDialog(DraggableMixin, QDialog):
    def __init__(self, parent=None, task_text="", task_desc=""):
        super().__init__(parent)
        self.setStyleSheet(DIALOG_STYLE)
        self.setWindowTitle("Asystent AI")
        
        # Ustawienia okna
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.resize(400, 450)

        layout = QVBoxLayout(self)

        # Nagłówek
        header = QHBoxLayout()
        title_lbl = QLabel("🧠 Sugestie AI")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #a29bfe; border: none;")
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.reject) # Reject przerywa też wątek jeśli trwa
        close_btn.setStyleSheet("background: transparent; color: #AAA; border: none; font-size: 16px;")
        
        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(close_btn)

        # Pole tekstowe na odpowiedź
        self.response_area = QPlainTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setPlaceholderText("Łączenie z AI...")
        self.response_area.setStyleSheet("""
            QPlainTextEdit {
                background-color: #252526; 
                color: #dcdcdc; 
                font-size: 14px; 
                border: 1px solid #3E3E3E;
            }
        """)

        # Przycisk Zamknij
        ok_btn = QPushButton("Dzięki, rozumiem")
        ok_btn.clicked.connect(self.accept)

        layout.addLayout(header)
        layout.addWidget(self.response_area)
        layout.addWidget(ok_btn)

        # Centrowanie
        self.adjust_position(parent)

        # Uruchomienie AI
        self.start_ai_query(task_text, task_desc)

    def adjust_position(self, parent):
        geo = self.frameGeometry()
        screen_geo = QApplication.desktop().availableGeometry(parent) if parent else QApplication.desktop().availableGeometry()
        geo.moveCenter(screen_geo.center())
        self.move(geo.topLeft())

    def start_ai_query(self, text, desc):
        self.response_area.setPlainText("🤖 Analizuję problem...\nProszę czekać.")
        
        self.worker = AIWorker(text, desc)
        self.worker.finished.connect(self.display_result)
        self.worker.error.connect(self.display_error)
        self.worker.start()

    def display_result(self, text):
        self.response_area.setPlainText(text)

    def display_error(self, error_msg):
        self.response_area.setPlainText(f"Wystąpił błąd połączenia:\n{error_msg}")
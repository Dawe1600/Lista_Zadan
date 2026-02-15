import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt

class ListaZadan(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self): 
        self.setWindowTitle('Lista Zadań')

        self.setGeometry(1500, 20, 400, 300)

        ## 1. Usuń ramki okna
        #self.setWindowFlags(Qt.FramelessWindowHint)
        ## 2. Ustaw przezroczyste tło
        #self.setAttribute(Qt.WA_TranslucentBackground)
        ## 3. Ustaw okno na spodzie i ukryj z paska zadań
        #self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.row1 = QHBoxLayout()
        self.col1 = QVBoxLayout()
        self.col2 = QVBoxLayout()
        self.setStyleSheet(""" 
                            color: white; font-size: 20px;
                            background-color: rgba(0, 0, 0, 100);
                            border-radius: 10px; padding: 10px;
                           """)

        self.col1.addWidget(QLabel("Zadania: "))
        self.col1.setAlignment(Qt.AlignLeft)
        
        self.dodaj = QPushButton('✏️')
        self.col2.addWidget(self.dodaj)  
        self.col2.setAlignment(Qt.AlignRight) 


        self.row1.addLayout(self.col1)
        self.row1.addLayout(self.col2)
        self.row1.setAlignment(Qt.AlignTop)
        self.setLayout(self.row1)
        self.dodaj.clicked.connect(self.dodaj_zadanie)


    def dodaj_zadanie(self):
        self.msg = QMessageBox()
        self.msg.setText("Dodaj zadanie:")
        self.msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        # 1. Usuń ramki okna
        self.msg.setWindowFlags(Qt.FramelessWindowHint)
        # 2. Ustaw przezroczyste tło
        self.msg.setAttribute(Qt.WA_TranslucentBackground)
        # 3. Ustaw okno na spodzie i ukryj z paska zadań
        self.msg.setWindowFlags(self.msg.windowFlags() | Qt.WindowStaysOnTopHint)

        input_field = QLineEdit()

        layout_input = self.msg.layout()
        layout_input.addWidget(input_field, 1, 1)
        self.msg.setStyleSheet(""" 
                            color: white; font-size: 20px;
                            background-color: rgba(0, 0, 0, 100);
                            border-radius: 10px; padding: 10px;
                           """)
        
        retval = self.msg.exec()
        if retval == QMessageBox.StandardButton.Ok:
            print("Wprowadzono:", input_field.text()) # Pobranie tekstu [3]
        else:
            print("Anulowano")


        ## 1. Usuń ramki okna
        #self.setWindowFlags(Qt.FramelessWindowHint)
        #
        ## 2. Ustaw przezroczyste tło
        #self.setAttribute(Qt.WA_TranslucentBackground)
        #
        ## 3. Ustaw okno na spodzie i ukryj z paska zadań
        #self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnBottomHint)

        ## Przykładowa treść (będzie widoczna, mimo przezroczystego tła)
        #layout = QVBoxLayout()
        #label = QLabel("To jest przezroczysta aplikacja")
        #label.setStyleSheet("color: white; font-size: 20px; background-color: rgba(0, 0, 0, 100); border-radius: 10px; padding: 10px;")
        #layout.addWidget(label)
        #self.setLayout(layout)
        #
        #self.setGeometry(100, 100, 400, 200)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ListaZadan = ListaZadan()
    ListaZadan.show()
    sys.exit(app.exec_())

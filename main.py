import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt

class ListaZadan(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self): 
        self.setWindowTitle('Lista Zadań')
        self.setGeometry(100, 100, 400, 300)


        self.dodaj = QPushButton('Dodaj Zadanie', self)
        self.dodaj.clicked.connect(self.dodaj_zadanie)
        self.




    def dodaj_zadanie(self):
        pass

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

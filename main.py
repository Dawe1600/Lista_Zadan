import sys
from PyQt5.QtWidgets import QApplication
from logic import ListaZadan

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ListaZadan()
    w.show()
    sys.exit(app.exec_())
import sys

from PyQt5.QtWidgets import QApplication

from .logic import ListaZadan


def main() -> int:
    app = QApplication(sys.argv)
    window = ListaZadan()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())

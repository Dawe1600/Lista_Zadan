import os
import sys

_SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from lista_zadan.__main__ import main

if __name__ == "__main__":
    sys.exit(main())

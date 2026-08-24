import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from app.ui import MainWindow

def main():
    app=QApplication(sys.argv)
    app.setApplicationName("Principais Capas")
    app.setOrganizationName("Principais Capas")
    w=MainWindow(); w.show()
    return app.exec()

if __name__=="__main__":
    raise SystemExit(main())

import os
import sys

# O Chromium do Qt não deve suspender timers/lazy-load das páginas que ficam
# anexadas fora da área visível. Isso aproxima o comportamento da WebView Android.
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows",
)

from PySide6.QtWidgets import QApplication
from app.ui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Principais Capas")
    app.setOrganizationName("Principais Capas")
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

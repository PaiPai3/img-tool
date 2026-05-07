import sys
from PyQt5.QtWidgets import QApplication
from app.main_window import MainWindow
from core.i18n import Translator
from core.cache_manager import CacheManager


def main():
    CacheManager.ensure_dirs()

    settings = CacheManager.load_settings()
    if settings.get("language"):
        Translator.instance().set_locale(settings["language"])

    app = QApplication(sys.argv)
    app.setApplicationName("Image Tool")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

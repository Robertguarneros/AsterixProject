import ctypes
import os
import platform
import sys

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

# Tocado por David
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asterix Decoder")

        # Create a central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Set App Icon not necessary when building the executable
        if platform.system() == "Windows":
            myappid = "mycompany.myproduct.subproduct.version"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # This allows us to set the icon for all the title bars and popups
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        self.setWindowIcon(QIcon(icon_path))

        # Create main menu
        main_menu = self.menuBar()

        # Create submenu for conversion
        conversion_menu = main_menu.addMenu("Conversion")
        conversion_menu.addAction("Convert to CSV")

        # Create submenu for help
        help_menu = main_menu.addMenu("Help")
        help_menu.addAction("Manual")
        help_menu.addAction("About")

        # Add map
        self.web_view = QWebEngineView()

        # Load the custom Leaflet map HTML file
        html_path = os.path.join(os.path.dirname(__file__), "map.html")
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(html_path)))

        # Create a layout for the central widget
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.web_view)

        # Example: Add an aircraft after loading
        self.web_view.loadFinished.connect(self.add_aircraft_example)

    def add_aircraft_example(self):
        """Adds an example aircraft at a specific position."""
        latitude = 41.3874 
        longitude = 2.1686
        self.web_view.page().runJavaScript(f"addAircraft({latitude}, {longitude});")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.showMaximized()
    sys.exit(app.exec_())

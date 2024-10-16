import ctypes
import os
import platform
import sys
import csv

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QFileDialog, QAction, QDialog, QHeaderView, QProgressBar, QComboBox, QPushButton,
    QHBoxLayout, QLabel
)

class ProgressDialog(QDialog):
    """Dialog to show the progress of CSV loading."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading CSV Data")
        self.setFixedSize(300, 100)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 240, 25)

        # Label
        self.label = QLabel("Loading, please wait...", self)
        self.label.setAlignment(Qt.AlignCenter)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def set_progress(self, value):
        """Updates the progress bar."""
        self.progress_bar.setValue(value)

class CSVTableDialog(QDialog):
    """Dialog to show CSV data in a table with filtering capabilities."""
    def __init__(self, csv_file_path, parent=None, progress_dialog=None):
        super().__init__(parent)
        self.setWindowTitle("CSV Data")

        # Create table widget
        self.table_widget = QTableWidget()

        # Filter options
        self.filter_combobox = QComboBox()
        self.filter_combobox.addItem("No Filter")
        self.filter_combobox.addItem("Remove Blancos Puros")
        self.filter_combobox.addItem("Remove Fixed Transponder")
        self.filter_combobox.addItem("Filter by Area (Lat/Long)")
        self.filter_combobox.addItem("Remove On Ground Flights")

        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.apply_filters)

        # Filter layout
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.filter_combobox)
        filter_layout.addWidget(self.apply_filter_button)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(filter_layout)
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

        # Load CSV data with a progress dialog
        self.load_csv_data(csv_file_path, progress_dialog)

        # Allow window to be maximized with a system maximize button
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        # Show the dialog in a normal windowed mode, user can maximize it
        self.showMaximized()

    def load_csv_data(self, csv_file_path, progress_dialog):
        """Loads data from the CSV file and displays it in the table."""
        with open(csv_file_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')  # Specify ';' as the delimiter
            data = list(reader)
            total_rows = len(data)

            if data:
                # Set row and column count
                self.table_widget.setRowCount(total_rows - 1)  # Exclude header
                self.table_widget.setColumnCount(len(data[0]))  # Use first row to set column count

                # Set headers
                headers = data[0]
                self.table_widget.setHorizontalHeaderLabels(headers)

                # Populate table with data and update progress dialog
                for row_idx, row_data in enumerate(data[1:]):  # Skip header
                    for col_idx, cell_data in enumerate(row_data):
                        self.table_widget.setItem(row_idx, col_idx, QTableWidgetItem(cell_data))

                    # Update progress dialog
                    progress_value = int((row_idx / total_rows) * 100)
                    if progress_dialog:
                        progress_dialog.set_progress(progress_value)
                    QApplication.processEvents()
                # Resize columns to fit content
                self.table_widget.resizeColumnsToContents()

                # Resize columns to fit content
                self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # Set progress to 100% when done
        if progress_dialog:
            progress_dialog.set_progress(100)
            # Close the dialog when done
            progress_dialog.accept()  # Close the dialog here

    def apply_filters(self):
        """Applies filters based on the selected option in the combobox."""
        selected_filter = self.filter_combobox.currentText()
        
        if selected_filter == "Remove Blancos Puros":
            self.filter_blancos_puros()
        elif selected_filter == "Remove Fixed Transponder":
            self.filter_fixed_transponder()
        elif selected_filter == "Filter by Area (Lat/Long)":
            self.filter_by_area()
        elif selected_filter == "Remove On Ground Flights":
            self.filter_on_ground()

    def filter_blancos_puros(self):
        """Filters out 'blancos puros' based on the type of interrogation."""


    def filter_fixed_transponder(self):
        """Filters out rows where the transponder is fixed."""


    def filter_by_area(self):
        """Filters flights based on geographic area (latitude and longitude)."""


    def filter_on_ground(self):
        """Filters out rows where the flight is 'on ground'."""



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
        # Add action to load and show CSV data
        load_csv_action = QAction("Load and Show CSV", self)
        load_csv_action.triggered.connect(self.open_csv_table)
        conversion_menu.addAction(load_csv_action)

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

    def open_csv_table(self):
        """Opens a file dialog to select a CSV file and shows it in a table."""
        csv_file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")

        if csv_file_path:
            # Show progress dialog during the loading
            progress_dialog = ProgressDialog(self)
            progress_dialog.show()

            # Show CSV table with data
            dialog = CSVTableDialog(csv_file_path, self, progress_dialog)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.showMaximized()
    sys.exit(app.exec_())

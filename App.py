import ctypes
import os
import platform
import sys
import csv

from PyQt5.QtCore import QUrl, Qt, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QFileDialog, QAction, QDialog, QHeaderView, QProgressBar, QComboBox, QPushButton,
    QHBoxLayout, QLabel, QMenu, QActionGroup, QSlider, QMessageBox
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

        self.aircraft_data = []  # List to store aircraft positions for the simulation
        self.aircraft_data_by_time = {}  # Initialize the attribute here

        # Create table widget
        self.table_widget = QTableWidget()

        # Lista para almacenar los filtros aplicados
        self.applied_filters = []

        # Create "Start Simulation" button, hidden by default
        self.start_simulation_button = QPushButton("Start Simulation")
        self.start_simulation_button.setVisible(False)
        self.start_simulation_button.clicked.connect(parent.start_simulation)

        # Filter options
        self.filter_combobox = QComboBox()
        self.filter_combobox.setEditable(False)  # No se puede editar el texto
        self.filter_combobox.addItem("Active Filters: None")  # Cabecera que mostrará filtros activos
        self.filter_combobox.model().item(0).setEnabled(False)  # Deshabilitar primera opción (cabecera)

        # Opciones de filtro
        self.filter_combobox.addItem("No Filter")
        self.filter_combobox.addItem("Remove Blancos Puros")
        self.filter_combobox.addItem("Remove Fixed Transponder")
        self.filter_combobox.addItem("Filter by Area (Lat/Long)")
        self.filter_combobox.addItem("Remove On Ground Flights")

        # Botón de aplicar filtros
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
        layout.addWidget(self.start_simulation_button) 
        self.setLayout(layout)

        # Load CSV data with a progress dialog
        self.load_csv_data(csv_file_path, progress_dialog)
        self.currently_visible_rows = set(range(self.table_widget.rowCount()))  # Todas las filas visibles al inicio


        # Allow window to be maximized with a system maximize button
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowModality(Qt.NonModal)  # Para que no bloquee la ventana principal
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)  # Permitir minimizar

        # Show the dialog in a normal windowed mode, user can maximize it
        self.showMaximized()

    def add_search_fields(self):
        """Adds a search field for each column in the table."""
        # Crear una barra de búsqueda para cada columna
        for col in range(self.table_widget.columnCount()):
            search_field = QLineEdit()
            search_field.setPlaceholderText(f"Search in {self.table_widget.horizontalHeaderItem(col).text()}")
            search_field.textChanged.connect(lambda text, col=col: self.filter_column(text, col))
            self.search_layout.addWidget(search_field)
            self.column_filters.append(search_field)

    def filter_column(self, text, column):
        """Filters rows based on the text in a specific column's search field."""
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, column)
            if text.lower() in item.text().lower():
                self.table_widget.setRowHidden(row, False)  # Mostrar si coincide
            else:
                self.table_widget.setRowHidden(row, True)  # Ocultar si no coincide

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

                time_idx = headers.index("TIME(s)")
                lat_idx = headers.index("LAT")
                lon_idx = headers.index("LON")
                ti_idx = headers.index("TI")
                h_idx = headers.index("H")
                heading_idx = headers.index("HEADING")

                # Dictionary to store aircraft data grouped by time
                self.aircraft_data_by_time = {}

                # Populate table with data and update progress dialog
                for row_idx, row_data in enumerate(data[1:]):  # Skip header
                    
                    aircraft_info = {
                        'time': row_data[time_idx],
                        'lat': float(row_data[lat_idx].replace(',', '.')),
                        'lon': float(row_data[lon_idx].replace(',', '.')),
                        'ti': row_data[ti_idx],
                        'h': float(row_data[h_idx].replace(',', '.')),
                        'heading': float(row_data[heading_idx].replace(',', '.'))
                    }
                    # Group aircraft by time
                    time = aircraft_info['time']
                    if time not in self.aircraft_data_by_time:
                        self.aircraft_data_by_time[time] = []
                    self.aircraft_data_by_time[time].append(aircraft_info)

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
                self.parent().aircraft_data_by_time = self.aircraft_data_by_time

        # Set progress to 100% when done
        if progress_dialog:
            progress_dialog.set_progress(100)
            # Close the dialog when done
            progress_dialog.accept()  # Close the dialog here

    def apply_filters(self):
        """Applies filters based on the selected option in the combobox."""
        selected_filter = self.filter_combobox.currentText()
        
        # Si no se ha seleccionado un filtro válido, no realizar ninguna acción
        if "Active Filters" in selected_filter:
            return  # Salir de la función si el texto contiene "Active Filters"
        
        # Aplicar el filtro seleccionado
        if selected_filter == "Remove Blancos Puros":
            self.filter_blancos_puros()
        elif selected_filter == "Remove Fixed Transponder":
            self.filter_fixed_transponder()
        elif selected_filter == "Filter by Area (Lat/Long)":
            self.filter_by_area()
        elif selected_filter == "Remove On Ground Flights":
            self.filter_on_ground()
        elif selected_filter == "No Filter":
            self.reset_filters()

        # Añadir el filtro a la lista si no ha sido activado previamente
        if selected_filter not in self.applied_filters and selected_filter != "No Filter":
            self.applied_filters.append(selected_filter)

        # Actualizar el texto de la cabecera para mostrar los filtros activos
        self.update_active_filters_label()

        # Seleccionar automáticamente el primer elemento (cabecera) del combobox
        self.filter_combobox.setCurrentIndex(0)

    def update_active_filters_label(self):
        """Updates the combobox header to show active filters."""
        if not self.applied_filters:
            header_text = "Active Filters: None"
        else:
            header_text = f"Active Filters: {', '.join(self.applied_filters)}"

        # Cambiar el texto de la cabecera en el primer elemento del QComboBox
        self.filter_combobox.setItemText(0, header_text)

    def filter_blancos_puros(self): # EN UN PRINCIPIO TODO PIOLA
        """Filters out rows that represent 'blancos puros', i.e., detections from PSR or SSR without Modo S."""
        detection_type_col_idx = 8  # Columna 9

        for row in range(self.table_widget.rowCount()):
            if row in self.currently_visible_rows:
                detection_type = self.table_widget.item(row, detection_type_col_idx).text()
                if "ModeS" not in detection_type:
                    self.table_widget.setRowHidden(row, True)
                    self.currently_visible_rows.discard(row)

    def filter_fixed_transponder(self):
        """Oculta filas donde el valor de la columna 24 es '7777'"""
        for row in range(self.table_widget.rowCount()):
            transponder_value = self.table_widget.item(row, 23).text()
            
            # Ocultar fila si el valor de transponder es '7777'
            if transponder_value == "7777":
                self.table_widget.setRowHidden(row, True)


    def filter_on_ground(self):  # FILTRAR TAMBIÉN LOS N/A, NOT ASSIGNED
        """Filters out rows where the flight is 'on ground' or has statuses like 'N/A' or 'Not assigned'."""
        ground_status_col_idx = 70  # Columna 71
        filter_texts = [
            "No alert, no SPI, aircraft on ground",
            "N/A",
            "Not assigned",
            "Alert, no SPI, aircraft on ground"
            "Unknow"
        ]

        for row in range(self.table_widget.rowCount()):
            if row in self.currently_visible_rows:
                item = self.table_widget.item(row, ground_status_col_idx)
                if item and item.text() in filter_texts:
                    self.table_widget.setRowHidden(row, True)
                    self.currently_visible_rows.discard(row)

    def filter_by_area(self): # AL APLICAR FILTRO Q PREGUNTE 2 LATITUDES Y 2 LONGITUDES PARA CONSTRUIR UN CUADRADO
        """Filters flights based on geographic area (latitude and longitude)."""

    def reset_filters(self):
        """Resets all filters and shows all rows in the table."""
        for row in range(self.table_widget.rowCount()):
            self.table_widget.setRowHidden(row, False)
        
        self.currently_visible_rows = set(range(self.table_widget.rowCount()))  # Comienza en 0
        
        self.applied_filters.clear()  # Limpiar filtros aplicados
        #self.update_active_filters_label()  # Actualizar la etiqueta de filtros aplicados


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asterix Decoder")

        self.aircraft_data_by_time = {}
        self.selected_speed = 1  # Store selected speed; default is 1x

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

        # Timer for simulation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)

        # Create a layout for the central widget
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.web_view)

        # Placeholder for the aircraft data and simulation index
        self.aircraft_data = []

        self.control_layout = QHBoxLayout()
        
        # Create a single button for Play/Pause functionality
        self.play_pause_button = QPushButton()
        self.play_pause_button.setText("Play")  # Set initial text to "Play"
        self.play_pause_button.clicked.connect(self.toggle_simulation)
        self.control_layout.addWidget(self.play_pause_button)  # Add the button to the layout

        # Create a single button for Play/Pause functionality
        self.reset_button = QPushButton()
        self.reset_button.setText("Reset")  # Set initial text to "Play"
        self.reset_button.clicked.connect(self.reset_simulation)
        self.control_layout.addWidget(self.reset_button)  # Add the button to the layout

        # Create a button for Speed selection
        self.speed_button = QPushButton("Speed")
        self.speed_button.setMenu(self.create_speed_menu())
        self.control_layout.addWidget(self.speed_button)  # Add the button to the layout

        
        self.time_label = QLabel(" ", self)  # Inicializar el label con el tiempo en 0
        self.control_layout.addWidget(self.time_label)

        # Add a progress bar for the simulation
        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.valueChanged.connect(self.seek_simulation)
        self.control_layout.addWidget(self.progress_bar)

        layout.addLayout(self.control_layout)
        for i in range(self.control_layout.count()):
            self.control_layout.itemAt(i).widget().setVisible(False)



    def show_play_pause_buttons(self):
        """Shows the Play/Pause button once the CSV is loaded."""
        for i in range(self.control_layout.count()):
            self.control_layout.itemAt(i).widget().setVisible(True)


    def seek_simulation(self, value):
        """Busca un tiempo específico en la simulación basado en el valor del slider."""
        self.current_time = value
        if self.current_time == int(min(self.aircraft_data_by_time.keys())):
            self.web_view.page().runJavaScript(f"clearAircraft()")

        self.time_label.setText(self.seconds_to_hhmmss(value))  

        self.update_aircraft_positions_before_current_time()
 

    def update_aircraft_positions_before_current_time(self):
        """Actualiza las posiciones de todas las aeronaves al último punto conocido antes del current_time."""
        all_times = sorted(map(int, self.aircraft_data_by_time.keys()))

        for aircraft in self.aircraft_data:
            ti = aircraft['ti']
            
            last_position = None
            
            # Buscar la última posición registrada para el avión antes del current_time
            for time in reversed(all_times):
                if time < self.current_time:
                    aircraft_list = self.aircraft_data_by_time.get(str(time), [])
                    for a in aircraft_list:
                        if a['ti'] == ti:
                            last_position = a
                            break
                if last_position is not None:
                    break
            
            if last_position:
                latitude = last_position['lat']
                longitude = last_position['lon']
                altitude = last_position['h']
                heading = last_position['heading']
                self.web_view.page().runJavaScript(f"updateAircraft('{ti}', {latitude}, {longitude}, {altitude}, {heading});")


    def create_speed_menu(self):
        speed_menu = QMenu(self)
        speed_group = QActionGroup(self)  # Create an action group for the speed options

        # Define speed options
        speeds = [("x0.5", 0.5), ("x1", 1), ("x2", 2), ("x4", 4), ("x8", 8)]
        
        for label, value in speeds:
            action = QAction(label, self, checkable=True)
            action.setChecked(value == self.selected_speed)  # Check the selected speed
            action.triggered.connect(lambda checked, v=value: self.set_speed(v))  # Bind speed setting
            speed_group.addAction(action)  # Add to the action group
            speed_menu.addAction(action)

        return speed_menu
 
    def set_speed(self, speed):
        """Sets the selected speed for the simulation."""
        self.selected_speed = speed  # Update the stored speed

        # Update the speed button text to reflect the current selection
        self.speed_button.setText(f"Speed: {speed}x")

        # Optionally, update the simulation timer interval if running
        if self.timer.isActive():
            self.timer.stop()
            interval = int(1000 / self.selected_speed)  
            self.timer.start(interval)   
  

    def reset_simulation(self):
        self.current_time = int(min(self.aircraft_data_by_time.keys()))
        self.current_index = 0  # Reset the index
        self.time_label.setText(self.seconds_to_hhmmss(self.current_time))
        self.progress_bar.setValue(self.current_time)  # Initial value

        self.web_view.page().runJavaScript(f"clearAircraft()")


    def toggle_simulation(self):
        """Handles both starting and pausing the simulation."""
        if not self.timer.isActive():
            # Start or resume the simulation
            self.start_simulation()
        else:
            # Pause the simulation
            self.toggle_pause()

    
    def seconds_to_hhmmss(self, seconds):
        """Convert seconds to hh:mm:ss format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours:02}:{minutes:02}:{remaining_seconds:02}"


    def start_simulation(self):
        """Starts the simulation by initializing the timer."""
        if not self.aircraft_data_by_time:
            print("Error: No aircraft data available to start the simulation.")
            return

        # Initialize the current_time with the first time in the dataset
        if not hasattr(self, 'current_time') or self.current_time is None:
            self.current_time = int(min(self.aircraft_data_by_time.keys()))
        else:
            # No reset of current_time, continue from where it left off
            self.update_simulation()  # Start the first update manually

        if not self.timer.isActive():
            # Start the timer only if it is not already active
            interval = int(1000 / self.selected_speed)  
            self.timer.start(interval)               
        # Change the button text and icon to "Pause"
        self.play_pause_button.setText("Pause")


    def toggle_pause(self):
        """Toggles between pausing and resuming the simulation."""
        if self.timer.isActive():
            self.timer.stop()
            self.play_pause_button.setText("Play")
        else:
            interval = int(1000 / self.selected_speed)  
            self.timer.start(interval)   
            self.play_pause_button.setText("Pause")


    def update_simulation(self):
        """Updates the aircraft positions based on the simulation time step."""
        current_time_str = str(self.current_time)

        if current_time_str in self.aircraft_data_by_time:
            # Get all aircraft for the current time step
            aircraft_list = self.aircraft_data_by_time[current_time_str]
            
            # Update positions for all aircraft in the list
            for aircraft in aircraft_list:
                latitude = aircraft["lat"]
                longitude = aircraft["lon"]
                ti = aircraft["ti"]
                altitude = aircraft["h"]
                heading = aircraft["heading"]

                if ti != "N/A":
                    self.web_view.page().runJavaScript(f"updateAircraft('{ti}', {latitude}, {longitude}, {altitude}, {heading});")
                
            self.time_label.setText(self.seconds_to_hhmmss(self.current_time))  # Actualiza el QLabel con el tiempo actual

        # Find the next time step in the data
        all_times = sorted(map(int, self.aircraft_data_by_time.keys()))
        current_index = all_times.index(self.current_time)

        self.progress_bar.setValue(self.current_time)  # Set the slider to current time


        if current_index < len(all_times) - 1:
            next_time = all_times[current_index + 1]
                
            # Calculate the time difference in seconds
            time_difference = next_time - self.current_time
                
            # Set the next update based on the time difference
            interval = int(1000 / self.selected_speed)  
            self.timer.start(time_difference * interval)  # Adjust to speed
                
            # Update current time to next time
            self.current_time = next_time
        else:
            self.timer.stop()  # Stop the simulation when the last time step is reached
            QMessageBox.information(self, "Simulation Ended", "The simulation has completed.")
            self.reset_simulation()
            self.play_pause_button.setText("Play")


    def open_csv_table(self):
        """Opens a file dialog to select a CSV file and shows it in a table."""
        csv_file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)")

        if csv_file_path:
            # Show progress dialog during the loading
            progress_dialog = ProgressDialog(self)
            progress_dialog.show()

            # Show CSV table with data
            dialog = CSVTableDialog(csv_file_path, self, progress_dialog)
            self.aircraft_data = dialog.aircraft_data  # Store aircraft data for simulation

            self.aircraft_data_by_time = dialog.aircraft_data_by_time  # Actualiza los datos en MainWindow

            if self.aircraft_data_by_time:
                min_time = int(min(self.aircraft_data_by_time.keys()))
                max_time = int(max(self.aircraft_data_by_time.keys()))
                self.progress_bar.setRange(min_time, max_time)  # Ajustar rango del slider
                self.progress_bar.setValue(min_time)  # Initial value

            
            self.show_play_pause_buttons()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.showMaximized()
    sys.exit(app.exec_())
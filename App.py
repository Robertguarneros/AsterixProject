import csv
import ctypes
import os
import platform
import sys

from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from conversion_functions import convert_to_csv


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
        self.label = QLabel("Loading CSV into table, please wait...", self)
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

        # Campos de entrada para latitudes y longitudes
        self.lat_min_input = QLineEdit()
        self.lat_max_input = QLineEdit()
        self.lon_min_input = QLineEdit()
        self.lon_max_input = QLineEdit()

        self.lat_min_input.setPlaceholderText("Lat Min")
        self.lat_max_input.setPlaceholderText("Lat Max")
        self.lon_min_input.setPlaceholderText("Lon Min")
        self.lon_max_input.setPlaceholderText("Lon Max")

        # Botón para aplicar filtro de área
        self.apply_area_filter_button = QPushButton("Apply Area Filter")
        self.apply_area_filter_button.clicked.connect(self.apply_area_filter)

        # Botón para deshacer el filtro de área
        self.reset_area_filter_button = QPushButton("Reset Area Filter")
        self.reset_area_filter_button.clicked.connect(self.reset_area_filter)

        # Etiqueta para mostrar las coordenadas del filtro activo
        self.active_area_filter_label = QLabel("Active Area Filter: None")

        # Create "Start Simulation" button, hidden by default
        self.start_simulation_button = QPushButton("Start Simulation")
        self.start_simulation_button.setVisible(False)
        self.start_simulation_button.clicked.connect(parent.start_simulation)

        # Add export button
        self.export_button = QPushButton("Export Filtered Data")
        self.export_button.clicked.connect(self.export_filtered_data)

        # Filter options
        self.filter_combobox = QComboBox()
        self.filter_combobox.setEditable(False)  # No se puede editar el texto
        self.filter_combobox.addItem("Active Filters: None")  # Cabecera que mostrará filtros activos
        self.filter_combobox.model().item(0).setEnabled(False)  # Deshabilitar primera opción (cabecera)

        # Opciones de filtro
        self.filter_combobox.addItem("No Filter")
        self.filter_combobox.addItem("Remove Blancos Puros")
        self.filter_combobox.addItem("Remove Fixed Transponder")
        self.filter_combobox.addItem("Remove On Ground Flights")

        # Botón de aplicar filtros
        self.apply_filter_button = QPushButton("Apply Filter")
        self.apply_filter_button.clicked.connect(self.apply_filters)

        # Filter layout
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.filter_combobox)
        filter_layout.addWidget(self.apply_filter_button)

        # Crear ComboBox para columna de búsqueda y QLineEdit para introducir texto
        self.search_column_combobox = QComboBox()
        self.search_column_combobox.setFixedWidth(150)  # Reducir el tamaño de la caja de texto del buscador
        self.search_column_combobox.addItem("Searcher")  # Texto visible como placeholder
        self.search_column_combobox.model().item(0).setEnabled(False)  # Deshabilitar este ítem para que no sea seleccionable

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search text")
        self.search_input.setFixedWidth(300)  # Reducir el tamaño de la caja de texto del buscador
        self.search_input.textChanged.connect(self.apply_search_filter)

        # Crear layout para el buscador y alinearlo a la derecha
        search_layout = QHBoxLayout()
        search_layout.addStretch()  # Asegura que el buscador se alinee a la derecha
        search_layout.addWidget(self.search_column_combobox)
        search_layout.addWidget(self.search_input)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(filter_layout)
        layout.addLayout(search_layout)  # Añadir el layout del buscador aquí
        layout.addWidget(self.table_widget)
        layout.addWidget(self.start_simulation_button)
        self.setLayout(layout)

        # Filtros de área en el layout horizontal
        area_filter_layout = QHBoxLayout()
        area_filter_layout.addWidget(QLabel("Latitude Range:"))
        area_filter_layout.addWidget(self.lat_min_input)
        area_filter_layout.addWidget(self.lat_max_input)
        area_filter_layout.addWidget(QLabel("Longitude Range:"))
        area_filter_layout.addWidget(self.lon_min_input)
        area_filter_layout.addWidget(self.lon_max_input)
        area_filter_layout.addWidget(self.apply_area_filter_button)
        area_filter_layout.addWidget(self.reset_area_filter_button)

        # Añadir los layouts al layout principal
        layout.addLayout(area_filter_layout)
        layout.addWidget(self.active_area_filter_label)

        # Sets to track rows hidden by area filter and other filters
        self.area_hidden_rows = set()
        self.other_filters_hidden_rows = set()

        # Add export button to layout
        layout.addWidget(self.export_button)

        # Load CSV data with a progress dialog
        self.load_csv_data(csv_file_path, progress_dialog)
    
        # Inicializamos las filas visibles y las que ha ocultado el buscador
        self.currently_visible_rows = set(range(self.table_widget.rowCount()))  # Todas las filas visibles al inicio
        self.search_hidden_rows = set()  # Filas ocultadas solo por el buscador
        
        # Populate search column combobox with table headers
        self.populate_search_columns()

        # Ocultar la columna de numeración de filas (índices de fila)
        self.table_widget.verticalHeader().setVisible(False)

        # Allow window to be maximized with a system maximize button
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
        )
        self.setWindowModality(Qt.NonModal)  # Para que no bloquee la ventana principal

        # Show the dialog in a normal windowed mode, user can maximize it
        self.showMaximized()

    def populate_search_columns(self):
        """Populate the search column combobox with the table's column headers."""
        for col in range(self.table_widget.columnCount()):
            header_text = self.table_widget.horizontalHeaderItem(col).text()
            self.search_column_combobox.addItem(header_text, col)

    def apply_search_filter(self):
        """Filter rows based on the text in the search input for the selected column."""
        search_text = self.search_input.text().strip().lower()
        selected_column = self.search_column_combobox.currentData()

        # Si no hay ninguna columna seleccionada o si el texto de búsqueda está vacío, no aplicar filtro.
        if selected_column is None or not search_text:
            # Restaurar solo las filas que ocultó el buscador
            for row in self.search_hidden_rows:
                # Mostrar la fila solo si no está oculta por otros filtros
                if row not in self.other_filters_hidden_rows and row not in self.area_hidden_rows:
                    self.table_widget.setRowHidden(row, False)
            # Limpiar el conjunto de filas ocultadas por el buscador
            self.search_hidden_rows.clear()
            return

        # Filtrar solo en filas actualmente visibles
        new_search_hidden_rows = set()  # Guardamos las filas que ocultaremos en esta búsqueda
        for row in self.currently_visible_rows:
            # Obtener el texto de la celda solo una vez para mejorar el rendimiento
            cell_text = self.table_widget.item(row, selected_column).text().strip().lower()

            if search_text not in cell_text:
                # Ocultamos la fila y la añadimos a las filas ocultadas por esta búsqueda
                self.table_widget.setRowHidden(row, True)
                new_search_hidden_rows.add(row)
            else:
                # Mostramos la fila solo si no está oculta por otros filtros
                if row in self.search_hidden_rows and row not in self.other_filters_hidden_rows and row not in self.area_hidden_rows:
                    self.table_widget.setRowHidden(row, False)

        # Actualizamos las filas ocultadas por el buscador para esta búsqueda
        self.search_hidden_rows = new_search_hidden_rows

    def export_filtered_data(self):
        """Exports the filtered data to a new CSV file using semicolons as the delimiter."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Filtered Data As", "", "CSV Files (*.csv);;All Files (*)", options=options
        )

        if file_path:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file, delimiter=';')  # Use semicolon as delimiter
                
                # Write headers
                headers = [self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())]
                writer.writerow(headers)

                # Write filtered rows
                for row in range(self.table_widget.rowCount()):
                    if not self.table_widget.isRowHidden(row):
                        row_data = [
                            self.table_widget.item(row, col).text() if self.table_widget.item(row, col) else ""
                            for col in range(self.table_widget.columnCount())
                        ]
                        writer.writerow(row_data)

            QMessageBox.information(self, "Export Successful", "Filtered data has been exported successfully.")

    def load_csv_data(self, csv_file_path, progress_dialog):
        """Loads data from the CSV file and displays it in the table."""
        with open(csv_file_path, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")  # Specify ';' as the delimiter
            data = list(reader)
            total_rows = len(data)

            if data:
                # Set row and column count
                self.table_widget.setRowCount(total_rows - 1)  # Exclude header
                self.table_widget.setColumnCount(
                    len(data[0])
                )  # Use first row to set column count

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
                    try:
                        aircraft_info = {
                            "time": row_data[time_idx],
                            "lat": float(row_data[lat_idx].replace(",", ".")),
                            "lon": float(row_data[lon_idx].replace(",", ".")),
                            "ti": row_data[ti_idx],
                            "h": float(row_data[h_idx].replace(",", ".")),
                            "heading": float(row_data[heading_idx].replace(",", ".")),
                        }
                        # Group aircraft by time
                        time = aircraft_info["time"]
                        if time not in self.aircraft_data_by_time:
                            self.aircraft_data_by_time[time] = []
                        self.aircraft_data_by_time[time].append(aircraft_info)

                        for col_idx, cell_data in enumerate(row_data):
                            self.table_widget.setItem(
                                row_idx, col_idx, QTableWidgetItem(cell_data)
                            )

                        # Update progress dialog
                        progress_value = int((row_idx / total_rows) * 100)
                        if progress_dialog:
                            progress_dialog.set_progress(progress_value)
                        QApplication.processEvents()
                    except Exception as e:
                        print(f"Error loading row {row_idx}: {e}")
                # Resize columns to fit content
                self.table_widget.resizeColumnsToContents()

                # Resize columns to fit content
                self.table_widget.horizontalHeader().setSectionResizeMode(
                    QHeaderView.Interactive
                )
                self.parent().aircraft_data_by_time = self.aircraft_data_by_time

        # Set progress to 100% when done
        if progress_dialog:
            progress_dialog.set_progress(100)
            # Close the dialog when done
            progress_dialog.accept()  # Close the dialog here

    def apply_filters(self):
        """Applies filters based on the selected option in the combobox."""

        selected_filter = self.filter_combobox.currentText()
        self.search_input.clear()  # Limpiar texto del buscador al aplicar filtros

        if "Active Filters" in selected_filter:
            return

        if selected_filter == "Remove Blancos Puros":
            self.filter_blancos_puros()
        elif selected_filter == "Remove Fixed Transponder":
            self.filter_fixed_transponder()
        elif selected_filter == "Remove On Ground Flights":
            self.filter_on_ground()
        elif selected_filter == "No Filter":
            self.reset_other_filters()

        if (
            selected_filter not in self.applied_filters
            and selected_filter != "No Filter"
        ):
            self.applied_filters.append(selected_filter)

        self.update_active_filters_label()
        self.filter_combobox.setCurrentIndex(0)

    def update_active_filters_label(self):
        """Updates the combobox header to show active filters."""
        if not self.applied_filters:
            header_text = "Active Filters: None"
        else:
            header_text = f"Active Filters: {', '.join(self.applied_filters)}"

        # Cambiar el texto de la cabecera en el primer elemento del QComboBox
        self.filter_combobox.setItemText(0, header_text)

    def filter_blancos_puros(self):
        detection_type_col_idx = 8  # Índice de la columna de tipo de detección
        for row in range(self.table_widget.rowCount()):
            if row in self.currently_visible_rows:
                detection_type = self.table_widget.item(
                    row, detection_type_col_idx
                ).text()
                # Si "ModeS" no está en el tipo de detección, se oculta la fila
                if "ModeS" not in detection_type:
                    self.table_widget.setRowHidden(row, True)  # Ocultar fila
                    self.other_filters_hidden_rows.add(
                        row
                    )  # Añadir a las filas ocultas
                else:
                    self.table_widget.setRowHidden(row, False)  # Mostrar fila
                    self.other_filters_hidden_rows.discard(
                        row
                    )  # Eliminar de las filas ocultas

        # Después de aplicar el filtro, actualizamos la visibilidad de las filas
        self.update_row_visibility()

    def filter_fixed_transponder(self):
        for row in range(self.table_widget.rowCount()):
            transponder_value = self.table_widget.item(row, 23).text()
            if transponder_value == "7777":
                self.other_filters_hidden_rows.add(row)
            else:
                self.other_filters_hidden_rows.discard(row)

        self.update_row_visibility()

    def filter_on_ground(self):
        ground_status_col_idx = 70
        filter_texts = [
            "No alert, no SPI, aircraft on ground",
            "N/A",
            "Not assigned",
            "Alert, no SPI, aircraft on ground",
            "Unknow",
        ]

        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, ground_status_col_idx)
            if item and item.text() in filter_texts:
                self.other_filters_hidden_rows.add(row)
            else:
                self.other_filters_hidden_rows.discard(row)

        self.update_row_visibility()

    def update_row_visibility(self):
        """Updates visibility of rows based on area and other filter sets, and refreshes the table."""
        for row in range(self.table_widget.rowCount()):
            if row in self.area_hidden_rows or row in self.other_filters_hidden_rows:
                self.table_widget.setRowHidden(row, True)
            else:
                self.table_widget.setRowHidden(row, False)
        # Force a UI update to reflect changes immediately
        QApplication.processEvents()

    def reset_other_filters(self):
        """Resets only the non-area filters and updates the table visibility."""
        self.other_filters_hidden_rows.clear()
        self.update_row_visibility()
        self.applied_filters.clear()
        self.update_active_filters_label()

    def apply_area_filter(self):
        """Applies an area filter based on latitude and longitude range inputs."""
        self.search_input.clear()  # Limpiar texto del buscador al aplicar filtros

        try:
            # Get the latitude and longitude range from the input fields
            lat_min = float(self.lat_min_input.text().replace(",", "."))
            lat_max = float(self.lat_max_input.text().replace(",", "."))
            lon_min = float(self.lon_min_input.text().replace(",", "."))
            lon_max = float(self.lon_max_input.text().replace(",", "."))
        except ValueError:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please enter valid numeric values for the coordinates.",
            )
            return  # Exit the function if the input is invalid

        # Limpiar el conjunto de filas ocultadas solo por el filtro de área
        self.area_hidden_rows.clear()

        # Aplicar el filtro de área a las filas visibles
        for row in range(self.table_widget.rowCount()):
            try:
                # Usar índices fijos para las columnas de latitud y longitud
                lat_item = self.table_widget.item(row, 5)
                lon_item = self.table_widget.item(row, 6)

                if lat_item and lon_item:
                    lat = float(lat_item.text().replace(",", "."))
                    lon = float(lon_item.text().replace(",", "."))

                    # Verificar si las coordenadas están dentro del rango especificado
                    if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                        # Solo mostrar la fila si no está oculta por otros filtros
                        if row not in self.other_filters_hidden_rows and row not in self.search_hidden_rows:
                            self.table_widget.setRowHidden(row, False)
                    else:
                        # Ocultar la fila y agregarla a las ocultadas por el filtro de área
                        self.table_widget.setRowHidden(row, True)
                        self.area_hidden_rows.add(row)
                else:
                    # Ocultar filas con latitud/longitud faltante y agregar a las filas ocultas por área
                    self.table_widget.setRowHidden(row, True)
                    self.area_hidden_rows.add(row)

            except ValueError:
                # Si ocurre un error de conversión a float, ocultar la fila y agregar a las ocultas por área
                self.table_widget.setRowHidden(row, True)
                self.area_hidden_rows.add(row)

        # Actualizar la etiqueta de filtro de área activo
        self.active_area_filter_label.setText(
            f"<b>Active Area Filter:</b><br>"
            f"  • <b>Latitude Range:</b> Min {lat_min}° - Max {lat_max}°<br>"
            f"  • <b>Longitude Range:</b> Min {lon_min}° - Max {lon_max}°"
        )


    def reset_area_filter(self):
        """Resets only the area filter and updates the table visibility."""
        # Limpiar el conjunto de filas ocultadas solo por el filtro de área
        self.search_input.clear()  # Limpiar texto del buscador al aplicar filtros
        self.area_hidden_rows.clear()

        # Restaurar solo las filas ocultadas por el filtro de área sin afectar a las filas de otros filtros
        for row in range(self.table_widget.rowCount()):
            if row not in self.other_filters_hidden_rows and row not in self.search_hidden_rows:
                self.table_widget.setRowHidden(row, False)

        # Restablecer los campos de entrada y la etiqueta de filtro de área activo
        self.active_area_filter_label.setText("Active Area Filter: None")
        self.lat_min_input.clear()
        self.lat_max_input.clear()
        self.lon_min_input.clear()
        self.lon_max_input.clear()


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
        convert_to_csv_action = QAction("Convert Asterix to CSV", self)
        convert_to_csv_action.triggered.connect(self.convert_to_csv)
        conversion_menu.addAction(convert_to_csv_action)
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
        self.control_layout.addWidget(
            self.play_pause_button
        )  # Add the button to the layout

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
            self.web_view.page().runJavaScript(r"clearAircraft()")

        self.time_label.setText(self.seconds_to_hhmmss(value))

        self.update_aircraft_positions_before_current_time()

    def update_aircraft_positions_before_current_time(self):
        """Actualiza las posiciones de todas las aeronaves al último punto conocido antes del current_time."""
        all_times = sorted(map(int, self.aircraft_data_by_time.keys()))

        for aircraft in self.aircraft_data:
            ti = aircraft["ti"]

            last_position = None

            # Buscar la última posición registrada para el avión antes del current_time
            for time in reversed(all_times):
                if time < self.current_time:
                    aircraft_list = self.aircraft_data_by_time.get(str(time), [])
                    for a in aircraft_list:
                        if a["ti"] == ti:
                            last_position = a
                            break
                if last_position is not None:
                    break

            if last_position:
                latitude = last_position["lat"]
                longitude = last_position["lon"]
                altitude = last_position["h"]
                heading = last_position["heading"]
                self.web_view.page().runJavaScript(
                    f"updateAircraft('{ti}', {latitude}, {longitude}, {altitude}, {heading});"
                )

    def create_speed_menu(self):
        speed_menu = QMenu(self)
        speed_group = QActionGroup(self)  # Create an action group for the speed options

        # Define speed options
        speeds = [("x0.5", 0.5), ("x1", 1), ("x2", 2), ("x4", 4), ("x8", 8), ("x16", 16), ("x32", 32), ("x50", 50)]

        for label, value in speeds:
            action = QAction(label, self, checkable=True)
            action.setChecked(value == self.selected_speed)  # Check the selected speed
            action.triggered.connect(
                lambda checked, v=value: self.set_speed(v)
            )  # Bind speed setting
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

        self.web_view.page().runJavaScript(r"clearAircraft()")

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
        if not hasattr(self, "current_time") or self.current_time is None:
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
                try:
                    latitude = aircraft["lat"]
                    longitude = aircraft["lon"]
                    ti = aircraft["ti"]
                    altitude = aircraft["h"]
                    heading = aircraft["heading"]

                    if ti != "N/A":
                        self.web_view.page().runJavaScript(
                            f"updateAircraft('{ti}', {latitude}, {longitude}, {altitude}, {heading});"
                        )
                except Exception as e:
                    print(f"Error updating aircraft: {e}")

            self.time_label.setText(
                self.seconds_to_hhmmss(self.current_time)
            )  # Actualiza el QLabel con el tiempo actual

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
            QMessageBox.information(
                self, "Simulation Ended", "The simulation has completed."
            )
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

    def convert_to_csv(self):
        """Opens a file dialog to select a CSV file and shows it in a table."""
        input_file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "Asterix (*.ast);;All Files (*)"
        )
        if input_file_path == "":
            return
        csv_file_path, _ = QFileDialog.getSaveFileName(
            self, "Save as", "", "CSV (*.csv);;All Files (*)"
        )
        if csv_file_path == "":
            return

        QMessageBox.information(self, "Conversion Started", "The conversion process has started. This may take a while.")

        convert_to_csv(input_file_path, csv_file_path)

        QMessageBox.information(self, "Conversion Successful", "The file has been converted successfully.")

        if csv_file_path:
            # Show progress dialog during the loading
            progress_dialog = ProgressDialog(self)
            progress_dialog.show()

            # Show CSV table with data
            dialog = CSVTableDialog(csv_file_path, self, progress_dialog)
            self.aircraft_data = (
                dialog.aircraft_data
            )  # Store aircraft data for simulation

            self.aircraft_data_by_time = (
                dialog.aircraft_data_by_time
            )  # Actualiza los datos en MainWindow

            if self.aircraft_data_by_time:
                min_time = int(min(self.aircraft_data_by_time.keys()))
                max_time = int(max(self.aircraft_data_by_time.keys()))
                self.progress_bar.setRange(
                    min_time, max_time
                )  # Ajustar rango del slider
                self.progress_bar.setValue(min_time)  # Initial value

            self.show_play_pause_buttons()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.showMaximized()
    sys.exit(app.exec_())

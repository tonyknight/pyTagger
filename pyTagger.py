import os
import json
import subprocess
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent, QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QGridLayout, QHBoxLayout, QLabel, \
    QLineEdit, QPushButton, QTextEdit, QTreeView, QVBoxLayout, QWidget


class CustomTreeView(QTreeView):
    def __init__(self, add_files_callback, parent=None):
        super().__init__(parent)
        self.add_files_callback = add_files_callback
        self.setDragDropMode(QTreeView.DragDropMode.DropOnly)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        print("drag called")
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        print("drop called")
        file_paths = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isdir(file_path):
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                            file_paths.append(os.path.join(root, file))
            elif file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                file_paths.append(file_path)

        if file_paths:
            self.add_files_callback(file_paths)
            event.acceptProposedAction()
        else:
            event.ignore()


class ImageMetadataProcessor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Image Metadata Processor')

        # Create GUI elements
        self.tree_view = CustomTreeView(self.add_files)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setDragEnabled(True)
        self.tree_view.setAcceptDrops(True)
        self.tree_view.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.tree_view.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.tree_view.viewport().setAcceptDrops(True)

        self.model = QStandardItemModel()
        self.model.setColumnCount(1)
        self.model.setHeaderData(0, Qt.Orientation.Horizontal, 'File Path')

        self.tree_view.setModel(self.model)

        self.hierarchical_subject_label = QLabel('Hierarchical Subject:')
        self.hierarchical_subject_field = QLineEdit()

        self.keywords_label = QLabel('Keywords:')
        self.keywords_field = QLineEdit()

        self.description_label = QLabel('Description:')
        self.description_field = QTextEdit()
        self.description_field.setMaximumHeight(80)
        self.description_field.setAcceptDrops(True)

        self.datetime_label = QLabel('Date Time Original:')
        self.datetime_field = QLineEdit()

        self.save_button = QPushButton('Save Metadata')
        self.save_button.clicked.connect(self.process_files)

        input_layout = QGridLayout()
        input_layout.addWidget(self.hierarchical_subject_label, 0, 0)
        input_layout.addWidget(self.hierarchical_subject_field, 0, 1)
        input_layout.addWidget(self.keywords_label, 1, 0)
        input_layout.addWidget(self.keywords_field, 1, 1)
        input_layout.addWidget(self.description_label, 2, 0)
        input_layout.addWidget(self.description_field, 2, 1)
        input_layout.addWidget(self.datetime_label, 3, 0)
        input_layout.addWidget(self.datetime_field, 3, 1)

        input_widget = QWidget()
        input_widget.setLayout(input_layout)

        drag_layout = QVBoxLayout()
        drag_layout.addWidget(self.tree_view)

        drag_widget = QWidget()
        drag_widget.setLayout(drag_layout)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)

        button_widget = QWidget()
        button_widget.setLayout(button_layout)

        layout = QVBoxLayout()
        layout.addWidget(input_widget)
        layout.addWidget(drag_widget)
        layout.addWidget(button_widget)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Connect signals to slots
        self.hierarchical_subject_field.setAcceptDrops(True)
        self.keywords_field.setAcceptDrops(True)


    def select_directory(self):
        # Open directory dialog
        directory_path = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if directory_path:
            self.add_files(
                [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.lower().endswith('.jpg')])

    def add_files(self, files):
        # Add files to model
        for file_path in files:
            self.model.appendRow(QStandardItem(file_path))

    def write_json_file(self, before_dict, after_dict, file_path):
        e = None  # assign None to e
        # Combine before and after dictionaries
        metadata_dict = {}
        metadata_dict.update(before_dict)
        metadata_dict.update(after_dict)

        # Create JSON string
        json_string = json.dumps(metadata_dict)

        # Write JSON string to file
        json_file_path = f"{os.path.splitext(file_path)[0]}.json"
        try:
            with open(json_file_path, 'w') as f:
                f.write(json_string)
            print(f"Metadata saved to {json_file_path}")
        except Exception as e:
            print(f"Error: Failed to save metadata to {json_file_path}")
            print(e)

        if e is not None:  # Check if e variable has a value before printing it
            print(e)

    def process_files(self):
        hierarchical_subject = self.hierarchical_subject_field.text()
        keywords = self.keywords_field.text()
        description = self.description_field.toPlainText()
        datetime_original_input = self.datetime_field.text()

        file_paths = [self.model.item(i).text() for i in range(self.model.rowCount())]

        if not file_paths:
            QMessageBox.warning(self, 'No Files Selected', 'Please select one or more files to process.')
            return

        successfully_processed_files = []
        all_metadata = []

        for file_path in file_paths:
            current_keywords_output = subprocess.check_output(
                ['exiftool', '-s', '-s', '-s', '-iptc:Keywords', file_path])
            current_keywords = current_keywords_output.decode('utf-8').split(", ")

            if keywords not in current_keywords:
                before = subprocess.check_output(
                    ['exiftool', '-j', '-xmp:all', '-iptc:all', '-DateTimeOriginal', file_path])
                before_dict = json.loads(before.decode('utf-8'))[0]

                # Modify metadata here
                subprocess.check_call(
                    ['exiftool', f'-HierarchicalSubject={hierarchical_subject}', f'-Keywords+={keywords}',
                     f'-Description={description}', f'-DateTimeOriginal={datetime_original_input}',
                     '-overwrite_original',
                     file_path])

                after = subprocess.check_output(
                    ['exiftool', '-j', '-xmp:all', '-iptc:all', '-DateTimeOriginal', file_path])
                after_dict = json.loads(after.decode('utf-8'))[0]

                # Calculate the differences between before and after metadata
                metaDiff = {key: (before_dict[key], after_dict[key]) for key in before_dict if
                            before_dict[key] != after_dict[key]}

                # Rename the file based on DateTimeOriginal, if it exists
                datetime_original = after_dict.get("EXIF:DateTimeOriginal", "")
                if datetime_original:
                    # Extract the date, time, and milliseconds (if available) from the DateTimeOriginal tag
                    date_part, time_part = datetime_original.split(" ")
                    date_formatted = date_part.replace(":", "-")
                    time_formatted = time_part.replace(":", "-")
                    milliseconds = ""

                    # Check if time contains milliseconds and format accordingly
                    if "." in time_formatted:
                        time_formatted, milliseconds = time_formatted.split(".")
                        milliseconds = f"({milliseconds})"

                    new_file_name = f"{date_formatted} {time_formatted}{milliseconds}{os.path.splitext(file_path)[1]}"
                    new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)

                    # Add a serial number if the new_file_path already exists
                    serial_number = 1
                    while os.path.exists(new_file_path):
                        new_file_name = f"{date_formatted} {time_formatted}{milliseconds} ({serial_number}){os.path.splitext(file_path)[1]}"
                        new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
                        serial_number += 1

                    os.rename(file_path, new_file_path)
                    file_path = new_file_path  # Update the file_path variable

                successfully_processed_files.append(file_path)
                metadata_entry = {'file_path': file_path, 'before': before_dict, 'after': after_dict,
                                  'metaDiff': metaDiff}
                all_metadata.append(metadata_entry)

        # Write a single JSON file for all images
        json_file_path = "metadata.json"
        with open(json_file_path, 'w') as f:
            json.dump(all_metadata, f)

        # Remove successfully processed files from the input list
        for file_path in successfully_processed_files:
            index = self.model.match(self.model.index(0, 0), Qt.ItemDataRole.DisplayRole, file_path, 1,
                                     Qt.MatchFlag.MatchExactly)[0].row()
            self.model.removeRow(index)

        # Write the combined JSON file for all images in the batch
        if all_metadata:
            json_file_path = os.path.join(os.path.dirname(file_paths[0]), "metadata.json")
            with open(json_file_path, 'w') as f:
                json.dump(all_metadata, f)

        QMessageBox.information(self, 'Processing Complete', f"Processed {len(successfully_processed_files)} images")


if __name__ == '__main__':
    app = QApplication([])
    try:
        processor = ImageMetadataProcessor()
        processor.show()
        app.exec()
    except Exception as e:
        print(e)

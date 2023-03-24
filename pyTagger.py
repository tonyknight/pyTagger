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
        datetime_original = self.datetime_field.text()

        file_paths = [self.model.item(i).text() for i in range(self.model.rowCount())]

        if not file_paths:
            QMessageBox.warning(self, 'No Files Selected', 'Please select one or more files to process.')
            return

        for file_path in file_paths:
            try:
                before = subprocess.check_output(['exiftool', '-j', '-xmp:all', '-iptc:all', '-DateTimeOriginal', file_path])
                print(f"Before data for file {file_path}:")
                print(before.decode('utf-8'))
                before_dict = json.loads(before.decode('utf-8'))[0] if len(json.loads(before.decode('utf-8'))) > 0 else {}
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON data for file {file_path}")
                print(f"Raw data: {before.decode('utf-8')}")
                continue

            # Modify metadata here
            subprocess.check_call(
                ['exiftool', f'-HierarchicalSubject={hierarchical_subject}', f'-Keywords+={keywords}',
                 f'-Description={description}', f'-DateTimeOriginal={datetime_original}', '-overwrite_original',
                 file_path])

            after = subprocess.check_output(['exiftool', '-j', '-xmp:all', '-iptc:all', '-DateTimeOriginal', file_path])

            after_dict = json.loads(after.decode('utf-8'))[0] if len(json.loads(after.decode('utf-8'))) > 0 else {}


            before_xmp = before_dict.get('XMP', {})
            before_iptc = before_dict.get('IPTC', {})
            before_datetime = before_dict.get('EXIF:DateTimeOriginal', '')

            after_xmp = after_dict.get('XMP', {})
            after_iptc = after_dict.get('IPTC', {})
            after_datetime = after_dict.get('EXIF:DateTimeOriginal', '')

            xmp_diff = set(after_xmp.items()) - set(before_xmp.items())
            iptc_diff = set(after_iptc.items()) - set(before_iptc.items())
            datetime_diff = after_datetime != before_datetime

            if xmp_diff or iptc_diff or datetime_diff:
                print(f"Metadata changes detected for {file_path}:")
                if xmp_diff:
                    print(f"  XMP: {xmp_diff}")
                if iptc_diff:
                    print(f"  IPTC: {iptc_diff}")
                if datetime_diff:
                    print(f"  DateTimeOriginal: {before_datetime} -> {after_datetime}")
            else:
                print(f"No metadata changes detected for {file_path}")

                self.write_json_file(before_dict, after_dict, file_path)

        QMessageBox.information(self, 'Processing Complete', f"Processed {len(file_paths)} images")


if __name__ == '__main__':
    app = QApplication([])
    try:
        processor = ImageMetadataProcessor()
        processor.show()
        app.exec()
    except Exception as e:
        print(e)

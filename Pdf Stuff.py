import sys
from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QMessageBox, QTabWidget, QLineEdit
from PyQt6.QtCore import Qt
from PyPDF2 import PdfReader, PdfWriter
from PyQt6.QtGui import QFont

class PDFHandler(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("PDF Splitter/Merger")

        self.main_layout = QVBoxLayout()

        # Top level layout for tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Split tab
        self.split_widget = QWidget()
        self.split_layout = QVBoxLayout()
        self.split_widget.setLayout(self.split_layout)

        self.split_input_label = QLabel("Select input PDF:")
        self.split_layout.addWidget(self.split_input_label)

        self.split_input_button = QPushButton("Browse...")
        self.split_input_button.clicked.connect(self.select_input_pdf)
        self.split_layout.addWidget(self.split_input_button)

        self.split_output_label = QLabel("Select output PDF:")
        self.split_layout.addWidget(self.split_output_label)

        self.split_output_button = QPushButton("Browse...")
        self.split_output_button.clicked.connect(self.select_output_pdf)
        self.split_layout.addWidget(self.split_output_button)

        self.split_start_page_label = QLabel("Start page:")
        self.split_layout.addWidget(self.split_start_page_label)

        self.split_start_page_edit = QLineEdit()
        self.split_layout.addWidget(self.split_start_page_edit)

        self.split_end_page_label = QLabel("End page:")
        self.split_layout.addWidget(self.split_end_page_label)

        self.split_end_page_edit = QLineEdit()
        self.split_layout.addWidget(self.split_end_page_edit)

        self.execute_split_button = QPushButton("Split PDF")
        self.execute_split_button.clicked.connect(self.split_pdf)
        self.split_layout.addWidget(self.execute_split_button)

        self.tabs.addTab(self.split_widget, "Split")

        # Merge tab
        self.merge_widget = QWidget()
        self.merge_layout = QVBoxLayout()
        self.merge_widget.setLayout(self.merge_layout)

        self.merge_input_label = QLabel("Select PDFs to merge:")
        self.merge_layout.addWidget(self.merge_input_label)

        self.merge_input_button = QPushButton("Add PDFs")
        self.merge_input_button.clicked.connect(self.add_pdf)
        self.merge_layout.addWidget(self.merge_input_button)

        self.merge_pdf_list = QListWidget()
        self.merge_pdf_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.merge_pdf_list.setAcceptDrops(True)
        self.merge_pdf_list.viewport().setAcceptDrops(True)
        self.merge_pdf_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)  # Enable internal move
        font = QFont()
        font.setFamily("Consolas")  # Font ailesini "Consolas" olarak ayarla
        font.setPointSize(12)
        self.merge_pdf_list.setFont(font)
        self.merge_layout.addWidget(self.merge_pdf_list)

        self.execute_merge_button = QPushButton("Merge PDFs")
        self.execute_merge_button.clicked.connect(self.merge_pdfs)
        self.merge_layout.addWidget(self.execute_merge_button)

        self.tabs.addTab(self.merge_widget, "Merge")

        self.setFixedSize(800,300)

        self.setLayout(self.main_layout)

    def select_input_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if file_name:
            self.input_pdf = PdfReader(file_name)
            self.split_input_label.setText(file_name)

    def select_output_pdf(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if file_name:
            self.output_pdf_path = file_name
            self.split_output_label.setText(file_name)
            #self.merge_output_label.setText(file_name)

    def add_pdf(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, "Open PDFs", "", "PDF Files (*.pdf)")
        if file_names:
            for file_name in file_names:
                self.merge_pdf_list.addItem(file_name)

    def remove_selected_pdf(self):
        selected_items = self.merge_pdf_list.selectedItems()
        for item in selected_items:
            self.merge_pdf_list.takeItem(self.merge_pdf_list.row(item))

    def split_pdf(self):
        try:
            start_page = int(self.split_start_page_edit.text())
            end_page = int(self.split_end_page_edit.text())

            output_file = self.split_output_label.text()
            self.input_pdf_writer = PdfWriter()
            for page in range(start_page - 1, end_page):
                self.input_pdf_writer.add_page(self.input_pdf.pages[page])

            with open(output_file, "wb") as out_file:
                self.input_pdf_writer.write(out_file)

            QMessageBox.information(self, "Job done", "PDF splitting successfully!")
            self.split_input_label.clear()
            self.split_input_label.setText("Select input PDF:")
            self.split_output_label.clear()
            self.split_output_label.setText("Select output PDF:")
            self.split_start_page_edit.clear()
            self.split_end_page_edit.clear()
        except Exception as e:
            QMessageBox.information(self, "Job done", "PDF split wasn't successful because " + str(e))

    def merge_pdfs(self):
        output_file, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "", "PDF Files (*.pdf)")
        if output_file:
            output_pdf = PdfWriter()
            for i in range(self.merge_pdf_list.count()):
                file_name = self.merge_pdf_list.item(i).text()
                input_pdf = PdfReader(file_name)
                for page in range(len(input_pdf.pages)):
                    output_pdf.add_page(input_pdf.pages[page])

            with open(output_file, "wb") as out_file:
                output_pdf.write(out_file)

            QMessageBox.information(self, "Job done", "PDFs merged successfully!")
        self.merge_pdf_list.clear()

    def mousePressEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.MouseButton.LeftButton:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        index = self.pdf_list.indexAt(self.drag_start_position)
        if not index.isValid():
            return
        item = self.pdf_list.takeItem(index.row())
        self.pdf_list.insertItem(self.pdf_list.rowAt(event.pos().y()), item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = PDFHandler()
    ex.show()
    sys.exit(app.exec())
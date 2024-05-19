import sys
from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QMessageBox, QTabWidget, QLineEdit
from PyQt6.QtCore import Qt
from PyPDF2 import PdfReader, PdfWriter
from PyQt6.QtGui import QFont
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

class PDFHandler(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("PDF Splitter/Merger/Image to PDF Converter")

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

        # Image to PDF tab
        self.image_widget = QWidget()
        self.image_layout = QVBoxLayout()
        self.image_widget.setLayout(self.image_layout)

        self.image_input_label = QLabel("Select images to convert to PDF:")
        self.image_layout.addWidget(self.image_input_label)

        self.image_input_button = QPushButton("Add Images")
        self.image_input_button.clicked.connect(self.add_images)
        self.image_layout.addWidget(self.image_input_button)

        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.image_list.setAcceptDrops(True)
        self.image_list.viewport().setAcceptDrops(True)
        self.image_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)  # Enable internal move
        self.image_list.setFont(font)
        self.image_layout.addWidget(self.image_list)

        self.execute_image_button = QPushButton("Convert to PDF")
        self.execute_image_button.clicked.connect(self.convert_images_to_pdf)
        self.image_layout.addWidget(self.execute_image_button)

        self.tabs.addTab(self.image_widget, "Images to PDF")

        self.setFixedSize(800, 600)
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

    def add_pdf(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, "Open PDFs", "", "PDF Files (*.pdf)")
        if file_names:
            for file_name in file_names:
                self.merge_pdf_list.addItem(file_name)

    def add_images(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_names:
            for file_name in file_names:
                self.image_list.addItem(file_name)

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

    def convert_images_to_pdf(self):
        if self.image_list.count() == 0:
            QMessageBox.warning(self, "Warning", "No images selected!")
            return

        output_file, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if not output_file:
            return

        try:
            c = canvas.Canvas(output_file, pagesize=letter)
            width, height = letter

            for i in range(self.image_list.count()):
                image_path = self.image_list.item(i).text()
                img = Image.open(image_path)
                img_width, img_height = img.size

                aspect_ratio = img_width / img_height
                if img_width > width or img_height > height:
                    if aspect_ratio > 1:
                        img_width = width
                        img_height = width / aspect_ratio
                    else:
                        img_height = height
                        img_width = height * aspect_ratio

                c.drawImage(image_path, 0, 0, img_width, img_height)
                c.showPage()

            c.save()
            QMessageBox.information(self, "Success", "Images have been converted to PDF successfully!")
            self.image_list.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = PDFHandler()
    ex.show()
    sys.exit(app.exec())

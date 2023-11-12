import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLineEdit, QComboBox, QMessageBox
from PySide6 import QtGui, QtCore
from PySide6.QtGui import QGuiApplication, QScreen
from PyPDF2 import PdfReader, PdfWriter

class PDFMergerApp(QMainWindow):
    def dilDegistir(self, index):
        if index == 0:  # Türkçe Seçildi
            self.start_page_input.clear()
            self.end_page_input.clear()
            self.output_name_input.clear()
            self.selected_file = ""
            self.select_button.setText("PDF Seç")
            self.start_page_input.setPlaceholderText("Başlangıç Sayfası")
            self.end_page_input.setPlaceholderText("Bitiş Sayfası")
            self.output_name_input.setPlaceholderText("Yeni PDF Dosya Adı")
            self.create_button.setText("Belirli Aralıktaki Sayfaları Oluştur")
        elif index == 1:  # English Chose
            self.start_page_input.clear()
            self.end_page_input.clear()
            self.output_name_input.clear()
            self.selected_file = ""
            self.select_button.setText("Select Any PDF File")
            self.start_page_input.setPlaceholderText("From")
            self.end_page_input.setPlaceholderText("Include To")
            self.output_name_input.setPlaceholderText("Output PDF Filename")
            self.create_button.setText("Create New PDF with Giving Range")

    def __init__(self):
        super().__init__()

        #self.setWindowTitle("PDF Sayfa Aralığından Yeni PDF Oluşturucu")
        width = 350  # Sabit pencere genişliği
        height = 370  # Sabit pencere yüksekliği
        self.setFixedSize(width, height)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        
        self.kapat_btn = QPushButton('X', self)  # Kapatma butonu
        self.kapat_btn.setGeometry(self.width() - 25, 5, 20, 20)
        self.kapat_btn.clicked.connect(self.close)
        self.comboBox = QComboBox(self) #Farklı Dil Seçenekleri
        self.comboBox.addItem("Türkçe")
        self.comboBox.addItem("English")
        self.comboBox.setGeometry(self.width() - 150, 5, 100, 20)
        self.comboBox.currentIndexChanged.connect(self.dilDegistir)
        self.comboBox.setStyleSheet("background-color: black; color: white; border: 1px solid white;")
        
        self.select_button = QPushButton("PDF Seç", self)
        self.select_button.clicked.connect(self.select_pdf)
        self.select_button.setGeometry(50, 50, 250, 50)

        self.start_page_input = QLineEdit(self)
        self.start_page_input.setPlaceholderText("Başlangıç Sayfası")
        self.start_page_input.setGeometry(50, 120, 250, 30)

        self.end_page_input = QLineEdit(self)
        self.end_page_input.setPlaceholderText("Bitiş Sayfası")
        self.end_page_input.setGeometry(50, 170, 250, 30)

        self.output_name_input = QLineEdit(self)
        self.output_name_input.setPlaceholderText("Yeni PDF Dosya Adı")
        self.output_name_input.setGeometry(50, 220, 250, 30)

        self.create_button = QPushButton("Belirli Aralıktaki Sayfaları Oluştur", self)
        self.create_button.clicked.connect(self.create_pdf_within_range)
        self.create_button.setGeometry(50, 270, 250, 50)

        self.selected_file = ""
        button_style = ("QPushButton {"
                        "background-color: black;"
                        "border: 2px solid white;"
                        "border-radius: 8px;"
                        "color: white;"
                        "}"
                        "QPushButton:hover {"
                        "background-color: black;"
                        "}")
        
        # Beyaz yazı rengi için stillendirme
        entry_style = ("QLineEdit {"
                       "color: white;"
                       "background-color: black;"
                       "border: 2px solid white;"
                       "border-radius: 8px;"
                       "}")

        self.setStyleSheet(button_style + entry_style)

    def sayfa_sayisi(self,pdf_yolu):
        with open(pdf_yolu, 'rb') as pdfDosyasi:
            pdf_okuyucu = PdfReader(pdfDosyasi)
            return len(pdf_okuyucu.pages)

    def select_pdf(self):
        file_dialog = QFileDialog()
        if self.comboBox.currentText() == "Türkçe":
            self.selected_file, _ = file_dialog.getOpenFileName(self, "PDF Dosyasını Seç", "", "PDF Dosyaları (*.pdf)")
        elif self.comboBox.currentText() == "English":
            self.selected_file, _ = file_dialog.getOpenFileName(self, "Choose PDF File", "", "PDF Files (*.pdf)")

    def create_pdf_within_range(self):
        if self.selected_file:
            start_page_text = self.start_page_input.text()
            end_page_text = self.end_page_input.text()
            output_name = self.output_name_input.text()
            sayfa_sayi = self.sayfa_sayisi(self.selected_file)

            if (start_page_text.isdigit() and end_page_text.isdigit() and output_name and int(start_page_text) > 0
                and int(start_page_text) < sayfa_sayi and int(end_page_text) > 0 and int(end_page_text) > int(start_page_text)
                and int(end_page_text) < (sayfa_sayi + 1)):
                start_page = int(start_page_text)
                end_page = int(end_page_text)
                output_file = output_name + ".pdf"

                pdf_reader = PdfReader(self.selected_file)
                pdf_writer = PdfWriter()

                for page_num in range(start_page - 1, min(end_page, len(pdf_reader.pages))):
                    pdf_writer.add_page(pdf_reader.pages[page_num])

                with open(output_file, 'wb') as output:
                    pdf_writer.write(output)
                    if self.comboBox.currentText() == "Türkçe":
                        QMessageBox.information(self, "Bilgi", f"Kayıt Başarılı. Yeni PDF {output_file} olarak kaydedildi.")
                    elif self.comboBox.currentText() == "English":
                        QMessageBox.information(self, "INFO", f"Successfully Saved. New PDF saved as {output_file}")
            else:
                if self.comboBox.currentText() == "Türkçe":
                    QMessageBox.warning(self, "Hata", "Başlangıç ve bitiş sayfa numaraları geçerli sayılar olmalıdır ve yeni PDF dosya adı gerekli.")
                elif self.comboBox.currentText() == "English":
                    QMessageBox.warning(self, "Warning", "Please enter valid numbers or filename")
        else:
            if self.comboBox.currentText() == "Türkçe":
                QMessageBox.warning(self, "Hata", "Lütfen Bir PDF Dosyası Seçiniz!!")
            elif self.comboBox.currentText() == "English":
                QMessageBox.warning(self, "Warning", "Please Select A PDF File!!")

    def center(self):
        ekran = QGuiApplication.primaryScreen()
        ekranGeometry = ekran.availableGeometry()
        pencereGeometry = self.frameGeometry()
        pencereGeometry.moveCenter(ekranGeometry.center())
        self.move(pencereGeometry.topLeft())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet('QMainWindow{background-color: black;border: 1px solid;}')
    window = PDFMergerApp()
    window.center()
    window.show()
    sys.exit(app.exec())
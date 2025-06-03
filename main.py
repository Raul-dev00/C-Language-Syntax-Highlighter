from PyQt5.QtWidgets import QApplication
from CLanguageSyntaxHighlighter import Highlighter

# QApplication: PyQt5 uygulamasının ana nesnesi
app = QApplication([])

# Highlighter sınıfımızı oluştur, pencereyi göster
win = Highlighter()
win.show()

# Uygulama döngüsünü başlat (ui canlı kalır)
app.exec_()
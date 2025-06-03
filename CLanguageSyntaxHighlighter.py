# CLanguageSyntaxHighlighter.py

from PyQt5.QtGui import (
    QTextCursor,
    QTextCharFormat,
    QFont,
    QColor,
    QSyntaxHighlighter
)
from PyQt5.QtWidgets import QMainWindow, QTextEdit
from PyQt5.QtCore import QRegularExpression

from uygulama_arayuz import Ui_MainWindow
from parseTree import tokenize, Parser, Token


class CSyntaxHighlighter(QSyntaxHighlighter):
    """
    C dili için gerçek zamanlı sözdizimi vurgulayıcı (QSyntaxHighlighter tabanlı).
    Aşağıdaki token tiplerini renklendirir:
      1. Identifiers (değişken/fonksiyon/ad) → koyu siyah
      2. Anahtar sözcükler (int, char, void, if, else, while, for, return, struct, union, typedef) → kırmızı/bold
      3. Preprocessor direktifleri (#include, #define vb.) → koyu mavi
      4. Tek satırlık yorum (//…) → koyu yeşil italik
      5. Çok satırlı yorum (/*…*/) → koyu yeşil italik
      6. String literal → magenta
      7. Char literal → magenta
      8. Ondalık sayılar (integer + float) → mavi
      9. Onaltılık sayılar (0x…) → mavi
     10. Operatörler (==, !=, <=, >=, ++, --, +=, -=, &&, ||, <<, >>, ->, +, -, *, /, %, <, >, &, ^, |, =, ~, !, ?, :) → koyu turuncu
     11. Ayraçlar (; , ( ) { } [ ]) → koyu turuncu
    """

    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        # 1) Identifiers → koyu siyah (en başta, böylece keyword’leri override etmeden önce tüm kelimeler siyaha boyanır)
        id_fmt = QTextCharFormat()
        id_fmt.setForeground(QColor("black"))
        pattern_id = QRegularExpression(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
        self.rules.append((pattern_id, id_fmt))

        # 2) Anahtar sözcükler → kırmızı, bold (identifier’dan sonra gelir, böylece int/char gibi önceden siyah olan kelimeler kırmızıya dönüşür)
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("red"))
        kw_fmt.setFontWeight(QFont.Bold)
        kws = ["int", "char", "void", "if", "else", "while", "for", "return", "struct", "union", "typedef"]
        pattern_kw = QRegularExpression(r"\b(" + "|".join(kws) + r")\b")
        self.rules.append((pattern_kw, kw_fmt))

        # 3) Preprocessor direktifleri → koyu mavi
        pp_fmt = QTextCharFormat()
        pp_fmt.setForeground(QColor("#000080"))
        # ^\s*#.*$ → satır başından başlayıp, boşluk + # + kalan tüm metin
        pp_pattern = QRegularExpression(r"^\s*#.*$", QRegularExpression.MultilineOption)
        self.rules.append((pp_pattern, pp_fmt))

        # 4) Tek satırlık yorum (//…) → koyu yeşil italik
        comment1_fmt = QTextCharFormat()
        comment1_fmt.setForeground(QColor("#006400"))
        comment1_fmt.setFontItalic(True)
        # // ile satır sonuna kadar her şeyi yakalar
        pattern1 = QRegularExpression(r"//[^\n]*")
        self.rules.append((pattern1, comment1_fmt))

        # 5) Çok satırlı yorum (/*…*/) — highlightBlock içinde işlenecek
        self.comment2_fmt = QTextCharFormat()
        self.comment2_fmt.setForeground(QColor("#006400"))
        self.comment2_fmt.setFontItalic(True)
        # Yalnızca başlangıç ve bitiş desenleri regex olarak saklanır; highlightBlock’ta aralık bulunur.
        self.comment2_start = QRegularExpression(r"/\*")
        self.comment2_end = QRegularExpression(r"\*/")

        # 6) String literal → magenta
        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("magenta"))
        # "(?:\\.|[^"\\])*" → escape karakteriyle başlayan veya normal karakter
        pattern_str = QRegularExpression(r"\"(?:\\.|[^\"\\])*\"")
        self.rules.append((pattern_str, string_fmt))

        # 7) Char literal → magenta
        char_fmt = QTextCharFormat()
        char_fmt.setForeground(QColor("magenta"))
        # '(?:\\.|[^'\\])*' → escape veya normal karakter
        pattern_ch = QRegularExpression(r"'(?:\\.|[^'\\])*'")
        self.rules.append((pattern_ch, char_fmt))

        # 8) Ondalık sayılar (integer + float) → mavi
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("blue"))
        # \b[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?\b
        pattern_num = QRegularExpression(r"\b[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?\b")
        self.rules.append((pattern_num, num_fmt))

        # 9) Onaltılık sayılar (0x…) → mavi
        hex_fmt = QTextCharFormat()
        hex_fmt.setForeground(QColor("blue"))
        pattern_hex = QRegularExpression(r"\b0[xX][0-9A-Fa-f]+\b")
        self.rules.append((pattern_hex, hex_fmt))

        # 10) Operatörler → koyu turuncu
        op_fmt = QTextCharFormat()
        op_fmt.setForeground(QColor("#8B4500"))
        # Çok karakterli operatörler öncelikli, sonra tek karakterli
        ops = [
            r"==", r"!=", r"<=", r">=", r"\+\+", r"--", r"\+=", r"-=", r"\*=", r"/=", r"&&", r"\|\|",
            r"<<", r">>", r"->",            # Çok karakterli operatörler
            r"[+\-*/%<>&\^|=~!?:]"          # Tek karakterli operatörler ve ?:
        ]
        pattern_op = QRegularExpression("(" + "|".join(ops) + ")")
        self.rules.append((pattern_op, op_fmt))

        # 11) Ayraçlar (; , ( ) { } [ ]) → koyu turuncu
        sep_fmt = QTextCharFormat()
        sep_fmt.setForeground(QColor("#8B4500"))
        pattern_sep = QRegularExpression(r"[;,()\[\]\{\}]")
        self.rules.append((pattern_sep, sep_fmt))

    def highlightBlock(self, text: str):
        """
        Her satır için çağrılır. Önce self.rules içindeki regex+format çiftlerini uygular,
        ardında çok satırlı yorum (/* ... */) bloklarını işleyecek ek mantığı çalıştırır.
        """
        # 1) Listedeki her bir (regex, format) çifti için globalMatch ile satırı tarar
        for regex, fmt in self.rules:
            it = regex.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()    # Eşleşmenin başladığı indeks
                length = match.capturedLength()  # Eşleşmenin uzunluğu
                self.setFormat(start, length, fmt)

        # 2) Çok satırlı yorum /*******/ bloklarını işle
        #    Önce bu satırın bir önceki blokta yorum içinde kalıp kalmadığını kontrol et
        self.setCurrentBlockState(0)
        start_idx = 0
        if self.previousBlockState() != 1:
            # Önceki blok yorum içinde değilse, bu satırda yeni bir /* açılışı ara
            match_start = self.comment2_start.match(text)
            start_idx = match_start.capturedStart() if match_start.hasMatch() else -1
        else:
            # Önceki blok hâlâ yorum içindeydi, satır başından ara
            start_idx = 0

        # Yorum başlangıcından itibaren döngüyle bitişi bulmaya çalış
        while start_idx >= 0:
            match_end = self.comment2_end.match(text, start_idx)
            if match_end.hasMatch():
                # Bitiş bulunduysa, aralığı renklendir
                end = match_end.capturedEnd()
                length = end - start_idx
                self.setFormat(start_idx, length, self.comment2_fmt)
                # Satır içinde başka /* var mı kontrol et
                match_start = self.comment2_start.match(text, end)
                start_idx = match_start.capturedStart() if match_start.hasMatch() else -1
            else:
                # Bitiş bulunmadıysa, satır boyunca renklendir ve bir sonraki satırda devam et
                length = len(text) - start_idx
                self.setFormat(start_idx, length, self.comment2_fmt)
                self.setCurrentBlockState(1)  # Bir sonraki satır da yorum içinde başlasın
                break


class Highlighter(QMainWindow):
    """
    Ana uygulama penceresi. UI tanımı uygulama_arayuz.py içinde,
    bu sınıfta şöyle işler gerçekleşir:
      - CSyntaxHighlighter, textEdit’in document’ına bağlanır → anlık vurgulama.
      - textEdit.textChanged sinyali → on_text_changed() metodunu tetikler.
      - on_text_changed(): tokenize → parser.parse() → hata listesini statusBar’da göster.
    """

    def __init__(self) -> None:
        super().__init__()
        self.window = Ui_MainWindow()    # PyQt5 Designer ile oluşturulmuş UI sınıfı
        self.window.setupUi(self)        # UI elemanlarını inşa eder

        # 1) Sözdizimi vurgulayıcıyı textEdit’in document’ına bağla
        self.highlighter = CSyntaxHighlighter(self.window.textEdit.document())

        # 2) Metin değiştiğinde parse et ve hata varsa statusBar’da göster
        self.window.textEdit.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        """
        Kullanıcı textEdit içeriğini her değiştirdiğinde çalışır.
        - Kodu al (string).
        - tokenize(code) ile token listesine dönüştür.
        - Parser(token list) oluştur, parse() ile sözdizimi hatalarını al.
        - Eğer errors listesi doluysa, “Line X, Col Y: mesaj” biçiminde statusBar’da göster.
          Yoksa “No syntax errors” mesajı çıkar.
        """
        code = self.window.textEdit.toPlainText()
        # a) Lexical analysis (tokenize)
        tokens = tokenize(code)
        # b) Syntax analysis (parse)
        parser = Parser(tokens)
        errors = parser.parse()

        # Hata listesi dolu mu?
        if errors:
            msgs = []
            for line, col, msg in errors:
                msgs.append(f"Line {line}, Col {col}: {msg}")
            # Birleştirilmiş hataları statusBar’a bildir
            self.window.statusbar.showMessage(" | ".join(msgs))
        else:
            # Hata yoksa temizle veya “No syntax errors” yaz
            self.window.statusbar.showMessage("No syntax errors")

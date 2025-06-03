# C Language Syntax Highlighter 

## Genel Bakış

Bu doküman, “C Kod Analiz Aracı” projesinin bileşenlerini ve nasıl çalıştığını detaylı biçimde açıklar. Araç temel olarak iki ana kısımdan oluşur:

1. **Lexical Analiz (Tokenizer)**  
   Kaynak kodu satır satır tarayıp, regex desenlerine göre “token” denilen sözcük/parça birimlerine ayırır.  

2. **Sözdizimi Analizi (Parser)**  
   Token akışını alıp, basit bir Top-Down (recursive-descent) yöntemle C dilinin belirlenmiş gramer kurallarına göre ayrıştırır. Eksik noktalı virgül, kapatılmamış blok gibi hataları tespit eder.

Ek olarak, **PyQt5** üzerinden bir GUI katmanı vardır. Bu katmanda:

- **Gerçek Zamanlı Syntax Vurgulama** yapılır (anahtar kelimeler, sayılar, operatörler, yorumlar vb. farklı renklerde).  
- Kullanıcı kodu her düzenlediğinde, tokenize ve parse işlemleri tetiklenir; eğer hata varsa status bar’da gösterilir.  

Ana Python dosyaları:

- `parseTree.py` → Lexer ve Parser işlevlerini barındırır.  
- `uygulama_arayuz.py` → Qt Designer ile oluşturulmuş, GUI öğelerini tanımlayan modül.  
- `uygulama_arayuz_kod.py` → GUI mantığını, `CSyntaxHighlighter` sınıfını ve parser entegrasyonunu içerir.  
- `main.py` → Uygulamayı başlatan betik.  

---

## Kurulum ve Gereksinimler

### Gereksinimler
- Python 3.8 veya üzeri  
- PyQt5  

## Proje Dosya Yapısı
PyQt5 yüklü değilse, terminalde şu komutu çalıştırın:
```bash
pip install PyQt5

Project-PD/
│
├── main.py                     # Uygulamayı başlatan Python betiği
│
├── parseTree.py                # Lexer & Parser işlevleri
│
├── uygulama_arayuz.py          # PyQt5 Designer’dan çıkmış UI tanımı
│
└── uygulama_arayuz_kod.py      # GUI mantığı, SyntaxHighlighter, parser entegrasyonu
```
## Çalıştırma Adımları
 - GitHub deposunu klonlayın veya indirin:
  `git clone https://github.com/Raul-dev00/Project-PD.git
cd Project-PD`
 - (Opsiyonel) Sanal ortam oluşturun ve aktif edin:
   ```
   python3 -m venv venv
   source venv/bin/activate    # macOS/Linux
   # venv\Scripts\activate     # Windows
   ```
 - Gerekli paketi yükleyin:
   `pip install PyQt5`
 - Uygulamayı başlatın:
   `python main.py`

# Lexer (Tokenizasyon)

##Token Türleri
`parseTree.py` içinde, C kaynak kodunun parçalanmasında kullanılan başlıca token türleri şunlardır:
```
| Tür              | Açıklama                                                                                                |   |                                                   |               |
| ---------------- | ------------------------------------------------------------------------------------------------------- | - | ------------------------------------------------- | ------------- |
| `PREPROCESSOR`   | Satır başında `#` ile başlayan ön işleyici direktifleri (`#include`, `#define` vb.).                    |   |                                                   |               |
| `COMMENT1`       | Tek satırlık yorumlar (`//...`).                                                                        |   |                                                   |               |
| `COMMENT2`       | Çok satırlı yorumlar (`/* ... */`).                                                                     |   |                                                   |               |
| `STRING_LITERAL` | Çift tırnak içindeki dizeler (escape destekli).                                                         |   |                                                   |               |
| `CHAR_LITERAL`   | Tek tırnak içindeki karakterler (escape destekli).                                                      |   |                                                   |               |
| `KEYWORD`        | C dilindeki anahtar sözcükler: `int, char, void, if, else, while, for, return, struct, union, typedef`. |   |                                                   |               |
| `NUMBER`         | Ondalık sayılar: tam sayılar ve bilimsel gösterim (`123`, `3.14`, `1e-5`).                              |   |                                                   |               |
| `HEXNUMBER`      | Onaltılık sayılar (`0x1A3F`).                                                                           |   |                                                   |               |
| `IDENTIFIER`     | Geçerli C değişken/fonksiyon isimleri (`[A-Za-z_][A-Za-z0-9_]*`).                                       |   |                                                   |               |
| `OP`             | Operatörler: \`==, !=, <=, >=, ++, --, +=, -=, \*=, /=, &&,                                             |   | , <<, >>, ->`, tek karakterli `+ - \* / % < > & ^ | = \~ ! ? :\`. |
| `SEPARATOR`      | Ayraçlar: `; , ( ) { } [ ]`.                                                                            |   |                                                   |               |
| `UNKNOWN`        | Yukarıdakilerle eşleşmeyen tek bir karakter (bilinmeyen).                                               |   |                                                   |               |
```

## Token Veri Yapısı
Her token’ın bilgisini tutan `Token` sınıfı şu alanları içerir:
```
class Token:
    __slots__ = ("type", "value", "position", "line", "column")

    def __init__(self, type_: str, value: str, position: int, line: int, column: int):
        self.type = type_       # Token türü (örn. "KEYWORD", "NUMBER")
        self.value = value      # Token'ın kaynak kod içindeki değeri
        self.position = position# Metindeki karakter indeksi (0-tabanlı)
        self.line = line        # Satır numarası (1-tabanlı)
        self.column = column    # Kolon numarası (1-tabanlı)
```

- `position`: Karakter bazında kaçıncı sıradaysa o indis.
- `line`: O token’ın yer aldığı satır numarası.
- `column`: Satır başından kaçıncı karakterde başladığı.

## Fonksiyon ```tokenize()``` 
`parseTree.py` içinde, gelen C kodunu regex tabanlı olarak tarayıp bir `Token` listesi döndürür:
```
_TOKEN_REGEX = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION),
    re.MULTILINE
)
```
# Adım Adım İşleyiş
1) `TOKEN_SPECIFICATION` isimli liste, `(Tür, RegexDeseni)` çiftlerini içerir.
   ```
   TOKEN_SPECIFICATION = [
    ("PREPROCESSOR", r"^\s*#.*"),
    ("COMMENT1",     r"//[^\n]*"),
    ("COMMENT2_START",  r"/\*"),
    ("COMMENT2_END",    r"\*/"),
    ("STRING_LITERAL",  r"\"(?:\\.|[^\"\\])*\""),
    ("CHAR_LITERAL",    r"'(?:\\.|[^'\\])*'"),
    ("KEYWORD",         r"\b(?:int|char|void|if|else|while|for|return|struct|union|typedef)\b"),
    ("NUMBER",          r"\b[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?\b"),
    ("HEXNUMBER",       r"\b0[xX][0-9A-Fa-f]+\b"),
    ("IDENTIFIER",      r"\b[A-Za-z_][A-Za-z0-9_]*\b"),
    ("OP",              r"==|!=|<=|>=|\+\+|--|\+=|-=|\*=|/=|&&|\|\||<<|>>|->|[+\-*/%<>&\^|=~!?:]"),
    ("SEPARATOR",       r"[;,()\[\]\{\}]"),
    ("SKIP",            r"[ \t\r\n]+"),
    ("MISMATCH",        r"."),
   ]
   ```
2) `_TOKEN_REGEX` ile bu desenler tek bir `re.Pattern` hâline getirilir:
   ```
   _TOKEN_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION),
                          re.MULTILINE)
   ```
3) İterasyon: ``finditer`` ile kodu baştan sona tarar:

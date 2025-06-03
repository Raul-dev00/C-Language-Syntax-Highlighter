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
   ```
   for mo in _TOKEN_REGEX.finditer(code):
    kind = mo.lastgroup
    value = mo.group(kind)
    start_pos = mo.start()
    # SKIP: boşluk, tab, newline ise satır-update, ama token ekleme
    # COMMENT2_START: çok satırlı yorum olup olmadığını kontrol et
    # MISMATCH: bilinmeyen karakter → UNKNOWN token
    # Diğer türler: normal token listesine ekle
   ```
4) Çok Satırlı Yorum İşleme: Eğer ``COMMENT2_START`` (``/*``) yakalanırsa, ``*/`` kapanışına kadar metni tek bir ``COMMENT2`` token’ı olarak toplar ve iterator’ı ileri kaydırır.
5) Satır & Kolon Güncelleme:
   - ``value.count("\n")`` ile satır numarasını günceller.
   - ``line_start`` değişkeni ile yeni satırın başlangıç indeksi hesaplanır; böylece ``column = start_pos - line_start + 1`` ifadesi ile doğru kolon elde edilir.
6) Geriye Dönüş: Tamamlanan ``tokens`` listesi döner.
   ```
   from parseTree import tokenize

   code = """
   int main() {
       // Basit bir örnek
       int x = 5;
       return x;
   }
   """
   tokens = tokenize(code)
   for tok in tokens:
       print(tok)
   ```
# Parser (Sözdizimi Analizi)
## Gramer ve Kısıtlamalar: 
- Bu parser, C dilinin tamamını değil, temel yapı taşlarını ele alan basitleştirilmiş bir gramer kullanır. Temel kurallar:
```
program             ::= ( declaration | function_def )*
declaration         ::= type_spec IDENTIFIER ("[" NUMBER "]")* ( "=" expression )? ";" 
function_def        ::= type_spec IDENTIFIER "(" params ")" compound_stmt
params              ::= ( param ("," param)* )?
param               ::= type_spec IDENTIFIER
type_spec           ::= "int" | "char" | "void"
compound_stmt       ::= "{" statement* "}"
statement           ::= expr_stmt | compound_stmt | selection_stmt | iteration_stmt | return_stmt
expr_stmt           ::= ( expression )? ";"
selection_stmt      ::= "if" "(" expression ")" statement ( "else" statement )?
iteration_stmt      ::= "while" "(" expression ")" statement 
                       | "for" "(" expr_stmt expr_stmt ( expression )? ")" statement
return_stmt         ::= "return" ( expression )? ";"
expression          ::= assignment
assignment          ::= logical_or ( ( "=" | "+=" | "-=" | "*=" | "/=" ) logical_or )?
logical_or          ::= logical_and ( "||" logical_and )*
logical_and         ::= equality ( "&&" equality )*
equality            ::= relational ( ( "==" | "!=" ) relational )*
relational          ::= additive ( ( "<" | ">" | "<=" | ">=" ) additive )*
additive            ::= multiplicative ( ( "+" | "-" ) multiplicative )*
multiplicative      ::= unary ( ( "*" | "/" | "%" ) unary )*
unary               ::= ( "+" | "-" | "!" ) unary | primary
primary             ::= IDENTIFIER | NUMBER | HEXNUMBER | STRING_LITERAL | CHAR_LITERAL | "(" expression ")"
```
## Parser Sınıfı Yapısı
- ``parseTree.py`` içindeki ``Parser`` sınıfı, yukarıdaki gramer kurallarını recursive-descent (önce üst, sonra alt) mantığıyla ayrıştırır. Ana bileşenler:
  ```
   class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens     # Token listesi
        self.pos = 0             # Geçerli token indeksi
        self.errors: List[Tuple[int, int, str]] = []  # (satır, kolon, mesaj)

    def current(self) -> Token:
        # Eğer pos dizinini aşarsa, sanal bir EOF token döndürür
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        last = self.tokens[-1] if self.tokens else Token("EOF", "", 0, 1, 1)
        return Token("EOF", "", last.position + len(last.value), last.line, last.column)

    def eat(self, expected_type: str, expected_val: str = None) -> Token:
        # Beklenen tür ve değer geliyorsa ilerle; gelmezse hata kaydet
        tok = self.current()
        if tok.type == expected_type and (expected_val is None or tok.value == expected_val):
            self.pos += 1
            return tok
        else:
            msg = f"Expected {expected_type}"
            if expected_val:
                msg += f"('{expected_val}')"
            msg += f" but found '{tok.value}'"
            self.errors.append((tok.line, tok.column, msg))
            self.pos += 1
            return tok

    def parse(self) -> List[Tuple[int, int, str]]:
        # program ::= ( declaration | function_def )*
        while self.pos < len(self.tokens):
            tok = self.current()
            if tok.type == "KEYWORD" and tok.value in ("int", "char", "void"):
                self.parse_declaration_or_function()
            else:
                self.errors.append((tok.line, tok.column, f"Unexpected token '{tok.value}'"))
                self.pos += 1
        return self.errors
  ```
  - ``parse_declaration_or_function()``
    ```
      def parse_declaration_or_function(self):
       # type_spec (int/char/void)
       self.eat("KEYWORD")
       # identifier (değişken ya da fonksiyon adı)
       self.eat("IDENTIFIER")
       # Eğer '(' geliyorsa function definition, aksi halde declaration
       if self.current().type == "SEPARATOR" and self.current().value == "(":
           self.parse_function_definition()
       else:
           self.parse_declaration()
    ```
  - ``parse_declaration()``
    ```
      def parse_declaration(self):
       # Dizi bildirimi olabilir: IDENTIFIER [ NUMBER ]*
       while self.current().type == "SEPARATOR" and self.current().value == "[":
           self.eat("SEPARATOR", "[")
           self.eat("NUMBER")
           if self.current().type == "SEPARATOR" and self.current().value == "]":
               self.eat("SEPARATOR", "]")
           else:
               tok = self.current()
               self.errors.append((tok.line, tok.column, "Missing ']' in array declaration"))
               self.pos += 1
       # Atama operatörü olabilir
       if self.current().type == "OP" and self.current().value in ("=", "+=", "-=", "*=", "/="):
           self.eat("OP")
           self.parse_expression()
       # Son olarak noktalı virgül
       if self.current().type == "SEPARATOR" and self.current().value == ";":
           self.eat("SEPARATOR", ";")
       else:
           tok = self.current()
           self.errors.append((tok.line, tok.column, "Missing ';' at end of declaration"))
           self.pos += 1
    ```
  - ``parse_function_definition()``
    ```
      def parse_function_definition(self):
    # '('
    self.eat("SEPARATOR", "(")
    self.parse_params()
    if self.current().type == "SEPARATOR" and self.current().value == ")":
        self.eat("SEPARATOR", ")")
    else:
        tok = self.current()
        self.errors.append((tok.line, tok.column, "Missing ')' after function parameters"))
        self.pos += 1
    # compound_stmt: { statement* }
    self.parse_compound_statement()
    ```
  - ``parse_params()``
    ```
      def parse_params(self):
    # Eğer hızlıca ')' gelirse parametre yok
    if self.current().type == "SEPARATOR" and self.current().value == ")":
        return
    # Parametre: type_spec IDENTIFIER
    if self.current().type == "KEYWORD":
        self.eat("KEYWORD")
        self.eat("IDENTIFIER")
    else:
        tok = self.current()
        self.errors.append((tok.line, tok.column, "Invalid parameter declaration"))
        self.pos += 1
    # Birden fazla parametre varsa virgülle ayrılır
    while self.current().type == "SEPARATOR" and self.current().value == ",":
        self.eat("SEPARATOR", ",")
        if self.current().type == "KEYWORD":
            self.eat("KEYWORD")
            self.eat("IDENTIFIER")
        else:
            tok = self.current()
            self.errors.append((tok.line, tok.column, "Invalid parameter declaration"))
            self.pos += 1
    ```
  - ``parse_compound_statement()``
    ```
      def parse_compound_statement(self):
    # '{'
    if self.current().type == "SEPARATOR" and self.current().value == "{":
        self.eat("SEPARATOR", "{")
    else:
        tok = self.current()
        self.errors.append((tok.line, tok.column, "Missing '{' at start of block"))
        self.pos += 1
        return
    # İçerideki statement'ları işle
    while not (self.current().type == "SEPARATOR" and self.current().value == "}"):
        if self.current().type == "EOF":
            self.errors.append((self.current().line, self.current().column, "Unclosed '{'"))
            return
        self.parse_statement()
    # '}'
    self.eat("SEPARATOR", "}")
    ```
  - ``parse_statement()`` ve alt tipleri
    ```
      def parse_statement(self):
    tok = self.current()
    if tok.type == "SEPARATOR" and tok.value == "{":
        self.parse_compound_statement()
    elif tok.type == "KEYWORD" and tok.value == "if":
        self.parse_selection_statement()
    elif tok.type == "KEYWORD" and tok.value in ("while", "for"):
        self.parse_iteration_statement()
    elif tok.type == "KEYWORD" and tok.value == "return":
        self.parse_return_statement()
    else:
        self.parse_expression_statement()
    ```
  - ``parse_selection_statement()``
    ```
      def parse_selection_statement(self):
    self.eat("KEYWORD", "if")
    if self.current().type == "SEPARATOR" and self.current().value == "(":
        self.eat("SEPARATOR", "(")
        self.parse_expression()
        if self.current().type == "SEPARATOR" and self.current().value == ")":
            self.eat("SEPARATOR", ")")
        else:
            tok = self.current()
            self.errors.append((tok.line, tok.column, "Missing ')' after if condition"))
            self.pos += 1
    else:
        tok = self.current()
        self.errors.append((tok.line, tok.column, "Missing '(' after 'if'"))
        self.pos += 1
    self.parse_statement()
    if self.current().type == "KEYWORD" and self.current().value == "else":
        self.eat("KEYWORD", "else")
        self.parse_statement()
    ```
  - ``parse_iteration_statement()``
    ```
      def parse_iteration_statement(self):
    if self.current().value == "while":
        self.eat("KEYWORD", "while")
        if self.current().type == "SEPARATOR" and self.current().value == "(":
            self.eat("SEPARATOR", "(")
            self.parse_expression()
            if self.current().type == "SEPARATOR" and self.current().value == ")":
                self.eat("SEPARATOR", ")")
            else:
                tok = self.current()
                self.errors.append((tok.line, tok.column, "Missing ')' after while condition"))
                self.pos += 1
        else:
            tok = self.current()
            self.errors.append((tok.line, tok.column, "Missing '(' after 'while'"))
            self.pos += 1
        self.parse_statement()
    else:
        self.eat("KEYWORD", "for")
        if self.current().type == "SEPARATOR" and self.current().value == "(":
            self.eat("SEPARATOR", "(")
            self.parse_expression_statement()
            self.parse_expression_statement()
            if self.current().type == "SEPARATOR" and self.current().value == ")":
                self.eat("SEPARATOR", ")")
            else:
                self.parse_expression()
                if self.current().type == "SEPARATOR" and self.current().value == ")":
                    self.eat("SEPARATOR", ")")
                else:
                    tok = self.current()
                    self.errors.append((tok.line, tok.column, "Missing ')' after for clauses"))
                    self.pos += 1
            self.parse_statement()
        else:
            tok = self.current()
            self.errors.append((tok.line, tok.column, "Missing '(' after 'for'"))
            self.pos += 1
    ```
  - ``parse_return_statement()``
      ```
      def parse_return_statement(self):
       self.eat("KEYWORD", "return")
       if not (self.current().type == "SEPARATOR" and self.current().value == ";"):
           self.parse_expression()
       if self.current().type == "SEPARATOR" and self.current().value == ";":
           self.eat("SEPARATOR", ";")
       else:
           tok = self.current()
           self.errors.append((tok.line, tok.column, "Missing ';' after return"))
           self.pos += 1
      ```
  - ``parse_expression_statement()`` ve alt dallar
      ```
         def parse_expression_statement(self):
          if not (self.current().type == "SEPARATOR" and self.current().value == ";"):
              self.parse_expression()
          if self.current().type == "SEPARATOR" and self.current().value == ";":
              self.eat("SEPARATOR", ";")
          else:
              tok = self.current()
              self.errors.append((tok.line, tok.column, "Missing ';' in expression statement"))
              self.pos += 1
      
      def parse_expression(self):
          self.parse_assignment()
      
      def parse_assignment(self):
          self.parse_logical_or()
          if self.current().type == "OP" and self.current().value in ("=", "+=", "-=", "*=", "/="):
              self.eat("OP")
              self.parse_logical_or()
      
      # Aşağıdaki metodlar aynı mantıkla birbiri ardına çağrılır:
      def parse_logical_or(self):
          self.parse_logical_and()
          while self.current().type == "OP" and self.current().value == "||":
              self.eat("OP")
              self.parse_logical_and()
      
      def parse_logical_and(self):
          self.parse_equality()
          while self.current().type == "OP" and self.current().value == "&&":
              self.eat("OP")
              self.parse_equality()
      
      def parse_equality(self):
          self.parse_relational()
          while self.current().type == "OP" and self.current().value in ("==", "!="):
              self.eat("OP")
              self.parse_relational()
      
      def parse_relational(self):
          self.parse_additive()
          while self.current().type == "OP" and self.current().value in ("<", ">", "<=", ">="):
              self.eat("OP")
              self.parse_additive()
      
      def parse_additive(self):
          self.parse_multiplicative()
          while self.current().type == "OP" and self.current().value in ("+", "-"):
              self.eat("OP")
              self.parse_multiplicative()
      
      def parse_multiplicative(self):
          self.parse_unary()
          while self.current().type == "OP" and self.current().value in ("*", "/", "%"):
              self.eat("OP")
              self.parse_unary()
      
      def parse_unary(self):
          if self.current().type == "OP" and self.current().value in ("+", "-", "!"):
              self.eat("OP")
              self.parse_unary()
          else:
              self.parse_primary()
      
      def parse_primary(self):
          tok = self.current()
          if tok.type in ("IDENTIFIER", "NUMBER", "HEXNUMBER", "STRING_LITERAL", "CHAR_LITERAL"):
              self.eat(tok.type)
          elif tok.type == "SEPARATOR" and tok.value == "(":
              self.eat("SEPARATOR", "(")
              self.parse_expression()
              if self.current().type == "SEPARATOR" and self.current().value == ")":
                  self.eat("SEPARATOR", ")")
              else:
                  self.errors.append((tok.line, tok.column, "Missing ')' in expression"))
                  self.pos += 1
          else:
              self.errors.append((tok.line, tok.column, f"Unexpected token '{tok.value}' in expression"))
              self.pos += 1
      ```
## Hata Yönetimi
   - Beklenen Token Bulunmazsa: ``eat()`` metodu içerisinde bir hata mesajı (``Expected … but found …``) ``self.errors`` listesine eklenir ve parser akışı bir sonraki token’a geçerek devam etmeye çalışır (“panic mode” benzeri).
   - Eksik Parantez-‘;’-Blok Kapanışı: Gerekli yerlere koşullu olarak hata satırı ve kolonu eklenir; ilerlerken olabildiğince sonraki token’ı okumaya çalışır.
   - Parse işlemi tamamlandığında ``errors`` listesi, ``(satır, kolon, mesaj)`` üçlüsünden oluşan hatalarla döner. ``Highlighter`` sınıfı bu listeyi alıp status bar’da gösterir.
---

# Syntax Vurgulayıcı (PyQt5)
## Token Kuralları ve Regex
``uygulama_arayuz_kod.py`` içinde, sözdizimi vurgulama için ``CSyntaxHighlighter`` sınıfı kullanılır. Burada her token tipi için bir ``QRegularExpression`` deseni ve ``QTextCharFormat`` stili tanımlanır.
```
| Token Kategorisi                | Regex Deseni                                                      | Renk/Stil          |         |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
| ------------------------------- | ----------------------------------------------------------------- | ------------------ | ------- | -- | ---- | ----- | --- | ------ | ------ | ----- | ------------ | -------------- | -- | -- | -- | ------------ | ---------- | ------------ |
| **Identifiers**                 | `\b[A-Za-z_][A-Za-z0-9_]*\b`                                      | Siyah              |         |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
| **Keywords**                    | \`\b(int                                                          | char               | void    | if | else | while | for | return | struct | union | typedef)\b\` | Kırmızı, Kalın |    |    |    |              |            |              |
| **Preprocessor Direktifleri**   | `^\s*#.*$` (MultilineOption)                                      | Koyu Mavi          |         |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
| **Tek Satır Yorum (`//…`)**     | `//[^\n]*`                                                        | Koyu Yeşil, İtalik |         |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
| **Çok Satırlı Yorum (`/*…*/`)** | Başlangıç: `/\*`   Bitiş: `\*/` (highlightBlock içinde yönetilir) | Koyu Yeşil, İtalik |         |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
| **String Literal**              | \`"(?:\\.                                                         | \[^"\\])\*"\`      | Magenta |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
| **Char Literal**                | \`'(?:\\.                                                         | \[^'\\])\*'\`      | Magenta |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
| **Ondalık Sayılar**             | `\b[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?\b`                     | Mavi               |         |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
| **Onaltılık Sayılar**           | `\b0[xX][0-9A-Fa-f]+\b`                                           | Mavi               |         |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
| **Operatörler**                 | \`(?:==                                                           | !=                 | <=      | >= | ++   | --    | +=  | -=     | \*=    | /=    | &&           | \|\|           | << | >> | -> | \[+-\*/%<>&^ | =\~!?:])\` | Koyu Turuncu |
| **Ayraçlar**                    | `[;,()\[\]\{\}]`                                                  | Koyu Turuncu       |         |    |      |       |     |        |        |       |              |                |    |    |    |              |            |              |
```
## ``CSyntaxHighlighter`` Sınıfı
```
class CSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        # 1) Identifiers → Siyah
        id_fmt = QTextCharFormat()
        id_fmt.setForeground(QColor("black"))
        pattern_id = QRegularExpression(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
        self.rules.append((pattern_id, id_fmt))

        # 2) Keywords → Kırmızı, Kalın
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("red"))
        kw_fmt.setFontWeight(QFont.Bold)
        kws = ["int", "char", "void", "if", "else", "while", "for", "return", "struct", "union", "typedef"]
        pattern_kw = QRegularExpression(r"\b(" + "|".join(kws) + r")\b")
        self.rules.append((pattern_kw, kw_fmt))

        # 3) Preprocessor Direktifleri → Koyu Mavi
        pp_fmt = QTextCharFormat()
        pp_fmt.setForeground(QColor("#000080"))
        pp_pattern = QRegularExpression(r"^\s*#.*$", QRegularExpression.MultilineOption)
        self.rules.append((pp_pattern, pp_fmt))

        # 4) Tek Satır Yorum (“//…”) → Koyu Yeşil İtalik
        comment1_fmt = QTextCharFormat()
        comment1_fmt.setForeground(QColor("#006400"))
        comment1_fmt.setFontItalic(True)
        pattern1 = QRegularExpression(r"//[^\n]*")
        self.rules.append((pattern1, comment1_fmt))

        # 5) Çok Satırlı Yorum (“/*…*/”) — highlightBlock içinde işlenecek
        self.comment2_fmt = QTextCharFormat()
        self.comment2_fmt.setForeground(QColor("#006400"))
        self.comment2_fmt.setFontItalic(True)
        self.comment2_start = QRegularExpression(r"/\*")
        self.comment2_end = QRegularExpression(r"\*/")

        # 6) String Literal → Magenta
        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("magenta"))
        pattern_str = QRegularExpression(r"\"(?:\\.|[^\"\\])*\"")
        self.rules.append((pattern_str, string_fmt))

        # 7) Char Literal → Magenta
        char_fmt = QTextCharFormat()
        char_fmt.setForeground(QColor("magenta"))
        pattern_ch = QRegularExpression(r"'(?:\\.|[^'\\])*'")
        self.rules.append((pattern_ch, char_fmt))

        # 8) Ondalık Sayılar → Mavi
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("blue"))
        pattern_num = QRegularExpression(r"\b[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?\b")
        self.rules.append((pattern_num, num_fmt))

        # 9) Onaltılık Sayılar → Mavi
        hex_fmt = QTextCharFormat()
        hex_fmt.setForeground(QColor("blue"))
        pattern_hex = QRegularExpression(r"\b0[xX][0-9A-Fa-f]+\b")
        self.rules.append((pattern_hex, hex_fmt))

        # 10) Operatörler → Koyu Turuncu
        op_fmt = QTextCharFormat()
        op_fmt.setForeground(QColor("#8B4500"))
        ops = [
            r"==", r"!=", r"<=", r">=", r"\+\+", r"--", r"\+=", r"-=", r"\*=", r"/=", r"&&", r"\|\|",
            r"<<", r">>", r"->",                       # Çok karakterli operatörler
            r"[+\-*/%<>&\^|=~!?:]"                     # Tek karakterli operatörler ve ?: 
        ]
        pattern_op = QRegularExpression("(" + "|".join(ops) + ")")
        self.rules.append((pattern_op, op_fmt))

        # 11) Ayraçlar → Koyu Turuncu
        sep_fmt = QTextCharFormat()
        sep_fmt.setForeground(QColor("#8B4500"))
        pattern_sep = QRegularExpression(r"[;,()\[\]\{\}]")
        self.rules.append((pattern_sep, sep_fmt))
```
## Vurgu İşleyişi
``highlightBlock(self, text: str)`` metodu her satır için şu adımları izler:
1) Önce self.rules içinde tanımlı ``(regex, format)`` çiftlerini sırayla uygular:
   ```
      for regex, fmt in self.rules:
    it = regex.globalMatch(text)
    while it.hasNext():
        match = it.next()
        start = match.capturedStart()
        length = match.capturedLength()
        self.setFormat(start, length, fmt)
   ```
2) Çok Satırlı Yorumlar (``/* … */``) için blok durumunu takip eder:
   - ``setCurrentBlockState(0)`` ile başlar.
   - Eğer önceki blok ``1`` durumundaysa hâlâ yorum içindedir.
   - ``self.comment2_start.match(text)`` ile ``/*`` arar. Bulursa ``start_idx`` elde edilir.
   - ``self.comment2_end.match(text, start_idx)`` ile ``*/`` aranır.
      - ``*/`` bulursa: ``start_idx`` ile ``end`` aralığını ``self.comment2_fmt`` ile renklendirir ve sıradaki ``/*`` aranır.
      - ``*/`` bulunamazsa: satır sonuna kadar ``self.comment2_fmt`` uygulanır ve ``setCurrentBlockState(1)`` ile bir sonraki satırın da yorum içinde başlaması sağlanır.
# GUI Entegrasyonu
## Ana Pencere: ``Highlighter``
``uygulama_arayuz_kod.py`` içinde, ``Highlighter`` sınıfı ``QMainWindow``’dan türetilmiştir:
```
class Highlighter(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.window = Ui_MainWindow()    # uygulama_arayuz.py’de tanımlı UI
        self.window.setupUi(self)

        # 1) QTextEdit’in document’ına CSyntaxHighlighter bağlanır
        self.highlighter = CSyntaxHighlighter(self.window.textEdit.document())

        # 2) Metin her değiştiğinde on_text_changed() çağrılır
        self.window.textEdit.textChanged.connect(self.on_text_changed)
```
### ``Ui_MainWindow`` İçeriği
``uygulama_arayuz.py`` PyQt5 Designer tarafından oluşturulmuş haliyle şu öğeleri içerir:
   - ``QTextEdit textEdit`` → Kod düzenleyici alanı
   - ``QStatusBar statusbar`` → Hata mesajlarını göstermek için
## Metin Değişiklikleri ve Parser Çağrısı
Her metin yazımı veya düzenlemesi sonrası ``on_text_changed()`` tetiklenir:
```
def on_text_changed(self):
    code = self.window.textEdit.toPlainText()
    # 1) Lexical analiz: tokenize
    tokens = tokenize(code)
    # 2) Parser: sözdizimi analizi
    parser = Parser(tokens)
    errors = parser.parse()

    # Hata kontrolü
    if errors:
        msgs = []
        for line, col, msg in errors:
            msgs.append(f"Line {line}, Col {col}: {msg}")
        self.window.statusbar.showMessage(" | ".join(msgs))
    else:
        self.window.statusbar.showMessage("No syntax errors")
```
   - ``tokenize(code)`` ile kodu token’lara ayırır.
   - ``Parser(tokens).parse()`` ile varsa sözdizimi hatalarını toplar.
   - Eğer ``errors`` listesi boş değilse, status bar’da hata mesajlarını birleştirerek gösterir; değilse “No syntax errors” mesajı çıkar.
# Örnek Kullanım
## Basit Örnek
``Highlighter`` penceresini açtıktan sonra aşağıdaki kodu metin düzenleyiciye yapıştırın:
```
// Merhaba Dünya örneği
int main() {
    printf("Hello, World!\n");
    return 0;
}
```
- Syntax Vurgulama:
   - ``int``, ``return`` → kırmızı ve kalın
   - ``main``, ``printf`` → siyah
   - ``"Hello, World!\n"`` → magenta
   - ``;`` → turuncu
   - ``// Merhaba Dünya örneği`` → yeşil itali
- Hata Yok:
   - Status bar “No syntax errors” gösterir.
   - 
# Hata Senaryosu
Aşağıdaki örnek, eksik noktalı virgül durumu:
```
int main() {
    int x = 10   // noktalı virgül eksik
    return x;
}
```
   - ``int x = 10 // noktalı virgül eksik`` satırı vurgulandıktan sonra parse aşamasında,
``parse_declaration`` metodu ``;`` beklediğinde hata yakalar:
   ```
      Line 2, Col 15: Missing ';' at end of declaration
   ```
   - Status bar’da kırmızı uyarı mesajı görünür.

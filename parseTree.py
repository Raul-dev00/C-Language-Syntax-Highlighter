# parseTree.py

import re
from typing import List, Tuple

# ----------------------------------------
# 1. TOKENIZER (LEXER) BÖLÜMÜ
# ----------------------------------------
#
# Bu bölümde, C kodunu token’lara ayırmak için “formal description & table-driven” yaklaşımı
# uygulanır. Yani, regex’ler bir tablo (TOKEN_SPECIFICATION) içinde tanımlanmış, ve
# aynı anda tüm bu desenler birleştirilerek _TOKEN_REGEX altında tek bir regex oluşturulmuştur.
# Ardından metin bu birleşik desenlere göre taranır; bulunan her eşleşme bir Token nesnesine dönüştürülür.
#
# Token tipleri:
#   - PREPROCESSOR:   Satır başında # ile başlayan satırlar (örneğin #include, #define).
#   - COMMENT1:       // ile başlayan tek satırlık yorumlar.
#   - COMMENT2_START: /* ile başlayan çok satırlı yorum başlangıcı (bitene kadar toplanacak).
#   - COMMENT2_END:   */ ile biten çok satırlı yorumun sonu.
#   - STRING_LITERAL: Çift tırnak içinde, escape karakterleri destekleyen string.
#   - CHAR_LITERAL:   Tek tırnak içinde, escape karakterleri destekleyen char literal.
#   - KEYWORD:        C dilindeki anahtar sözcükler (int, char, void, if, else, while, for, return, struct, union, typedef).
#   - NUMBER:         Ondalık sayılar (tam sayı veya float gösterimi).
#   - HEXNUMBER:      Onaltılık sayılar (0x... biçiminde).
#   - IDENTIFIER:     Değişken veya fonksiyon isimleri: harf veya _ ile başlayıp harf/num/arac bulundurabilir.
#   - OP:             Operatörler: ==, !=, <=, >=, ++, --, +=, -=, *=, /=, &&, ||, <<, >>, ->, ya da tek karakterli + - * / % < > & ^ | = ~ ! ? :
#   - SEPARATOR:      Ayraçlar: ; , ( ) { } [ ]
#   - SKIP:           Boşluk, tab, newline; bu token’lar atlanır.
#   - MISMATCH:       Yukarıdakilerle eşleşmeyen diğer karakterler; UNKNOWN olarak işaretlenir.
#
# Çok satırlı yorumlar (COMMENT2_START) bulununca “*/” kapanışına kadar devam eden metin tek bir
# COMMENT2 token’ı olarak eklenir. Eğer kapanış yoksa, kalan tüm metin yorum sayılır.


TOKEN_SPECIFICATION: List[Tuple[str, str]] = [
    ("PREPROCESSOR",     r"^\s*#.*"),                        # Satır başında # içeren direktifler
    ("COMMENT1",         r"//[^\n]*"),                       # // ile başlayan tek satırlık yorum
    ("COMMENT2_START",   r"/\*"),                            # /* ile başlayan çok satırlı yorum başlangıcı
    ("COMMENT2_END",     r"\*/"),                            # Çok satırlı yorumun bitişi (kod içinde yakalanacak)
    ("STRING_LITERAL",   r"\"(?:\\.|[^\"\\])*\""),           # Çift tırnak içinde, escape dizilerini destekler
    ("CHAR_LITERAL",     r"'(?:\\.|[^'\\])*'"),              # Tek tırnak içinde, escape dizilerini destekler
    ("KEYWORD",          r"\b(?:int|char|void|if|else|while|for|return|struct|union|typedef)\b"),
    ("NUMBER",           r"\b[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?\b"),  # Ondalık tam sayılar ve float
    ("HEXNUMBER",        r"\b0[xX][0-9A-Fa-f]+\b"),          # Onaltılık sayılar (0x...)
    ("IDENTIFIER",       r"\b[A-Za-z_][A-Za-z0-9_]*\b"),     # Geçerli C değişken/fonksiyon ismi
    ("OP",               r"==|!=|<=|>=|\+\+|--|\+=|-=|\*=|/=|&&|\|\||<<|>>|->|"
                         r"[+\-*/%<>&\^|=~!?:]"),           # Çok ve tek karakterli operatörler
    ("SEPARATOR",        r"[;,()\[\]\{\}]"),                 # ; , ( ) { } [ ]
    ("SKIP",             r"[ \t\r\n]+"),                     # Boşluk, tab, satır başı: ignore edilecek
    ("MISMATCH",         r"."),                              # Diğer karakterler (bilinmeyen)
]

# Yukarıdaki desenleri tek bir regex’e dönüştürüyoruz.
_TOKEN_REGEX = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION),
    re.MULTILINE
)


class Token:
    """
    Tek bir token bilgisini tutmak için sınıf:
    - type:    Token’ın türü (örneğin KEYWORD, IDENTIFIER, NUMBER...).
    - value:   Token’ın kaynak koddaki tam metni.
    - position: Metindeki karakter indeksi (0 tabanlı).
    - line:    Satır numarası (1 tabanlı).
    - column:  Kolon numarası (1 tabanlı, satır başından itibaren).
    """
    __slots__ = ("type", "value", "position", "line", "column")

    def __init__(self, type_: str, value: str, position: int, line: int, column: int):
        self.type = type_
        self.value = value
        self.position = position
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line}, col={self.column})"


def tokenize(code: str) -> List[Token]:
    """
    Gelen C kodunu tarayıp, token listesi döner.
    - Kod birden fazla satır içerebilir; satır sayısını newline count’a göre güncelliyoruz.
    - Çok satırlı yorumlar (/* ... */) tek bir COMMENT2 token’ı hâline getiriliyor.
    - SKIP token’ları (boşluk, tab, newline) atlanıyor.
    - MISMATCH durumunda, bilinmeyen karakterler “UNKNOWN” türü ile tokenize ediliyor.
    """
    tokens: List[Token] = []
    line_num = 1           # Başlangıçta satır numarası 1
    line_start = 0         # O satırın karakter bazlı başlangıç indeksi

    it = _TOKEN_REGEX.finditer(code)
    idx_iter = iter(it)    # Çok satırlı yorum atlama işlemi için iterator’ı kontrol ediyoruz
    for mo in idx_iter:
        kind = mo.lastgroup       # Hangi grup (token türü) yakalandı
        value = mo.group(kind)    # Eşleşen dizge
        start_pos = mo.start()    # Metindeki başlangıç indeksi

        if kind == "SKIP":
            # SKIP token: yalnızca newline içeriyorsa satır numarasını güncelle
            newlines = value.count("\n")
            if newlines:
                line_num += newlines
                # Son newline’dan sonraki metin satır başı kabul edilir
                line_start = mo.end() - (value.rfind("\n") + 1)
            continue  # Yeni token okumaya devam et

        # Çok satırlı yorum, COMMENT2_START olarak eşleştiğinde:
        if kind == "COMMENT2_START":
            # Kalan metin içinde '*/' desenini arıyoruz
            rest = code[mo.end():]
            end_match = re.search(r"\*/", rest)
            if end_match:
                # Yorum bloğunun tam metnini al
                comment_text = code[mo.start(): mo.end() + end_match.end()]
                # Yorum bloğunda newline varsa satır numarasını güncelle
                inner = code[mo.end(): mo.end() + end_match.end()]
                ln = inner.count("\n")
                if ln:
                    line_num += ln
                    line_start = mo.end() + end_match.end() - (inner.rfind("\n") + 1)
                # Tek bir COMMENT2 token olarak ekle
                tokens.append(Token("COMMENT2", comment_text, mo.start(),
                                    line_num, mo.start() - line_start + 1))
                # ‘finditer’ akışını yorum bloğu sonuna atlamak için iterator’ı ilerlet
                for _ in range(end_match.end()):
                    next(idx_iter, None)
                continue
            else:
                # Eğer kapanış bulunmazsa, bütün kalan kod yorum sayılır
                comment_text = code[mo.start():]
                tokens.append(Token("COMMENT2", comment_text, mo.start(),
                                    line_num, mo.start() - line_start + 1))
                break  # Artık kodun geri kalanını işlemeye gerek yok

        # MISMATCH: tanımsız karakterler “UNKNOWN” olarak tokenize edilir
        if kind == "MISMATCH":
            tokens.append(Token("UNKNOWN", value, start_pos,
                                line_num, start_pos - line_start + 1))
        else:
            # Diğer türler normal olarak eklenir
            tokens.append(Token(kind, value, start_pos,
                                line_num, start_pos - line_start + 1))

        # Eğer value içerisinde newline varsa, satır numarasını güncelle
        if "\n" in value:
            newlines = value.count("\n")
            line_num += newlines
            # Son newline’dan sonraki metin satır başlangıcı kabul edilir
            line_start = mo.end() - (value.rfind("\n") + 1)

    return tokens


# ----------------------------------------
# 2. PARSER (RECURSIVE-DESCENT / TOP-DOWN) BÖLÜMÜ
# ----------------------------------------
#
# Basit bir C dil gramerini Top-Down (recursive-descent) metoduyla parse eder.
# Grammar kuralları minimal tutulmuştur:
#   - program ::= (declaration | function_def)*
#   - declaration ::= type_spec IDENTIFIER ("[" NUMBER "]")* ("=" expression)? ";"
#   - function_def ::= type_spec IDENTIFIER "(" params ")" compound_stmt
#   - params ::= (param ("," param)*)?
#   - param ::= type_spec IDENTIFIER
#   - type_spec ::= "int" | "char" | "void"
#   - compound_stmt ::= "{" stmt_list "}"
#   - stmt_list ::= (statement)*
#   - statement ::= expr_stmt | compound_stmt | selection_stmt | iteration_stmt | return_stmt
#   - expr_stmt ::= (expression)? ";"
#   - selection_stmt ::= "if" "(" expression ")" statement ("else" statement)?
#   - iteration_stmt ::= "while" "(" expression ")" statement | "for" "(" expr_stmt expr_stmt (expression)? ")" statement
#   - return_stmt ::= "return" (expression)? ";"
#   - expression ::= assignment
#   - assignment ::= logical_or (("=" | "+=" | "-=" | "*=" | "/=") logical_or)?
#   - logical_or ::= logical_and ("||" logical_and)*
#   - logical_and ::= equality ("&&" equality)*
#   - equality ::= relational (("==" | "!=") relational)*
#   - relational ::= additive (("<" | ">" | "<=" | ">=") additive)*
#   - additive ::= multiplicative (("+" | "-") multiplicative)*
#   - multiplicative ::= unary (("*" | "/" | "%") unary)*
#   - unary ::= ("+" | "-" | "!") unary | primary
#   - primary ::= IDENTIFIER | NUMBER | HEXNUMBER | STRING_LITERAL | CHAR_LITERAL | "(" expression ")"
#
# Hata bulunduğunda errors listesine (satır, kolon, mesaj) formatında ekler; hata yoksa boş liste döner.

class Parser:
    """
    Basit C parser’ı (Top-Down recursive-descent).
    tokenize() ile elde edilen Token listesi üzerinde gezerek,
    gramer kurallarına göre parse etmeye çalışır. Hata tespit ettiğinde,
    errors listesine satır, kolon ve açıklama ekler.
    """

    def __init__(self, tokens: List[Token]):
        # Gelen token listesi
        self.tokens = tokens
        # Şu an işlenen token indeksi
        self.pos = 0
        # Bulunan hataları toplayacak liste
        self.errors: List[Tuple[int, int, str]] = []

    def current(self) -> Token:
        """
        Geçerli konumdaki token’ı döndürür.
        Eğer pos, token listesinin sonunu geçtiyse, EOF yerine
        uydurma bir Token döndürür (kayıtlı son token’ın pozisyonuna yakın).
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        # Token kalmadıysa uydurma bir EOF token oluştur
        last = self.tokens[-1] if self.tokens else Token("EOF", "", 0, 1, 1)
        return Token("EOF", "", last.position + len(last.value), last.line, last.column)

    def eat(self, expected_type: str, expected_val: str = None) -> Token:
        """
        Eğer current token’un tipi expected_type ve optional olarak değeri expected_val ile
        eşleşiyorsa, pos++ yapıp o token’ı döndürür. Aksi halde hata kaydedip yine pos++ yapar
        ve hatalı token’ı döndürür. (Panic-mode recovery basit bir şekilde uygulanıyor.)
        """
        tok = self.current()
        if tok.type == expected_type and (expected_val is None or tok.value == expected_val):
            self.pos += 1
            return tok
        else:
            # Hata mesajı oluştur
            msg = f"Expected {expected_type}"
            if expected_val:
                msg += f"('{expected_val}')"
            msg += f" but found '{tok.value}'"
            self.errors.append((tok.line, tok.column, msg))
            self.pos += 1
            return tok

    def peek(self, offset=1) -> Token:
        """
        İleri sa gudak goruntuleme (lookahead). pos + offset
        index’indeki token’ı döner. Eğer o indeks yoksa current döner.
        """
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return self.current()

    def parse(self) -> List[Tuple[int, int, str]]:
        """
        En üstten parse işlemini başlatır.
        program ::= (declaration | function_def)*
        """
        while self.pos < len(self.tokens):
            tok = self.current()
            # Eğer KEYWORD ve değeri int, char veya void ise hem declaration hem function
            # olma ihtimali var. Bu yüzden parse_declaration_or_function() kullanılır.
            if tok.type == "KEYWORD" and tok.value in ("int", "char", "void"):
                self.parse_declaration_or_function()
            else:
                # Beklenmeyen token geldi → hata kaydet
                self.errors.append((tok.line, tok.column, f"Unexpected token '{tok.value}'"))
                self.pos += 1

        return self.errors

    def parse_declaration_or_function(self):
        """
        declaration_or_function ::= type_spec IDENTIFIER ("(" params ")" compound_stmt | declaration_rest)
        Eğer “type_spec IDENTIFIER (“ şeklinde devam ediyorsa function_definition,
        değilse değişken bildirimi (declaration).
        """
        # type_spec kısmı (int/char/void)
        self.eat("KEYWORD")
        # IDENTIFIER kısmı
        self.eat("IDENTIFIER")
        # Şimdi bak: eğer "(" geliyorsa function definition
        if self.current().type == "SEPARATOR" and self.current().value == "(":
            self.parse_function_definition()
        else:
            # Yoksa declaration
            self.parse_declaration()

    def parse_declaration(self):
        """
        declaration ::= type_spec IDENTIFIER ("[" NUMBER "]")* ("=" expression)? ";"
        """
        # Dizi bildirimi parantezleri olabilir: [ NUMBER ]
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

    def parse_function_definition(self):
        """
        function_definition ::= "(" params ")" compound_stmt
        (type_spec ve IDENTIFIER zaten parse_declaration_or_function’da yendi.)
        """
        # '(' eki
        self.eat("SEPARATOR", "(")
        self.parse_params()
        if self.current().type == "SEPARATOR" and self.current().value == ")":
            self.eat("SEPARATOR", ")")
        else:
            tok = self.current()
            self.errors.append((tok.line, tok.column, "Missing ')' after function parameters"))
            self.pos += 1

        # compound statement (fonksiyon gövdesi)
        self.parse_compound_statement()

    def parse_params(self):
        """
        params ::= (param (',' param)*)?
        param ::= type_spec IDENTIFIER
        Eğer hiç parametre yoksa doğrudan ')' gelebilir.
        """
        # Hiç parametre yok
        if self.current().type == "SEPARATOR" and self.current().value == ")":
            return

        # 1. parametre: type_spec IDENTIFIER olmalı
        if self.current().type == "KEYWORD":
            self.eat("KEYWORD")
            self.eat("IDENTIFIER")
        else:
            tok = self.current()
            self.errors.append((tok.line, tok.column, "Invalid parameter declaration"))
            self.pos += 1

        # Eğer birden fazla parametre varsa virgülle ayrılmış
        while self.current().type == "SEPARATOR" and self.current().value == ",":
            self.eat("SEPARATOR", ",")
            if self.current().type == "KEYWORD":
                self.eat("KEYWORD")
                self.eat("IDENTIFIER")
            else:
                tok = self.current()
                self.errors.append((tok.line, tok.column, "Invalid parameter declaration"))
                self.pos += 1

    def parse_compound_statement(self):
        """
        compound_stmt ::= '{' stmt_list '}'
        """
        # Blok başlangıcı '{'
        if self.current().type == "SEPARATOR" and self.current().value == "{":
            self.eat("SEPARATOR", "{")
        else:
            tok = self.current()
            self.errors.append((tok.line, tok.column, "Missing '{' at start of block"))
            self.pos += 1
            return

        # İçerideki satırları tek tek parse et
        while not (self.current().type == "SEPARATOR" and self.current().value == "}"):
            if self.current().type == "EOF":
                # Eğer '}' gelmeden dosya biterse, unclosed block hatası
                self.errors.append((self.current().line, self.current().column, "Unclosed '{'"))
                return
            self.parse_statement()

        # Blok kapanışı '}'
        self.eat("SEPARATOR", "}")

    def parse_statement(self):
        """
        statement ::= expr_stmt | compound_stmt | selection_stmt | iteration_stmt | return_stmt
        Burada, mevcut token’a bakarak hangi türde statement olduğu seçiliyor.
        """
        tok = self.current()
        if tok.type == "SEPARATOR" and tok.value == "{":
            # İç içe blok
            self.parse_compound_statement()
        elif tok.type == "KEYWORD" and tok.value == "if":
            # if (…) …
            self.parse_selection_statement()
        elif tok.type == "KEYWORD" and tok.value in ("while", "for"):
            # while veya for
            self.parse_iteration_statement()
        elif tok.type == "KEYWORD" and tok.value == "return":
            # return …
            self.parse_return_statement()
        else:
            # Diğer tüm ifadeler
            self.parse_expression_statement()

    def parse_selection_statement(self):
        """
        selection_stmt ::= 'if' '(' expression ')' statement ('else' statement)?
        """
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

        # if gövdesi
        self.parse_statement()

        # else varsa
        if self.current().type == "KEYWORD" and self.current().value == "else":
            self.eat("KEYWORD", "else")
            self.parse_statement()

    def parse_iteration_statement(self):
        """
        iteration_stmt ::= 'while' '(' expression ')' statement
                         | 'for' '(' expr_stmt expr_stmt (expression)? ')' statement
        """
        if self.current().value == "while":
            # while
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
            # for döngüsü
            self.eat("KEYWORD", "for")
            if self.current().type == "SEPARATOR" and self.current().value == "(":
                self.eat("SEPARATOR", "(")
                self.parse_expression_statement()   # 1. ifade
                self.parse_expression_statement()   # 2. ifade
                if self.current().type == "SEPARATOR" and self.current().value == ")":
                    # Üçüncü ifade yoksa doğrudan )
                    self.eat("SEPARATOR", ")")
                else:
                    # Üçüncü ifade var
                    self.parse_expression()
                    if self.current().type == "SEPARATOR" and self.current().value == ")":
                        self.eat("SEPARATOR", ")")
                    else:
                        tok = self.current()
                        self.errors.append((tok.line, tok.column, "Missing ')' after for clauses"))
                        self.pos += 1
                # for gövdesi
                self.parse_statement()
            else:
                tok = self.current()
                self.errors.append((tok.line, tok.column, "Missing '(' after 'for'"))
                self.pos += 1

    def parse_return_statement(self):
        """
        return_stmt ::= 'return' (expression)? ';'
        """
        self.eat("KEYWORD", "return")
        # Eğer noktalı virgül gelmediyse bir expression parse et
        if not (self.current().type == "SEPARATOR" and self.current().value == ";"):
            self.parse_expression()
        # Son olarak noktalı virgülü bekle
        if self.current().type == "SEPARATOR" and self.current().value == ";":
            self.eat("SEPARATOR", ";")
        else:
            tok = self.current()
            self.errors.append((tok.line, tok.column, "Missing ';' after return"))
            self.pos += 1

    def parse_expression_statement(self):
        """
        expr_stmt ::= (expression)? ';'
        Eğer ifade yoksa doğrudan ';' olabilir (boş ifade).
        """
        if not (self.current().type == "SEPARATOR" and self.current().value == ";"):
            self.parse_expression()
        if self.current().type == "SEPARATOR" and self.current().value == ";":
            self.eat("SEPARATOR", ";")
        else:
            tok = self.current()
            self.errors.append((tok.line, tok.column, "Missing ';' in expression statement"))
            self.pos += 1

    def parse_expression(self):
        """
        expression ::= assignment
        """
        self.parse_assignment()

    def parse_assignment(self):
        """
        assignment ::= logical_or (('=' | '+=', '-=', '*=', '/=') logical_or)?
        """
        self.parse_logical_or()
        if self.current().type == "OP" and self.current().value in ("=", "+=", "-=", "*=", "/="):
            self.eat("OP")
            self.parse_logical_or()

    def parse_logical_or(self):
        """
        logical_or ::= logical_and ("||" logical_and)*
        """
        self.parse_logical_and()
        while self.current().type == "OP" and self.current().value == "||":
            self.eat("OP")
            self.parse_logical_and()

    def parse_logical_and(self):
        """
        logical_and ::= equality ("&&" equality)*
        """
        self.parse_equality()
        while self.current().type == "OP" and self.current().value == "&&":
            self.eat("OP")
            self.parse_equality()

    def parse_equality(self):
        """
        equality ::= relational (("==" | "!=") relational)*
        """
        self.parse_relational()
        while self.current().type == "OP" and self.current().value in ("==", "!="):
            self.eat("OP")
            self.parse_relational()

    def parse_relational(self):
        """
        relational ::= additive (("<" | ">" | "<=" | ">=") additive)*
        """
        self.parse_additive()
        while self.current().type == "OP" and self.current().value in ("<", ">", "<=", ">="):
            self.eat("OP")
            self.parse_additive()

    def parse_additive(self):
        """
        additive ::= multiplicative (("+" | "-") multiplicative)*
        """
        self.parse_multiplicative()
        while self.current().type == "OP" and self.current().value in ("+", "-"):
            self.eat("OP")
            self.parse_multiplicative()

    def parse_multiplicative(self):
        """
        multiplicative ::= unary (("*" | "/" | "%") unary)*
        """
        self.parse_unary()
        while self.current().type == "OP" and self.current().value in ("*", "/", "%"):
            self.eat("OP")
            self.parse_unary()

    def parse_unary(self):
        """
        unary ::= ("+" | "-" | "!") unary | primary
        """
        if self.current().type == "OP" and self.current().value in ("+", "-", "!"):
            self.eat("OP")
            self.parse_unary()
        else:
            self.parse_primary()

    def parse_primary(self):
        """
        primary ::= IDENTIFIER | NUMBER | HEXNUMBER | STRING_LITERAL | CHAR_LITERAL | "(" expression ")"
        """
        tok = self.current()
        if tok.type in ("IDENTIFIER", "NUMBER", "HEXNUMBER", "STRING_LITERAL", "CHAR_LITERAL"):
            # Geçerli bir birincil ifade: sadece yeme
            self.eat(tok.type)
        elif tok.type == "SEPARATOR" and tok.value == "(":
            # Parantezli ifade
            self.eat("SEPARATOR", "(")
            self.parse_expression()
            if self.current().type == "SEPARATOR" and self.current().value == ")":
                self.eat("SEPARATOR", ")")
            else:
                # Kapanış parantezi eksik
                self.errors.append((tok.line, tok.column, "Missing ')' in expression"))
                self.pos += 1
        else:
            # Hiçbir şeye uymadıysa unexpected token hatası
            self.errors.append((tok.line, tok.column, f"Unexpected token '{tok.value}' in expression"))
            self.pos += 1

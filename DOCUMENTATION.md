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
   ```python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows
```


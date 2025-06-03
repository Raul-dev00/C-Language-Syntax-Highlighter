# C Language Syntax Highlighter

Bu proje, C dilinde yazılmış kaynak kodunu gerçek zamanlı olarak analiz eden ve kullanıcıya renkli sözdizimi vurgulama ile hata tespiti sunan bir masaüstü uygulamasıdır. Kodunuz anında renklendirilir, token bazlı analiz yapılır ve basit sözdizimi hataları status bar’da gösterilir.

# Özellikler

1. **Gerçek Zamanlı Syntax Vurgulama**  
   - C anahtar kelimeleri,  
   - Değişken ve fonksiyon isimleri,
   - Sayısal değerler (ondalık ve onaltılık), 
   - Operatörler,  
   - String ve char literal’ler,
   - Yorum satırları vurgular. 
   - Kod düzenleyicide her değişiklik anında renklendirme güncellenir.

2. **Lexical Analiz (Token Listesi)**  
   - Kod, token’lara ayrılarak her bir parçanın türü (keyword, identifier, number, operator, separator, comment vb.) çıkarılır.  

3. **Sözdizimi Hata Tespiti**  
   - Eksik noktalı virgül (`;`), kapalı parantez (`)`, `}`) veya beklenmeyen sembol gibi basit sözdizimi hataları anında tespit edilir.  
   - Alt kısımdaki status bar’da “Line X, Col Y: Hata Mesajı” formatında bilgilendirme yapılır.

# Gereksinimler

- **Python 3.8+**  
- **PyQt5** (GUI için)  

# Kullanım
  1. **Kod Düzenleyici**
     - Açılan pencerede ortada bir metin düzenleyici bulunur.
     - Buraya C kodunuzu yazın veya yapıştırın.
  2. **Gerçek Zamanlı Vurgulama**
     - Düzenleyicide metin her değiştiğinde, sözdizimi vurgulaması otomatik güncellenir.
     - Anahtar kelimeler kırmızı, sayılar mavi, metinler magenta, operatörler turuncu, yorumlar yeşil italik şeklinde gösterilir.
  3. **Status Bar (Hata Mesajı)**
     - Kodda sözdizimi hatası varsa, alt kısımdaki status bar kırmızı uyarı mesajı görüntüler.
     - Hata mesajı “Line X, Col Y: Missing ‘;’” gibi formatta bilgi verir.
     - Hata yoksa “No syntax errors” mesajı çıkar.
  4. **Token Listesi (Lexical Analiz)**
     - Kodun token’larını görmek isterseniz, parseTree.py’daki tokenize fonksiyonunu doğrudan kullanın.
     - Örneğin, main.py içinde aşağıdaki satırı ekleyerek token listesi konsola yazdırılabilir:
     - `print(tokenize(code))`

# Proje Yapısı

**Project-PD/**
- `README.md`                    Projeyi tanıtımı
- `documentation.md`             Detaylı teknik dokümantasyon
- `main.py`                      Uygulamayı başlatan Python betiği
- `parseTree.py`                 Tokenizer & Basit parser (hata tespiti)
- `uygulama_arayuz.py`           PyQt5 Designer ile oluşturulmuş UI tanımı
- `uygulama_arayuz_kod.py`       UI mantığı, CSyntaxHighlighter, tokenize & parse entegrasyonu


# Örnek Kod
```
int topla(int a, int b) {
    return a + b;
}

int main() {
    int x = 10;
    int y = 20;
    int sonuc = topla(x, y);
    printf("Sonuc: %d\n", sonuc);
    return 0;
}
```

# Proje Videosu

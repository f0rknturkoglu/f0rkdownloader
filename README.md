# f0rkn_d0wnl0ader

YouTube, Twitter/X, TikTok ve Facebook platformlarından video indirmek için geliştirilmiş komut satırı uygulaması.

## Özellikler

### YouTube

- Arama yaparak video bulma ve indirme
- Tek video veya playlist indirme
- 4K dahil en yüksek kalitede indirme
- Premium hesap desteği (cookie ile)

### Twitter/X

- Tek tweet videosu indirme
- Toplu URL listesinden indirme
- Yer işaretlerinden toplu indirme (cookie gerekli)

### TikTok

- Tek video link ile indirme
- Toplu URL listesinden indirme
- Liked videoları indirme (URL listesi gerekli)
- Bookmarks/Favorites indirme (URL listesi gerekli)
- Tarayıcı scripti ile URL çıkarma

### Facebook 🆕

- Tek video indirme
- Toplu URL listesinden indirme
- Grup videoları indirme (Selenium ile)
- Watch, Reel ve Video formatları desteği
- Cookie tabanlı oturum yönetimi

### Genel

- Duplicate kontrolü (aynı video tekrar indirilmez)
- İndirilen dosyaları görüntüleme ve silme
- Cookie tabanlı hesap bağlama
- Universal Login (tek cookie ile tüm platformlar)

---

## Sistem Gereksinimleri

| Gereksinim | Minimum Versiyon | Açıklama               |
| ---------- | ---------------- | ---------------------- |
| Python     | 3.10+            | Ana runtime            |
| FFmpeg     | 4.0+             | Video/ses birleştirme  |
| Deno       | 1.0+             | YouTube JS çözümlemesi |
| Chrome     | 90+              | Selenium için (opsiyonel) |
| Windows    | 10/11            | veya Linux/macOS       |

---

## Kurulum

### Windows

1. Python 3.10 veya üstünü yükleyin: https://www.python.org/downloads/
   - Kurulumda "Add Python to PATH" seçeneğini işaretleyin

2. Proje klasörünü açın ve `install.bat` dosyasını çift tıklayın

3. Kurulum scripti aşağıdakileri otomatik yapar:
   - Python sanal ortam oluşturur
   - Pip paketlerini yükler
   - FFmpeg yükler (winget ile)
   - Deno yükler (winget ile)

4. Kurulum tamamlandıktan sonra `run.bat` ile uygulamayı başlatın

### Linux / macOS

```bash
chmod +x install.sh run.sh
./install.sh
./run.sh
```

---

## Proje Yapısı

```
f0rkn_d0wnl0ader/
├── main.py                 # Ana uygulama giriş noktası
├── requirements.txt        # Python bağımlılıkları
├── install.bat             # Windows kurulum scripti
├── install.sh              # Linux/macOS kurulum scripti
├── run.bat                 # Windows çalıştırma scripti
├── run.sh                  # Linux/macOS çalıştırma scripti
├── build.bat               # PyInstaller ile EXE oluşturma
├── README.md               # Bu dosya
├── .gitignore              # Git ignore kuralları
│
├── scripts/                # Tarayıcı scriptleri
│   └── universal_video_collector.user.js  # TikTok/Facebook/Twitter URL toplayıcı
│
└── src/                    # Kaynak kod
    ├── __init__.py
    ├── config.py           # Uygulama konfigürasyonu
    │
    ├── core/               # İndirme modülleri
    │   ├── __init__.py
    │   ├── base.py         # Temel indirici sınıfı
    │   ├── youtube.py      # YouTube indirici (yt-dlp)
    │   ├── twitter.py      # Twitter indirici (gallery-dl)
    │   ├── tiktok.py       # TikTok indirici (yt-dlp)
    │   ├── facebook.py     # Facebook indirici (Selenium + yt-dlp)
    │   └── auth.py         # Kimlik doğrulama yönetimi
    │
    ├── ui/                 # Kullanıcı arayüzü
    │   ├── __init__.py
    │   ├── interface.py    # CLI arayüz bileşenleri
    │   └── theme.py        # Renk ve stil tanımları
    │
    └── utils/              # Yardımcı modüller
        ├── __init__.py
        ├── file_ops.py     # Dosya işlemleri
        └── history.py      # İndirme geçmişi yönetimi
```

---

## İndirme Klasörü Yapısı

Tüm indirmeler kullanıcının Downloads klasöründe oluşturulur:

```
~/Downloads/f0rkn_d0wnl0ader/
├── YouTube/                    # YouTube videoları
│   └── [PlaylistAdi]/          # Playlist alt klasörleri
├── Twitter/                    # Twitter videoları
├── TikTok/                     # TikTok videoları
├── Facebook/                   # Facebook videoları
└── .download_history.json      # İndirme geçmişi (gizli dosya)
```

---

## Cookie Dosyası Kullanımı

Premium YouTube içerikleri veya sosyal medya yer işaretleri için cookie gereklidir.

### Cookie Alma Adımları

1. Tarayıcınıza "Get cookies.txt LOCALLY" eklentisini yükleyin
   - Chrome: Chrome Web Store
   - Firefox: Firefox Add-ons

2. YouTube, Twitter veya Facebook'a giriş yapın

3. Eklenti ikonuna tıklayın ve "Export" seçin

4. Dosyayı `Downloads` klasörüne kaydedin (örneğin: `cookies.txt`)

5. Uygulamada "Universal Login" menüsünden dosyayı seçin

### Universal Login 🆕

Tek bir cookie dosyası ile tüm platformlara giriş yapabilirsiniz:

1. "Hesap İşlemleri" > "Universal Cookie Girişi" seçin
2. Cookie dosyanızı seçin
3. Sistem otomatik olarak YouTube, Twitter, TikTok ve Facebook çerezlerini tespit eder

---

## Universal Video Collector (Tampermonkey Script)

Tek script ile TikTok, Facebook ve Twitter'dan video URL'lerini toplayın!

### Kurulum

1. Tarayıcınıza [Tampermonkey](https://www.tampermonkey.net/) eklentisini yükleyin
2. `scripts/universal_video_collector.user.js` dosyasını açın
3. İçeriği kopyalayın
4. Tampermonkey > Yeni script oluştur > Yapıştır > Kaydet

### Desteklenen Platformlar

| Platform | Simge | Toplanan Linkler |
|----------|-------|------------------|
| TikTok   | 🎵    | `/video/` linkleri |
| Facebook | 📘    | `/watch/`, `/videos/`, `/reel/` |
| Twitter  | 🐦    | `/status/` linkleri |

### Özellikler

- **🔄 Otomatik Scroll & Topla** - Sayfayı otomatik kaydırır ve tüm videoları bulur
- **🔍 Bu Sayfayı Tara** - Görünen videoların URL'lerini toplar
- **💾 TXT Olarak Kaydet** - Doğrudan .txt dosyası indirir
- **📋 Panoya Kopyala** - URL'leri kopyalar

Script, hangi platformda olduğunuzu otomatik algılar ve uygun renk temasını gösterir.

---

## Facebook Özel Notlar

Facebook videoları için özel Selenium entegrasyonu bulunur:

### Çalışma Mantığı

1. Önce yt-dlp ile indirme denenir
2. Başarısız olursa Selenium (headless Chrome) devreye girer
3. Cookie'ler otomatik olarak Selenium'a yüklenir
4. Video sayfası yüklenir ve video URL'si çıkarılır

### Grup Videoları

Kapalı grup videoları için:
- Cookie dosyasında Facebook oturumunuz olmalı
- O gruba üye olmalısınız
- Universal Login yapılmış olmalı

İlk Selenium çalıştırmasında ChromeDriver otomatik indirilir.

---

## Bağımlılıklar

requirements.txt içeriği:

| Paket           | Versiyon   | Açıklama            |
| --------------- | ---------- | ------------------- |
| yt-dlp          | >=2024.0.0 | YouTube/TikTok indirici |
| gallery-dl      | >=1.26.0   | Twitter indirici    |
| selenium        | >=4.0.0    | Facebook Selenium   |
| webdriver-manager| >=4.0.0   | ChromeDriver yönetimi|
| rich            | >=13.0.0   | Terminal UI         |
| questionary     | >=2.0.0    | İnteraktif menü     |
| requests        | >=2.31.0   | HTTP istemcisi      |
| beautifulsoup4  | >=4.12.0   | HTML parsing        |

---

## Sorun Giderme

### "Requested format is not available" hatası

Sebep: JavaScript runtime eksik.

Çözüm:
```
deno --version
winget install DenoLand.Deno
```

### Video düşük kalitede iniyor

Sebep: FFmpeg yüklü değil.

Çözüm:
```
ffmpeg -version
winget install Gyan.FFmpeg
```

### Facebook "Cannot parse data" hatası

Sebep: Video özel bir grupta veya silinmiş.

Çözüm:
1. Universal Login yapın
2. Cookie'nizin güncel olduğundan emin olun
3. Gruba üye olduğunuzu kontrol edin
4. Video silinmiş olabilir

### Selenium hataları

Sebep: Chrome yüklü değil veya versiyonu uyumsuz.

Çözüm:
1. Google Chrome'un yüklü olduğundan emin olun
2. ChromeDriver otomatik güncellenir, tekrar deneyin

---

## EXE Oluşturma (Opsiyonel)

Tek dosya executable oluşturmak için:

```
build.bat
```

Çıktı: `dist/f0rkn_d0wnl0ader.exe`

Not: EXE çalıştırmak için FFmpeg ve Deno sistemde PATH'te olmalı.

---

## Lisans

MIT License

---

## Teknik Notlar

- YouTube indirmeleri yt-dlp kütüphanesi ile yapılır
- Twitter indirmeleri gallery-dl subprocess olarak çalıştırılır
- TikTok indirmeleri yt-dlp subprocess olarak çalıştırılır
- Facebook indirmeleri Selenium + yt-dlp kombinasyonu ile yapılır
- Cookie dosyaları Netscape formatında olmalıdır
- İndirme geçmişi JSON formatında saklanır

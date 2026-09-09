# f0rkn_d0wnl0ader

<div align="center">

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
[![CI](https://github.com/f0rknturkoglu/f0rkdownloader/actions/workflows/ci.yml/badge.svg)](https://github.com/f0rknturkoglu/f0rkdownloader/actions/workflows/ci.yml)
![Tests](https://img.shields.io/badge/Tests-98%2F98%20Passing-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Architecture](https://img.shields.io/badge/Architecture-MVC%20Modular-orange)

**YouTube, Twitter/X, TikTok ve Facebook için Yüksek Performanslı, Çoklu İş Parçacıklı CLI Video & Ses İndirici**

</div>

---

## 📌 Genel Bakış

**f0rkn_d0wnl0ader**, sosyal medya platformlarından video ve ses içeriklerini en yüksek kalitede, güvenli ve organize bir biçimde indirmek için tasarlanmış modern bir konsol (CLI) uygulamasıdır. 

Modüler **MVC (Model-View-Controller)** mimarisi, thread-safe (iş parçacığı güvenli) indirme geçmişi, eşzamanlı toplu indirme motoru ve tarayıcıda gezinirken video bağlantılarını tek tıkla toplayan dahili **Tampermonkey UserScript** eklentisiyle eksiksiz bir indirme deneyimi sunar.

---

## ✨ Özellikler

### 🌐 Platform Desteği
- **YouTube:**
  - Tekli video ve kısa video (Shorts) indirme
  - Oynatma listesi (Playlist) ve kanal kütüphanesi indirme
  - YouTube üzerinde interaktif arama yapıp doğrudan sonuçtan indirme
  - Metin dosyasından (`.txt`) çoklu iş parçacıklı **Toplu İndirme**
  - MP4 (Video) veya MP3 (192 kbps Ses) format dönüştürme
  - Sistemdeki veya WinGet altındaki FFmpeg'i otomatik tespit edip önbelleğe alma
- **Twitter / X:**
  - Tek tweet veya video URL'si indirme
  - Hesabınıza kayıtlı tüm **Yer İmlerini (Bookmarks)** otomatik çekip indirme
  - Metin dosyasından eşzamanlı **Toplu İndirme**
  - Çapraz platform `gallery-dl` motoru
- **TikTok:**
  - Tekli video veya slayt indirme (filigransız / watermark-free)
  - Beğenilen videoları (**Liked**) ve **Favorileri** indirme
  - TikTok resmi veri dışa aktarımı (**Data Export ZIP/JSON**) desteği
  - Metin dosyasından eşzamanlı **Toplu İndirme**
  - Doğrudan `yt-dlp` Python kütüphane motoru (harici subprocess bağımlılığı yok)
- **Facebook:**
  - Normal videolar, Watch bağlantıları ve Facebook Reels indirme
  - Metin dosyasından **Toplu İndirme**
  - **Hibrit İndirme Motoru:** Hızlı doğrudan indirme + Modern headless Selenium 4 entegrasyonu
  - `atexit` güvenliği ile zombi ChromeDriver/Chrome süreçlerinin otomatik kapatılması

### ⚡ Performans ve Mimari
- **Eşzamanlı İndirme (Multithreading):** Ayarlar menüsünden 1 ila 5 iş parçacığı (`max_workers`) seçilebilir. 100+ videoluk listeler donma olmadan paralel indirilir.
- **Akıllı İndirme Geçmişi (Duplicate Prevention):** Daha önce indirilen videolar benzersiz video ID'leri ve disk doğrulamasıyla anında tespit edilir, mükerrer indirmeler atlanır. Toplu indirmelerde diske yüzlerce kez yazmak yerine indirme sonunda tek seferde toplu kayıt (batch save) yapılır.
- **Ağ Dayanıklılığı (Resilience):** 30 saniyelik socket timeout ve otomatik tekrar deneme (retries) ile internet kopmalarında kilitlenme yaşanmaz.
- **Bellek Dostu Akış (Stream Chunking):** Videolar RAM'e doldurulmaz; doğrudan 64 KB'lık akış blokları halinde diske yazılır. RAM tüketimi 60-90 MB arasında sabit kalır.

### 🎨 Kullanıcı Deneyimi & Erişilebilirlik (A11y)
- **WCAG AA Uyumlu Temalar:** Ubuntu (Vibrant Violet), Macintosh (Minimalist Monochrome), Fedora (Accessible Blue) temaları.
- **Yüksek Kontrast:** Koyu terminallerde net okunan başlıklar, breadcrumb göstergeleri ve menü ipuçları.
- **Renk Körlüğü Dostu:** Yalnızca renkle değil; açık metinler ve simgelerle durum bildirme (`✓ Başarılı`, `✗ Hata`, `○ Atlandı`).
- **Özel ASCII Banner:** Açılışta şık ve dinamik olarak temaya göre renklendirilen ASCII Art başlığı.

## Kurulum

### Gereksinimler
- Python 3.10 veya uzeri
- FFmpeg (Sistem yolunda ekli olmali)
- Deno (Opsiyonel, bazi scriptler icin)

### Hizli Kurulum

**Windows:**
```cmd
install.bat
```

**MacOS/Linux:**
```bash
chmod +x install.sh
./install.sh
```

Bu scriptler otomatik olarak:
1. Python surumunu kontrol eder (3.10+)
2. Sanal ortam (.venv) olusturur
3. Gerekli kutuphaneleri yukler
4. FFmpeg ve Deno durumunu kontrol eder

### Manuel Kurulum

1. Sanal ortam olusturun:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# MacOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

2. Bagimliliklari yukleyin:
```bash
pip install -r requirements.txt
```

## Calistirma

**Windows:**
```cmd
run.bat
```

**MacOS/Linux:**
```bash
./run.sh
```

**Manuel Calistirma:**
```bash
python main.py
```

## Mimari

Proje MVC (Model-View-Controller) mimarisi kullanir:

```
f0rkdownloader/
├── main.py                 # Uygulama giris noktasi ve yonlendirici
├── build.bat               # PyInstaller standalone .exe olusturucu
├── install.bat / run.bat   # Windows baslaticilar (UTF-8 destekli)
├── install.sh / run.sh     # Unix baslaticilar
├── src/
│   ├── config.py           # Uygulama ayarlari (JSON ile kalici)
│   ├── controllers/        # Is mantigi kontrolorleri
│   │   ├── base.py         # Soyut temel kontrolor & get_resource_path
│   │   ├── youtube_controller.py
│   │   ├── twitter_controller.py
│   │   ├── tiktok_controller.py
│   │   ├── facebook_controller.py
│   │   ├── settings_controller.py
│   │   └── account_controller.py
│   ├── core/               # Platform indirme modulleri
│   │   ├── base.py         # Temel indirici sinifi
│   │   ├── youtube.py      # yt-dlp + FFmpeg cache + Concurrency
│   │   ├── twitter.py      # gallery-dl + Concurrency
│   │   ├── tiktok.py       # yt-dlp dahili kutuphane + Concurrency
│   │   ├── facebook.py     # Selenium (atexit) + yt-dlp
│   │   └── auth.py         # Kimlik dogrulama
│   ├── ui/
│   │   ├── interface.py    # Kullanici arayuzu & ASCII Art
│   │   └── theme.py        # Tema renkleri (Ubuntu, Mac, Fedora)
│   └── utils/
│       ├── history.py      # Thread-safe indirme gecmisi & toplu kayit
│       └── logger.py       # Merkezi loglama
├── tests/                  # Unit testler (51/51 basarili)
│   ├── test_downloaders.py # Platform indiricileri & UI testleri
│   ├── test_history.py     # Gecmis & fallback testleri
│   ├── test_config.py      # Ayar kaliciligi & workers testleri
│   └── test_logger.py      # Loglama testleri
└── scripts/                # Universal Tampermonkey toplayici script
```

## 📖 Kullanım Rehberi

### 1. YouTube İndirme
- **Link ile İndir:** Tek bir video veya oynatma listesi URL'sini yapıştırarak doğrudan indirin.
- **Toplu İndir (URL Listesi):** İçinde her satırda bir YouTube linki bulunan bir `.txt` dosyası verin. Videolar seçtiğiniz `max_workers` iş parçacığı adedince paralel indirilir.
- **YouTube'da Ara:** İndirmek istediğiniz videonun adını yazın; çıkan listeden seçim yaparak indirin.
- **Kütüphanemden İndir:** Oturum açtıysanız beğendiğiniz veya kaydettiğiniz oynatma listelerini çekip indirin.

### 2. Twitter / X İndirme
- **Tek Tweet İndir:** Tweet bağlantısını yapıştırın.
- **Yer İmlerini İndir:** Hesabınızdaki kayıtlı videoları otomatik tarayıp indirir.
- **Toplu İndir:** Tweet bağlantılarını içeren `.txt` dosyasını eşzamanlı indirir.

### 3. TikTok İndirme
- **Tek Video:** TikTok URL'sini girin (kısa `vm.tiktok.com` linkleri de desteklenir).
- **Beğenilenler & Favoriler:** Çerezlerinizle oturum açtıktan sonra otomatik çekip indirin.
- **Veri Export (ZIP/JSON):** TikTok uygulamasından talep ettiğiniz profil veri arşivini doğrudan göstererek tüm videolarınızı arşivleyin.
- **Toplu İndir:** Metin dosyasındaki tüm linkleri filigransız olarak toplu indirin.

### 4. Facebook İndirme
- **Tek Video:** Watch, Reel veya video bağlantısını yapıştırın. Sistem önce doğrudan akış dener; video gizli veya karmaşık yapıdaysa otomatik olarak headless Selenium 4 devreye girer.
- **Toplu İndir:** Facebook bağlantı listesini sırayla indirir ve işlem bittiğinde tarayıcıyı temiz şekilde kapatır.

---

## 🔑 Kimlik Doğrulama (Otomatik Cookie Taraması)

Özel oynatma listeleri, TikTok favorileri, Twitter yer imleri veya gizli Facebook videoları için oturum açılması gerekir. **Elle dosya yolu girmeye gerek yoktur;** uygulama İndirilenler (`~/Downloads`) klasörünüzü otomatik olarak tarar!

### ⚡ Otomatik Cookie Yükleme (Önerilen)
1. Tarayıcınıza güvenilir bir Netscape cookie eklentisi kurun:
   - Chrome / Brave / Edge: **Get cookies.txt LOCALLY**
   - Firefox: **cookies.txt**
2. İlgili sosyal medya platformunda oturum açıp eklentiyle çerezleri indirin (dosya doğrudan `İndirilenler` klasörünüze kaydedilir).
3. Uygulamada **"Hesap İşlemleri"** menüsüne girin:
   - **⚡ İndirilenler Klasörünü Tara ve Otomatik Bağla (TEK TIK):** En güncel cookie dosyasını tespit eder, YouTube, Twitter, TikTok ve Facebook için geçerliliğini test eder ve hepsini tek tıkla bağlar.
   - **Seçimli / Platform Bazlı Giriş:** İndirilenler klasöründeki tespit edilen cookie dosyaları tarih/saat ve boyutlarıyla listelenir; yön tuşlarıyla seçip hemen onaylayabilirsiniz.
   - **Manuel Giriş:** İsteğe bağlı olarak farklı bir dizindeki dosya yolunu elle de girebilirsiniz.


---

## 🧩 Universal Video Collector (Tampermonkey Script)

`scripts/universal_video_collector.user.js` dosyasında yer alan kullanıcı betiği (UserScript), Facebook, Twitter ve TikTok sayfalarında gezinirken video URL'lerini otomatik olarak toplar:

1. Tarayıcınıza **Tampermonkey** veya **Violentmonkey** eklentisini kurun.
2. Eklenti panelinden **"Yeni Script Ekle"** seçin ve `universal_video_collector.user.js` dosyasının içeriğini yapıştırın.
3. TikTok, Twitter veya Facebook'a girdiğinizde sağ üstte şık bir toplama paneli açılır:
   - **🔄 Otomatik Scroll & Topla:** Sayfayı otomatik aşağı kaydırarak tüm videoları yakalar.
   - **💾 TXT Olarak Kaydet:** Toplanan tüm linkleri doğrudan uygulamaya verebileceğiniz formatta dışa aktarır.
   - **📋 Panoya Kopyala:** Linkleri panoya kopyalar.

---

## ⚙️ Ayarlar ve İndirilenlerin Konumu

Tüm kullanıcı verileri ve indirilen içerikler varsayılan olarak kullanıcının `Downloads` klasöründe tutulur:

```
~/Downloads/f0rkn_d0wnl0ader/
├── settings.json              # Uygulama ayarları (Tema, format, kalite, workers)
├── .download_history.json     # İndirme geçmişi (Mükerrer kontrolü)
├── .logs/                     # Günlük log dosyaları (app_YYYYMMDD.log)
├── YouTube/                   # İndirilen YouTube videoları
├── Twitter/                   # İndirilen Twitter videoları
├── TikTok/                    # İndirilen TikTok videoları
└── Facebook/                  # İndirilen Facebook videoları
```

### Ayarlar Menüsü:
- **Tema:** Ubuntu, Macintosh veya Fedora.
- **Video Kalitesi:** En İyi, 1080p, 720p, En Düşük.
- **İndirme Formatı:** Video (MP4) veya Sadece Ses (MP3).
- **Eşzamanlı İndirme:** 1 (Sıralı), 2 (Dengeli), 3 (Varsayılan Hızlı), 5 (Maksimum Performans).

---

## 🧪 Testler ve CI/CD İşlem Hattı

Uygulamanın tüm modülleri, uç senaryoları ve iş parçacığı güvenliği **98 adet kapsamlı birim test** ile doğrulanmaktadır:

- `test_config.py`: Konfigürasyon yükleme, kaydetme, sıfırlama ve doğrulama (10 test)
- `test_history.py`: İndirme geçmişi, video ID çıkarımı ve eşzamanlı disk kontrolü (16 test)
- `test_logger.py`: Singleton kayıtçısı, kimlik ve indirme logları (5 test)
- `test_auth.py`: Çerez dosyası, tarayıcı çerezleri ve playlist yönetimi (14 test)
- `test_theme.py`: Renk şemaları, WCAG AA erişilebilirlik ve tema yedekleri (5 test)
- `test_base_core.py`: İndirici temel seçenekleri ve özel hata hiyerarşisi (4 test)
- `test_controllers.py`: Otomatik cookie taraması, kontrolcü hata yakalama ve ayar eylemleri (13 test)
- `test_downloaders.py`: Platform motorları, önbellek ve UI bileşenleri (31 test)

```bash
# Sanal ortam aktifken:
python -m unittest discover -s tests -v
```

**Test Çıktısı:**
```text
Ran 98 tests in 0.540s

OK (98/98 Başarılı)
```

### 🚀 Sürekli Entegrasyon (CI/CD)
Projede **GitHub Actions** kullanılarak çoklu işletim sistemi ve Python sürüm matrisi üzerinde otomatik test koşumu sağlanmıştır (`.github/workflows/ci.yml`):
- **İşletim Sistemleri:** `Ubuntu (Linux)`, `Windows`, `macOS`
- **Python Sürümleri:** `3.10`, `3.11`, `3.12`
- Her `push` ve `pull_request` işleminde tüm testler otomatik çalıştırılır ve kod bütünlüğü korunur.


---

## ⚖️ Sorumluluk Reddi (Disclaimer)

Bu yazılım yalnızca kişisel arşivleme ve eğitim amaçlı geliştirilmiştir. İndirdiğiniz içeriklerin telif hakları ilgili hak sahiplerine aittir. Kullanıcıların platformların hizmet şartlarına ve telif hakkı yasalarına uygun hareket etmesi kendi sorumluluğundadır.

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

# f0rkn Downloader

Premium video downloader uygulamasi. YouTube, Twitter/X, TikTok ve Facebook platformlarindan video indirme destegi sunar.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Ozellikler

### Platform Destegi
- **YouTube**: Video, playlist ve kutuphane indirme
- **Twitter/X**: Tek video, toplu indirme ve bookmarks
- **TikTok**: Tek video, toplu indirme, liked ve favorites (veri export destegi)
- **Facebook**: Tek video ve toplu indirme (Selenium ile gelismis destek)

### Teknik Ozellikler
- **Cookie tabanli kimlik dogrulama** - Tum platformlar icin
- **Indirme gecmisi** - Mukerrer indirmeleri onler
- **Kapsamli loglama** - Hata ayiklama icin
- **Kalici ayarlar** - JSON formatinda
- **Tema destegi** - Ubuntu, Macintosh, Fedora
- **MVC mimarisi** - Temiz ve genisletilebilir kod

## Kurulum

### Gereksinimler
- Python 3.10 veya uzeri
- FFmpeg (Sistem yolunda ekli olmali)
- Deno (Opsiyonel, bazi scriptler icin)

### Hizli Kurulum (MacOS/Linux)

```bash
chmod +x install.sh
./install.sh
```

Bu script otomatik olarak:
1. Python surumunu kontrol eder (3.10+)
2. Sanal ortam (venv) olusturur
3. Gerekli kutuphaneleri yukler
4. FFmpeg ve Deno durumunu kontrol eder

### Manuel Kurulum

1. Sanal ortam olusturun:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Bagimliliklari yukleyin:
```bash
pip install -r requirements.txt
```

## Calistirma

Kurulum scriptini kullandiysaniz:
```bash
./run.sh
```

Manuel calistirmak icin:
```bash
python main.py
```

## Mimari

Proje MVC (Model-View-Controller) mimarisi kullanir:

```
benimDownloader/
├── main.py                 # Uygulama giris noktasi ve yonlendirici
├── src/
│   ├── config.py           # Uygulama ayarlari (JSON ile kalici)
│   ├── controllers/        # Is mantigi kontrolorleri
│   │   ├── base.py         # Soyut temel kontrolor
│   │   ├── youtube_controller.py
│   │   ├── twitter_controller.py
│   │   ├── tiktok_controller.py
│   │   ├── facebook_controller.py
│   │   ├── settings_controller.py
│   │   └── account_controller.py
│   ├── core/               # Platform indirme modulleri
│   │   ├── base.py         # Temel indirici sinifi
│   │   ├── youtube.py
│   │   ├── twitter.py      # gallery-dl kullanir
│   │   ├── tiktok.py       # yt-dlp kullanir
│   │   ├── facebook.py     # Selenium + yt-dlp
│   │   └── auth.py         # Kimlik dogrulama
│   ├── ui/
│   │   ├── interface.py    # Kullanici arayuzu
│   │   └── theme.py        # Tema renkleri
│   └── utils/
│       ├── history.py      # Indirme gecmisi yonetimi
│       ├── logger.py       # Merkezi loglama
├── tests/                  # Unit testler
│   ├── test_history.py
│   ├── test_config.py
│   └── test_logger.py
└── scripts/                # Yardimci scriptler
```

## Testler

Testleri calistirmak icin:

```bash
# Tum testler
python -m unittest discover tests/
```

## Kimlik Dogrulama

### Cookie Dosyasi Hazirlama

1. **Tarayici eklentisi kullanin:**
   - Chrome: Get cookies.txt LOCALLY
   - Firefox: cookies.txt

2. **Ilgili platformda oturum acin:**
   - YouTube: youtube.com
   - Twitter/X: x.com veya twitter.com
   - TikTok: tiktok.com
   - Facebook: facebook.com

3. **Cookie'leri export edin** ve `Downloads` klasorune kaydedin

4. **Uygulamada "Hesap Islemleri"** menusunden dosya yolunu gosterin

### Universal Cookie Girisi

Tek bir cookie dosyasinda birden fazla platform bilgisi varsa (ornegin tum siteler icin tek export aldiysaniz), "Tek Dosya ile Toplu Giris" secenegini kullanarak tek seferde tum platformlar icin oturum acabilirsiniz.

## Loglama

Log dosyalari `~/Downloads/f0rkn_d0wnl0ader/.logs/` klasorunde tutulur:
- Gunluk log dosyalari: `app_YYYYMMDD.log`
- 7 gunden eski loglar otomatik silinir

## Ayarlar

Ayarlar `~/Downloads/f0rkn_d0wnl0ader/settings.json` dosyasinda saklanir:
- Tema rengi
- Video kalitesi
- Format tercihi (video/audio)
- Platform kimlik bilgileri

## Sorumluluk Reddi

Bu uygulama sadece egitim amaclidir. Indirdiginiz iceriklerin telif haklari size ait olmali veya icerik sahiplerinden izin almis olmalisiniz. Yasadisi icerik indirmek kullanicinin sorumlulugundadir.

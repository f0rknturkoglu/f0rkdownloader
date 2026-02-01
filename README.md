# f0rkn_d0wnl0ader

YouTube ve Twitter/X platformlarından video indirmek için geliştirilmiş komut satırı uygulaması.

## Ozellikler

### YouTube

- Arama yaparak video bulma ve indirme
- Tek video veya playlist indirme
- 4K dahil en yuksek kalitede indirme
- Premium hesap destegi (cookie ile)

### Twitter/X

- Tek tweet videosu indirme
- Toplu URL listesinden indirme
- Yer isaretlerinden toplu indirme (cookie gerekli)

### Genel

- Duplicate kontrolu (ayni video tekrar indirilmez, dosya silinirse tekrar indirilebilir)
- Indirilen dosyalari goruntuleme ve silme
- Cookie tabanli hesap baglama

---

## Sistem Gereksinimleri

| Gereksinim | Minimum Versiyon | Aciklama               |
| ---------- | ---------------- | ---------------------- |
| Python     | 3.10+            | Ana runtime            |
| FFmpeg     | 4.0+             | Video/ses birlestirme  |
| Deno       | 1.0+             | YouTube JS cozumlemesi |
| Windows    | 10/11            | veya Linux/macOS       |

---

## Kurulum

### Windows

1. Python 3.10 veya ustunu yukleyin: https://www.python.org/downloads/
   - Kurulumda "Add Python to PATH" secenegini isaretleyin

2. Proje klasorunu acin ve `install.bat` dosyasini cift tiklayin

3. Kurulum scripti asagidakileri otomatik yapar:
   - Python sanal ortam olusturur
   - Pip paketlerini yukler
   - FFmpeg yukler (winget ile)
   - Deno yukler (winget ile)

4. Kurulum tamamlandiktan sonra `run.bat` ile uygulamayi baslatin

### Linux / macOS

```bash
chmod +x install.sh run.sh
./install.sh
./run.sh
```

---

## Proje Yapisi

```
f0rkn_d0wnl0ader/
├── main.py                 # Ana uygulama giris noktasi
├── requirements.txt        # Python bagimliliklari
├── install.bat             # Windows kurulum scripti
├── install.sh              # Linux/macOS kurulum scripti
├── run.bat                 # Windows calistirma scripti
├── run.sh                  # Linux/macOS calistirma scripti
├── build.bat               # PyInstaller ile EXE olusturma
├── README.md               # Bu dosya
├── .gitignore              # Git ignore kurallari
│
└── src/                    # Kaynak kod
    ├── __init__.py
    ├── config.py           # Uygulama konfigurasyonu
    │
    ├── core/               # Indirme modulleri
    │   ├── __init__.py
    │   ├── base.py         # Temel indirici sinifi
    │   ├── youtube.py      # YouTube indirici (yt-dlp)
    │   ├── twitter.py      # Twitter indirici (gallery-dl)
    │   └── auth.py         # Kimlik dogrulama yonetimi
    │
    ├── ui/                 # Kullanici arayuzu
    │   ├── __init__.py
    │   ├── interface.py    # CLI arayuz bilesenleri
    │   └── theme.py        # Renk ve stil tanimlari
    │
    └── utils/              # Yardimci moduller
        ├── __init__.py
        ├── file_ops.py     # Dosya islemleri
        └── history.py      # Indirme gecmisi yonetimi
```

---

## Indirme Klasoru Yapisi

Tum indirmeler kullanicinin Downloads klasorunde olusturulur:

```
~/Downloads/f0rkn_d0wnl0ader/
├── YouTube/                    # YouTube videolari
│   └── [PlaylistAdi]/          # Playlist alt klasorleri
├── Twitter/                    # Twitter videolari
└── .download_history.json      # Indirme gecmisi (gizli dosya)
```

---

## Cookie Dosyasi Kullanimi

Premium YouTube icerikleri veya Twitter yer isaretleri icin cookie gereklidir.

### Cookie Alma Adimlari

1. Tarayiciniza "Get cookies.txt LOCALLY" eklentisini yukleyin
   - Chrome: Chrome Web Store
   - Firefox: Firefox Add-ons

2. YouTube veya Twitter'a giris yapin

3. Eklenti ikonuna tiklayin ve "Export" secin

4. Dosyayi `Downloads` klasorune kaydedin (ornegin: `cookies.txt`)

5. Uygulamada "Hesap Bagla" menusunden dosyayi secin

### Cookie Formati

Dosya Netscape cookie formatinda olmalidir. Ornek:

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1234567890	LOGIN_INFO	xxxxx
.youtube.com	TRUE	/	FALSE	1234567890	SID	xxxxx
```

---

## Bagimliliklar

requirements.txt icerigi:

| Paket         | Versiyon   | Aciklama            |
| ------------- | ---------- | ------------------- |
| yt-dlp        | >=2024.0.0 | YouTube indirici    |
| yt-dlp-ejs    | >=0.4.0    | JS challenge cozucu |
| gallery-dl    | >=1.26.0   | Twitter indirici    |
| rich          | >=13.0.0   | Terminal UI         |
| questionary   | >=2.0.0    | Interaktif menu     |
| requests      | >=2.31.0   | HTTP istemcisi      |
| pycryptodomex | >=3.20.0   | Sifreleme           |
| brotli        | >=1.1.0    | Sikistirma          |
| websockets    | >=12.0     | WebSocket destegi   |

---

## Sorun Giderme

### "Requested format is not available" hatasi

Sebep: JavaScript runtime eksik veya calismiyordur.

Cozum:

```
deno --version
```

Eger Deno yuklu degilse:

```
winget install DenoLand.Deno
```

### Video dusuk kalitede iniyor

Sebep: FFmpeg yuklu degil, video ve ses akislari birlestirilemiyordur.

Cozum:

```
ffmpeg -version
```

Eger FFmpeg yuklu degilse:

```
winget install Gyan.FFmpeg
```

### Twitter indirme calismiyor

Sebep: Cookie dosyasi eksik veya suresi dolmus.

Cozum:

1. Tarayicidan yeni cookie dosyasi alin
2. Downloads klasorune koyun
3. Uygulamadan tekrar secin

### "Bu video zaten indirilmis" ama dosya yok

Bu durum artik olmaz. Uygulama indirme gecmisini kontrol ederken dosyanin fiziksel olarak var olup olmadigini da kontrol eder. Dosya silinmisse, tekrar indirmeye izin verir.

---

## EXE Olusturma (Opsiyonel)

Tek dosya executable olusturmak icin:

```
build.bat
```

Cikti: `dist/f0rkn_d0wnl0ader.exe`

Not: EXE calistirmak icin FFmpeg ve Deno sistemde PATH'te olmali veya ayni dizinde bulunmalidir.

---

## Lisans

MIT License

---

## Teknik Notlar

- YouTube indirmeleri yt-dlp kutuphanesi ile yapilir
- Twitter indirmeleri gallery-dl subprocess olarak calistirilir
- Cookie dosyalari Netscape formatinda olmalidir
- Indirme gecmisi JSON formatinda saklanir
- Dosya varlik kontrolu her indirme oncesi yapilir

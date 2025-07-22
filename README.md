# 🤖 Bot WhatsApp AI Media

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![AI](https://img.shields.io/badge/AI-Gemini%202.0-purple.svg)
![Platform](https://img.shields.io/badge/Platform-1000+-orange.svg)
![Indonesia](https://img.shields.io/badge/Bahasa-Indonesia-red.svg)

**Downloader Media Universal + Analisis AI untuk WhatsApp**

*Download, transkripsi, dan analisis konten dari 1000+ platform dengan kemampuan AI canggih*

</div>

## ✨ Fitur

### 📥 Download Media Universal
- 🎵 **Download Audio** - Ekstraksi MP3 berkualitas tinggi
- 🎬 **Download Video** - Pilihan kualitas beragam (480p-1080p)
- 🌐 **1000+ Platform** - YouTube, TikTok, Instagram, Facebook, Twitter, SoundCloud, Vimeo, Twitch, Reddit, dan lainnya
- ⚡ **Pemrosesan Cepat** - Kecepatan download yang dioptimalkan

### 🧠 Fitur AI Canggih
- 📝 **Transkripsi Pintar** - Konversi audio/video ke teks dengan Gemini AI
- 📊 **Ringkasan Konten** - Ringkasan bertenaga AI dalam bahasa Indonesia
- 🔍 **Analisis Cerdas** - Wawasan konten mendalam dan kategorisasi
- 🎯 **Pengenalan Media** - Deteksi otomatis media yang di-quote di WhatsApp

### 🎬 Optimasi Konten YouTube
- 📈 **Generator Judul** - 3 saran judul SEO-optimized (maks 60 karakter)
- 📝 **Pembuat Deskripsi** - Paragraf hook, ringkasan, dan CTA
- #️⃣ **Riset Hashtag** - 15 hashtag strategis (viral + niche + long-tail)
- 🎨 **Ide Thumbnail** - Saran kreatif berdasarkan konten
- ⏰ **Timing Upload** - Rekomendasi waktu terbaik
- 👥 **Targeting Audience** - Identifikasi audience utama

### 🚀 Pemrosesan Pintar
- 🔄 **Multi-Fitur AI** - Gabungan transkripsi + ringkasan + analisis
- 📱 **WhatsApp Native** - Reply media langsung untuk analisis AI instan
- 🧹 **Auto Cleanup** - Manajemen file dan pembersihan otomatis
- 🛡️ **Error Handling** - Recovery error yang robust dan feedback user

## 🛠️ Instalasi

### Prasyarat
- Python 3.8+
- yt-dlp terinstall
- Akun WhatsApp
- API key Gemini

### Setup Cepat

1. **Clone repository**
```bash
git clone https://github.com/username/bot-whatsapp-ai-media.git
cd bot-whatsapp-ai-media
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install yt-dlp**
```bash
pip install yt-dlp
# atau
sudo apt install yt-dlp  # Linux
brew install yt-dlp      # macOS
```

4. **Konfigurasi API Key**
```python
# Edit script dan ganti:
GEMINI_API_KEY = "api-key-gemini-anda-di-sini"
```

5. **Jalankan bot**
```bash
python whatsapp_ai_bot.py
```

## 📱 Penggunaan

### Perintah Dasar

```
🏓 ping                    - Test konektivitas bot
📚 help                    - Tampilkan semua perintah
ℹ️ info <URL>             - Dapatkan informasi media
```

### Perintah Download

```
🎵 mp3 <URL>               - Download audio (MP3)
🎬 video <URL> [kualitas]  - Download video
   Kualitas: worst, 480p, 720p, 1080p, best
```

### Perintah Bertenaga AI

```
📝 transcribe <URL>        - Transkripsi audio
📊 summary <URL>          - Ringkasan konten AI
🔍 analyze <URL>          - Analisis AI lengkap
🧠 smart <URL>            - Download + transkripsi + ringkasan + analisis
```

### Kreasi Konten YouTube

```
🎬 ytvideo <URL>          - Analisis video untuk optimasi YouTube
🎵 ytaudio <URL>          - Analisis audio untuk optimasi YouTube
```

### Analisis Media (Reply ke Media)

```
Reply ke media apapun dengan:
🔍 analyze                - Analisis media yang di-quote dengan AI
📝 transcribe             - Transkripsi audio/video yang di-quote
```

### Chat AI Langsung

```
🤖 ai <pertanyaan anda>   - Chat langsung dengan Gemini AI
```

## 🌐 Platform yang Didukung

<details>
<summary>Klik untuk melihat semua platform yang didukung</summary>

### 📺 Platform Video
- YouTube, YouTube Music
- TikTok, TikTok Music
- Instagram (Posts, Reels, IGTV, Stories)
- Facebook, Facebook Watch
- Twitter/X, Twitter Spaces
- Vimeo, Dailymotion
- Twitch, Twitch Clips
- Reddit Videos

### 🎵 Platform Audio
- SoundCloud
- Spotify (preview)
- Bandcamp
- Mixcloud
- AudioMack

### 📱 Media Sosial
- Snapchat
- Pinterest
- LinkedIn
- Varian TikTok (vm.tiktok.com, vt.tiktok.com)

### 🎮 Gaming & Streaming
- Twitch
- YouTube Gaming
- Facebook Gaming

### 📰 Berita & Media
- CNN, BBC, NBC
- Berbagai outlet berita
- Platform podcast

*Dan 900+ platform lainnya yang didukung yt-dlp!*

</details>

## 🎯 Kasus Penggunaan

### 👨‍💼 Content Creator
- Analisis konten kompetitor
- Generate judul dan deskripsi YouTube
- Ekstrak audio dari video untuk podcast
- Dapatkan insight dan ringkasan konten

### 📚 Peneliti & Mahasiswa
- Transkripsi kuliah dan wawancara
- Ringkas konten long-form
- Ekstrak audio dari video edukasi
- Analisis tema konten media

### 📈 Social Media Manager
- Download konten untuk analisis
- Generate saran optimasi
- Buat ringkasan konten
- Ekstrak insight dari konten viral

### 🎵 Musisi & Produser
- Ekstrak audio dari video
- Analisis konten musik
- Transkripsi lirik dan wawancara
- Download track referensi

## 🔥 Contoh Demo

### Contoh Smart Processing
```
User: smart https://youtu.be/dQw4w9WgXcQ

Respon Bot:
🎵 Never Gonna Give You Up
👤 Rick Astley | YouTube
⏱️ Durasi: 3m 33s
👁️ Views: 1.4B

📝 Transkripsi:
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you...

📊 Ringkasan AI:
📝 Ringkasan Singkat: Lagu pop klasik tahun 1987 dari Rick Astley yang menjadi fenomena internet "Rickroll"

🎯 Poin-poin Penting:
• Lagu romantis dengan komitmen tanpa syarat
• Menjadi meme internet populer sejak 2007  
• Video musik retro dengan dance moves ikonik

🏷️ Kategori: musik, pop, retro, meme internet

🔍 Analisis Video:
Video menampilkan Rick Astley menyanyi dan menari dengan gaya khas tahun 80an...
```

### Contoh Optimasi YouTube
```
User: ytvideo https://youtu.be/example

Respon Bot:
🎬 ANALISIS KONTEN YOUTUBE:

JUDUL YOUTUBE (3 pilihan terbaik):
1. "Rahasia Sukses Content Creator 2025 | Tips Viral"
2. "Cara Mudah Jadi YouTuber Sukses - Tutorial Lengkap"  
3. "Content Creator Pemula Wajib Tahu Ini!"

DESKRIPSI:
Apakah kamu bermimpi menjadi content creator sukses? Video ini akan mengubah permainanmu! Dalam 15 menit, kamu akan mempelajari strategi rahasia yang digunakan YouTuber top untuk membangun audience loyal...

HASHTAG (15 hashtag):
#ContentCreator #YouTube #TipsViral #Tutorial #YouTuber #MediaSosial #Marketing #Viral #Sukses #Tips #Indonesia #Creator #Konten #Digital #Strategi

BONUS:
🎯 Target audience: Calon content creator usia 18-35
⏰ Waktu upload terbaik: Kamis-Minggu, 19:00-21:00 WIB
🎨 Ide thumbnail: Wajah ekspresif + teks besar "RAHASIA SUKSES" + panah pointing
```

## ⚙️ Konfigurasi

### Environment Variables
```bash
# Opsional: Set via environment variables
export GEMINI_API_KEY="api-key-anda"
export DOWNLOAD_DIR="./downloads"
export CLEANUP_HOURS="24"
```

### Opsi Kustomisasi
- Modifikasi prompt AI untuk bahasa yang berbeda
- Sesuaikan default kualitas download
- Ubah interval pembersihan file
- Kustomisasi format response

## 🔒 Privasi & Keamanan

- ✅ Pemrosesan file lokal
- ✅ Pembersihan file otomatis
- ✅ Tidak ada penyimpanan data beyond session
- ✅ Keamanan API key
- ⚠️ Gunakan secara bertanggung jawab dan hormati hak cipta

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan submit Pull Request.

1. Fork project
2. Buat feature branch (`git checkout -b feature/FiturKeren`)
3. Commit perubahan (`git commit -m 'Tambah FiturKeren'`)
4. Push ke branch (`git push origin feature/FiturKeren`)
5. Buka Pull Request

## 📄 Lisensi

Project ini dilisensikan dengan MIT License - lihat file [LICENSE](LICENSE) untuk detail.

## ⚠️ Disclaimer

Tool ini hanya untuk keperluan edukasi dan personal. User bertanggung jawab untuk mematuhi terms of service dari platform yang mereka download kontennya. Hormati hak cipta dan intellectual property.

## 🆘 Dukungan

Jika mengalami masalah atau punya pertanyaan:

1. Cek halaman [Issues](../../issues)
2. Buat issue baru dengan informasi detail
3. Join diskusi komunitas

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=username/bot-whatsapp-ai-media&type=Date)](https://star-history.com/#username/bot-whatsapp-ai-media&Date)

---

<div align="center">

**Dibuat dengan ❤️ dan 🤖 AI di Indonesia**

*Jangan lupa ⭐ star repo ini jika bermanfaat!*

</div>
```

---

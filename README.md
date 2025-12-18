# 🛡️ WiFi Deauther Pro

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/Version-2.0-purple.svg)

Tool deauthentication WiFi dengan fitur **multi-target**, **channel hopping**, **thermal protection**, dan dukungan **WPA2/WPA3 detection**.

> ⚠️ **DISCLAIMER**: Tool ini hanya untuk tujuan edukasi dan pengujian keamanan jaringan **milik sendiri**. Penggunaan terhadap jaringan tanpa izin adalah **ilegal**.

---

## 📑 Daftar Isi

- [Fitur](#-fitur)
- [Requirements](#-requirements)
- [Instalasi](#-instalasi)
- [Cara Penggunaan](#-cara-penggunaan)
- [Penjelasan Menu](#-penjelasan-menu)
- [Konfigurasi](#️-konfigurasi)
- [Thermal Protection](#️-thermal-protection)
- [Troubleshooting](#-troubleshooting)
- [Struktur Proyek](#-struktur-proyek)
- [Legal Disclaimer](#️-legal-disclaimer)

---

## ✨ Fitur

| Fitur | Deskripsi |
|-------|-----------|
| 🎯 **Multi-Target Attack** | Serang banyak target sekaligus (konfigurasi via `MAX_TARGETS`) |
| 📡 **Dual Band Scan** | Scan jaringan 2.4GHz dan 5GHz |
| 🔐 **WPA2/WPA3 Detection** | Deteksi tipe enkripsi jaringan |
| 🌡️ **Thermal Protection** | Auto-shutdown saat suhu chip mencapai batas kritis |
| 👥 **Client Targeting** | Serang client spesifik (lebih efektif dari broadcast) |
| 🔄 **Channel Hopping** | Serang target di channel berbeda-beda dengan 1 adapter |
| � **Beacon Flood** | Spam SSID palsu di semua channel |
| 🎨 **Colored Output** | Output terminal berwarna untuk setiap target |
| 🔌 **Graceful Shutdown** | Restore NetworkManager otomatis saat keluar |

---

## 📋 Requirements

### Sistem Operasi
- **Linux** (Ubuntu/Debian/Kali Linux/Arch)

### Dependencies
```bash
# Install semua dependencies yang diperlukan
sudo apt update
sudo apt install -y aircrack-ng mdk4 xterm python3
```

### Hardware
- WiFi adapter dengan dukungan **monitor mode** dan **packet injection**
- Chipset yang direkomendasikan:
  - Atheros AR9271
  - Ralink RT3070
  - Realtek RTL8812AU
  - MediaTek MT7921 (dengan thermal monitoring)

---

## 🚀 Instalasi

```bash
# 1. Clone repository
git clone https://github.com/ilhambintang17/wifideauther.git

# 2. Masuk ke direktori
cd wifideauther

# 3. Jalankan program (memerlukan root/sudo)
sudo python3 main.py
```

---

## 📖 Cara Penggunaan

### Menjalankan Program

```bash
sudo python3 main.py
```

### Menu Utama

Setelah program dijalankan, Anda akan melihat menu:

```
============================================================
  MULTI-TARGET DEAUTH (Optimized for Same-Channel) | TEMP: 45°C
============================================================

1. Scan & Attack (Broadcast)
2. Stop All Attacks
3. Restart Driver
4. Exit
5. Scan Network & Clients (TARGETED) ✨
6. MDK4 Beacon Flood (Spam WiFi)
7. MDK4 Deauth + Channel Hop 🔊

Choice [1-7]:
```

---

## 📚 Penjelasan Menu

### 1️⃣ Scan & Attack (Broadcast)

**Fungsi:** Scan jaringan dan serang dengan deauth broadcast

**Cara Pakai:**
1. Pilih menu `1`
2. Jendela xterm akan terbuka untuk scanning
3. Tekan `Ctrl+C` di jendela xterm setelah target terlihat
4. Masukkan nomor target (contoh: `1,2,3` untuk multi-target)
5. Attack akan berjalan di jendela xterm baru

**Catatan:**
- ⚠️ Broadcast deauth mungkin **diabaikan** oleh beberapa perangkat
- ✅ Paling efektif jika semua target di **channel yang sama**
- ❌ **Tidak bisa** mix 2.4GHz dan 5GHz sekaligus
- 💡 Jumlah max target bisa diubah di `config.py` → `MAX_TARGETS`

---

### 2️⃣ Stop All Attacks

**Fungsi:** Menghentikan semua serangan yang sedang berjalan

**Cara Pakai:**
1. Pilih menu `2`
2. Semua jendela xterm attack akan ditutup
3. Proses `aireplay-ng` dan `mdk4` akan dihentikan

---

### 3️⃣ Restart Driver

**Fungsi:** Restart driver WiFi adapter jika terjadi masalah

**Cara Pakai:**
1. Pilih menu `3`
2. Driver akan di-unload dan load ulang
3. Berguna jika adapter stuck atau tidak responsif

---

### 4️⃣ Exit

**Fungsi:** Keluar dari program dengan aman

**Yang Terjadi:**
- Semua attack dihentikan
- Monitor mode dinonaktifkan
- NetworkManager di-restart otomatis
- Koneksi WiFi normal kembali

---

### 5️⃣ Scan Network & Clients (TARGETED) ✨

**Fungsi:** Scan jaringan DAN client yang terhubung, lalu serang client spesifik

**Cara Pakai:**
1. Pilih menu `5`
2. Scanning akan menampilkan jumlah client per AP
3. Pilih nomor AP yang ingin diserang
4. Program akan scan ulang client di AP tersebut
5. Pilih opsi:
   - `a` = Attack semua client
   - `1,2,3` = Attack client spesifik
   - `b` = Broadcast attack
   - Atau masukkan MAC address manual

**Keunggulan:**
- ✅ **Lebih efektif** dari broadcast karena target spesifik
- ✅ Mengirim 128 paket per request (64 ke AP + 64 ke client)
- ✅ Client tidak bisa mengabaikan deauth targeted

---

### 6️⃣ MDK4 Beacon Flood (Spam WiFi)

**Fungsi:** Membuat SSID palsu yang muncul di daftar WiFi sekitar

**Cara Pakai:**
1. Pilih menu `6`
2. Masukkan nama SSID yang ingin di-spam (contoh: `Free WiFi`)
3. Masukkan jumlah copy (contoh: `50` untuk buat 50 SSID)
4. Pilih mode channel:
   - `1` = Single channel (current)
   - `2` = **All channels** (broadcast di 2.4GHz + 5GHz)
5. SSID palsu akan muncul di semua perangkat sekitar!

**Contoh Output:**
```
Daftar WiFi di HP korban:
- Free WiFi 1
- Free WiFi 2
- Free WiFi 3
... (sampai 50)
```

---

### 7️⃣ MDK4 Deauth + Channel Hop 🔊

**Fungsi:** Deauth attack dengan **channel hopping** - bisa serang target di **channel berbeda-beda**!

**Cara Pakai:**
1. Pilih menu `7`
2. Scan networks akan berjalan
3. Pilih target (bisa multi: `1,2,3,4,5`)
4. Attack akan berjalan dengan channel hopping otomatis

**Cara Kerja:**
```
Loop:
  → Switch ke Channel 1
  → Kirim deauth ke target di Ch 1
  → Switch ke Channel 6
  → Kirim deauth ke target di Ch 6
  → Switch ke Channel 11
  → Kirim deauth ke target di Ch 11
  → Repeat...
```

**Keunggulan:**
- ✅ Bisa serang target di **channel berbeda** dengan **1 adapter**
- ✅ Output berwarna berbeda per target (mudah dibaca)
- ✅ Tidak perlu punya 2 adapter untuk multi-channel attack

**Contoh Output Terminal:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║               MDK4 DEAUTH - CHANNEL HOPPING MODE                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
Target List (with colors):
  [1] TOTOLINK (AA:BB:CC:11:22:33) Ch:4       ← Hijau
  [2] TP-Link_9F1A (DD:EE:FF:44:55:66) Ch:6   ← Cyan
  [3] Samsung Galaxy (11:22:33:AA:BB:CC) Ch:11 ← Kuning
──────────────────────────────────────────────────────────────────────────────
[Ch:  4] TOTOLINK          : deauth sent      ← Hijau
[Ch:  6] TP-Link_9F1A      : deauth sent      ← Cyan
[Ch: 11] Samsung Galaxy    : deauth sent      ← Kuning
```

---

## ⚙️ Konfigurasi

Edit file `deauther/config.py` untuk menyesuaikan pengaturan:

```python
# ============================================================
# CONFIGURATION - Deauther Tool Settings
# ============================================================

# --- INTERFACE ---
INTERFACE_ASLI = "wlp1s0"     # Nama interface WiFi Anda

# --- ATTACK PARAMETERS ---
MAX_TARGETS = 5                # Maksimal target simultan (bisa diubah sesuai kebutuhan)
DEAUTH_PACKETS = 0             # 0 = continuous attack
DEAUTH_DELAY = 0.05            # Delay antar paket (detik)
CHANNEL_LOCK_TIME = 1.0        # Waktu stabilisasi channel
BURST_STAGGER = 0.15           # Delay spawn antar proses

# --- THERMAL PROTECTION ---
TEMP_THRESHOLD = 60.0          # Suhu shutdown otomatis (°C)
TEMP_WARNING = 55.0            # Suhu peringatan (°C)
TEMP_CHECK_INTERVAL = 1.0      # Interval cek suhu (detik)
```

### Penjelasan Parameter

| Parameter | Default | Deskripsi |
|-----------|---------|-----------|
| `INTERFACE_ASLI` | `wlp1s0` | Nama interface WiFi (cek: `ip link show`) |
| `MAX_TARGETS` | `5` | Batas maksimal target simultan (**bisa diubah**) |
| `DEAUTH_PACKETS` | `0` | Jumlah paket (0 = unlimited/continuous) |
| `TEMP_THRESHOLD` | `60.0` | Suhu auto-shutdown (°C) |
| `TEMP_WARNING` | `55.0` | Suhu peringatan kuning (°C) |

### Cara Mengetahui Nama Interface

```bash
# Metode 1
ip link show

# Metode 2
iwconfig

# Metode 3
ls /sys/class/net | grep -E "wl|wlan"
```

---

## 🌡️ Thermal Protection

Tool ini memiliki proteksi thermal untuk chipset sensitif (MediaTek, Intel):

| Suhu | Status | Aksi |
|------|--------|------|
| < 55°C | 🟢 Normal | Operasi normal |
| 55-60°C | � Warning | Peringatan di terminal |
| > 60°C | 🔴 Kritis | **Auto-shutdown** semua attack |

### Chipset yang Diberi Proteksi
- MediaTek MT7921
- Intel AX200/AX210

---

## 🔧 Troubleshooting

### Interface tidak terdeteksi
```bash
sudo systemctl restart NetworkManager
sudo rfkill unblock wifi
```

### Monitor mode gagal
```bash
sudo airmon-ng check kill
sudo airmon-ng start wlan0
```

### Permission denied
```bash
sudo python3 main.py  # Pastikan pakai sudo
```

### Xterm tidak muncul
```bash
sudo apt install xterm
export DISPLAY=:0  # Jika di SSH
```

### MDK4 tidak ditemukan
```bash
sudo apt install mdk4
```

---

## 📁 Struktur Proyek

```
wifideauther/
├── main.py              # Entry point program
├── README.md            # Dokumentasi (file ini)
└── deauther/
    ├── __init__.py      # Package exports
    ├── config.py        # Konfigurasi user
    ├── colors.py        # Warna terminal
    ├── utils.py         # Utilitas umum
    ├── interface.py     # Manajemen WiFi interface
    ├── scanner.py       # Network & client scanning
    ├── attack.py        # Fungsi deauth & beacon flood
    └── thermal.py       # Monitoring suhu chip
```

---

## ⚖️ Legal Disclaimer

Tool ini **HANYA** untuk:
- ✅ Pengujian jaringan **milik sendiri**
- ✅ Riset keamanan dengan **izin tertulis**
- ✅ Tujuan edukasi

**DILARANG** untuk:
- ❌ Menyerang jaringan tanpa izin
- ❌ Mengganggu layanan publik
- ❌ Aktivitas ilegal lainnya

> **Pengembang tidak bertanggung jawab atas penyalahgunaan tool ini.**

---

## 📄 License

MIT License - Lihat [LICENSE](LICENSE) untuk detail.

---

<p align="center">
  <b>Made with ☕ for educational purposes</b><br>
  <sub>WiFi Deauther Pro v2.0</sub>
</p>

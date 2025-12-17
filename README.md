# 🛡️ WiFi Deauther

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Tool deauthentication WiFi multi-target dengan fitur thermal protection dan dukungan WPA2/WPA3 detection.

> ⚠️ **DISCLAIMER**: Tool ini hanya untuk tujuan edukasi dan pengujian keamanan jaringan **milik sendiri**. Penggunaan terhadap jaringan tanpa izin adalah **ilegal**.

## ✨ Fitur

- 🎯 **Multi-Target Attack** - Serang hingga 5 target sekaligus
- 📡 **Dual Band Support** - Scan 2.4GHz dan 5GHz
- 🔐 **WPA2/WPA3 Detection** - Deteksi enkripsi jaringan
- 🌡️ **Thermal Protection** - Auto-shutdown saat suhu kritis
- 👥 **Client Targeting** - Serang client spesifik (lebih efektif)
- 🔄 **Graceful Shutdown** - Restore NetworkManager otomatis

## 📋 Requirements

### Sistem Operasi
- Linux (Ubuntu/Debian/Kali Linux)

### Dependencies
```bash
# Install dependencies
sudo apt update
sudo apt install -y aircrack-ng xterm python3
```

### Hardware
- WiFi adapter dengan dukungan **monitor mode**
- Chipset yang direkomendasikan: Atheros, Ralink, Realtek RTL8812AU

## 🚀 Instalasi

```bash
# Clone repository
git clone https://github.com/ilhambintang17/wifideauther.git
cd wifideauther

# Jalankan (memerlukan root)
sudo python3 main.py
```

## ⚙️ Konfigurasi

Edit file `deauther/config.py` untuk menyesuaikan pengaturan:

```python
# ============================================================
# CONFIGURATION - Deauther Tool Settings
# ============================================================

# --- INTERFACE ---
INTERFACE_ASLI = "wlp1s0"     # Nama interface WiFi Anda
                               # Cek dengan: ip link show

# --- ATTACK PARAMETERS ---
MAX_TARGETS = 5                # Maksimal target simultan (1-5)
DEAUTH_PACKETS = 100           # Jumlah paket per burst (50-200)
DEAUTH_DELAY = 0.05            # Delay antar paket (detik)
CHANNEL_LOCK_TIME = 1.0        # Waktu stabilisasi channel
BURST_STAGGER = 0.15           # Delay spawn antar proses

# --- THERMAL PROTECTION ---
TEMP_THRESHOLD = 60.0          # Suhu shutdown otomatis (°C)
TEMP_WARNING = 55.0            # Suhu peringatan (°C)
TEMP_CHECK_INTERVAL = 1.0      # Interval cek suhu (detik)
```

### 📝 Penjelasan Konfigurasi

| Parameter | Default | Deskripsi |
|-----------|---------|-----------|
| `INTERFACE_ASLI` | `wlp1s0` | Nama interface WiFi. Jalankan `ip link show` untuk melihat nama interface Anda |
| `MAX_TARGETS` | `5` | Batas maksimal target yang bisa diserang bersamaan |
| `DEAUTH_PACKETS` | `100` | Jumlah paket deauth per burst. Semakin tinggi = lebih agresif |
| `DEAUTH_DELAY` | `0.05` | Delay antar paket untuk stabilitas |
| `TEMP_THRESHOLD` | `60.0` | Suhu maksimal sebelum auto-shutdown untuk melindungi hardware |
| `TEMP_WARNING` | `55.0` | Suhu peringatan (warna kuning di display) |

### 🔍 Cara Mengetahui Nama Interface

```bash
# Metode 1: ip link
ip link show

# Metode 2: iwconfig
iwconfig

# Metode 3: list wireless
ls /sys/class/net | grep -E "wl|wlan"
```

Output contoh:
```
wlp1s0    IEEE 802.11  ESSID:off/any
          Mode:Managed  Access Point: Not-Associated
```

Nama interface Anda adalah `wlp1s0` (atau bisa `wlan0`, `wlan1`, dll).

## 📖 Cara Penggunaan

### Menu Utama

```
============================================================
  MULTI-TARGET DEAUTH (Optimized for Same-Channel) | TEMP: 45°C
============================================================

1. Scan & Attack (Broadcast)
2. Stop All Attacks
3. Restart Driver
4. Exit
5. Scan Network & Clients (TARGETED) ✨
```

### Mode 1: Broadcast Attack
1. Pilih opsi `1`
2. Jendela xterm akan terbuka untuk scanning
3. Tekan `Ctrl+C` di jendela xterm setelah target terlihat
4. Pilih target dengan nomor (contoh: `1,2,3`)
5. Attack berjalan otomatis

### Mode 5: Targeted Attack (Lebih Efektif) ✨
1. Pilih opsi `5`
2. Scan akan mendeteksi network DAN client
3. Pilih AP target
4. Pilih client spesifik atau semua client
5. Attack lebih efektif karena target spesifik

### Tips Efektivitas

| Kondisi | Efektivitas |
|---------|-------------|
| Semua target di **channel sama** | 🟢 **100%** |
| Target di **channel berbeda** (2.4GHz) | 🟡 **~30%** |
| Mix **2.4GHz + 5GHz** | 🔴 **Tidak didukung** |

## 🌡️ Thermal Protection

Tool ini memiliki proteksi thermal untuk chipset sensitif:

- **Hijau (< 55°C)**: Operasi normal
- **Kuning (55-60°C)**: Peringatan, pertimbangkan jeda
- **Merah (> 60°C)**: Auto-shutdown attack

### Chipset Sensitif
- MediaTek MT7921
- Intel AX200/AX210 (beberapa varian)

## 🔧 Troubleshooting

### Interface tidak terdeteksi
```bash
# Restart NetworkManager
sudo systemctl restart NetworkManager

# Unblock WiFi
sudo rfkill unblock wifi
```

### Monitor mode gagal
```bash
# Kill proses yang mengganggu
sudo airmon-ng check kill

# Restart driver
sudo modprobe -r <driver_name>
sudo modprobe <driver_name>
```

### Permission denied
```bash
# Pastikan menjalankan dengan sudo
sudo python3 main.py
```

## 📁 Struktur Proyek

```
wifi-deauther-pro/
├── main.py              # Entry point
├── README.md            # Dokumentasi
└── deauther/
    ├── __init__.py      # Package exports
    ├── config.py        # Konfigurasi
    ├── colors.py        # Warna terminal
    ├── utils.py         # Utilitas umum
    ├── interface.py     # Manajemen interface
    ├── scanner.py       # Network scanning
    ├── attack.py        # Fungsi deauth
    └── thermal.py       # Monitoring suhu
```

## ⚖️ Legal Disclaimer

Tool ini **hanya** untuk:
- ✅ Pengujian jaringan **milik sendiri**
- ✅ Riset keamanan dengan **izin tertulis**
- ✅ Tujuan edukasi

**DILARANG** untuk:
- ❌ Menyerang jaringan tanpa izin
- ❌ Mengganggu layanan publik
- ❌ Aktivitas ilegal lainnya

Pengembang **tidak bertanggung jawab** atas penyalahgunaan tool ini.

## 📄 License

MIT License - Lihat [LICENSE](LICENSE) untuk detail.

---

<p align="center">Made with ☕ for educational purposes</p>

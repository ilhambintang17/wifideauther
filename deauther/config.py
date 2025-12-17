# ============================================================
# CONFIGURATION - Deauther Tool Settings
# ============================================================

# --- INTERFACE ---
INTERFACE_ASLI = "wlp1s0"

# --- ATTACK PARAMETERS ---
MAX_TARGETS = 5
DEAUTH_PACKETS = 100  # Naikan dari 50 untuk same-channel
DEAUTH_DELAY = 0.05   # Slight delay untuk stabilitas
CHANNEL_LOCK_TIME = 1.0  # Waktu tunggu setelah lock channel
BURST_STAGGER = 0.15  # Delay spawn antar proses

# --- THERMAL PROTECTION ---
TEMP_THRESHOLD = 60.0  # Safety cut-off temperature (°C)
TEMP_WARNING = 55.0    # Warning temperature (°C)
TEMP_CHECK_INTERVAL = 1.0  # Check temperature every 1 second

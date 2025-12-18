# ============================================================
# CONFIGURATION - Deauther Tool Settings
# ============================================================

# --- INTERFACE ---
INTERFACE_ASLI = "wlp1s0"

# --- ATTACK PARAMETERS ---
MAX_TARGETS = 20
# Use 0 for continuous infinite packets (MOST AGGRESSIVE)
# Higher number = more packets per burst
DEAUTH_PACKETS = 0  # 0 = continuous attack (tidak berhenti)
DEAUTH_DELAY = 0.1    # No delay between bursts for maximum effectiveness
CHANNEL_LOCK_TIME = 1.0  # Waktu tunggu setelah lock channel
BURST_STAGGER = 0.1  # Faster spawn for quicker attack start

# --- THERMAL PROTECTION ---
TEMP_THRESHOLD = 60.0  # Safety cut-off temperature (°C)
TEMP_WARNING = 55.0    # Warning temperature (°C)
TEMP_CHECK_INTERVAL = 1.0  # Check temperature every 1 second

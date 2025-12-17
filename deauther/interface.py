# ============================================================
# INTERFACE - Network interface management
# ============================================================

import os
import re
import subprocess
import time

from .config import INTERFACE_ASLI, CHANNEL_LOCK_TIME
from .colors import Color
from .utils import run_command

# Global state
current_locked_channel = None


def get_mon_interface():
    """Get the monitor mode interface name"""
    try:
        result = subprocess.check_output(
            "iwconfig 2>/dev/null | grep 'Mode:Monitor' | awk '{print $1}'", 
            shell=True
        ).decode().strip()
        return result if result else None
    except:
        return None


def is_monitor_mode(interface):
    """Check if a specific interface is in monitor mode"""
    try:
        result = subprocess.check_output(
            f"iwconfig {interface} 2>/dev/null",
            shell=True
        ).decode()
        return "Mode:Monitor" in result
    except:
        return False


def enable_monitor_mode():
    """Enable monitor mode on the wireless interface
    
    Handles cases where interface name doesn't change after enabling monitor mode
    (e.g., wlan1 stays as wlan1 instead of becoming wlan1mon)
    """
    print(f"{Color.BLUE}[*] Enable Monitor Mode...{Color.ENDC}")
    
    # Stop services that can interfere with monitor mode
    subprocess.call("systemctl stop NetworkManager 2>/dev/null", shell=True, 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call("systemctl stop avahi-daemon 2>/dev/null", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call("systemctl stop wpa_supplicant 2>/dev/null", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Kill interfering processes - run twice to catch respawning processes
    run_command("airmon-ng check kill")
    time.sleep(0.5)
    run_command("airmon-ng check kill")
    
    # Kill any remaining avahi-daemon processes directly
    subprocess.call("pkill -9 avahi-daemon 2>/dev/null", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call("pkill -9 wpa_supplicant 2>/dev/null", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(0.5)
    
    # Now enable monitor mode
    run_command(f"airmon-ng start {INTERFACE_ASLI}")
    time.sleep(2)
    
    # First, try to get interface that has 'mon' suffix (standard behavior)
    mon = get_mon_interface()
    if mon:
        print(f"{Color.GREEN}[+] Monitor interface: {mon}{Color.ENDC}")
        return mon
    
    # If no 'mon' interface found, check if original interface is now in monitor mode
    # This handles adapters that don't rename interface (e.g., some MediaTek drivers)
    if is_monitor_mode(INTERFACE_ASLI):
        print(f"{Color.GREEN}[+] Monitor mode enabled on: {INTERFACE_ASLI} (name unchanged){Color.ENDC}")
        return INTERFACE_ASLI
    
    # Also check for common variations like wlan0mon, wlan1mon, etc.
    common_mon_names = [
        f"{INTERFACE_ASLI}mon",
        INTERFACE_ASLI.replace("wlp", "wlan") + "mon" if "wlp" in INTERFACE_ASLI else None,
        "wlan0mon", "wlan1mon", "wlan2mon"
    ]
    for mon_name in common_mon_names:
        if mon_name and is_monitor_mode(mon_name):
            print(f"{Color.GREEN}[+] Found monitor interface: {mon_name}{Color.ENDC}")
            return mon_name
    
    # Final fallback - assume original interface can be used
    print(f"{Color.WARNING}[!] Could not verify monitor mode, using: {INTERFACE_ASLI}{Color.ENDC}")
    return INTERFACE_ASLI


def verify_channel_lock(mon_iface, expected_channel):
    """Verify that the channel is actually locked"""
    try:
        result = subprocess.check_output(
            f"iwconfig {mon_iface} 2>/dev/null",
            shell=True
        ).decode()
        
        # Pattern 1: "(Channel X)" - format umum
        if f"(Channel {expected_channel})" in result:
            return True
        
        # Pattern 2: "Channel X" atau "Channel:X" 
        if f"Channel {expected_channel}" in result or f"Channel:{expected_channel}" in result:
            return True
        
        # Pattern 3: Regex untuk mencari channel number di berbagai format
        # Matches: (Channel 6), Channel:6, Channel 6, Channel= 6
        pattern = r'[Cc]hannel[:\s=]*(\d+)'
        match = re.search(pattern, result)
        if match and match.group(1) == str(expected_channel):
            return True
        
        # Fallback: cek dari frequency (expanded map)
        freq_map = {
            "1": "2.412", "2": "2.417", "3": "2.422", "4": "2.427",
            "5": "2.432", "6": "2.437", "7": "2.442", "8": "2.447",
            "9": "2.452", "10": "2.457", "11": "2.462", "12": "2.467",
            "13": "2.472",
            # 5GHz
            "36": "5.180", "40": "5.200", "44": "5.220", "48": "5.240",
            "149": "5.745", "153": "5.765", "157": "5.785", "161": "5.805"
        }
        if str(expected_channel) in freq_map:
            if freq_map[str(expected_channel)] in result:
                return True
        
        # Last resort: jika tidak error dan command berhasil, assume OK
        # Karena beberapa driver tidak report channel dengan jelas
        return False
    except Exception as e:
        # Jika error, return False
        return False


def lock_channel_robust(mon_iface, channel):
    """Lock channel with verification and retry - more lenient"""
    global current_locked_channel
    
    max_retries = 3
    for attempt in range(max_retries):
        # Set channel
        result = subprocess.call(
            f"iwconfig {mon_iface} channel {channel}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(CHANNEL_LOCK_TIME)
        
        # Jika command sukses (return 0), lanjutkan
        if result == 0:
            # Try to verify, tapi jangan gagalkan jika verifikasi gagal
            if verify_channel_lock(mon_iface, channel):
                current_locked_channel = channel
                print(f"{Color.GREEN}[✓] Channel {channel} locked (verified){Color.ENDC}")
                return True
            else:
                # Verifikasi gagal tapi iwconfig sukses - lanjutkan saja
                # (seperti behavior di deauth.py yang tidak verifikasi)
                if attempt == max_retries - 1:
                    current_locked_channel = channel
                    print(f"{Color.WARNING}[~] Channel {channel} set (unverified, but proceeding){Color.ENDC}")
                    return True
        
        print(f"{Color.WARNING}[!] Retry lock channel {channel} (attempt {attempt+1}/{max_retries})...{Color.ENDC}")
    
    # Fallback terakhir: coba set sekali lagi dan lanjutkan
    subprocess.call(
        f"iwconfig {mon_iface} channel {channel}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.5)
    current_locked_channel = channel
    print(f"{Color.WARNING}[~] Channel {channel} forced (proceeding anyway){Color.ENDC}")
    return True


def restart_driver():
    """Reset the WiFi driver (mt7921e)"""
    # Import here to avoid circular imports
    from .attack import kill_all_attacks
    
    print(f"\n{Color.WARNING}[!] Resetting Driver...{Color.ENDC}")
    kill_all_attacks()
    
    mon = get_mon_interface()
    if mon:
        print(f"{Color.BLUE}[*] Stop Monitor Mode...{Color.ENDC}")
        run_command(f"airmon-ng stop {mon}")
        time.sleep(1)
    
    print(f"{Color.BLUE}[*] Reset interface...{Color.ENDC}")
    run_command(f"ifconfig {INTERFACE_ASLI} down")
    run_command(f"iw {INTERFACE_ASLI} set type managed")
    run_command(f"ifconfig {INTERFACE_ASLI} up")
    time.sleep(1)
    
    print(f"{Color.BLUE}[*] Reload driver mt7921e...{Color.ENDC}")
    run_command("modprobe -r mt7921e")
    time.sleep(1)
    run_command("modprobe mt7921e")
    time.sleep(2)
    
    print(f"{Color.BLUE}[*] Start NetworkManager...{Color.ENDC}")
    run_command("sudo systemctl start NetworkManager")
    
    print(f"{Color.GREEN}[+] Done.{Color.ENDC}")
    input("Press Enter...")


def get_current_locked_channel():
    """Get the currently locked channel"""
    return current_locked_channel

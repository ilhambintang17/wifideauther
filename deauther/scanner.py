# ============================================================
# SCANNER - Network and client scanning functions
# ============================================================

import os
import csv
import glob
import time

from .colors import Color
from .utils import run_command


def get_band_from_channel(channel):
    """Detect band from channel number"""
    try:
        ch = int(channel)
        if ch >= 1 and ch <= 14:
            return "2.4G"
        elif ch >= 36:
            return "5G"
        else:
            return "?"
    except:
        return "?"


def parse_clients_from_csv(csv_file):
    """Parse connected clients from airodump-ng CSV file"""
    clients = []
    in_client_section = False
    
    try:
        with open(csv_file, 'r', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 1:
                    continue
                
                # Deteksi bagian Station (client)
                first_col = row[0].strip()
                if first_col == "Station MAC":
                    in_client_section = True
                    continue
                
                if in_client_section and len(row) >= 6:
                    station_mac = row[0].strip()
                    # Validasi MAC address format
                    if len(station_mac) == 17 and station_mac.count(':') == 5:
                        first_seen = row[1].strip() if len(row) > 1 else ""
                        last_seen = row[2].strip() if len(row) > 2 else ""
                        power = row[3].strip() if len(row) > 3 else "-1"
                        packets = row[4].strip() if len(row) > 4 else "0"
                        bssid = row[5].strip() if len(row) > 5 else "(not associated)"
                        
                        # Filter client yang tidak terkoneksi atau sinyal lemah
                        try:
                            pwr_int = int(power)
                            pkt_int = int(packets)
                            if pwr_int == -1 or pwr_int < -85:
                                continue
                            if bssid == "(not associated)":
                                continue
                        except:
                            continue
                        
                        clients.append({
                            "station_mac": station_mac,
                            "bssid": bssid,
                            "power": power,
                            "packets": packets
                        })
    except Exception as e:
        print(f"{Color.FAIL}[!] Error parsing clients: {e}{Color.ENDC}")
    
    return clients


def scan_networks_and_clients(mon_iface):
    """Scan networks AND clients simultaneously (2.4GHz + 5GHz)"""
    print(f"{Color.BLUE}[*] Opening scan window (Networks + Clients)...{Color.ENDC}")
    print(f"{Color.CYAN}[*] Scanning ALL bands: 2.4GHz + 5GHz{Color.ENDC}")
    print(f"{Color.WARNING}[!] Press Ctrl+C in XTERM when done!{Color.ENDC}")
    print(f"{Color.CYAN}[TIP] Scan lebih lama = lebih banyak client terdeteksi{Color.ENDC}")
    time.sleep(2)
    
    run_command("rm -f /tmp/kismet_scan*")
    
    # --band abg = scan semua band (a=5GHz, b/g=2.4GHz)
    cmd = f"xterm -geometry 120x35 -title 'SCANNING ALL BANDS (2.4GHz + 5GHz) - CTRL+C TO STOP' -e 'airodump-ng --band abg --output-format csv -w /tmp/kismet_scan {mon_iface}'"
    os.system(cmd)
    
    networks = []
    clients = []
    
    try:
        list_of_files = glob.glob('/tmp/kismet_scan*.csv')
        if not list_of_files:
            return [], []
        latest_file = max(list_of_files, key=os.path.getctime)
        
        # Parse networks
        in_ap_section = True
        with open(latest_file, 'r', errors='ignore') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) < 1:
                    continue
                
                first_col = row[0].strip()
                
                # Deteksi pergantian section
                if first_col == "Station MAC":
                    in_ap_section = False
                    continue
                
                if in_ap_section and len(row) >= 14:
                    bssid = row[0].strip()
                    channel = row[3].strip()
                    privacy = row[5].strip() if len(row) > 5 else ""  # WPA2, WPA3, OPN, WEP
                    cipher = row[6].strip() if len(row) > 6 else ""   # CCMP, TKIP
                    auth = row[7].strip() if len(row) > 7 else ""     # PSK, MGT, SAE
                    power = row[8].strip()
                    essid = row[13].strip()
                    
                    if bssid == "BSSID":
                        continue
                    if not essid:
                        essid = "<Hidden>"
                    
                    try:
                        pwr_int = int(power)
                        if pwr_int == -1 or pwr_int < -78:
                            continue
                    except:
                        continue
                    
                    # Format encryption string
                    enc = privacy if privacy else "OPN"
                    if cipher:
                        enc = f"{privacy}/{cipher}"
                    if "SAE" in auth:
                        enc = "WPA3" if "WPA3" in privacy else f"WPA2/WPA3"
                    
                    networks.append({
                        "bssid": bssid,
                        "channel": channel,
                        "essid": essid,
                        "power": power,
                        "band": get_band_from_channel(channel),
                        "encryption": enc
                    })
        
        # Parse clients
        clients = parse_clients_from_csv(latest_file)
        
    except Exception as e:
        print(f"{Color.FAIL}[!] Error: {e}{Color.ENDC}")
    
    networks = sorted(networks, key=lambda x: int(x['power']), reverse=True)
    return networks, clients


def scan_networks_live(mon_iface):
    """Scan networks only (2.4GHz + 5GHz)"""
    print(f"{Color.BLUE}[*] Opening scan window...{Color.ENDC}")
    print(f"{Color.CYAN}[*] Scanning ALL bands: 2.4GHz + 5GHz{Color.ENDC}")
    print(f"{Color.WARNING}[!] Press Ctrl+C in XTERM when done!{Color.ENDC}")
    time.sleep(2)
    
    run_command("rm -f /tmp/kismet_scan*")
    
    # --band abg = scan semua band (a=5GHz, b/g=2.4GHz)
    cmd = f"xterm -geometry 100x30 -title 'SCANNING ALL BANDS (2.4GHz + 5GHz) - CTRL+C TO STOP' -e 'airodump-ng --band abg --output-format csv -w /tmp/kismet_scan {mon_iface}'"
    os.system(cmd)
    
    networks = []
    try:
        list_of_files = glob.glob('/tmp/kismet_scan*.csv')
        if not list_of_files: 
            return []
        latest_file = max(list_of_files, key=os.path.getctime)
        
        with open(latest_file, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) < 14: 
                    continue
                bssid = row[0].strip()
                channel = row[3].strip()
                privacy = row[5].strip() if len(row) > 5 else ""  # WPA2, WPA3, OPN, WEP
                cipher = row[6].strip() if len(row) > 6 else ""   # CCMP, TKIP
                auth = row[7].strip() if len(row) > 7 else ""     # PSK, MGT, SAE
                power = row[8].strip()
                essid = row[13].strip()
                
                if bssid == "BSSID" or bssid == "Station MAC": 
                    continue
                if not essid: 
                    essid = "<Hidden>"
                
                try:
                    pwr_int = int(power)
                    if pwr_int == -1 or pwr_int < -78: 
                        continue
                except:
                    continue
                
                # Format encryption string
                enc = privacy if privacy else "OPN"
                if cipher:
                    enc = f"{privacy}/{cipher}"
                if "SAE" in auth:
                    enc = "WPA3" if "WPA3" in privacy else f"WPA2/WPA3"

                networks.append({
                    "bssid": bssid, 
                    "channel": channel, 
                    "essid": essid, 
                    "power": power,
                    "band": get_band_from_channel(channel),
                    "encryption": enc
                })
    except Exception as e:
        print(f"{Color.FAIL}[!] Error: {e}{Color.ENDC}")
        
    return sorted(networks, key=lambda x: int(x['power']), reverse=True)


def scan_networks_timed(mon_iface, duration=10):
    """Scan networks with automatic timeout (no Ctrl+C needed)
    
    Args:
        mon_iface: Monitor mode interface name
        duration: Scan duration in seconds (default 10)
    
    Returns:
        List of networks sorted by signal strength
    """
    import subprocess
    
    print(f"{Color.BLUE}[*] Auto-scanning for {duration} seconds...{Color.ENDC}")
    print(f"{Color.CYAN}[*] Scanning ALL bands: 2.4GHz + 5GHz{Color.ENDC}")
    
    run_command("rm -f /tmp/kismet_scan*")
    
    # Run airodump-ng in background with timeout
    scan_cmd = f"timeout {duration} airodump-ng --band abg --output-format csv -w /tmp/kismet_scan {mon_iface}"
    
    # Open xterm with the scan command - will auto-close after timeout
    xterm_cmd = f"xterm -geometry 120x35 -title 'SCANNING ({duration}s remaining) - AUTO CLOSE' -e '{scan_cmd}'"
    os.system(xterm_cmd)
    
    print(f"{Color.GREEN}[+] Scan complete!{Color.ENDC}")
    
    networks = []
    try:
        list_of_files = glob.glob('/tmp/kismet_scan*.csv')
        if not list_of_files: 
            return []
        latest_file = max(list_of_files, key=os.path.getctime)
        
        with open(latest_file, 'r', errors='ignore') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) < 14: 
                    continue
                bssid = row[0].strip()
                channel = row[3].strip()
                privacy = row[5].strip() if len(row) > 5 else ""
                cipher = row[6].strip() if len(row) > 6 else ""
                auth = row[7].strip() if len(row) > 7 else ""
                power = row[8].strip()
                essid = row[13].strip()
                
                if bssid == "BSSID" or bssid == "Station MAC": 
                    continue
                if not essid: 
                    essid = "<Hidden>"
                
                try:
                    pwr_int = int(power)
                    if pwr_int == -1 or pwr_int < -78: 
                        continue
                except:
                    continue
                
                # Format encryption string
                enc = privacy if privacy else "OPN"
                if cipher:
                    enc = f"{privacy}/{cipher}"
                if "SAE" in auth:
                    enc = "WPA3" if "WPA3" in privacy else f"WPA2/WPA3"

                networks.append({
                    "bssid": bssid, 
                    "channel": channel, 
                    "essid": essid, 
                    "power": power,
                    "band": get_band_from_channel(channel),
                    "encryption": enc
                })
    except Exception as e:
        print(f"{Color.FAIL}[!] Error: {e}{Color.ENDC}")
        
    return sorted(networks, key=lambda x: int(x['power']), reverse=True)

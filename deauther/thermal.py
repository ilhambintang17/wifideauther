# ============================================================
# THERMAL - Temperature monitoring and protection
# ============================================================

import os
import sys
import subprocess
import time
import threading
import glob

from .config import TEMP_THRESHOLD, TEMP_WARNING, TEMP_CHECK_INTERVAL
from .colors import Color

# Global state
thermal_monitor_running = False
current_temp = 0.0
temp_sensor_path = None


def find_mt7921_sensor():
    """
    Auto-detect MT7921 WiFi chip temperature sensor path.
    Scans /sys/class/hwmon/hwmon*/name for 'mt7921' or 'mediatek'.
    Returns the full path to temp1_input or None if not found.
    """
    hwmon_base = "/sys/class/hwmon"
    
    try:
        # Iterate through all hwmon devices
        for hwmon_dir in glob.glob(f"{hwmon_base}/hwmon*"):
            name_file = os.path.join(hwmon_dir, "name")
            
            if os.path.exists(name_file):
                try:
                    with open(name_file, 'r') as f:
                        sensor_name = f.read().strip().lower()
                    
                    # Check if this is MT7921 or MediaTek WiFi sensor
                    if 'mt7921' in sensor_name or 'mt7922' in sensor_name or 'mediatek' in sensor_name:
                        temp_file = os.path.join(hwmon_dir, "temp1_input")
                        if os.path.exists(temp_file):
                            return temp_file
                except:
                    continue
    except Exception as e:
        print(f"{Color.WARNING}[!] Error scanning sensors: {e}{Color.ENDC}")
    
    return None


def read_temperature():
    """
    Read current temperature from the sensor.
    Returns temperature in Celsius or None if error.
    The sensor reports in millidegrees, so divide by 1000.
    """
    global temp_sensor_path
    
    # Auto-detect sensor path if not set
    if temp_sensor_path is None:
        temp_sensor_path = find_mt7921_sensor()
        if temp_sensor_path:
            print(f"{Color.GREEN}[+] Thermal sensor found: {temp_sensor_path}{Color.ENDC}")
        else:
            return None
    
    try:
        with open(temp_sensor_path, 'r') as f:
            # Temperature is in millidegrees Celsius
            temp_millidegrees = int(f.read().strip())
            return temp_millidegrees / 1000.0
    except FileNotFoundError:
        # Sensor path might have changed after suspend/reboot
        temp_sensor_path = None
        return None
    except Exception:
        return None


def get_temp_status(temp):
    """Get status string and color based on temperature"""
    if temp is None:
        return "N/A", Color.WARNING
    elif temp >= TEMP_THRESHOLD:
        return "OVERHEAT!", Color.FAIL
    elif temp >= TEMP_WARNING:
        return "WARNING", Color.WARNING
    else:
        return "Safe", Color.GREEN


def emergency_thermal_shutdown():
    """
    Emergency shutdown procedure when temperature exceeds threshold.
    1. Kill all aireplay-ng processes
    2. Stop monitor mode
    3. Unblock WiFi
    4. Restart NetworkManager
    """
    global thermal_monitor_running
    
    # Import here to avoid circular imports
    from .attack import kill_all_attacks
    from .interface import get_mon_interface
    
    print(f"\n\n{Color.FAIL}{'='*60}{Color.ENDC}")
    print(f"{Color.FAIL}  ⚠️  EMERGENCY STOP: OVERHEAT DETECTED! ⚠️{Color.ENDC}")
    print(f"{Color.FAIL}{'='*60}{Color.ENDC}")
    print(f"{Color.WARNING}[!] Temperature exceeded {TEMP_THRESHOLD}°C safety limit!{Color.ENDC}")
    print(f"{Color.WARNING}[!] Initiating emergency shutdown...{Color.ENDC}")
    
    # Stop thermal monitor
    thermal_monitor_running = False
    
    # 1. Kill all attack processes
    print(f"{Color.BLUE}[1/4] Killing aireplay-ng processes...{Color.ENDC}")
    kill_all_attacks()
    subprocess.call("pkill -9 aireplay-ng", shell=True, 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 2. Stop monitor mode
    print(f"{Color.BLUE}[2/4] Stopping monitor mode...{Color.ENDC}")
    mon = get_mon_interface()
    if mon:
        subprocess.call(f"airmon-ng stop {mon}", shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. Unblock WiFi
    print(f"{Color.BLUE}[3/4] Unblocking WiFi (rfkill)...{Color.ENDC}")
    subprocess.call("rfkill unblock wifi", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 4. Restart NetworkManager
    print(f"{Color.BLUE}[4/4] Restarting NetworkManager...{Color.ENDC}")
    subprocess.call("systemctl restart NetworkManager", shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f"\n{Color.GREEN}[+] Emergency shutdown complete.{Color.ENDC}")
    print(f"{Color.CYAN}[*] WiFi connection should be restored shortly.{Color.ENDC}")
    print(f"{Color.WARNING}[!] Let the chip cool down before running again!{Color.ENDC}")


def thermal_monitor_thread():
    """
    Background thread for real-time temperature monitoring.
    Runs while thermal_monitor_running is True.
    Shows temperature in TERMINAL TITLE BAR (doesn't interfere with input).
    Triggers emergency shutdown if temperature exceeds threshold.
    """
    global thermal_monitor_running, current_temp
    
    # Import here to avoid circular imports
    from .attack import active_attack_processes
    
    while thermal_monitor_running:
        temp = read_temperature()
        current_temp = temp if temp else 0.0
        
        if temp is not None:
            status, color = get_temp_status(temp)
            
            # Check for overheat
            if temp >= TEMP_THRESHOLD:
                emergency_thermal_shutdown()
                return
            
            # Update terminal TITLE BAR with temperature (real-time, non-intrusive)
            # Format: \033]0;TITLE\007
            attack_count = len(active_attack_processes)
            title = f"🌡️ {temp:.1f}°C ({status}) | Attacks: {attack_count} | DEAUTH TOOL"
            sys.stdout.write(f"\033]0;{title}\007")
            sys.stdout.flush()
            
            # Warning at 55°C (print once)
            if temp >= TEMP_WARNING and not hasattr(thermal_monitor_thread, '_warned'):
                print(f"\n{Color.WARNING}[!] TEMP WARNING: {temp:.1f}°C - approaching limit!{Color.ENDC}")
                thermal_monitor_thread._warned = True
        
        time.sleep(TEMP_CHECK_INTERVAL)


def start_thermal_monitor():
    """Start the thermal monitoring thread (silent mode - only checks for overheat)"""
    global thermal_monitor_running, temp_sensor_path
    
    # Don't start if already running
    if thermal_monitor_running:
        return None
    
    # Try to find sensor first
    temp_sensor_path = find_mt7921_sensor()
    if not temp_sensor_path:
        print(f"{Color.WARNING}[!] MT7921 thermal sensor not found - monitoring disabled{Color.ENDC}")
        return None
    
    # Reset warning flag
    if hasattr(thermal_monitor_thread, '_warned'):
        delattr(thermal_monitor_thread, '_warned')
    
    thermal_monitor_running = True
    monitor_thread = threading.Thread(target=thermal_monitor_thread, daemon=True)
    monitor_thread.start()
    
    # Show initial temp
    temp = read_temperature()
    if temp:
        status, color = get_temp_status(temp)
        print(f"{Color.CYAN}[THERMAL] {temp:.1f}°C ({status}) - Monitoring active (Limit: {TEMP_THRESHOLD}°C){Color.ENDC}")
    
    return monitor_thread


def stop_thermal_monitor():
    """Stop the thermal monitoring thread"""
    global thermal_monitor_running
    if thermal_monitor_running:
        thermal_monitor_running = False
        time.sleep(0.1)  # Give thread time to stop

# ============================================================
# DEAUTHER PACKAGE
# ============================================================
# Multi-Target Deauthentication Tool with Thermal Protection
# ============================================================

from .config import (
    INTERFACE_ASLI,
    MAX_TARGETS,
    DEAUTH_PACKETS,
    DEAUTH_DELAY,
    CHANNEL_LOCK_TIME,
    BURST_STAGGER,
    TEMP_THRESHOLD,
    TEMP_WARNING,
    TEMP_CHECK_INTERVAL
)

from .colors import Color

from .utils import (
    check_root,
    run_command,
    clear_screen,
    cleanup_and_exit,
    reset_cleanup_state
)

from .thermal import (
    find_mt7921_sensor,
    read_temperature,
    get_temp_status,
    emergency_thermal_shutdown,
    start_thermal_monitor,
    stop_thermal_monitor
)

from .interface import (
    get_mon_interface,
    is_monitor_mode,
    enable_monitor_mode,
    verify_channel_lock,
    lock_channel_robust,
    restart_driver,
    get_current_locked_channel
)

from .scanner import (
    get_band_from_channel,
    parse_clients_from_csv,
    scan_networks_and_clients,
    scan_networks_live,
    scan_networks_timed
)

from .attack import (
    kill_all_attacks,
    deauth_attack_single_optimized,
    deauth_attack_clients,
    deauth_attack_multi,
    parse_target_selection,
    get_active_attack_count,
    active_attack_processes
)

__all__ = [
    # Config
    'INTERFACE_ASLI',
    'MAX_TARGETS',
    'DEAUTH_PACKETS',
    'DEAUTH_DELAY',
    'CHANNEL_LOCK_TIME',
    'BURST_STAGGER',
    'TEMP_THRESHOLD',
    'TEMP_WARNING',
    'TEMP_CHECK_INTERVAL',
    # Colors
    'Color',
    # Utils
    'check_root',
    'run_command',
    'clear_screen',
    'cleanup_and_exit',
    'reset_cleanup_state',
    # Thermal
    'find_mt7921_sensor',
    'read_temperature',
    'get_temp_status',
    'emergency_thermal_shutdown',
    'start_thermal_monitor',
    'stop_thermal_monitor',
    # Interface
    'get_mon_interface',
    'is_monitor_mode',
    'enable_monitor_mode',
    'verify_channel_lock',
    'lock_channel_robust',
    'restart_driver',
    'get_current_locked_channel',
    # Scanner
    'get_band_from_channel',
    'parse_clients_from_csv',
    'scan_networks_and_clients',
    'scan_networks_live',
    'scan_networks_timed',
    # Attack
    'kill_all_attacks',
    'deauth_attack_single_optimized',
    'deauth_attack_clients',
    'deauth_attack_multi',
    'parse_target_selection',
    'get_active_attack_count',
    'active_attack_processes'
]

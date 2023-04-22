import re
import os

# not in standard library
try: import psutil
except ModuleNotFoundError: psutil = None

# To quiet down linting errors in editors like VSCode
from lib.logger import debug, error

# ENV module version: 2023-03-29



#############################  ENVIRONMENT  ##############################
###                                                                    ###
###                                                                    ###
###      ███████ ███    ██ ██    ██ ██ ██████   ██████  ███    ██      ###
###      ██      ████   ██ ██    ██ ██ ██   ██ ██    ██ ████   ██      ###
###      █████   ██ ██  ██ ██    ██ ██ ██████  ██    ██ ██ ██  ██      ###
###      ██      ██  ██ ██  ██  ██  ██ ██   ██ ██    ██ ██  ██ ██      ###
###      ███████ ██   ████   ████   ██ ██   ██  ██████  ██   ████      ###
###                                                                    ###
###                                                                    ###
##########################################################################
# Set up some useful environment variables


def get_env_info():
    DISTRO_NAME = None
    SESSION_TYPE = None
    DESKTOP_ENV = None

    env_info = {}
    _distro_name = ""
    _desktop_env = ""
    ########################################################################
    ##  Get distro name
    if 1 == 2:
        pass
    elif os.path.isfile('/etc/os-release'):
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('NAME='):
                    _distro_name = line.split('=')[1].strip().strip('"')
                    break
                elif line.startswith('PRETTY_NAME='):
                    _distro_name = line.split('=')[1].strip().strip('"')
                    break
    elif os.path.isfile('/etc/lsb-release'):
        with open('/etc/lsb-release', 'r') as f:
            for line in f:
                if line.startswith('DISTRIB_ID='):
                    _distro_name = line.split('=')[1].strip()
                    break
                elif line.startswith('DISTRIB_DESCRIPTION='):
                    _distro_name = line.split('=')[1].strip().strip('"')
                    break
    elif os.path.isfile('/etc/arch-release'):
        _distro_name = 'arch'

    distro_names = {                # simplify distro names need special overrides
        'elementary':               'eos',
        'Fedora':                   'fedora',
        'Manjaro':                  'manjaro',
        'KDE Neon':                 'neon',
        'Pop!_OS':                  'popos',
        'Ubuntu':                   'ubuntu',
    }

    for k, v in distro_names.items():
        # debug(f'{k = :<10} {v = :<10}')
        if re.search(k, _distro_name, re.I):
            DISTRO_NAME = v
            break

    # If distro name not found in list that needs overrides, just show original name
    if not DISTRO_NAME:
        DISTRO_NAME = _distro_name

    env_info['DISTRO_NAME'] = DISTRO_NAME


    ########################################################################
    ##  Get session type
    SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE") or None
    if not SESSION_TYPE:  # Why isn't XDG_SESSION_TYPE set? This shouldn't happen.
        error(f'ENV: XDG_SESSION_TYPE should really be set. Are you in a graphical environment?')
        SESSION_TYPE = os.environ.get("WAYLAND_DISPLAY")
        if not SESSION_TYPE:
            raise EnvironmentError(
                f'\n\nENV: Detecting session type from XDG_SESSION_TYPE or WAYLAND_DISPLAY failed.\n')
    if SESSION_TYPE.casefold() not in ['x11', 'xorg', 'wayland']:
        raise EnvironmentError(f'\n\nENV: Unknown session type: {SESSION_TYPE}.\n')

    env_info['SESSION_TYPE'] = SESSION_TYPE


    ########################################################################
    ##  Get desktop environment
    _desktop_env = os.environ.get("XDG_SESSION_DESKTOP") or os.environ.get("XDG_CURRENT_DESKTOP")

    if not _desktop_env:
        _desktop_env = None
        error("ERROR: Desktop Environment not found in XDG_SESSION_DESKTOP or XDG_CURRENT_DESKTOP.")
        error("ERROR: Config file will not be able to adapt automatically to Desktop Environment.")

    # Produce a simplified desktop environment name
    desktop_env_names = {
        'Budgie':                   'budgie',
        'Cinnamon':                 'cinnamon',
        'Deepin':                   'deepin',
        'Enlightenment':            'enlightenment',
        'GNOME':                    'gnome',
        'Hyprland':                 'hypr',
        'IceWM':                    'icewm',
        'KDE':                      'kde',
        'LXDE':                     'lxde',
        'LXQt':                     'lxqt',
        'MATE':                     'mate',
        'Pantheon':                 'pantheon',
        'Plasma':                   'kde',
        'SwayWM':                   'sway',
        'Ubuntu':                   'gnome',    # "Ubuntu" in XDG_CURRENT_DESKTOP, but DE is GNOME
        'Unity':                    'unity',
        'Xfce':                     'xfce',
    }

    for k, v in desktop_env_names.items():
        # debug(f'{k = :<10} {v = :<10}')
        if re.search(k, _desktop_env, re.I):
            DESKTOP_ENV = v
        if DESKTOP_ENV:
            break

    if not DESKTOP_ENV:
        error(f'Desktop Environment not in de_names list! Should fix this.\n\t{_desktop_env = }')
        DESKTOP_ENV = _desktop_env

    if psutil:
        # Doublecheck the desktop environment by checking for identifiable running processes
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] in ['plasmashell', 'kwin_ft', 'kwin_x11']:
                if DESKTOP_ENV != 'kde':
                    error(f'Desktop may have been misidentified: {DESKTOP_ENV = }. KWin detected.')
                    DESKTOP_ENV = 'kde'
                    break
            if proc.info['name'] == 'gnome-shell':
                if DESKTOP_ENV != 'gnome':
                    error(f'Desktop may have been misidentified: {DESKTOP_ENV = }. GNOME Shell detected.')
                    DESKTOP_ENV = 'gnome'
                    break
            if proc.info['name'] == 'sway':
                if DESKTOP_ENV != 'sway':
                    error(f'Desktop may have been misidentified: {DESKTOP_ENV = }. SwayWM detected.')
                    DESKTOP_ENV = 'sway'
                    break
    else:
        debug(f'ENV: The process doublecheck was bypassed because "psutil" was not imported.')

    env_info['DESKTOP_ENV'] = DESKTOP_ENV
    
    return env_info

#!/usr/bin/env python3


import os
import sys
import pwd
import grp
import json
import signal
import shutil
import argparse
import datetime
import platform
import subprocess

from typing import Dict
# local import
import lib.env as env
from lib.logger import debug, error


if os.name == 'posix' and os.geteuid() == 0:
    print("This app should not be run as root/superuser.")
    sys.exit(1)

def signal_handler(sig, frame):
    """handle signals like Ctrl+C"""
    if sig in (signal.SIGINT, signal.SIGQUIT):
        # Perform any cleanup code here before exiting
        # traceback.print_stack(frame)
        print(f'\nSIGINT or SIGQUIT received. Exiting.\n')
        sys.exit(0)

if platform.system() != 'Windows':
    signal.signal(signal.SIGINT,    signal_handler)
    signal.signal(signal.SIGQUIT,   signal_handler)
    signal.signal(signal.SIGHUP,    signal_handler)
    signal.signal(signal.SIGUSR1,   signal_handler)
    signal.signal(signal.SIGUSR2,   signal_handler)
else:
    signal.signal(signal.SIGINT,    signal_handler)
    print(f'This is only meant to run on Linux. Exiting...')
    sys.exit(1)



class InstallerSettings:
    """set up variables for necessary information to be used by all functions"""
    def __init__(self) -> None:
        self.env_info_dct       = None
        self.DISTRO_NAME        = None
        self.DISTRO_VER         = None
        self.SESSION_TYPE       = None
        self.DESKTOP_ENV        = None

        self.pkgs_json_dct      = None
        self.pkgs_for_distro    = None
        self.pip_pkgs           = None

        self.home_dir_path      = os.path.abspath(os.path.expanduser('~'))
        self.toshy_dir_path     = os.path.join(self.home_dir_path, '.config', 'toshy')
        self.venv_path          = os.path.join(self.toshy_dir_path, '.venv')

        self.keyszer_clone_cmd  = 'clone -b adapt_to_capslock https://github.com/RedBearAK/keyszer.git'

        self.input_group_name   = 'input'
        self.user_name          = pwd.getpwuid(os.getuid()).pw_name


def get_environment():
    """get back the distro, session and desktop info from `env.py` module"""
    cnfg.env_info_dct: Dict[str, str]   = env.get_env_info()
    cnfg.DISTRO_NAME    = cnfg.env_info_dct.get('DISTRO_NAME',  ''  ).casefold()
    cnfg.DISTRO_VER     = cnfg.env_info_dct.get('DISTRO_VER',   ''  ).casefold()
    cnfg.SESSION_TYPE   = cnfg.env_info_dct.get('SESSION_TYPE', ''  ).casefold()
    cnfg.DESKTOP_ENV    = cnfg.env_info_dct.get('DESKTOP_ENV',  ''  ).casefold()
    print(  f'Toshy installer sees this environment:'
            f'\n\t{cnfg.DISTRO_NAME     = }'
            f'\n\t{cnfg.DISTRO_VER      = }'
            f'\n\t{cnfg.SESSION_TYPE    = }'
            f'\n\t{cnfg.DESKTOP_ENV     = }')


def load_package_list():
    """load package list from JSON file"""
    with open('packages.json') as f:
        cnfg.pkgs_json_dct = json.load(f)
    cnfg.pip_pkgs = cnfg.pkgs_json_dct['pip']
    cnfg.pkgs_for_distro = cnfg.pkgs_json_dct[cnfg.DISTRO_NAME]


def install_distro_pkgs():
    """install needed packages from list for distro type"""
    print(f'\nInstalling native packages...\n')

    if True is False: pass  # dummy first line just because
    
    elif cnfg.DISTRO_NAME in ['ubuntu', 'debian']:
        subprocess.run(['sudo', 'apt', 'install', '-y'] + cnfg.pkgs_for_distro)
    
    elif cnfg.DISTRO_NAME in ['fedora', 'fedoralinux']:
        subprocess.run(['sudo', 'dnf', 'install', '-y'] + cnfg.pkgs_for_distro)
    
    elif cnfg.DISTRO_NAME in ['arch', 'manjaro']:
        print('It is essential to have an Arch-based system completely updated.')
        response = input('Have you run "sudo pacman -Syyu" recently? [y/N]')
        if response in ['y', 'Y']:
            subprocess.run(['sudo', 'pacman', '-S', '--noconfirm'] + cnfg.pkgs_for_distro)
        else:
            print('Get your Arch system up to date first, then run the installer again. Exiting.')
            sys.exit(0)
    
    else:
        print(f"Sorry, no package list available for distro: {cnfg.DISTRO_NAME}")
        sys.exit(0)


def clone_keyszer_branch():
    """clone the latest `keyszer` from GitHub"""
    print(f'\nCloning keyszer branch...\n')
    keyszer_tmp_dir_path = os.path.join('.', 'keyszer-temp')
    if os.path.exists(keyszer_tmp_dir_path):
        # force a fresh copy of keyszer every time script is run
        shutil.rmtree(keyszer_tmp_dir_path, ignore_errors=True)
    subprocess.run(['git', cnfg.keyszer_clone_cmd, keyszer_tmp_dir_path])


def install_keyszer_for_user():
    """install `keyszer` for the local user"""
    print(f'\nInstalling keyszer for user...\n')
    if os.path.exists('./keyszer-temp'):
        subprocess.run(['pip', 'install', '--user', '--upgrade', './keyszer-temp'])
    else:
        print(f'"keyszer-temp" folder missing... Unable to install "keyszer"...')
        sys.exit(1)


def backup_toshy_config():
    """backup existing Toshy config folder"""
    print(f'\nBacking up existing Toshy config folder...\n')
    timestamp = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S')
    toshy_backup_dir_path = os.path.abspath(cnfg.toshy_dir_path + timestamp)

    try:
        # Copy files recursively from source to destination
        shutil.copytree(cnfg.toshy_dir_path, toshy_backup_dir_path)
    except shutil.Error as e:
        print(f"Failed to copy directory: {e}")
    except OSError as e:
        print(f"Failed to create backup directory: {e}")


def install_toshy_files():
    """install Toshy files"""
    print(f'\nInstalling Toshy files...\n')
    script_name = os.path.basename(__file__)

    try:
        if os.path.exists(cnfg.toshy_dir_path):
            shutil.rmtree(cnfg.toshy_dir_path, ignore_errors=True)
        # Copy files recursively from source to destination
        shutil.copytree('.', cnfg.toshy_dir_path, ignore=shutil.ignore_patterns(script_name))
    except shutil.Error as e:
        print(f"Failed to copy directory: {e}")
    except OSError as e:
        print(f"Failed to create backup directory: {e}")


def setup_virtual_env():
    """setup a virtual environment to install Python packages"""
    print(f'\nSetting up virtual environment...\n')

    # Create the virtual environment if it doesn't exist
    if not os.path.exists(cnfg.venv_path):
        subprocess.run([sys.executable, '-m', 'venv', cnfg.venv_path])
    # We do not need to "activate" the venv right now, just create it


def install_pip_pkgs():
    """install `pip` packages for Python"""
    print(f'\nInstalling/upgrading Python packages...\n')
    pip_cmd = os.path.join(cnfg.venv_path, 'bin', 'pip')
    subprocess.run([pip_cmd, 'install', '--upgrade'] + cnfg.pip_pkgs)


def apply_desktop_tweaks():
    """
    fix things like Meta key activating overview in GNOME or KDE Plasma
    and fix the Unicode sequences in KDE Plasma
    """
    print(f'\nApplying any necessary desktop tweaks...\n')
    
    # if GNOME, disable `overlay-key`
    # gsettings set org.gnome.mutter overlay-key ''
    if cnfg.DESKTOP_ENV == 'gnome':
        subprocess.run(['gsettings', 'set', 'org.gnome.mutter', 'overlay-key', "''"])
    
    # if KDE Plasma, disable Meta key opening app menu
    # append this to ~/.config/kwinrc:
    # [ModifierOnlyShortcuts]
    # Meta=
    # then run command: 
    # qdbus org.kde.KWin /KWin reconfigure
    if cnfg.DESKTOP_ENV == 'kde':
        subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'reconfigure'])
    
    # if KDE, install `ibus` or `fcitx` and choose as input manager (ask for confirmation)


def remove_desktop_tweaks():
    """undo the relevant desktop tweaks"""

    # if GNOME, re-enable `overlay-key`
    # gsettings reset org.gnome.mutter overlay-key
    if cnfg.DESKTOP_ENV == 'gnome':
        subprocess.run(['gsettings', 'reset', 'org.gnome.mutter', 'overlay-key'])

    # if KDE Plasma, remove tweak from ~/.config/kwinrc
    # then run command: 
    # qdbus org.kde.KWin /KWin reconfigure
    if cnfg.DESKTOP_ENV == 'kde':
        subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'reconfigure'])


def install_udev_rules():
    """set up udev rules file to give user/keyszer access to uinput"""
    if not os.path.exists('/etc/udeb/rules.d/90-keymapper-input.rules'):
        print(f'\nInstalling "udev" rules file for keymapper...\n')
        rule_content = 'SUBSYSTEM=="input", GROUP="input"\nKERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input"\n'
        command = 'sudo tee /etc/udev/rules.d/90-keymapper-input.rules'
        try:
            subprocess.run(command, input=rule_content.encode(), shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f'\nERROR: Problem when trying to install "udev" rules file for keymapper...\n')


def verify_user_groups():
    """Check if the `input` group exists and user is in group"""
    try:
        grp.getgrnam(cnfg.input_group_name)
    except KeyError:
        # The group doesn't exist, so create it
        print(f'Creating "input" group...\n')
        subprocess.run(['sudo', 'groupadd', cnfg.input_group_name])

    # Check if the user is already in the `input` group
    group_info = grp.getgrnam(cnfg.input_group_name)
    if cnfg.user_name in group_info.gr_mem:
        print(f'\nUser {cnfg.user_name} is a member of group {cnfg.input_group_name}, continuing...\n')
    else:
        # Add the user to the input group
        subprocess.run(['sudo', 'usermod', '-aG', cnfg.input_group_name, cnfg.user_name])
        print(f'\nUser {cnfg.user_name} added to group {cnfg.input_group_name}...')
        print(f'May need to REBOOT or at least LOG OUT/IN to have proper permissions...\n')


if __name__ == '__main__':

    cnfg = InstallerSettings()

    get_environment()
    load_package_list()
    install_distro_pkgs()
    clone_keyszer_branch()
    install_keyszer_for_user()
    backup_toshy_config()
    install_toshy_files()
    setup_virtual_env()
    install_pip_pkgs()
    apply_desktop_tweaks()
    install_udev_rules()
    verify_user_groups()

    print(f'\n')

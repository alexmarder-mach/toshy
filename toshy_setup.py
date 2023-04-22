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



class Settings:
    """set up variables for necessary information to be used by all functions"""
    def __init__(self) -> None:
        self.env_info_dct       = None
        self.DISTRO_NAME        = None
        self.SESSION_TYPE       = None
        self.DESKTOP_ENV        = None

        self.packages_json_dct  = None
        self.pkgs_for_distro    = None
        self.pip_pkgs           = None

        self.keyszer_branch     = 'https://github.com/joshgoebel/keyszer'

        self.group_name         = 'input'
        self.user_name          = pwd.getpwuid(os.getuid()).pw_name


def get_environment():
    """get back the distro, session and desktop info from `env.py` module"""
    cnfg.env_info_dct   = env.get_env_info()
    cnfg.DISTRO_NAME    = cnfg.env_info_dct.get('DISTRO_NAME').casefold()
    cnfg.SESSION_TYPE   = cnfg.env_info_dct.get('SESSION_TYPE').casefold()
    cnfg.DESKTOP_ENV    = cnfg.env_info_dct.get('DESKTOP_ENV').casefold()
    print(  f'Toshy installer sees this environment:'
            f'\n\t{cnfg.DISTRO_NAME  = }'
            f'\n\t{cnfg.SESSION_TYPE = }'
            f'\n\t{cnfg.DESKTOP_ENV  = }')


def load_package_list():
    """load package list"""
    with open('packages.json') as f:
        cnfg.packages_json_dct = json.load(f)
    cnfg.pip_pkgs = cnfg.packages_json_dct['pip']
    cnfg.pkgs_for_distro = cnfg.packages_json_dct[cnfg.DISTRO_NAME]


def install_distro_pkgs():
    """install needed packages from list for distro type"""
    print(f'\nInstalling native packages...\n')

    if cnfg.DISTRO_NAME in ['ubuntu', 'debian']:
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


def install_pip_packages():
    """install `pip` packages for Python"""
    print(f'\nInstalling/upgrading Python packages...\n')
    subprocess.run(['pip', 'install', '--user', '--upgrade'] + cnfg.pip_pkgs)


def clone_keyszer():
    """clone the latest `keyszer` from GitHub"""
    print(f'\nCloning keyszer branch...\n')
    if os.path.exists('./keyszer'):
        # force a fresh copy of keyszer every time script is run
        shutil.rmtree('keyszer', ignore_errors=True)
    subprocess.run(['git', 'clone', f'{cnfg.keyszer_branch}'])


def install_keyszer_for_user():
    """install `keyszer` for the local user"""
    print(f'\nInstalling keyszer for user...\n')
    if os.path.exists('./keyszer'):
        subprocess.run(['pip', 'install', '--user', '--upgrade', './keyszer'])
    else:
        print(f'"keyszer" folder missing... Unable to install "keyszer"...')
        sys.exit(1)


def backup_toshy_config():
    """backup existing Toshy config folder"""
    print(f'\nBacking up existing Toshy config folder...\n')
    home_dir_path = os.path.abspath(os.path.expanduser('~'))
    toshy_dir_path = os.path.join(home_dir_path, '.config/toshy')
    timestamp = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S')
    toshy_backup_dir_path = os.path.abspath(toshy_dir_path + timestamp)
    try:
        # Create destination directory if it doesn't exist
        if not os.path.exists(toshy_backup_dir_path):
            os.makedirs(toshy_backup_dir_path)

        # Copy files recursively from source to destination
        shutil.copytree(toshy_dir_path, toshy_backup_dir_path)

    except shutil.Error as e:
        print(f"Failed to copy directory: {e}")
    except OSError as e:
        print(f"Failed to create destination directory: {e}")


def install_toshy():
    """install Toshy files"""
    print(f'\nInstalling Toshy...\n')
    pass


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
        grp.getgrnam(cnfg.group_name)
    except KeyError:
        # The group doesn't exist, so create it
        print(f'Creating "input" group...\n')
        subprocess.run(['sudo', 'groupadd', cnfg.group_name])

    # Check if the user is already in the `input` group
    group_info = grp.getgrnam(cnfg.group_name)
    if cnfg.user_name in group_info.gr_mem:
        print(f'\nUser {cnfg.user_name} is already a member of group {cnfg.group_name}...\n')
    else:
        # Add the user to the input group
        subprocess.run(['sudo', 'usermod', '-aG', cnfg.group_name, cnfg.user_name])
        print(f'\nUser {cnfg.user_name} added to group {cnfg.group_name}...')
        print(f'May need to REBOOT or at least LOG OUT/IN to have proper permissions...\n')


if __name__ == '__main__':
    cnfg: Settings = Settings()
    # get_environment()
    # load_package_list()
    # install_distro_pkgs()
    # install_pip_packages()
    # clone_keyszer()
    # install_keyszer_for_user()
    backup_toshy_config()
    # install_toshy()
    # apply_desktop_tweaks()
    # install_udev_rules()
    # verify_user_groups()
    print()

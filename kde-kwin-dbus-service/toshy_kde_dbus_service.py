#!/usr/bin/env python3

import os
import sys
import dbus
import time
import shutil
import signal
import platform
import subprocess
import dbus.service
import dbus.mainloop.glib

from gi.repository import GLib
from dbus.exceptions import DBusException
from subprocess import DEVNULL
# from dbus.service import method
from typing import Dict, List, Union
from keyszer.lib.logger import debug, error, warn, info, log

# Add paths to avoid errors like ModuleNotFoundError or ImportError
home_dir = os.path.expanduser("~")
parent_folder_path  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
current_folder_path = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, current_folder_path)
sys.path.insert(0, parent_folder_path)

existing_path = os.environ.get('PYTHONPATH', '')
os.environ['PYTHONPATH'] = f'{parent_folder_path}:{current_folder_path}:{existing_path}'

# local imports
# from ..lib.env import get_env_info
import lib.env as env

# Independent module/script to create a D-Bus window context
# service in a KDE Plasma environment, which will be notified
# of window focus changes by the Toshy KWin script

if os.name == 'posix' and os.geteuid() == 0:
    error("This app should not be run as root/superuser.")
    sys.exit(1)

def signal_handler(sig, frame):
    """handle signals like Ctrl+C"""
    if sig in (signal.SIGINT, signal.SIGQUIT):
        # Perform any cleanup code here before exiting
        # traceback.print_stack(frame)
        debug(f'\nSIGINT or SIGQUIT received. Exiting.\n')
        sys.exit(0)

if platform.system() != 'Windows':
    signal.signal(signal.SIGINT,    signal_handler)
    signal.signal(signal.SIGQUIT,   signal_handler)
else:
    error(f'This is only meant to run on Linux. Exiting...')
    sys.exit(1)


LOG_PFX = 'TOSHY_KDE_DBUS_SVC'

DISTRO_NAME     = None
DISTRO_VER      = None
SESSION_TYPE    = None
DESKTOP_ENV     = None


def check_environment():
    """Retrieve the current environment from env module"""
    env_info: Dict[str, str] = env.get_env_info()   # Returns a dict
    global DISTRO_NAME, DISTRO_VER, SESSION_TYPE, DESKTOP_ENV
    DISTRO_NAME     = env_info.get('DISTRO_NAME')
    DISTRO_VER      = env_info.get('DISTRO_VER')
    SESSION_TYPE    = env_info.get('SESSION_TYPE')
    DESKTOP_ENV     = env_info.get('DESKTOP_ENV')


check_environment()

loop_delay = 2
while True:
    if loop_delay > 8:
        error(f'{LOG_PFX}: Not a Wayland+KDE environment. Exiting.')
        sys.exit(0)
    if DESKTOP_ENV in ['kde', 'plasma'] and SESSION_TYPE == 'wayland':
        break
    else:
        time.sleep(loop_delay)
        loop_delay += 2
        check_environment()


toshy_kwin_script_name = 'toshy-dbus-notifyactivewindow'
qdbus_cmd = 'qdbus-qt5' if shutil.which('qdbus-qt5') else 'qdbus'
kwin_scripting_obj = 'org.kde.KWin'
kwin_scripting_path = '/Scripting'
kwin_scripting_iface = 'org.kde.kwin.Scripting'
methods = [
    'isScriptLoaded',
    'loadScript',
    'start',
    'unloadScript'
]

if shutil.which(qdbus_cmd):

    def is_script_loaded():
        try:
            output = subprocess.check_output([  qdbus_cmd,
                                                kwin_scripting_obj,
                                                '/Scripting',
                                                'org.kde.kwin.Scripting.isScriptLoaded',
                                                toshy_kwin_script_name    ])
            return output.strip() == 'true'
        except subprocess.CalledProcessError as e:
            print(f"Error checking if KWin script is loaded: {e}")
            return False

    print(f"Script {toshy_kwin_script_name} loaded: {is_script_loaded()}")
else:
    print(f"Cannot find '{qdbus_cmd}'. Please install it to check KWin script status.")



# loop breaks if environment is suitable, so run the kickstart script here
kickstart_script    = 'toshy-kwin-script-kickstart.sh'
kickstart_cmd       = os.path.join(home_dir, '.config', 'toshy', 'scripts', kickstart_script)
subprocess.Popen([kickstart_cmd], stderr=DEVNULL, stdout=DEVNULL)

# debug("")
# debug(  f'Toshy KDE D-Bus service script sees this environment:'
#         f'\n\t{DISTRO_NAME      = }'
#         f'\n\t{DISTRO_VER       = }'
#         f'\n\t{SESSION_TYPE     = }'
#         f'\n\t{DESKTOP_ENV      = }\n', ctx="CG")


TOSHY_KDE_DBUS_SVC_PATH         = '/org/toshy/Toshy'
TOSHY_KDE_DBUS_SVC_IFACE        = 'org.toshy.Toshy'


class DBUS_Object(dbus.service.Object):
    """Class to handle D-Bus interactions"""
    def __init__(self, session_bus, object_path, interface_name):
        super().__init__(session_bus, object_path)
        self.interface_name     = interface_name
        self.dbus_svc_bus_name  = dbus.service.BusName(interface_name, bus=session_bus)
        self.caption            = "NO_DATA"
        self.resource_class     = "NO_DATA"
        self.resource_name      = "NO_DATA"

    @dbus.service.method(TOSHY_KDE_DBUS_SVC_IFACE, in_signature='sss')
    def NotifyActiveWindow(self, caption, resource_class, resource_name):
        debug(f'{LOG_PFX}: NotifyActiveWindow() called...')
        self.caption            = str(caption)
        self.resource_class     = str(resource_class)
        self.resource_name      = str(resource_name)
        debug(f'{LOG_PFX}: Active window attributes:'
                f"\n\t caption        = '{self.caption}'"
                f"\n\t resource_class = '{self.resource_class}'"
                f"\n\t resource_name  = '{self.resource_name}'"
        )

    @dbus.service.method(TOSHY_KDE_DBUS_SVC_IFACE, out_signature='a{sv}')
    def GetActiveWindow(self):
        debug(f'{LOG_PFX}: GetActiveWindow() called...')
        return {    'caption':          self.caption,
                    'resource_class':   self.resource_class,
                    'resource_name':    self.resource_name }


def main():
    # Initialize the D-Bus main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # Connect to the session bus
    session_bus = dbus.SessionBus()

    # Create the DBUS_Object
    try:
        DBUS_Object(session_bus, TOSHY_KDE_DBUS_SVC_PATH, TOSHY_KDE_DBUS_SVC_IFACE)
    except DBusException as dbus_error:
        error(f"{LOG_PFX}: Error occurred while creating D-Bus service object:\n\t{dbus_error}")
        sys.exit(1)

    # Run the main loop
    # dbus.mainloop.glib.DBusGMainLoop().run()
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()

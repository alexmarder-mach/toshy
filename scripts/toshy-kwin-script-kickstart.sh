#!/usr/bin/env bash

# Script to create a KWin event that will get the KWin script to start working

# Check if the script is being run as root
if [[ $EUID -eq 0 ]]; then
    echo "This script must not be run as root"
    exit 1
fi

# Check if $USER and $HOME environment variables are not empty
if [[ -z $USER ]] || [[ -z $HOME ]]; then
    echo "\$USER and/or \$HOME environment variables are not set. We need them."
    exit 1
fi

sleep 2

title="Toshy"
icon_file="${HOME}/.local/share/icons/toshy_app_icon_rainbow.svg"
time1_s=2
time2_s=3
message="Kickstarting the Toshy KWin script."


if command -v timeout &> /dev/null; then
    timeout_cmd="timeout -k ${time2_s}s -s SIGTERM ${time1_s}s "
else
    timeout_cmd=""
fi

if command -v zenity &> /dev/null; then
    zenity --info --icon="" &>/dev/null
    if [ $? -eq 0 ]; then
        ${timeout_cmd} zenity --info --no-wrap --title="${title}" --icon="${icon_file}" \
            --text="${message}" --timeout=${time2_s} >/dev/null 2>&1
    else
        ${timeout_cmd} zenity --info --no-wrap --title="${title}" \
            --text="${message}" --timeout=${time2_s} >/dev/null 2>&1
    fi
    exit 0
elif command -v kdialog &> /dev/null; then
    ${timeout_cmd} kdialog --title="${title}" --icon "${icon_file}" \
        --msgbox "${message}" >/dev/null 2>&1
    exit 0
elif command -v xmessage &> /dev/null; then
    ${timeout_cmd} xmessage "${message}" -timeout ${time2_s} >/dev/null 2>&1
    exit 0
else
    echo "ERROR: Toshy cannot kickstart the KWin script. Dialog commands unavailable."
fi

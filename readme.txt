# Alimentation Tool - User Guide

## Overview
The Alimentation Tool is a desktop application designed to control and monitor power supplies through a graphical interface. It allows users to connect to various power supply devices, control voltage and current settings, and monitor power output.

## Installation
1. Extract the Alimentation Tool.exe file to a location of your choice
2. Ensure you have the required files in the correct locations:
   Your-Chosen-Folder/
   ├── Alimentation Tool.exe
   ├── alimentation.ini (optional but recommended)
   └── resources/
       ├── Garrett.ico
       └── Garrett.json

## Required Files
- Alimentation Tool.exe: The main application executable
- resources/Garrett.ico: Application icon file
- resources/Garrett.json: Theme file for the application
- alimentation.ini: Configuration file for device names (optional)

## Basic Usage
1. Launch the application by double-clicking "Alimentation Tool.exe"
2. Click "Search Devices" to scan for connected power supplies
3. Select a device from the list to connect to it
4. Use the control panel to:
   - Connect/disconnect from the device
   - Turn power on/off
   - Set voltage levels
   - Configure protection settings (OVP/OCP)
   - Measure current values

## Device Configuration
The alimentation.ini file allows you to customize device names. The file should follow this format:

[device_names]
2342-06 B = Keysight E36312A
34465A = Keysight 34465A

## FAQ

Q: Why can't the application find any devices?
A: Ensure that:
- Your power supply is properly connected to your computer via USB or GPIB
- The appropriate device drivers are installed
- The device is powered on
- You have the necessary permissions to access the device

Q: Why do I get an error when connecting to a device?
A: This could be due to:
- Another application is already connected to the device
- The device is in a locked state
- Communication issues with the device

Q: Why can't I set the voltage?
A: The voltage settings are locked until you have configured both OVP (Over Voltage Protection) and OCP (Over Current Protection) settings. This is a safety feature to ensure that proper protection limits are in place before applying voltage to your device under test.

Q: How do I add a new device type to the application?
A: Edit the alimentation.ini file and add a new entry under the [device_names] section with the format:
device_identifier = Display Name

Where device_identifier is a unique string that appears in the device's identification response.

Q: What does OVP and OCP mean?
A:
- OVP (Over Voltage Protection): Prevents the power supply from exceeding a set voltage limit
- OCP (Over Current Protection): Prevents the power supply from exceeding a set current limit

Q: The application crashes on startup with an icon error
A: Ensure that the resources folder exists and contains the Garrett.ico file. The folder should be in the same directory as the executable.

Q: The theme doesn't look right
A: Check that the resources folder contains the Garrett.json theme file and is properly located in the same directory as the executable.

## Troubleshooting

--> Missing Files
If you encounter errors about missing files, verify that:
1. All required files are present in the correct locations
2. The application has read permissions for these files

--> Connection Issues
If you have trouble connecting to devices:
1. Try restarting the device
2. Disconnect and reconnect the USB/GPIB cable
3. Ensure no other applications are using the device (EAPC tool ....)
4. Check that the correct drivers are installed

--> Performance Issues
If the application is slow or unresponsive:
1. Reduce the number of connected devices
2. Close other applications that might be using system resources
3. Restart the application
# Alimentation Tool - Source Code

## Overview
The Alimentation Tool is a desktop application designed to control and monitor power supplies through a graphical interface. It allows users to connect to various power supply devices, control voltage and current settings, and monitor power output.

## Project Structure
- `main.py`: Main application entry point and UI implementation
- `resources/`: Contains theme and icon files
  - `Garrett.ico`: Application icon
  - `Garrett.json`: CustomTkinter theme file
- `alimentation.ini`: Configuration file for device names

## Dependencies
- Python 3.7+ (used 3.13.2) 
- Required packages:
  - customtkinter
  - pyvisa
  - configparser

## Development Setup
1. Create a virtual environment (recommended):
   ````bash
   python -m venv .venv
   .venv\Scripts\activate
   ````

2. Install dependencies:
   ````bash
   pip install -r requirements.txt
   ```` 
python -m venv .venv
.venv\Scripts\activate

## Running the Application
To run the application:
   ````bash
    python main.py
   ````
## Configuration
Device names are configured in `alimentation.ini`.

## Customization
The application theme and icon can be customized in the `resources` directory.

## Building the Executable
To create a standalone executable:
   ````bash
   pyinstaller --onefile --windowed --add-data "alimentation.ini;." --add-data "resources/Garrett.ico;resources" --add-data "resources/Garrett.json;resources" --icon=resources/Garrett.ico --name="Alimentation Tool" main.py
   ````
## Key Features
- Automatic device detection and identification
- Support for multiple power supply models including dual-channel devices
- Control voltage and current settings
- Real-time measurements of power output
- Device-specific naming via configuration file

## Safety features
- Voltage settings are locked until OVP and OCP protection limits are configured
- Power state indicators with color coding
- Error handling for device communication issues

## Troubleshooting Development Issues
- If you encounter issues with PyVISA, ensure that the appropriate backend is installed
- For UI layout issues, check the frame dimensions and positioning
- Debug device communication by adding logging to the PowerSupply class methods
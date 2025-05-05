import customtkinter as ctk
import pyvisa
import configparser
import os
import time

class PowerSupply:
    _rm = None

    @staticmethod
    def list_available_devices():
        if PowerSupply._rm is None:
            PowerSupply._rm = pyvisa.ResourceManager()
            
        devices = PowerSupply._rm.list_resources()
        device_info = []
        
        for device in devices:
            try:
                inst = PowerSupply._rm.open_resource(device)
                idn = inst.query('*IDN?').strip()
                device_info.append((device, idn))
                inst.close()
            except:
                device_info.append((device, "Unable to identify"))
                
        return device_info

    def __init__(self, resource_name):
        if PowerSupply._rm is None:
            PowerSupply._rm = pyvisa.ResourceManager()
        self.device = PowerSupply._rm.open_resource(resource_name)

class AlimentationTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.device_frames = []
        self.identified_devices = []
        self.current_power_supply = None
        self.protection_settings = {}
        
        # Configure window with initial size (just enough for log + buttons)
        self.title("Alimentation Tool")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "Garrett.ico")
        self.iconbitmap(icon_path)
        self.initial_height = 270  # Height for log box + buttons + padding
        self.geometry(f"800x{self.initial_height}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Load Garrett theme depending on system
        ctk.set_appearance_mode("system")
        theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "Garrett.json")
        ctk.set_default_color_theme(theme_path)

        # Create log text box first (moved to top)
        self.log_textbox = ctk.CTkTextbox(
            self,
            width=780,
            height=200,
            state="disabled"
        )
        self.log_textbox.place(x=10, y=10)  # Moved to top position

        # Create search button (adjusted Y position)
        self.search_button = ctk.CTkButton(
            self,
            text="Search Devices",
            command=self.search_devices,
            width=100,
            height=30
        )
        self.search_button.place(x=10, y=220)  # Adjusted Y position

        # Create clear button
        self.clear_button = ctk.CTkButton(
            self,
            text="Clear Device List",
            command=self.clear_devices,
            state="disabled",
            width=100,
            height=30
        )
        self.clear_button.place(x=120, y=220)  # Place between Search and Exit

        # Create exit button (adjusted Y position)
        self.exit_button = ctk.CTkButton(
            self,
            text="Exit",
            command=self.on_closing,
            width=100,
            height=30
        )
        self.exit_button.place(x=690, y=220)  # Adjusted Y position

    def search_devices(self):
        # Clear existing devices if any
        for controls in self.device_frames:
            controls['frame'].destroy()
        self.device_frames.clear()
        self.identified_devices.clear()
            
        try:
            devices_info = PowerSupply.list_available_devices()
            self.identified_devices = []
            
            # Process devices and split dual channel devices into separate entries
            device_index = 0  # Track the actual device index (not frame index)
            for device, info in devices_info:
                if info != "Unable to identify":
                    device_index += 1  # Increment device index for each physical device
                    
                    if "2342-06 B" in info:  # Dual channel device
                        # Add two entries for the dual channel device with same device_index
                        self.identified_devices.append((device, info, "1", device_index))  # Channel 1
                        self.identified_devices.append((device, info, "2", device_index))  # Channel 2
                    else:
                        # Regular single channel device
                        self.identified_devices.append((device, info, None, device_index))
            
            if not self.identified_devices:
                # Reset window to initial size
                self.geometry(f"800x{self.initial_height}")
                self.log_message("No identifiable devices found")
                return
                
            self.log_message(f"Devices found: {len(self.identified_devices)}")
            
            # Calculate new window height based on number of devices
            # Use 155px spacing between frames, but only 5px for the last frame
            new_height = (
                self.initial_height +                         # Initial height
                (len(self.identified_devices) - 1) * 160 +    # Regular spacing for all but last frame (increased from 125 to 155)
                160  +                                        # Height of last frame (increased from 120 to 150)
                5                                             # Height of last frame for spacing
            )
            self.geometry(f"800x{new_height}")
            
            # Create frame for each device/channel
            for i, device_info in enumerate(self.identified_devices):
                device, info, channel, device_index = device_info
                device_frame = self.create_device_frame(device, info, i, channel, device_index)
                
                # Check power status right after creating the frame
                try:
                    # Temporarily connect to check power status
                    temp_power_supply = PowerSupply(device)
                    
                    # Query power status based on device type
                    if channel:
                        power_state = temp_power_supply.device.query(f'OUTP? (@{channel})').strip()
                    else:
                        power_state = temp_power_supply.device.query('OUTP?').strip()
                    
                    # Update power status based on query result
                    if power_state in ('1', 'ON'):
                        device_frame['power_status'].configure(text="Power ON", text_color="green")
                        device_frame['power_on_button'].configure(state="disabled")
                        device_frame['power_off_button'].configure(state="normal")
                    else:
                        device_frame['power_status'].configure(text="Power OFF", text_color="red")
                        device_frame['power_on_button'].configure(state="normal")
                        device_frame['power_off_button'].configure(state="disabled")
                    
                    # Close temporary connection
                    temp_power_supply.device.close()
                    
                except Exception as e:
                    self.log_message(f"Could not check power status: {str(e)}")
                
                # Log appropriate message based on device type
                if channel:
                    self.log_message(f"{device_index} - {info} (Channel {channel}) at {device}")
                else:
                    self.log_message(f"{device_index} - {info} at {device}")

            # Enable clear button
            self.search_button.configure(state="disabled")
            self.clear_button.configure(state="normal")

        except Exception as e:
            # Reset window to initial size on error
            self.geometry(f"800x{self.initial_height}")
            self.log_message(f"Error searching devices: {str(e)}")

    def clear_devices(self):
        """Clear all devices from the list and reset window size"""
        # Disconnect from all devices that might be connected
        for controls in self.device_frames:
            device = controls.get('connect_button').device
            channel = controls.get('channel')
            info = getattr(controls.get('connect_button'), 'info', None)
            
            try:
                # Create a temporary connection to each device to disconnect it properly
                temp_power_supply = PowerSupply(device)
                
                # Disconnect from the device
                if channel:
                    temp_power_supply.device.write(f'SYST:LOCK OFF (@{channel})')
                else:
                    temp_power_supply.device.write('SYST:LOCK OFF')

                self.log_message("Disconnected device", device, info, channel)

                # Close the temporary connection
                temp_power_supply.device.close()
                
            except Exception as e:
                self.log_message(f"Error disconnecting device: {str(e)}")
            
        # Close the current power supply connection if it exists
        if self.current_power_supply:
            try:
                self.current_power_supply.device.close()
            except:
                pass
            self.current_power_supply = None
            
        # Clear existing devices
        for controls in self.device_frames:
            controls['frame'].destroy()
        self.device_frames.clear()
        self.identified_devices.clear()
        
        # Reset protection settings
        self.protection_settings = {}

        # Reset window to initial size
        self.geometry(f"800x{self.initial_height}")
        self.log_message("Device list cleared")

        # Reset search button state
        self.search_button.configure(state="normal")
        self.clear_button.configure(state="disabled")

    def create_device_frame(self, device, info, frame_index, channel=None, device_index=None):
        # Create frame for device
        frame = ctk.CTkFrame(
            self,
            width=780,
            height=155
        )
        frame.place(x=10, y=260 + (frame_index * 160))
        frame.grid_propagate(False)
        
        # Use device_index for display if provided, otherwise use frame_index+1
        display_index = device_index if device_index is not None else frame_index + 1
        
        # Line 1: Device name with channel if applicable and connection status
        if channel:
            formatted_name = f"Alimentation {display_index}: {self.get_formatted_device_name(info)} Channel {channel}"
        else:
            formatted_name = f"Alimentation {display_index}: {self.get_formatted_device_name(info)}"
            
        name_label = ctk.CTkLabel(
            frame,
            text=formatted_name,
            width=200,
            height=30
        )
        name_label.place(x=10, y=5)
        
        # Status indicators - with separator
        status_label = ctk.CTkLabel(
            frame,
            text="Status:",
            width=60,
            height=30
        )
        status_label.place(x=530, y=5)
        
        connection_status = ctk.CTkLabel(
            frame,
            text="Disconnected",
            width=100,
            height=30,
            text_color="red",
            corner_radius=8
        )
        connection_status.place(x=580, y=5)
        
        # Add separator label
        separator_label = ctk.CTkLabel(
            frame,
            text="|",
            width=10,
            height=30
        )
        separator_label.place(x=680, y=5)
        
        # Power status label
        power_status = ctk.CTkLabel(
            frame,
            text="Power OFF",
            width=80,
            height=30,
            text_color="red",
            corner_radius=8
        )
        power_status.place(x=690, y=5)
        
        # Line 2: Control buttons
        connect_button = ctk.CTkButton(
            frame,
            text="Connect",
            command=lambda d=device, i=info, c=channel: self.connect_device(d, i, c),
            width=100,
            height=30,
            state="normal"
        )
        connect_button.place(x=10, y=40)
        connect_button.device = device
        connect_button.info = info
        connect_button.channel = channel
        
        disconnect_button = ctk.CTkButton(
            frame,
            text="Disconnect",
            command=lambda d=device, i=info, c=channel: self.disconnect_device(d, i, c),
            width=100,
            height=30,
            state="disabled"
        )
        disconnect_button.place(x=120, y=40)
        disconnect_button.device = device
        disconnect_button.channel = channel
        
        power_on_button = ctk.CTkButton(
            frame,
            text="Power ON",
            command=lambda d=device, i=info, c=channel: self.power_on(d, i, c),
            width=80,
            height=30,
            state="disabled"
        )
        power_on_button.place(x=600, y=40)
        power_on_button.device = device
        power_on_button.channel = channel
        
        power_off_button = ctk.CTkButton(
            frame,
            text="Power OFF",
            command=lambda d=device, i=info, c=channel: self.power_off(d, i, c),
            width=80,
            height=30,
            state="disabled"
        )
        power_off_button.place(x=690, y=40)
        power_off_button.device = device
        power_off_button.channel = channel
        
        # Line 3: Voltage, OVP, and OCP controls
        # Voltage section
        voltage_label = ctk.CTkLabel(
            frame,
            text="Voltage:",
            width=60,
            height=30
        )
        voltage_label.place(x=10, y=80)
        
        # Initially disable all entry fields
        voltage_entry = ctk.CTkEntry(
            frame,
            width=60,
            height=30,
            placeholder_text="0.0",
            state="disabled"
        )
        voltage_entry.place(x=70, y=80)
        
        set_voltage_button = ctk.CTkButton(
            frame,
            text="Set Voltage",
            command=lambda d=device, v=voltage_entry, i=info, c=channel: self.set_voltage(d, v, i, c),
            width=80,
            height=30,
            state="disabled"
        )
        set_voltage_button.place(x=140, y=80)
        set_voltage_button.device = device
        set_voltage_button.channel = channel
        
        # Over Voltage Protection section
        overvolt_label = ctk.CTkLabel(
            frame,
            text="Over Voltage Limit:",
            width=120,
            height=30
        )
        overvolt_label.place(x=230, y=80)
        
        # Initially disable OVP entry and button
        overvolt_entry = ctk.CTkEntry(
            frame,
            width=60,
            height=30,
            placeholder_text="0.0",
            state="disabled"
        )
        overvolt_entry.place(x=350, y=80)
        
        set_overvolt_button = ctk.CTkButton(
            frame,
            text="Set OVP",
            command=lambda d=device, v=overvolt_entry, i=info, c=channel: self.set_overvoltage(d, v, i, c),
            width=60,
            height=30,
            state="disabled"
        )
        set_overvolt_button.place(x=420, y=80)
        set_overvolt_button.device = device
        set_overvolt_button.channel = channel
        
        # Over Current Protection section
        overcurr_label = ctk.CTkLabel(
            frame,
            text="Over Current Limit:",
            width=120,
            height=30
        )
        overcurr_label.place(x=490, y=80)
        
        # Initially disable OCP entry and button
        overcurr_entry = ctk.CTkEntry(
            frame,
            width=60,
            height=30,
            placeholder_text="0.0",
            state="disabled"
        )
        overcurr_entry.place(x=610, y=80)
        
        set_overcurr_button = ctk.CTkButton(
            frame,
            text="Set OCP",
            command=lambda d=device, v=overcurr_entry, i=info, c=channel: self.set_overcurrent(d, v, i, c),
            width=60,
            height=30,
            state="disabled"
        )
        set_overcurr_button.place(x=680, y=80)
        set_overcurr_button.device = device
        set_overcurr_button.channel = channel
        
        # Line 4: Measurement section
        measure_button = ctk.CTkButton(
            frame,
            text="Measure",
            command=lambda d=device, i=info, c=channel: self.measure_values(d, i, c),
            width=80,
            height=30,
            state="disabled"
        )
        measure_button.place(x=10, y=120)
        measure_button.device = device
        measure_button.channel = channel
        
        # Voltage measurement display
        voltage_measure_label = ctk.CTkLabel(
            frame,
            text="Voltage: -- V",
            width=120,
            height=30
        )
        voltage_measure_label.place(x=100, y=120)
        
        # Current measurement display
        current_measure_label = ctk.CTkLabel(
            frame,
            text="Current: -- A",
            width=120,
            height=30
        )
        current_measure_label.place(x=230, y=120)
        
        # Power measurement display
        power_measure_label = ctk.CTkLabel(
            frame,
            text="Power: -- W",
            width=120,
            height=30
        )
        power_measure_label.place(x=360, y=120)
        
        # OVP and OCP status indicators
        protection_label = ctk.CTkLabel(
            frame,
            text="Protections:",
            width=60,
            height=30
        )
        protection_label.place(x=530, y=120)

        ovp_status = ctk.CTkLabel(
            frame,
            text="Set OVP",
            width=80,
            height=30,
            text_color="red"
        )
        ovp_status.place(x=600, y=120)
        
        separator_label2 = ctk.CTkLabel(
            frame,
            text="|",
            width=10,
            height=30
        )
        separator_label2.place(x=680, y=120)
        
        ocp_status = ctk.CTkLabel(
            frame,
            text="Set OCP",
            width=80,
            height=30,
            text_color="red"
        )
        ocp_status.place(x=690, y=120)
        
        # Controls dictionary
        controls = {
            'frame': frame,
            'connection_status': connection_status,
            'power_status': power_status,
            'connect_button': connect_button,
            'disconnect_button': disconnect_button,
            'voltage_entry': voltage_entry,
            'set_voltage_button': set_voltage_button,
            'overvolt_entry': overvolt_entry,
            'set_overvolt_button': set_overvolt_button,
            'overcurr_entry': overcurr_entry,
            'set_overcurr_button': set_overcurr_button,
            'power_on_button': power_on_button,
            'power_off_button': power_off_button,
            'measure_button': measure_button,
            'voltage_measure_label': voltage_measure_label,
            'current_measure_label': current_measure_label,
            'power_measure_label': power_measure_label,
            'ovp_status': ovp_status,
            'ocp_status': ocp_status,
            'channel': channel
        }
        
        self.device_frames.append(controls)
        return controls

    def get_formatted_device_name(self, info):
        """Format the device name based on the model using configuration file"""
        # Default to first part of info if no match
        default_name = info.split(',')[0]
        
        # Check if configuration file exists
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alimentation.ini')
        if not os.path.exists(config_path):
            return default_name
            
        # Read configuration
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(config_path)
        
        # Check if device_names section exists
        if 'device_names' not in config:
            return default_name

        # Check for each key in the device_names section
        for model_id, display_name in config['device_names'].items():
            if model_id in info:
                return display_name
                
        # Return default if no match found
        return default_name

    def log_message(self, message, device=None, info=None, channel=None):
        """Add a message to the log textbox with device information if provided"""
        # Get current date and time in the specified format
        current_time = time.strftime("[%d/%m/%y | %H:%M]")
        
        # Format the message with device info if provided
        if device and info:
            device_name = self.get_formatted_device_name(info)
            if channel:
                formatted_message = f"{current_time}   Alimentation: {device_name} Channel {channel} - {message}"
            else:
                formatted_message = f"{current_time}   Alimentation: {device_name} - {message}"
        else:
            formatted_message = f"{current_time}   {message}"
        
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{formatted_message}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")

    def on_closing(self):
        # Disconnect from all devices that might be connected
        for controls in self.device_frames:
            device = controls.get('connect_button').device
            channel = controls.get('channel')
            info = getattr(controls.get('connect_button'), 'info', None)
            
            try:
                # Create a temporary connection to each device to disconnect it properly
                temp_power_supply = PowerSupply(device)
                
                # Disconnect from the device
                if channel:
                    temp_power_supply.device.write(f'SYST:LOCK OFF (@{channel})')
                else:
                    temp_power_supply.device.write('SYST:LOCK OFF')

                self.log_message("Disconnected device", device, info, channel)

                # Close the temporary connection
                temp_power_supply.device.close()
                
            except Exception as e:
                self.log_message(f"Error disconnecting device: {str(e)}")
        
        # Close the current power supply connection if it exists
        if self.current_power_supply:
            try:
                self.current_power_supply.device.close()
            except:
                pass
            self.current_power_supply = None
        
        # Destroy the window
        self.destroy()

    def clear_devices(self):
        """Clear all devices from the list and reset window size"""
        # Disconnect from all devices that might be connected
        for controls in self.device_frames:
            device = controls.get('connect_button').device
            channel = controls.get('channel')
            info = getattr(controls.get('connect_button'), 'info', None)
            
            try:
                # Create a temporary connection to each device to disconnect it properly
                temp_power_supply = PowerSupply(device)
                
                # Disconnect from the device
                if channel:
                    temp_power_supply.device.write(f'SYST:LOCK OFF (@{channel})')
                else:
                    temp_power_supply.device.write('SYST:LOCK OFF')

                self.log_message("Disconnected device", device, info, channel)

                # Close the temporary connection
                temp_power_supply.device.close()
                
            except Exception as e:
                self.log_message(f"Error disconnecting device: {str(e)}")
            
        # Close the current power supply connection if it exists
        if self.current_power_supply:
            try:
                self.current_power_supply.device.close()
            except:
                pass
            self.current_power_supply = None
            
        # Clear existing devices
        for controls in self.device_frames:
            controls['frame'].destroy()
        self.device_frames.clear()
        self.identified_devices.clear()
        
        # Reset window to initial size
        self.geometry(f"800x{self.initial_height}")
        self.log_message("Device list cleared")

        # Reset search button state
        self.search_button.configure(state="normal")
        self.clear_button.configure(state="disabled")

    def connect_device(self, device, info, channel=None):
        """Connect to the selected power supply"""
        try:
            self.current_power_supply = PowerSupply(device)
            
            # Find the device frame to update status
            device_frame = next(controls for controls in self.device_frames 
                            if controls['connect_button'].device == device and 
                            controls['connect_button'].channel == channel)
            
            if channel:
                self.current_power_supply.device.write(f'SYST:LOCK ON (@{channel})')
            else:
                self.current_power_supply.device.write('SYST:LOCK ON')

            self.log_message("Connected", device, info, channel)
                
            # Update connection status
            device_frame['connection_status'].configure(text="Connected", text_color="Green")

            # Enable all controls
            device_frame['disconnect_button'].configure(state="normal")
            device_frame['overvolt_entry'].configure(state="normal")
            device_frame['set_overvolt_button'].configure(state="normal")
            device_frame['overcurr_entry'].configure(state="normal")
            device_frame['set_overcurr_button'].configure(state="normal")
            device_frame['measure_button'].configure(state="normal")

            
            # Disable connect button while connected
            device_frame['connect_button'].configure(state="disabled")
            
        except Exception as e:
            self.log_message(f"Error connecting to device: {str(e)}")
            if self.current_power_supply:
                self.current_power_supply.device.close()
                self.current_power_supply = None
            
    def disconnect_device(self, device, info, channel=None):
        """Disconnect from the selected power supply"""
        try:
            self.current_power_supply = PowerSupply(device)
            
            # Find the device frame to update status
            device_frame = next(controls for controls in self.device_frames 
                            if controls['connect_button'].device == device and 
                            controls['connect_button'].channel == channel)
                
            if channel:
                self.current_power_supply.device.write(f'SYST:LOCK OFF (@{channel})')
            else:
                self.current_power_supply.device.write('SYST:LOCK OFF')

            self.log_message("Disconnected", device, info, channel)

            # Update connection status
            device_frame['connection_status'].configure(text="Disconnected", text_color="red")

            # Disable all controls except connect button
            device_frame['disconnect_button'].configure(state="disabled")
            device_frame['power_on_button'].configure(state="disabled")
            device_frame['power_off_button'].configure(state="disabled")
            device_frame['voltage_entry'].configure(state="disabled")
            device_frame['set_voltage_button'].configure(state="disabled")
            device_frame['overvolt_entry'].configure(state="disabled")
            device_frame['set_overvolt_button'].configure(state="disabled")
            device_frame['overcurr_entry'].configure(state="disabled")
            device_frame['set_overcurr_button'].configure(state="disabled")
            device_frame['measure_button'].configure(state="disabled")
            
            # Re-enable connect button
            device_frame['connect_button'].configure(state="normal")

            self.current_power_supply.device.close()
            self.current_power_supply = None

        except Exception as e:
            self.log_message(f"Error disconnecting from device: {str(e)}")

    def set_voltage(self, device, voltage_entry, info, channel=None):
        """Set the voltage for the power supply"""
        try:
            # Create a new PowerSupply instance each time to ensure connection
            self.current_power_supply = PowerSupply(device)
            
            voltage = voltage_entry.get()
            if not voltage:
                self.log_message("Please enter a voltage value", device, info, channel)
                return
                
            try:
                voltage_value = float(voltage)
            except ValueError:
                self.log_message("Invalid voltage value", device, info, channel)
                return
                
            if channel:
                self.current_power_supply.device.write(f'VOLT {voltage_value} (@{channel})')
            else:
                self.current_power_supply.device.write(f'VOLT {voltage_value}')

            self.log_message(f"Voltage set to {voltage_value}V", device, info, channel)

        except Exception as e:
            self.log_message(f"Error setting voltage: {str(e)}")
            if self.current_power_supply:
                self.current_power_supply.device.close()
                self.current_power_supply = None

    def set_overvoltage(self, device, entry, info, channel=None):
        """Set over voltage protection"""
        try:
            # Create a new PowerSupply instance each time to ensure connection
            self.current_power_supply = PowerSupply(device)
            
            overvolt = entry.get()
            if not overvolt:
                self.log_message("Please enter an overvoltage value", device, info, channel)
                return
                
            try:
                overvolt_value = float(overvolt)
            except ValueError:
                self.log_message("Invalid overvoltage value", device, info, channel)
                return

            try:                
                if channel:
                    self.current_power_supply.device.write(f'VOLT:PROT {overvolt_value} (@{channel})')
                else:
                    self.current_power_supply.device.write(f'VOLT:PROT {overvolt_value}')
                
                self.log_message(f"Overvoltage protection set to {overvolt_value}V", device, info, channel)
                
            except Exception as e:
                self.log_message(f"Failed to set OVP: {str(e)}", device, info, channel)
                return

            # Update protection settings tracking
            device_key = f"{device}_{channel}" if channel else device
            if device_key not in self.protection_settings:
                self.protection_settings[device_key] = {"ovp": False, "ocp": False}
            
            self.protection_settings[device_key]["ovp"] = True

            for device_frame in self.device_frames:
                if (device_frame['connect_button'].device == device and 
                    device_frame['connect_button'].channel == channel):
                    device_frame['ovp_status'].configure(text="OVP Set", text_color="green")
                    break

            # Check if both protections are set
            if self.protection_settings[device_key]["ovp"] and self.protection_settings[device_key]["ocp"]:
                # Find the device frame
                device_frame = next(controls for controls in self.device_frames 
                            if controls['connect_button'].device == device and 
                            controls['connect_button'].channel == channel)
                
                # Enable voltage controls
                device_frame['voltage_entry'].configure(state="normal")
                device_frame['set_voltage_button'].configure(state="normal")
                
                self.log_message("Protection limits set. Voltage control enabled.", device, info, channel) 

        except Exception as e:
            self.log_message(f"Error setting over voltage protection: {str(e)}")
            if self.current_power_supply:
                self.current_power_supply.device.close()
                self.current_power_supply = None

    def set_overcurrent(self, device, entry, info, channel=None):
        """Set over current protection"""
        try:
            # Create a new PowerSupply instance each time to ensure connection
            self.current_power_supply = PowerSupply(device)
            
            overcurr = entry.get()
            if not overcurr:
                self.log_message("Please enter an overcurrent value", device, info, channel)
                return
                
            try:
                overcurr_value = float(overcurr)
            except ValueError:
                self.log_message("Invalid overcurrent value", device, info, channel)
                return

            try:    
                if channel:
                    self.current_power_supply.device.write(f'CURR:PROT {overcurr_value} (@{channel})')
                else:
                    self.current_power_supply.device.write(f'CURR:PROT {overcurr_value}')
                self.log_message(f"Overcurrent protection set to {overcurr_value}A", device, info, channel)

            except Exception as e:
                self.log_message(f"Failed to set OCP: {str(e)}", device, info, channel)
                return

            # Update protection settings tracking
            device_key = f"{device}_{channel}" if channel else device
            if device_key not in self.protection_settings:
                self.protection_settings[device_key] = {"ovp": False, "ocp": False}
            
            self.protection_settings[device_key]["ocp"] = True

            for device_frame in self.device_frames:
                if (device_frame['connect_button'].device == device and 
                    device_frame['connect_button'].channel == channel):
                    device_frame['ocp_status'].configure(text="OCP Set", text_color="green")
                    break

            # Check if both protections are set
            if self.protection_settings[device_key]["ovp"] and self.protection_settings[device_key]["ocp"]:
                # Find the device frame
                device_frame = next(controls for controls in self.device_frames 
                            if controls['connect_button'].device == device and 
                            controls['connect_button'].channel == channel)
                
                # Enable voltage controls
                device_frame['voltage_entry'].configure(state="normal")
                device_frame['set_voltage_button'].configure(state="normal")
                
                self.log_message("Protection limits set. Voltage control enabled.", device, info, channel) 

        except Exception as e:
            self.log_message(f"Error setting over current protection: {str(e)}")
            if self.current_power_supply:
                self.current_power_supply.device.close()
                self.current_power_supply = None

    def power_on(self, device, info, channel=None):
        """Turn on the power supply output"""
        try:
            # Create a new PowerSupply instance each time to ensure connection
            self.current_power_supply = PowerSupply(device)
            
            # Find the device frame to update status
            device_frame = next(controls for controls in self.device_frames 
                            if controls['connect_button'].device == device and 
                            controls['connect_button'].channel == channel)
            
            if channel:
                self.current_power_supply.device.write(f'OUTP ON (@{channel})')
            else:
                self.current_power_supply.device.write('OUTP ON')
                
            self.log_message("Power output turned ON", device, info, channel)
                
            # Update power status indicator
            device_frame['power_status'].configure(text="Power ON", text_color="Green")
            device_frame['power_on_button'].configure(state="disabled")
            device_frame['power_off_button'].configure(state="normal")
            
        except Exception as e:
            self.log_message(f"Error turning power on: {str(e)}")
            if self.current_power_supply:
                self.current_power_supply.device.close()
                self.current_power_supply = None
    
    def power_off(self, device, info, channel=None):
        """Turn off the power supply output"""
        try:
            # Create a new PowerSupply instance each time to ensure connection
            self.current_power_supply = PowerSupply(device)
            
            # Find the device frame to update status
            device_frame = next(controls for controls in self.device_frames 
                            if controls['connect_button'].device == device and 
                            controls['connect_button'].channel == channel)
            
            if channel:
                self.current_power_supply.device.write(f'OUTP OFF (@{channel})')
            else:
                self.current_power_supply.device.write('OUTP OFF')

            self.log_message("Power output turned OFF", device, info, channel) 

            # Update power status indicator
            device_frame['power_status'].configure(text="Power OFF", text_color="red")
            device_frame['power_on_button'].configure(state="normal")
            device_frame['power_off_button'].configure(state="disabled")
            
        except Exception as e:
            self.log_message(f"Error turning power off: {str(e)}")
            if self.current_power_supply:
                self.current_power_supply.device.close()
                self.current_power_supply = None

    def measure_values(self, device, info, channel=None):
        """Measure and display voltage, current and power values"""
        try:
            # Find the device frame to update measurements
            device_frame = next(controls for controls in self.device_frames 
                            if controls['connect_button'].device == device and 
                            controls['connect_button'].channel == channel)
            
            # Make sure we have a connection
            if not self.current_power_supply or self.current_power_supply.device is None:
                self.current_power_supply = PowerSupply(device)
            
            # Query measurements based on device type
            if channel:
                voltage = self.current_power_supply.device.query(f'MEAS:VOLT? (@{channel})').strip()
                current = self.current_power_supply.device.query(f'MEAS:CURR? (@{channel})').strip()
                power = self.current_power_supply.device.query(f'MEAS:POW? (@{channel})').strip()
            else:
                voltage = self.current_power_supply.device.query('MEAS:VOLT?').strip()
                current = self.current_power_supply.device.query('MEAS:CURR?').strip()
                power = self.current_power_supply.device.query('MEAS:POW?').strip()

            # Update measurement labels
            device_frame['voltage_measure_label'].configure(text=f"Voltage: {voltage}")
            device_frame['current_measure_label'].configure(text=f"Current: {current}")
            device_frame['power_measure_label'].configure(text=f"Power: {power}")
            
            self.log_message(f"Measured: {voltage}, {current}, {power}", device, info, channel)
            
        except Exception as e:
            self.log_message(f"Error measuring values: {str(e)}")

if __name__ == "__main__":
    app = AlimentationTool()
    app.mainloop()
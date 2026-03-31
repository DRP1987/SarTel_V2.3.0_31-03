"""PCAN driver interface for CAN bus communication."""

import sys
import os
import can
import threading
import time
from typing import Optional, Callable, List
from PyQt5.QtCore import QObject, pyqtSignal

# Setup DLL search paths for PyInstaller
if hasattr(sys, '_MEIPASS'):
    print(f"DEBUG: Running from PyInstaller bundle:  {sys._MEIPASS}")
    
    pcan_paths = [
        sys._MEIPASS,
        r'C:\Windows\System32',
        r'C:\Windows\SysWOW64',
    ]
    
    for path in pcan_paths: 
        if os.path.exists(path):
            try:
                if hasattr(os, 'add_dll_directory'):
                    os.add_dll_directory(path)
                    print(f"DEBUG: Added DLL directory: {path}")
            except Exception as e:
                print(f"DEBUG: Could not add DLL directory {path}: {e}")

# Try to import PCANBasic for low-level channel detection
try:
    from PCANBasic import *
    PCAN_BASIC_AVAILABLE = True
    print("DEBUG: PCANBasic imported successfully")
except ImportError as e:
    PCAN_BASIC_AVAILABLE = False
    print(f"DEBUG: PCANBasic not available: {e}")

# Default bitrate for channel detection
DETECTION_BITRATE = 500000


class PCANInterface(QObject):
    """Interface for PCAN CAN bus communication."""

    # Qt signals for thread-safe communication
    message_received = pyqtSignal(object)  # Emits CAN message
    error_occurred = pyqtSignal(str)  # Emits error message

    def __init__(self):
        """Initialize PCAN interface."""
        super().__init__()
        self.bus: Optional[can.Bus] = None
        self.running = False
        self. receive_thread: Optional[threading. Thread] = None
        self. current_baudrate: Optional[int] = None

    @staticmethod
    def get_available_channels() -> List[str]:
        """
        Detect available PCAN channels.

        Returns:
            List of available PCAN channel names (e.g., ['PCAN_USBBUS1', 'PCAN_USBBUS2'])
        """
        print("DEBUG: Starting channel detection...")
        
        # Method 1: Try PCANBasic low-level detection (more reliable in PyInstaller)
        if PCAN_BASIC_AVAILABLE:
            try:
                print("DEBUG: Using PCANBasic for channel detection")
                return PCANInterface._detect_channels_pcanbasic()
            except Exception as e:
                print(f"DEBUG: PCANBasic detection failed: {e}")
                # Fall through to python-can method
        
        # Method 2: Fall back to python-can detection
        print("DEBUG: Using python-can for channel detection")
        return PCANInterface._detect_channels_pythoncan()
    
    @staticmethod
    def _detect_channels_pcanbasic() -> List[str]:
        """
        Detect channels using low-level PCANBasic API.
        More reliable in PyInstaller executables.
        """
        available_channels = []
        
        try:
            pcan = PCANBasic()
            print("DEBUG: PCANBasic instance created")
            
            # Channels to test
            channels_to_test = [
                (PCAN_USBBUS1, 'PCAN_USBBUS1'),
                (PCAN_USBBUS2, 'PCAN_USBBUS2'),
                (PCAN_USBBUS3, 'PCAN_USBBUS3'),
                (PCAN_USBBUS4, 'PCAN_USBBUS4'),
                (PCAN_USBBUS5, 'PCAN_USBBUS5'),
                (PCAN_USBBUS6, 'PCAN_USBBUS6'),
                (PCAN_USBBUS7, 'PCAN_USBBUS7'),
                (PCAN_USBBUS8, 'PCAN_USBBUS8'),
            ]
            
            for channel, channel_name in channels_to_test:
                try: 
                    # Use GetValue with PCAN_CHANNEL_CONDITION
                    result = pcan.GetValue(channel, PCAN_CHANNEL_CONDITION)
                    
                    print(f"DEBUG: {channel_name} - result code: {result[0]}, condition: {result[1]}")
                    
                    # Check if call succeeded and channel is available
                    if result[0] == PCAN_ERROR_OK: 
                        # Check the AVAILABLE bit
                        if (result[1] & PCAN_CHANNEL_AVAILABLE) != 0:
                            print(f"DEBUG: ✅ {channel_name} is available")
                            available_channels.append(channel_name)
                        else:
                            print(f"DEBUG: ❌ {channel_name} not available (condition={result[1]})")
                    else:
                        print(f"DEBUG: ❌ {channel_name} GetValue failed (error={result[0]})")
                        
                except Exception as e:
                    print(f"DEBUG: {channel_name} exception: {e}")
            
            print(f"DEBUG:  PCANBasic detection found:  {available_channels}")
            return available_channels
            
        except Exception as e: 
            print(f"DEBUG: PCANBasic detection error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def _detect_channels_pythoncan() -> List[str]:
        """
        Detect channels using python-can library.
        Original detection method (fallback).
        """
        available_channels = []
        potential_channels = [f'PCAN_USBBUS{i}' for i in range(1, 9)]
        
        for channel in potential_channels: 
            bus = None
            try: 
                # Try to initialize the channel with a common bitrate
                bus = can.Bus(
                    interface='pcan',
                    channel=channel,
                    bitrate=DETECTION_BITRATE
                )
                # If successful, channel is available
                available_channels. append(channel)
                print(f"DEBUG: ✅ {channel} available (python-can)")
            except Exception as e:
                # Channel not available
                print(f"DEBUG: ❌ {channel} not available (python-can): {e}")
            finally:
                # Always cleanup
                if bus:
                    try:
                        bus. shutdown()
                    except Exception: 
                        pass
        
        print(f"DEBUG: python-can detection found: {available_channels}")
        return available_channels

    def connect(self, channel: str = 'PCAN_USBBUS1', baudrate: int = 500000) -> bool:
        """
        Connect to PCAN interface. 

        Args:
            channel:  PCAN channel name
            baudrate: CAN bus baud rate

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.bus = can.Bus(
                interface='pcan',
                channel=channel,
                bitrate=baudrate
            )
            self.current_baudrate = baudrate
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to connect: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from PCAN interface."""
        self.stop_receiving()
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception as e: 
                self.error_occurred. emit(f"Error during disconnect:  {str(e)}")
            finally:
                self.bus = None

    def start_receiving(self):
        """Start receiving CAN messages in background thread."""
        if not self.bus:
            self.error_occurred.emit("Not connected to CAN bus")
            return

        if self.running:
            return

        self. running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

    def stop_receiving(self):
        """Stop receiving CAN messages."""
        self.running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
            self.receive_thread = None

    def _receive_loop(self):
        """Background thread loop for receiving CAN messages."""
        while self.running and self.bus:
            try:
                message = self.bus.recv(timeout=0.1)
                if message:
                    self.message_received.emit(message)
            except Exception as e:
                if self.running:  # Only emit error if still running
                    self.error_occurred.emit(f"Error receiving message: {str(e)}")
                    time.sleep(0.1)

    def send_message(self, can_id: int, data:  List[int]) -> bool:
        """
        Send a CAN message.

        Args:
            can_id: CAN message ID
            data: CAN message data bytes (up to 8 bytes)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.bus:
            self.error_occurred.emit("Not connected to CAN bus")
            return False

        try:
            message = can. Message(
                arbitration_id=can_id,
                data=data,
                is_extended_id=False
            )
            self.bus.send(message)
            return True
        except Exception as e:
            self. error_occurred.emit(f"Failed to send message: {str(e)}")
            return False

    def detect_baudrate(self, channel: str = 'PCAN_USBBUS1', 
                       callback: Optional[Callable[[int], None]] = None) -> Optional[int]:
        """
        Auto-detect CAN bus baud rate. 

        Args:
            channel:  PCAN channel name
            callback:  Optional callback function for progress updates

        Returns:
            Detected baud rate or None if detection failed
        """
        common_baudrates = [125000, 250000, 500000, 1000000]

        for baudrate in common_baudrates:
            if callback:
                callback(baudrate)

            bus = None
            try:
                # Try to connect at this baud rate
                bus = can.Bus(
                    interface='pcan',
                    channel=channel,
                    bitrate=baudrate
                )

                # Listen for messages for 2 seconds
                message_count = 0
                start_time = time.time()
                timeout = 2.0

                while time. time() - start_time < timeout:
                    message = bus. recv(timeout=0.1)
                    if message:
                        message_count += 1
                        # If we receive at least 2 valid messages, consider it successful
                        if message_count >= 2:
                            return baudrate

            except Exception as e:
                # This baud rate failed, try next one
                continue
            finally:
                # Always cleanup bus connection
                if bus: 
                    try:
                        bus.shutdown()
                    except Exception:
                        pass

        return None

    def is_connected(self) -> bool:
        """
        Check if connected to CAN bus.

        Returns:
            True if connected, False otherwise
        """
        return self.bus is not None
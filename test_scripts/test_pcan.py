"""Test PCAN detection."""

import sys
import os

print(f"Python:  {sys.version}")
print(f"Working dir: {os.getcwd()}")
print(f"Running as exe: {hasattr(sys, '_MEIPASS')}")

if hasattr(sys, '_MEIPASS'):
    print(f"Temp dir: {sys._MEIPASS}")

print("\n--- Testing PCAN Import ---")
try:
    from PCANBasic import *
    print("✅ PCANBasic imported successfully")
    
    # Try to create interface
    pcan = PCANBasic()
    print("✅ PCANBasic instance created")
    
    # Try to get available channels
    print("\n--- Testing Channel Detection ---")
    
    channels_to_test = [
        (PCAN_USBBUS1, "PCAN_USBBUS1"),
        (PCAN_USBBUS2, "PCAN_USBBUS2"),
        (PCAN_USBBUS3, "PCAN_USBBUS3"),
        (PCAN_USBBUS4, "PCAN_USBBUS4"),
        (PCAN_USBBUS5, "PCAN_USBBUS5"),
        (PCAN_USBBUS6, "PCAN_USBBUS6"),
        (PCAN_USBBUS7, "PCAN_USBBUS7"),
        (PCAN_USBBUS8, "PCAN_USBBUS8"),
    ]
    
    available = []
    for channel, channel_name in channels_to_test:
        try:
            result = pcan. GetValue(channel, PCAN_CHANNEL_CONDITION)
            if result[0] == PCAN_ERROR_OK: 
                if result[1] & PCAN_CHANNEL_AVAILABLE:
                    available.append(channel_name)
                    print(f"✅ Found:  {channel_name}")
        except Exception as e: 
            print(f"⚠️  Error checking {channel_name}: {e}")
    
    if available:
        print(f"\n✅ Total channels found: {len(available)}")
        print(f"Channels: {available}")
    else:
        print("\n❌ No PCAN channels found")
        print("\nPossible reasons:")
        print("- PCAN device not connected")
        print("- PCAN drivers not installed")
        print("- Device in use by another application")
        print("\nTry:")
        print("- Connect PCAN USB device")
        print("- Run PCAN-View to verify device works")
        
except ImportError as e:
    print(f"❌ Failed to import PCANBasic:  {e}")
    print("\nPCANBasic module not found.")
    print("Install with: pip install python-can")
    
except Exception as e: 
    print(f"❌ Error:  {e}")
    import traceback
    traceback.print_exc()

print("\n--- Press Enter to exit ---")
input()
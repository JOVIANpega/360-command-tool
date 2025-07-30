# Test all imports
try:
    import tkinter as tk
    print("✓ tkinter OK")
except Exception as e:
    print(f"✗ tkinter error: {e}")

try:
    import serial
    print("✓ serial OK")
except Exception as e:
    print(f"✗ serial error: {e}")

try:
    import json
    print("✓ json OK")
except Exception as e:
    print(f"✗ json error: {e}")

try:
    import threading
    print("✓ threading OK")
except Exception as e:
    print(f"✗ threading error: {e}")

try:
    from config_core import load_setup
    print("✓ config_core OK")
except Exception as e:
    print(f"✗ config_core error: {e}")

try:
    from ui_parts.ui_main import MainUI
    print("✓ ui_main OK")
except Exception as e:
    print(f"✗ ui_main error: {e}")

print("Import test complete")
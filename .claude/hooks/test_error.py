#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
import sys
import traceback

# Try importing the way send_event.py does
try:
    from utils.summarizer import generate_event_summary
    print("✓ Import successful")
except ModuleNotFoundError as e:
    print(f"✗ ModuleNotFoundError: {e}")
    traceback.print_exc()
except ImportError as e:
    print(f"✗ ImportError: {e}")
    traceback.print_exc()

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
import sys
sys.path.insert(0, '/Users/rivero/ai/agentic-mas/.claude/hooks')
try:
    from utils.summarizer import generate_event_summary
    print("✓ summarizer import works")
except ImportError as e:
    print(f"✗ summarizer import failed: {e}")

try:
    from utils.model_extractor import get_model_from_transcript
    print("✓ model_extractor import works")
except ImportError as e:
    print(f"✗ model_extractor import failed: {e}")

"""Exact sanitized page. Does not rebuild a preview from the generator.

The path argument is the page under test. Its bytes are hashed before and after.
A build clock is whatever that file already prints, not a hardcoded older snapshot.
"""
import runpy
import sys
from pathlib import Path

target = Path(__file__).with_name("test_e1rm_exact.py")
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")

"""Pytest configuration: make the project root importable and its layout stable.

``wordcount.py`` sits at the project root; tests import it directly and drive the
real command line through a subprocess, so the root must be on ``sys.path`` no
matter how pytest is invoked.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

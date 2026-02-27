"""CyberShield package metadata."""

from cybershield.api import create_app
from cybershield.core.scanner_engine import ScannerEngine

__version__ = "0.1.0"
__author__ = "CyberShield Team"

__all__ = ["create_app", "ScannerEngine", "__version__", "__author__"]


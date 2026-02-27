"""
CyberShield - Unified Cybersecurity Platform
Main entry point for the application
"""

__version__ = "0.1.0"
__author__ = "CyberShield Team"

from cybershield.api.app import create_app
from cybershield.core.scanner_engine import ScannerEngine

__all__ = ["create_app", "ScannerEngine"]

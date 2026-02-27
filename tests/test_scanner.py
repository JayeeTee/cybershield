"""
Tests for CyberShield
"""
import pytest
from cybershield.core.scanner_engine import ScannerEngine


def test_scanner_engine_init():
    """Test ScannerEngine initialization"""
    engine = ScannerEngine()
    assert engine is not None


def test_version():
    """Test package version"""
    import cybershield
    assert cybershield.__version__ == "0.1.0"


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint"""
    # Will implement when API is built
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

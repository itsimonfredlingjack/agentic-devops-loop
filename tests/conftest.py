"""
Pytest configuration for test suite.
"""
import sys
from pathlib import Path

# Add project root to Python path FIRST
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import app package explicitly to ensure we get the correct one
# This prevents Python from finding document_upload_app/app.py
import app as _app_package
assert hasattr(_app_package, 'create_app'), "Failed to import correct app package"

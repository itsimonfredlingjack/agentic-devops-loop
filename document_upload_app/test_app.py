"""Tests for the document upload Flask application."""

import os
import sys
import pytest
import tempfile
import zipfile
from pathlib import Path
from io import BytesIO
from datetime import datetime
from importlib import reload

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app import app, get_timestamped_filename, allowed_file


@pytest.fixture
def client(tmp_path):
    """Create a test client for the Flask app with fresh upload directory."""
    import shutil

    # Set config
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = tmp_path

    # Ensure directory is empty before test
    upload_path = Path(tmp_path)
    if upload_path.exists():
        for item in upload_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    with app.test_client() as test_client:
        yield test_client

    # Cleanup after test
    app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'


class TestHelperFunctions:
    """Test helper functions."""

    def test_allowed_file_valid_extensions(self):
        """Test that valid file extensions are allowed."""
        from app import allowed_file
        assert allowed_file('document.txt') is True
        assert allowed_file('image.png') is True
        assert allowed_file('photo.jpg') is True
        assert allowed_file('spreadsheet.xlsx') is False

    def test_allowed_file_no_extension(self):
        """Test that files without extensions are rejected."""
        assert allowed_file('filename') is False

    def test_timestamped_filename_format(self):
        """Test that timestamped filename has correct format."""
        result = get_timestamped_filename('test.txt')

        # Should contain original name, timestamp, and extension
        assert 'test' in result
        assert '.txt' in result
        assert '_' in result
        # Should match pattern: name_YYYYMMDD_HHMMSS.ext
        parts = result.split('_')
        assert len(parts) >= 3

    def test_timestamped_filename_includes_date(self):
        """Test that timestamped filename includes current date."""
        result = get_timestamped_filename('document.pdf')
        today = datetime.now().strftime('%Y%m%d')
        assert today in result


class TestMainPage:
    """Test main page rendering."""

    def test_index_page_loads(self, client):
        """Test that the main page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Document Upload' in response.data
        assert b'Glass Morphism' in response.data


class TestFileUpload:
    """Test file upload functionality."""

    def test_upload_valid_file(self, client):
        """Test uploading a valid file."""
        data = {
            'file': (BytesIO(b'test content'), 'test.txt')
        }
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True
        assert 'test' in json_data['filename']
        assert json_data['filename'].endswith('.txt')

    def test_upload_no_file(self, client):
        """Test upload without file returns error."""
        response = client.post('/api/upload', data={})

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data

    def test_upload_empty_filename(self, client):
        """Test upload with empty filename returns error."""
        data = {
            'file': (BytesIO(b'test'), '')
        }
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data

    def test_upload_invalid_file_type(self, client):
        """Test uploading invalid file type returns error."""
        data = {
            'file': (BytesIO(b'test'), 'test.exe')
        }
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'File type not allowed' in json_data['error']

    def test_filename_includes_timestamp(self, client):
        """Test that uploaded filename includes timestamp."""
        data = {
            'file': (BytesIO(b'test content'), 'document.txt')
        }
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        json_data = response.get_json()
        filename = json_data['filename']

        # Extract timestamp pattern
        assert '_' in filename
        parts = filename.replace('.txt', '').split('_')
        # Should have format: name_YYYYMMDD_HHMMSS
        assert len(parts) >= 3


class TestFileOperations:
    """Test file listing and download operations."""

    def test_list_files_empty(self, client):
        """Test listing files when none exist."""
        response = client.get('/api/files')

        assert response.status_code == 200
        files = response.get_json()
        assert files == []

    def test_list_files_with_files(self, client):
        """Test listing uploaded files."""
        # Upload a file first
        data = {
            'file': (BytesIO(b'test content'), 'test.txt')
        }
        client.post('/api/upload', data=data, content_type='multipart/form-data')

        # List files
        response = client.get('/api/files')
        assert response.status_code == 200
        files = response.get_json()

        assert len(files) > 0
        assert 'name' in files[0]
        assert 'size' in files[0]
        assert 'modified' in files[0]

    def test_download_existing_file(self, client):
        """Test downloading an existing file."""
        # Upload a file first
        upload_data = {
            'file': (BytesIO(b'test content for download'), 'download_test.txt')
        }
        upload_response = client.post('/api/upload', data=upload_data,
                                     content_type='multipart/form-data')
        filename = upload_response.get_json()['filename']

        # Download the file
        response = client.get(f'/api/download/{filename}')
        assert response.status_code == 200
        assert b'test content for download' in response.data

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist."""
        response = client.get('/api/download/nonexistent.txt')

        assert response.status_code == 404
        json_data = response.get_json()
        assert 'File not found' in json_data['error']


class TestExport:
    """Test export functionality."""

    def test_export_no_files(self, client):
        """Test export when no files exist."""
        response = client.post('/api/export')

        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data

    def test_export_with_files(self, client):
        """Test exporting files as zip."""
        # Upload multiple files
        for i in range(2):
            data = {
                'file': (BytesIO(f'content {i}'.encode()), f'file{i}.txt')
            }
            client.post('/api/upload', data=data, content_type='multipart/form-data')

        # Export files
        response = client.post('/api/export')

        assert response.status_code == 200
        assert response.content_type == 'application/zip'

        # Verify zip contents
        zip_buffer = BytesIO(response.data)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            names = zip_file.namelist()
            assert len(names) == 2
            # Files should have timestamps in names
            for name in names:
                assert '_' in name


class TestSecurityAndErrorHandling:
    """Test security and error handling."""

    def test_directory_traversal_prevention(self, client):
        """Test that directory traversal attacks are prevented."""
        response = client.get('/api/download/../../etc/passwd')

        assert response.status_code == 404

    def test_large_file_handling(self, client):
        """Test handling of large files (respects MAX_FILE_SIZE)."""
        # Create a file larger than the limit
        large_content = b'x' * (51 * 1024 * 1024)  # 51MB (over 50MB limit)
        data = {
            'file': (BytesIO(large_content), 'large.txt')
        }

        response = client.post('/api/upload', data=data, content_type='multipart/form-data')

        # Should fail due to size limit
        assert response.status_code == 413  # Request entity too large

    def test_special_characters_in_filename(self, client):
        """Test handling of special characters in filenames."""
        data = {
            'file': (BytesIO(b'test'), 'file with spaces & special@chars.txt')
        }
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        json_data = response.get_json()
        # Filename should be sanitized
        assert json_data['success'] is True


class TestIntegration:
    """Integration tests."""

    def test_full_workflow(self, client):
        """Test complete workflow: upload, list, download, export."""
        # 1. Upload a file
        upload_data = {
            'file': (BytesIO(b'integration test content'), 'integration_test.txt')
        }
        upload_response = client.post('/api/upload', data=upload_data,
                                     content_type='multipart/form-data')
        assert upload_response.status_code == 200
        filename = upload_response.get_json()['filename']

        # 2. List files
        list_response = client.get('/api/files')
        assert list_response.status_code == 200
        files = list_response.get_json()
        assert len(files) > 0

        # 3. Download the file
        download_response = client.get(f'/api/download/{filename}')
        assert download_response.status_code == 200
        assert b'integration test content' in download_response.data

        # 4. Export files
        export_response = client.post('/api/export')
        assert export_response.status_code == 200
        assert export_response.content_type == 'application/zip'

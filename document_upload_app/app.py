"""Document upload Flask application with glass morphism design."""

import os
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

DEFAULT_UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
app.config['UPLOAD_FOLDER'] = DEFAULT_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
DEFAULT_UPLOAD_FOLDER.mkdir(exist_ok=True)


def get_upload_folder() -> Path:
    """Get the current upload folder from app config."""
    return Path(app.config.get('UPLOAD_FOLDER', DEFAULT_UPLOAD_FOLDER))


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_timestamped_filename(original_filename: str) -> str:
    """Generate filename with current date and time."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(original_filename)
    secure_name = secure_filename(name)
    return f"{secure_name}_{timestamp}{ext}"


@app.route('/')
def index():
    """Render the main upload page."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Generate timestamped filename
    timestamped_name = get_timestamped_filename(file.filename)
    upload_folder = get_upload_folder()
    filepath = upload_folder / timestamped_name

    try:
        file.save(str(filepath))
        return jsonify({
            'success': True,
            'filename': timestamped_name,
            'message': f'File uploaded successfully: {timestamped_name}'
        }), 200
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/files', methods=['GET'])
def list_files():
    """List all uploaded files."""
    files = []
    upload_folder = get_upload_folder()
    if upload_folder.exists():
        for file_path in upload_folder.glob('*'):
            if file_path.is_file():
                files.append({
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
    return jsonify(files), 200


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename: str):
    """Download a file."""
    # Security: prevent directory traversal
    safe_filename = secure_filename(filename)
    upload_folder = get_upload_folder()
    filepath = upload_folder / safe_filename

    if not filepath.exists() or not filepath.is_file():
        return jsonify({'error': 'File not found'}), 404

    try:
        return send_file(str(filepath), as_attachment=True, download_name=safe_filename)
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@app.route('/api/export', methods=['POST'])
def export_files():
    """Export all files as a zip archive."""
    import zipfile
    import io

    # Check if folder exists and has files
    upload_folder = get_upload_folder()
    files = []
    if upload_folder.exists():
        files = [f for f in upload_folder.glob('*') if f.is_file()]

    if not files:
        return jsonify({'error': 'No files to export'}), 400

    try:
        # Create zip in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in files:
                zip_file.write(file_path, arcname=file_path.name)

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'documents_export_{timestamp}.zip'
        )
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

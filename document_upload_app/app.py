"""Flask application for document upload with glass morphism design."""
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size


def format_filename(original_filename: str) -> str:
    """Format filename with current date.

    Args:
        original_filename: Original filename from upload

    Returns:
        Formatted filename with date prefix (YYYYMMDD_originalname)
    """
    date_str = datetime.now().strftime("%Y%m%d")
    # Split filename and extension
    name_part = Path(original_filename).stem
    ext_part = Path(original_filename).suffix
    return f"{date_str}_{name_part}{ext_part}"


@app.route('/')
def index():
    """Serve the main upload page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file:
        # Format the filename with date
        formatted_name = format_filename(file.filename)
        filepath = app.config['UPLOAD_FOLDER'] / formatted_name
        file.save(str(filepath))

        return jsonify({
            'success': True,
            'filename': formatted_name,
            'path': str(filepath)
        }), 200

    return jsonify({'error': 'Upload failed'}), 500


@app.route('/export', methods=['GET'])
def export():
    """Export uploaded files (placeholder)."""
    # This endpoint exists for the export functionality
    # Actual implementation depends on what format/action is needed
    uploads = list(app.config['UPLOAD_FOLDER'].glob('*'))
    files = [f.name for f in uploads if f.is_file()]
    return jsonify({'files': files}), 200


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)

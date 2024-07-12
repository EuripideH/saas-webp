import os
from flask import Flask, request, render_template, send_file, after_this_request
from werkzeug.utils import secure_filename
from PIL import Image
import io
import zipfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

ALLOWED_EXTENSIONS = {'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('index.html', error='No file part')
        file = request.files['file']
        if file.filename == '':
            return render_template('index.html', error='No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Convert the image
            converted_files = convert_image(filepath)
            
            # Create a zip file containing all converted images
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w') as zf:
                for fmt, img_bytes in converted_files.items():
                    zf.writestr(f"{os.path.splitext(filename)[0]}.{fmt}", img_bytes.getvalue())
            memory_file.seek(0)
            
            @after_this_request
            def remove_file(response):
                os.remove(filepath)
                return response
            
            return send_file(memory_file, mimetype='application/zip', 
                             as_attachment=True, download_name='converted_images.zip')
        else:
            return render_template('index.html', error='Invalid file type. Please upload a WebP image.')
    return render_template('index.html')

def convert_image(filepath):
    converted_files = {}
    with Image.open(filepath) as img:
        for fmt in ['JPEG', 'PNG', 'GIF']:
            img_io = io.BytesIO()
            if fmt == 'JPEG':
                # Convert to RGB mode for JPEG
                img.convert('RGB').save(img_io, format=fmt)
            else:
                img.save(img_io, format=fmt)
            img_io.seek(0)
            converted_files[fmt.lower()] = img_io
    return converted_files

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
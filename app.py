from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
import os
from zipfile import ZipFile
import shutil
import zlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Upload and download folders
UPLOAD_FOLDER = os.path.abspath('uploads')
DOWNLOAD_FOLDER = os.path.abspath('Download_folder')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# Create the upload and download folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

def compress_files():
    with ZipFile(os.path.join(app.config['DOWNLOAD_FOLDER'], 'compressed.zip'), 'w') as zip:
        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
            for file in files:
                zip.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), app.config['UPLOAD_FOLDER']))
    
    # Move compressed file to DOWNLOAD_FOLDER
    shutil.move(os.path.join(app.config['UPLOAD_FOLDER'], 'compressed.zip'), os.path.join(app.config['DOWNLOAD_FOLDER'], 'compressed.zip'))
    socketio.emit('compression_complete')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'fileToCompress[]' not in request.files:
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    files = request.files.getlist('fileToCompress[]')
    
    if not files:
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    for file in files:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    # Appeler la fonction compress_folder pour compresser les fichiers téléchargés
    compress_folder(app.config['UPLOAD_FOLDER'])
    
    return jsonify({'success': 'Fichiers téléchargés, compressés et téléchargés avec succès.'})

@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

def compress_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.jpeg') or filename.endswith('.png') or filename.endswith('.mp4'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'rb') as f:
                data = f.read()
            compressed_data = zlib.compress(data)
            compressed_file_path = os.path.join(folder_path, filename + '.compressed')
            with open(compressed_file_path, 'wb') as f:
                f.write(compressed_data)

if __name__ == "__main__":
    socketio.run(app)

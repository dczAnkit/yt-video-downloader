
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import yt_dlp
import os
import uuid
import tempfile
import shutil


app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-key'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Allowed extensions for cookies file
ALLOWED_EXTENSIONS = {'txt', 'cookies'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        mode = request.form.get('mode')
        cookies_file = request.files.get('cookies')
        if not url:
            flash('Please enter a YouTube URL.', 'error')
            return redirect(url_for('index'))
        file_id = str(uuid.uuid4())
        temp_cookies_path = None
        try:
            # Save cookies file if provided
            if cookies_file and cookies_file.filename != '' and allowed_file(cookies_file.filename):
                temp_dir = tempfile.mkdtemp()
                temp_cookies_path = os.path.join(temp_dir, cookies_file.filename)
                cookies_file.save(temp_cookies_path)
            if mode == 'audio':
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            else:
                ydl_opts = {
                    'format': 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': f'{DOWNLOAD_FOLDER}/{file_id}.%(ext)s',
                    'merge_output_format': 'mp4',
                }
            if temp_cookies_path:
                ydl_opts['cookiefile'] = temp_cookies_path
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if mode == 'audio':
                    filename = f"{file_id}.mp3"
                else:
                    filename = f"{file_id}.mp4"
            return redirect(url_for('download_file', filename=filename))
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if 'Sign in to confirm you’re not a bot' in error_msg or 'cookies' in error_msg:
                flash('Download failed: YouTube requires authentication. Please upload your cookies.txt file exported from your browser.', 'error')
            else:
                flash(f'Error: {error_msg}', 'error')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Unexpected error: {str(e)}', 'error')
            return redirect(url_for('index'))
        finally:
            if temp_cookies_path:
                shutil.rmtree(os.path.dirname(temp_cookies_path), ignore_errors=True)
    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    flash('File not found.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

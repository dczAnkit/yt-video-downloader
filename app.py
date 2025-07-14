from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import yt_dlp
import os
import uuid

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-key'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        mode = request.form.get('mode')
        if not url:
            flash('Please enter a YouTube URL.', 'error')
            return redirect(url_for('index'))
        file_id = str(uuid.uuid4())
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
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if mode == 'audio':
                    filename = f"{file_id}.mp3"
                else:
                    filename = f"{file_id}.mp4"
            return redirect(url_for('download_file', filename=filename))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('index'))
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

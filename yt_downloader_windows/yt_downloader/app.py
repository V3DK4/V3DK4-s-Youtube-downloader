from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from yt_dlp import YoutubeDL
from pathlib import Path
import tempfile, shutil, re

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024

@app.get('/')
def home():
    return render_template('index.html')

@app.post('/download')
def download():
    data = request.get_json(silent=True) or {}
    url = str(data.get('url', '')).strip()
    kind = data.get('kind', 'video')
    quality = str(data.get('quality', '720'))
    
    is_yt = re.match(r'https://(www\.|m\.)?youtube\.com/(watch\?v=|shorts/|live/)|^https://youtu\.be/', url, re.I)
    is_tk = re.match(r'https://(www\.|m\.|vm\.|vt\.)?tiktok\.com/', url, re.I)

    if not is_yt and not is_tk:
        return jsonify(error='Adj meg egy érvényes YouTube vagy TikTok linket!'), 400

    if kind not in ('audio', 'video') or quality not in ('360','480','720','1080'):
        return jsonify(error='Hibás formátum vagy minőség.'), 400
        
    folder = Path(tempfile.mkdtemp(prefix='yt_local_'))
    try:
        opts = {
            'outtmpl': str(folder / '%(title).100s.%(ext)s'),
            'noplaylist': True,
            'max_filesize': 500 * 1024 * 1024,
            'quiet': True,
            'no_warnings': True,
            # 'restrictfilenames': True,  <-- Ezt kitöröltem, így megmarad az eredeti cím
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            },
        }
        
        if kind == 'audio':
            opts.update(format='bestaudio/best', postprocessors=[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}])
        else:
            opts.update(format=f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best', merge_output_format='mp4', postprocessors=[{'key':'FFmpegVideoConvertor','preferedformat':'mp4'}])
        
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
            
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ('.mp3' if kind == 'audio' else '.mp4')]
        if not files:
            raise RuntimeError('Nem sikerült elkészíteni a kért fájlt.')
            
        file = max(files, key=lambda p: p.stat().st_size)
        
        @after_this_request
        def cleanup(response):
            response.call_on_close(lambda: shutil.rmtree(folder, ignore_errors=True))
            return response
            
        return send_file(file, as_attachment=True, download_name=file.name)
        
    except Exception as e:
        shutil.rmtree(folder, ignore_errors=True)
        return jsonify(error=f'Letöltési hiba: {str(e)[:300]}'), 400

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)

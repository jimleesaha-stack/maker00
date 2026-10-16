# AI YouTube Video Maker — Samsung Ultra starter

Mobile-first Flask web app that creates illustrated Hindi story slides, optionally adds Hindi narration, renders an MP4 with FFmpeg, and allows preview/download.

## Scope and limitations
- Works without an AI key using built-in starter scripts.
- Optional Gemini API integration generates a new Hindi script when `GEMINI_API_KEY` is set.
- Hindi narration uses gTTS and needs internet access.
- FFmpeg renders the MP4.
- This starter creates slideshow-style illustrated scenes, **not full AI-generated moving cartoon footage**. Background music and direct YouTube upload are not implemented.
- Free hosting can sleep, restrict FFmpeg, or use temporary storage. Download your MP4 after generation.

## Run locally
Requires Python 3.10+ and FFmpeg installed and on PATH.

Windows:
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Mac/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`. To test on the phone over the same Wi-Fi, open `http://COMPUTER-LAN-IP:5000` on the Samsung Ultra.

## Optional AI scripts
Get a key from Google AI Studio and set `GEMINI_API_KEY` in your server environment. Never put the key in browser code. Without the key or if the request fails, the app falls back to built-in scripts.

## Deploy online
1. Push this project to a GitHub repository.
2. Create a Web Service on Render and connect the repository.
3. Use `render.yaml` or build command `pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg fonts-dejavu-core`.
4. Start command: `gunicorn app:app --workers 1 --timeout 300 --bind 0.0.0.0:$PORT`.
5. Optionally add `GEMINI_API_KEY` in the host's environment settings and deploy.
6. Open the HTTPS service URL on the phone. In Chrome/Samsung Internet, browser menu → Add to Home screen.

## Structure
- `app.py`: API, optional script generation, image cards, TTS and FFmpeg render
- `templates/index.html`: mobile UI
- `static/`: PWA metadata
- `outputs/`: temporary generated videos

Before public launch, add authentication, rate limiting, quotas, background jobs, storage cleanup, persistent storage, monitoring, a privacy policy and YouTube OAuth only with explicit user consent.

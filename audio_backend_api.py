# audio_backend_api.py — Smart Sampler API @ sampler.v1su4.com
import os
import tempfile
from robyn import Robyn, Request, jsonify, OpenApi
import librosa
import numpy as np
import collections
from collections.abc import MutableSequence

# madmom (0.16.x) still imports MutableSequence from collections directly.
# Python 3.10+ moved these ABCs to collections.abc, so ensure the attribute exists.
if not hasattr(collections, "MutableSequence"):
    collections.MutableSequence = MutableSequence

import madmom
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions

load_dotenv()

app = Robyn(__file__)

# === SCALAR DOCS[](https://sampler.v1su4.com/docs) ===
app.open_api = OpenApi(
    title="Smart Sampler API",
    version="1.0.0",
    description="Unlimited Serato Sample / Ableton Simpler intelligence @ sampler.v1su4.com",
    license_info="MIT"
)

@app.get("/docs")
async def docs(_: Request):
    return """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <title>Smart Sampler API – sampler.v1su4.com</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@scalar/api-reference@1.0.0/dist/index.css">
      </head>
      <body>
        <script id="api-reference" data-url="/openapi.json"></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference@1.0.0"></script>
      </body>
    </html>
    """

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    raise RuntimeError("Set DEEPGRAM_API_KEY in Coolify secrets!")
dg_client = DeepgramClient(DEEPGRAM_API_KEY)

@app.get("/health")
async def health(_: Request):
    return "Smart Sampler API @ sampler.v1su4.com – ready ✓"

@app.post("/analyze")
async def analyze(request: Request):
    mode = request.query_params.get("mode", "full")   # ?mode=fast or ?mode=full
    file_obj = (await request.files()).get("file")
    url = request.query_params.get("url")

    if not file_obj and not url:
        return jsonify({"error": "Provide 'file' or 'url'"}, status_code=400)

    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    try:
        if file_obj:
            with open(tmp_path, "wb") as f:
                f.write(await file_obj.read())
        else:
            import urllib.request
            urllib.request.urlretrieve(url, tmp_path)

        lyrics_data = {"full_text": "", "words": [], "phrases": []}
        if mode == "full":
            with open(tmp_path, "rb") as f:
                source = {"buffer": f, "mimetype": "audio/mpeg"}
                options = PrerecordedOptions(model="nova-2", smart_format=True, utterances=True, punctuate=True, language="en")
                resp = dg_client.listen.prerecorded.v("1").transcribe_file(source, options)
                alt = resp.results.channels[0].alternatives[0]
                lyrics_data = {
                    "full_text": alt.transcript,
                    "words": [{"word": w.word, "start": round(w.start, 3), "end": round(w.end, 3)} for w in alt.words],
                    "phrases": [{"text": u.transcript.strip(), "start": round(u.start, 3), "end": round(u.end, 3)} 
                                for u in resp.results.utterances] if hasattr(resp.results, "utterances") else []
                }

        # madmom transients
        proc = madmom.features.OnsetPeakPickingProcessor(fps=200, threshold=0.3, combine=0.03)
        act = madmom.features.RNNOnsetProcessor()(tmp_path)
        transients = sorted([round(float(t), 3) for t in proc(act)])

        # Librosa
        y, sr = librosa.load(tmp_path, sr=None, mono=True)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = [round(t, 3) for t in librosa.frames_to_time(beat_frames, sr=sr).tolist()[:300]]

        chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
        key_idx = np.argmax(chroma)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = f"{keys[key_idx]} major" if chroma[key_idx] > chroma[(key_idx + 3) % 12] else f"{keys[(key_idx + 9) % 12]} minor"

        return jsonify({
            "mode": mode,
            "duration_sec": round(librosa.get_duration(filename=tmp_path), 2),
            "tempo_bpm": round(float(tempo), 2),
            "key": key,
            "markers": {"beats_sec": beat_times, "transients_sec": transients},
            "lyrics": lyrics_data
        })

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

print("Smart Sampler API → https://sampler.v1su4.com")
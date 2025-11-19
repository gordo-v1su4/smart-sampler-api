# audio_backend_api.py — Smart Sampler API @ sampler.v1su4.com
import os
import tempfile
from robyn import Robyn, Request, jsonify
from robyn.openapi import OpenAPI, OpenAPIInfo
import librosa
import numpy as np
import madmom
from dotenv import load_dotenv
from deepgram import DeepgramClient

load_dotenv()

app = Robyn(
    file_object=__file__,
    openapi=OpenAPI(
        info=OpenAPIInfo(
            title="Smart Sampler API",
            description="Audio analysis API with beat detection, transient detection, tempo, key detection, and lyrics extraction",
            version="1.0.0",
        )
    )
)

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
dg_client = DeepgramClient(api_key=DEEPGRAM_API_KEY) if DEEPGRAM_API_KEY else None

@app.get("/health")
async def health(request: Request):
    # Robyn headers.get() only takes one argument
    host = request.headers.get("host") or "unknown"
    print(f"Incoming /health from Host: {host}")
    return "Smart Sampler API @ sampler.v1su4.com - ready"

@app.get("/healthz")
async def healthz(_: Request):
    return "ok"

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
            if dg_client is None:
                return jsonify(
                    {"error": "DEEPGRAM_API_KEY not configured on server"},
                    status_code=500,
                )
            with open(tmp_path, "rb") as f:
                buffer_data = f.read()
            resp = dg_client.listen.v1.media.transcribe_file(
                request=buffer_data,
                model="nova-2",
                smart_format=True,
                utterances=True,
                punctuate=True,
                language="en"
            )

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

if __name__ == "__main__":
    # Robyn CLI automatically handles --processes, --workers, etc.
    # app.start() reads ROBYN_HOST and ROBYN_PORT from env vars
    # Default to 0.0.0.0:8080 for Docker if not set
    host = os.getenv("ROBYN_HOST", "0.0.0.0")
    port = int(os.getenv("ROBYN_PORT", "8080"))
    app.start(host=host, port=port)
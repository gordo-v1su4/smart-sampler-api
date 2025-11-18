# audio_backend_api.py — Smart Sampler API (Ableton + Serato + Deepgram)
import os
import tempfile
from robyn import Robyn, Request, jsonify
import librosa
import numpy as np
import madmom
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions

load_dotenv()

app = Robyn(__file__)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not DEEPGRAM_API_KEY:
    raise RuntimeError("Set DEEPGRAM_API_KEY in Coolify secrets!")

dg_client = DeepgramClient(DEEPGRAM_API_KEY)

@app.get("/health")
async def health(_: Request):
    return "Smart Sampler API ready – madmom + Deepgram"

@app.post("/analyze")
async def analyze(request: Request):
    files = await request.files()
    file_obj = files.get("file")
    url = request.query_params.get("url")

    if not file_obj and not url:
        return jsonify({"error": "Provide file or url"}, status_code=400)

    tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    try:
        if file_obj:
            with open(tmp_path, "wb") as f:
                f.write(await file_obj.read())
        else:
            import urllib.request
            urllib.request.urlretrieve(url, tmp_path)

        # DEEPGRAM – words + phrases
        with open(tmp_path, "rb") as f:
            source = {"buffer": f, "mimetype": "audio/mpeg"}
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                utterances=True,
                punctuate=True,
                language="en"
            )
            resp = dg_client.listen.prerecorded.v("1").transcribe_file(source, options)

        alt = resp.results.channels[0].alternatives[0]
        words = [{"word": w.word, "start": round(w.start, 3), "end": round(w.end, 3), "confidence": round(w.confidence, 3)} 
                 for w in alt.words]
        phrases = [{"text": u.transcript.strip(), "start": round(u.start, 3), "end": round(u.end, 3)} 
                   for u in resp.results.utterances] if hasattr(resp.results, "utterances") else []

        # MADMOM – Ableton-quality transients
        proc = madmom.features.OnsetPeakPickingProcessor(fps=200, threshold=0.3, combine=0.03)
        act = madmom.features.RNNOnsetProcessor()(tmp_path)
        transients = proc(act)

        # LIBROSA – tempo, beats, key
        y, sr = librosa.load(tmp_path, sr=None, mono=True)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

        chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
        key_idx = np.argmax(chroma)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = f"{keys[key_idx]} major" if chroma[key_idx] > chroma[(key_idx + 3) % 12] else f"{keys[(key_idx + 9) % 12]} minor"

        return jsonify({
            "duration_sec": round(librosa.get_duration(filename=tmp_path), 2),
            "tempo_bpm": round(float(tempo), 2),
            "key": key,
            "markers": {
                "beats_sec": [round(t, 3) for t in beat_times[:300],
                "transients_sec": sorted([round(float(t), 3) for t in transients]),
            },
            "lyrics": {
                "full_text": alt.transcript,
                "words": words,
                "phrases": phrases
            }
        })

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

print("Smart Sampler API → http://localhost:8080")
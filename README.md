# Smart Sampler API

A high-performance audio analysis API built with Robyn, combining Ableton-quality transient detection (madmom), Deepgram transcription, and librosa audio analysis. Perfect for building smart sampler applications that can detect beats, transients, tempo, key, and extract lyrics from audio files.

## Features

- 🎵 **Beat Detection** - Precise beat tracking using librosa
- 🎹 **Transient Detection** - Ableton-quality transients using madmom
- 🎤 **Lyrics Extraction** - Word-level transcription with Deepgram
- 🎼 **Musical Analysis** - Tempo (BPM) and key detection
- ⚡ **High Performance** - Built with Robyn for blazing-fast responses
- 🐳 **Docker Ready** - One-command deployment with Coolify

## Tech Stack

- **Robyn** - Fast Python web framework
- **madmom** - Music Information Retrieval (transient detection)
- **Deepgram** - Speech-to-text transcription
- **librosa** - Audio analysis (tempo, beats, key)
- **uv** - Lightning-fast Python package manager

## API Documentation

**Interactive API Docs:** `https://sampler.v1su4.com/docs`

The API documentation is available via Scalar API Reference at `/docs`. This provides an interactive interface to explore and test all endpoints directly in your browser.

**OpenAPI Spec:** `https://sampler.v1su4.com/openapi.json`

The OpenAPI specification is available at `/openapi.json` for integration with API clients and tools like Postman, Insomnia, or code generators.

## API Endpoints

**Base URL:** `https://sampler.v1su4.com`

### `GET /health`
Health check endpoint.

**Example:**
```bash
curl https://sampler.v1su4.com/health
```

**Response:**
```
Smart Sampler API @ sampler.v1su4.com - ready
```

### `POST /analyze`
Analyze an audio file for beats, transients, tempo, key, and lyrics.

**Request:**
- **Form Data:** `file` - Audio file (mp3, wav, etc.)
- **Query Parameters:**
  - `url` - URL to audio file (alternative to file upload)
  - `mode` - `fast` (skips Deepgram lyrics) or `full` (includes lyrics, default)

**Examples:**

Upload file:
```bash
curl -F "file=@song.mp3" https://sampler.v1su4.com/analyze | jq
```

Analyze from URL (fast mode):
```bash
curl "https://sampler.v1su4.com/analyze?url=https://example.com/audio.mp3&mode=fast" | jq
```

Analyze from URL (full mode with lyrics):
```bash
curl "https://sampler.v1su4.com/analyze?url=https://example.com/audio.mp3&mode=full" | jq
```

**Response:**
```json
{
  "duration_sec": 180.5,
  "tempo_bpm": 128.0,
  "key": "C major",
  "markers": {
    "beats_sec": [0.0, 0.468, 0.937, ...],
    "transients_sec": [0.123, 0.456, 0.789, ...]
  },
  "lyrics": {
    "full_text": "Complete transcribed text...",
    "words": [
      {
        "word": "hello",
        "start": 0.5,
        "end": 0.8,
        "confidence": 0.95
      }
    ],
    "phrases": [
      {
        "text": "Hello world",
        "start": 0.5,
        "end": 1.2
      }
    ]
  }
}
```

## Deployment

### GitHub Actions + Coolify Auto-Deployment

This project includes GitHub Actions workflows for automated testing and deployment.

#### Setup Instructions

1. **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

2. **Configure Coolify**
   - Go to Coolify → New Resource → Dockerfile
   - Connect your GitHub repository
   - Add `DEEPGRAM_API_KEY` as a secret environment variable
   - Copy the **Webhook URL** from Coolify (found in your resource settings)

3. **Add GitHub Secret**
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `COOLIFY_WEBHOOK_URL`
   - Value: Paste the webhook URL from Coolify
   - Click "Add secret"

4. **Deploy!**
   - Every push to `main` branch will:
     - ✅ Run tests and linting
     - ✅ Automatically trigger Coolify deployment
   - Check GitHub Actions tab to see deployment status

#### Port Configuration
   - The container listens on port **8080** internally (required for Coolify/Traefik)
   - Configure external port mapping in Coolify settings if needed
   - Use subdomains (e.g., `sampler.yourdomain.com`) for cleaner URLs

#### Manual Deployment (Alternative)

If you prefer manual deployment without GitHub Actions:
   - Just push to GitHub and Coolify will auto-detect changes
   - Or use Coolify's manual "Redeploy" button

### Docker Build (Manual)

```bash
docker build -t smart-sampler-api .
docker run -e DEEPGRAM_API_KEY=your_key smart-sampler-api
```

**Note:** For production deployment, use Coolify which handles port mapping automatically. The API is available at `https://sampler.v1su4.com`.

## Development Workflow

- **CI/CD:** `git push` → GitHub Actions runs tests → Auto-deploys to Coolify with SSL
- **Production:** Automatic deployment on every push to `main` branch
- **API:** Available at `https://sampler.v1su4.com`

### Best Practices
- ✅ Never edit files directly on the server
- ✅ Use Coolify secrets for environment variables
- ✅ Keep Dockerfile and docker-compose.yaml in project root
- ✅ All changes go through Git → GitHub → Coolify auto-deployment

## Project Structure

```
smart-sampler-api/
├── audio_backend_api.py    # Main API application
├── Dockerfile              # Docker configuration
├── docker-compose.yaml     # Docker Compose config (optional)
├── pyproject.toml         # Project dependencies (uv)
├── .gitignore             # Git ignore rules
├── .github/
│   └── workflows/
│       └── deploy.yml     # GitHub Actions CI/CD workflow
├── setup.sh               # Linux setup script
└── README.md              # This file
```

## Dependencies

- `robyn>=0.30.0` - Web framework
- `librosa>=0.10.2` - Audio analysis
- `madmom>=0.16.1` - Transient detection
- `deepgram-sdk>=3.5.0` - Speech-to-text
- `numpy<2.0` - Required for madmom compatibility
- `scipy` - Scientific computing
- `soundfile` - Audio file I/O
- `python-dotenv` - Environment variables
- `python-multipart` - File upload support

## Notes

- **Port 8080:** This is the industry standard for containerized Python services in 2024-2025. Keep it as-is in the code/Dockerfile.
- **numpy<2.0:** Critical constraint - madmom is not yet compatible with numpy 2.x
- **uv:** Lightning-fast package manager that makes development on Windows as fast as Linux

## License

[Add your license here]

## Contributing

##

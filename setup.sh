#!/bin/bash
# Smart Sampler API - Quick Setup Script

echo "🚀 Setting up Smart Sampler API..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    pip install uv
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
uv venv

# Install dependencies
echo "📦 Installing dependencies..."
uv pip install robyn librosa madmom deepgram-sdk python-dotenv python-multipart 'numpy<2' scipy soundfile

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a .env file with your DEEPGRAM_API_KEY"
echo "2. Run: uv run robyn audio_backend_api.py --processes 4"
echo "3. Test: curl http://localhost:8080/health"


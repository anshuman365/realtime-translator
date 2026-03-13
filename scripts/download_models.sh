#!/bin/bash
# Model download script for real-time translator
# This script downloads required Vosk STT models, Piper TTS voices, and prepares HuggingFace models

set -e

echo "=== Real-Time Translator Model Setup ==="
echo ""

# Create model directories
mkdir -p models/vosk models/piper models/huggingface

# Function to download and extract Vosk model
download_vosk_model() {
    local model_name=$1
    local model_url=$2
    
    if [ ! -d "models/vosk/$model_name" ]; then
        echo "Downloading Vosk model: $model_name"
        cd models/vosk
        wget -q --show-progress "$model_url"
        unzip -q "${model_name}.zip"
        rm "${model_name}.zip"
        cd ../..
        echo "✓ $model_name downloaded"
    else
        echo "✓ $model_name already exists"
    fi
}

# Function to download Piper voice
download_piper_voice() {
    local voice_name=$1
    local voice_url=$2
    
    if [ ! -f "models/piper/${voice_name}.onnx" ]; then
        echo "Downloading Piper voice: $voice_name"
        cd models/piper
        wget -q --show-progress "${voice_url}.onnx"
        wget -q --show-progress "${voice_url}.onnx.json"
        cd ../..
        echo "✓ $voice_name downloaded"
    else
        echo "✓ $voice_name already exists"
    fi
}

# Download Vosk models (small models for faster download and inference)
echo ""
echo "--- Downloading Vosk STT Models ---"

# English (US)
download_vosk_model \
    "vosk-model-small-en-us-0.15" \
    "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

# Hindi
download_vosk_model \
    "vosk-model-small-hi-0.22" \
    "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip"

# Spanish
download_vosk_model \
    "vosk-model-small-es-0.42" \
    "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"

# French
download_vosk_model \
    "vosk-model-small-fr-0.22" \
    "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"

# German
download_vosk_model \
    "vosk-model-small-de-0.15" \
    "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip"

# Download Piper TTS voices
echo ""
echo "--- Downloading Piper TTS Voices ---"

# English (US)
download_piper_voice \
    "en_US-lessac-medium" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium"

# Hindi
download_piper_voice \
    "hi_IN-female-medium" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/female/medium/hi_IN-female-medium"

# Spanish
download_piper_voice \
    "es_ES-female-medium" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/female/medium/es_ES-female-medium"

# French  
download_piper_voice \
    "fr_FR-siwis-medium" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium"

# German
download_piper_voice \
    "de_DE-thorsten-medium" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium"

# Note: HuggingFace models will be downloaded automatically on first use
# They will be cached in models/huggingface directory

echo ""
echo "=== Model Setup Complete ==="
echo ""
echo "Note: Translation models from HuggingFace will be downloaded"
echo "automatically on first use. This may take a few minutes on first run."
echo ""

# Speaker Diarization and Transcription (Azure)

## Description

This tool performs speaker diarization and transcription of audio or video files. Speaker diarization identifies individual speakers within an audio file containing conversations or dialogues between two or more people. The tool generates an SRT file with the transcribed dialogue texts, indicating which speaker said each line.

## Features

- **Audio/Video Input**: Supports various media file formats such as MP4, MKV, MOV, and MP3.
- **Audio Extraction**: Extracts audio from video files and converts stereo audio to mono.
- **Azure Blob Storage Integration**: Uploads audio files to Azure Blob Storage and generates a SAS URL for access.
- **Batch Transcription**: Uses Azure Cognitive Services to perform batch transcription with speaker diarization.
- **SRT File Generation**: Creates an SRT file with the dialogue texts, including speaker identification.

## Prerequisites

- Python 3.x
- Azure Cognitive Services Speech API key and region
- Azure Blob Storage account details

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/speaker-diarization-transcription-tool.git
   cd speaker-diarization-transcription-tool
   
## Usage

2. Set your Azure Cognitive Services and Blob Storage credentials in the script:

  ```python
    speech_service_key = "your_speech_service_key"
    speech_service_region = "your_speech_service_region"
    storage_account_name = "your_storage_account_name"
    storage_account_key = "your_storage_account_key"
    storage_container_name = "your_storage_container_name"
    storage_connection_string = "your_storage_connection_string"
  ```

Run the script:
  ```bash
  python diarization_transcription.py
  ```

3. Select the media file using the file dialog that appears.

The tool will process the file, upload the audio to Azure Blob Storage, perform transcription with speaker diarization, and generate an SRT file in the same directory as the media file.

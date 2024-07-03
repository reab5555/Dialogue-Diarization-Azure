import os
import sys
import requests
import json
import moviepy.editor as mp
from moviepy.editor import AudioFileClip
from pydub import AudioSegment
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from datetime import datetime, timedelta
import time
import tkinter as tk
from tkinter import filedialog
import srt


speech_service_key = "speech_service_key"
speech_service_region = "speech_service_region"
storage_account_name = "storage_account_name"
storage_account_key = "storage_account_key"
storage_container_name = "storage_container_name"
storage_connection_string = "storage_connection_string"

language = 'en-US'
# options -> en-US, he-IL, fr-FR, it-IT, sv-SE, ar-IL, zh-CN...
minspeakers = 2
maxspeakers = 2




# Use tkinter to select the video or audio file
root = tk.Tk()
root.withdraw()
media_file_path = filedialog.askopenfilename(title="Select the media file", filetypes=[("Media files", "*.mp4 *.mkv *.mov *.mp3")])
if media_file_path.endswith(('.mkv', '.mp4', '.mov')):
    # Extract audio from video and save it as a stereo WAV file
    stereo_audio_file_path = media_file_path.replace(".mkv", ".wav").replace(".mp4", ".wav").replace(".mov", ".wav")
    video_clip = mp.VideoFileClip(media_file_path)
    video_clip.audio.write_audiofile(stereo_audio_file_path)
    # Convert the stereo WAV file to mono
    audio = AudioSegment.from_wav(stereo_audio_file_path)
    audio_mono = audio.set_channels(1)
    audio_mono_path = stereo_audio_file_path.replace(".wav", "_mono.wav")
    audio_mono.export(audio_mono_path, format="wav")
    # Remove the temporary stereo WAV file
    os.remove(stereo_audio_file_path)
if media_file_path.endswith('.mp3'):
    stereo_audio_file_path = media_file_path.replace(".mp3", ".wav")
    audio_clip = AudioFileClip(media_file_path)
    audio_clip.write_audiofile(stereo_audio_file_path)
    # Convert the stereo WAV file to mono
    audio = AudioSegment.from_wav(stereo_audio_file_path)
    audio_mono = audio.set_channels(1)
    audio_mono_path = stereo_audio_file_path.replace(".wav", "_mono.wav")
    audio_mono.export(audio_mono_path, format="wav")
    # Remove the temporary stereo WAV file
    os.remove(stereo_audio_file_path)
audio_file_name = os.path.basename(audio_mono_path)

print('Uploading the audio file to Azure Blob Storage')
## Upload the mono audio file to Azure Blob Storage
blob_service_client = BlobServiceClient(account_url=f"https://{storage_account_name}.blob.core.windows.net", credential=storage_account_key)
container_client = blob_service_client.get_container_client(storage_container_name)
blob_name = os.path.basename(audio_mono_path)
blob_client = container_client.get_blob_client(blob_name)

with open(audio_mono_path, "rb") as audio_file:
    blob_client.upload_blob(audio_file, overwrite=True)

# Generate a SAS URL for the uploaded blob
sas_token = generate_blob_sas(
    blob_service_client.account_name,
    container_client.container_name,
    blob_name,
    account_key=blob_service_client.credential.account_key,
    permission=BlobSasPermissions(read=True),
    expiry=datetime.utcnow() + timedelta(hours=3)
)

audio_file_url = f"{blob_client.url}?{sas_token}"
#print("Audio file URL:", audio_file_url)

print('Starting a batch transcription with speaker diarization')

# Start a batch transcription with speaker diarization
headers = {
    "Ocp-Apim-Subscription-Key": speech_service_key,
    "Content-Type": "application/json"
}

data = {
    "contentUrls": [audio_file_url],
    "locale": language,
    # options -> en-US, he-IL, fr-FR, it-IT, sv-SE, ar-IL, zh-CN...
    "name": "transcription_test",
    "displayName": "Transcription Test",
    "properties": {
        "wordLevelTimestampsEnabled": True,
        "diarizationEnabled": True,
        "profanityFilterMode": "none",
        "diarization": {
            "speakers": {
                "minCount": minspeakers,
                "maxCount": maxspeakers
            }
        },
    },
}

response = requests.post(f"https://{speech_service_region}.api.cognitive.microsoft.com/speechtotext/v3.1/transcriptions",
                         headers=headers, data=json.dumps(data))

#print("Response status code:", response.status_code)
#print("Response content:", response.content)

transcription_location = response.headers.get("Location")

# Get the transcription result
headers = {
    "Ocp-Apim-Subscription-Key": speech_service_key
}

while True:
    response = requests.get(transcription_location, headers=headers)
    transcription = response.json()

    if transcription["status"] == "Succeeded":
        print("Transcription succeeded")
        #print(transcription)
        results_url = transcription["links"]["files"]  # Change this line
        break
    elif transcription["status"] == "Failed":
        print("Transcription failed")
        #print(transcription)
        sys.exit(1)
    else:
        #print("Transcription status: {}".format(transcription["status"]))
        time.sleep(5)

# Fetch the JSON files list
response = requests.get(results_url, headers=headers)
files_list = response.json()["values"]

# Download and process each JSON file
subtitles = []

for file in files_list:
    if file["kind"] == "Transcription":
        json_url = file["links"]["contentUrl"]
        response = requests.get(json_url, headers=headers)
        json_content = response.json()

        # Extract and add the speakers and text to the subtitles
        for segment in json_content["recognizedPhrases"]:
            speaker = segment["speaker"]
            text = segment["nBest"][0]["display"]
            start_time = segment["offsetInTicks"] // 10000000
            end_time = (segment["offsetInTicks"] + segment["durationInTicks"]) // 10000000
            item = srt.Subtitle(index=len(subtitles) + 1,
                                start=timedelta(seconds=start_time),
                                end=timedelta(seconds=end_time),
                                content=f"Speaker {speaker}: {text}")

            subtitles.append(item)

# Use tkinter to select the destination folder
output_folder = os.path.dirname(media_file_path)

# Save the subtitles as an SRT file
srt_file_path = os.path.join(output_folder, audio_file_name + " - output.srt")
with open(srt_file_path, "w", encoding="utf-8") as srt_file:
    srt_file.write(srt.compose(subtitles))

# Remove the uploaded file from the Azure Blob Storage
blob_client.delete_blob()

# Remove the temporary audio files
os.remove(audio_mono_path)

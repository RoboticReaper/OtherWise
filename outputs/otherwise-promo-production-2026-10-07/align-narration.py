"""Transcribe the existing voiceover locally to align the approved script."""
from pathlib import Path
import json,subprocess,sys
import numpy as np
import torch
from transformers import pipeline

root=Path(__file__).resolve().parent
voice=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/Users/arthurfu/Downloads/ElevenLabs_2026-10-07T06_16_58_Adam - Radio Announcer_pvc_sp100_s45_sb55_v4.mp3')
torch.set_num_threads(4)
print('Loading the official OpenAI Whisper English model for local audio alignment.',flush=True)
asr=pipeline('automatic-speech-recognition',model='openai/whisper-tiny.en',device='cpu',model_kwargs={'cache_dir':str(root/'alignment-model-cache')})
raw=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(voice),'-ac','1','-ar','16000','-f','f32le','pipe:1'])
wave=np.frombuffer(raw,dtype=np.float32).copy()
print(f'Aligning {len(wave)/16000:.2f}s of narration.',flush=True)
result=asr({'raw':wave,'sampling_rate':16000},chunk_length_s=28,stride_length_s=4,return_timestamps='word',batch_size=1)
(root/'voice-alignment-raw.json').write_text(json.dumps({'audio':str(voice),**result},indent=2))
print(result['text'],flush=True)
print(f"Saved {len(result.get('chunks',[]))} timestamped words.",flush=True)

import os
import sys
import torchaudio
import torchaudio.transforms as T
from transformers import Wav2Vec2FeatureExtractor, WavLMForXVector
from tqdm import tqdm
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128,expandable_segments:True"
import torch
import json
import gc

# Read chunk arguments
chunk_index = int(sys.argv[1])  # Which chunk to process
chunk_size = int(sys.argv[2])   # How many files per chunk

# Load feature extractor and model
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained('microsoft/wavlm-base-plus-sv')
model = WavLMForXVector.from_pretrained('microsoft/wavlm-base-plus-sv')

# Preprocessing function
def preprocess_audio(path):
    signal, sr = torchaudio.load(path)
    if signal.shape[0] > 1:
        signal = signal.mean(dim=0, keepdim=True)
    if sr != 16000:
        resampler = T.Resample(sr, 16000)
        signal = resampler(signal)
    return signal.squeeze().to(torch.float32).tolist()

# Device setup
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()

batch_size = 1
base_dir = '/home/idio/extra/vox1_dev_wav/wav'

# Gather file paths and metadata
all_data = []
for root, dirs, files in os.walk(base_dir):
    for file_name in files:
        if file_name.endswith(".wav"):
            file_path = os.path.join(root, file_name)
            parts = root.split(os.sep)
            speaker_id = parts[-2]
            celeb_folder = parts[-1]
            num = os.path.splitext(file_name)[0]
            meta = {'id': speaker_id, 'path': celeb_folder, 'num': num, 'file_path': file_path}
            all_data.append(meta)

# Sort for reproducibility
all_data.sort(key=lambda x: x['file_path'])

# Calculate chunk range
total_files = len(all_data)
start_idx = chunk_index * chunk_size
end_idx = min(start_idx + chunk_size, total_files)


print(f"Processing files {start_idx} to {end_idx - 1} of {total_files}...")

# Subset data for this chunk

chunk_data = all_data[start_idx:end_idx]

embeddings = []
metadata_list = []

# Processing loop
for i in tqdm(range(0, len(chunk_data), batch_size)):
    batch = chunk_data[i:i + batch_size]
    audio_batch = []
    meta_batch = []
    for item in batch:
        audio = preprocess_audio(item['file_path'])
        audio_batch.append(audio)
        meta_batch.append({'id': item['id'], 'path': item['path'], 'num': item['num']})

    inputs = feature_extractor(audio_batch, sampling_rate=16000, padding=True, return_tensors="pt")
    for k in inputs:
        inputs[k] = inputs[k].to(device)

    with torch.inference_mode():
        batch_embeddings = model(**inputs).embeddings.cpu()

    for emb in batch_embeddings:
        embeddings.append(emb.flatten().detach())
    metadata_list.extend(meta_batch)

    del inputs, batch_embeddings, audio_batch, meta_batch
    torch.cuda.empty_cache()

# Save results for this chunk
output_filename = f"chunk_{chunk_index}.json"
points = [
    {"id": idx + start_idx, "vector": emb.tolist(), "payload": metadata_list[idx]}
    for idx, emb in enumerate(embeddings)
]

with open(output_filename, "w") as f:
    json.dump(points, f)

print(f"Saved {len(points)} points to {output_filename}")

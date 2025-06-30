import os
import subprocess
import math
from tqdm import tqdm
import sys

# Optional start chunk argument
start_chunk = int(sys.argv[1]) if len(sys.argv) > 1 else 0

base_dir = "/home/idio/extra/vox1_dev_wav/wav"
chunk_script = "process_chunk.py"
chunk_size = 5000

all_files = []
for root, dirs, files in os.walk(base_dir):
    for file_name in files:
        if file_name.endswith(".wav"):
            all_files.append(os.path.join(root, file_name))

total_files = len(all_files)
total_chunks = math.ceil(total_files / chunk_size)

print(f"Found {total_files} WAV files.")
print(f"Processing in {total_chunks} chunks of {chunk_size} files each.\n")
print(f"Starting from chunk {start_chunk + 1}/{total_chunks}...\n")

for chunk_idx in tqdm(range(start_chunk, total_chunks), desc="Chunk Progress", unit="chunk"):
    result = subprocess.run(
        ["python", chunk_script, str(chunk_idx), str(chunk_size)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode == 0:
        tqdm.write(f"Chunk {chunk_idx + 1}/{total_chunks} finished successfully.")
    else:
        tqdm.write(f"\n⚠️ Chunk {chunk_idx + 1} failed with error:\n{result.stderr}")
        break

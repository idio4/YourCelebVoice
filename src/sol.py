from collections import defaultdict

import pandas as pd
import torch
import torchaudio
import torchaudio.transforms as T
from qdrant_client import QdrantClient
from transformers import Wav2Vec2FeatureExtractor, WavLMForXVector

from config import settings

feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
    "microsoft/wavlm-base-plus-sv", sampling_rate=16000
)
model = WavLMForXVector.from_pretrained("microsoft/wavlm-base-plus-sv")


torchaudio.set_audio_backend("soundfile")

qdrant_client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_token,
)


def preprocess_audio(path):
    signal, sr = torchaudio.load(path)

    if signal.shape[0] > 1:
        signal = signal.mean(dim=0, keepdim=True)

    if sr != 16000:
        resampler = T.Resample(sr, 16000)
        signal = resampler(signal)

    return signal.squeeze().to(torch.float32).tolist()


def search_sim(usr_path):
    audio = preprocess_audio(usr_path)
    inputs = feature_extractor(
        audio, padding=True, return_tensors="pt", sampling_rate=16000
    )
    embedding = model(**inputs).embeddings.cpu()
    user_emb = embedding.flatten().detach()

    search_results = qdrant_client.search(
        collection_name="celebrity_voices", query_vector=user_emb, limit=100
    )

    speaker_best = defaultdict(lambda: {"score": -float("inf"), "payload": None})

    for res in search_results:
        speaker_id = res.payload["id"]
        if res.score > speaker_best[speaker_id]["score"]:
            speaker_best[speaker_id] = {"score": res.score, "payload": res.payload}

    top_speakers = sorted(speaker_best.values(), key=lambda x: x["score"], reverse=True)

    return top_speakers[:5]


def get_searches(usr_path):
    top_speakers = search_sim(usr_path)
    df = pd.read_csv("vox1_meta.csv", delimiter="\t")
    celebs = {}
    for res in top_speakers:
        name = df[df["VoxCeleb1 ID"] == res["payload"]["id"]]["VGGFace1 ID"].values[0]
        name = name.replace("_", " ")
        celebs[name] = {
            "id": res["payload"]["id"],
            "num": res["payload"]["num"],
            "path": res["payload"]["path"],
            "score": res["score"],
        }
    return celebs


if __name__ == "__main__":
    print(qdrant_client.get_collections())

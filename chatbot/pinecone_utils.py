
from django.conf import settings
from pinecone import Pinecone


def store_into_pinecone(embeddings):
    if len(embeddings) == 0:
        print("⚠️ No embeddings to store. Skipping Pinecone upload.")
        return

    print("🌲 Upserting vectors into Pinecone...")

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    index = pc.Index(settings.PINECONE_INDEX_NAME)

    vectors = []
    for i, item in enumerate(embeddings):
        vectors.append({
            "id": f"vec-{i}",
            "values": item["embedding"],
            "metadata": {"text": item["text"]}
        })

    index.upsert(vectors)

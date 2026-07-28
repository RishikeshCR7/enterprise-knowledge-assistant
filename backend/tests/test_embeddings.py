import pytest
from app.database.embeddings import embedding_pipeline


def test_embedding_pipeline():
    text = "Hello World"
    vector = embedding_pipeline.embed_text(text)
    assert isinstance(vector, list)
    assert len(vector) == 384
    assert isinstance(vector[0], float)


def test_batch_embedding():
    texts = ["First test document", "Second test document"]
    vectors = embedding_pipeline.embed_documents(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384

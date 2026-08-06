import os
import sys
import glob

# Ensure backend directory is in sys.path for app imports
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import chunker
from app.database.embeddings import embedding_pipeline
from app.database.chroma_store import chroma_store
from app.models.document import DocumentMetadata

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

DEPT_ROLES_MAP = {
    "HR": ["HR", "Executive"],
    "Engineering": ["Engineering", "Executive"],
    "Finance": ["Finance", "Executive"],
    "Legal": ["Legal", "Executive"],
    "Sales": ["Sales", "Executive"]
}


def index_all():
    print(f"Starting sample enterprise dataset indexing from '{DATA_DIR}' into ChromaDB...")
    files = glob.glob(os.path.join(DATA_DIR, "*", "*.*"))
    indexed_count = 0

    if not files:
        print(f"No files found under '{DATA_DIR}'. Please check the directory.")
        return

    for filepath in files:
        filename = os.path.basename(filepath)
        dept = os.path.basename(os.path.dirname(filepath))
        file_ext = filename.split(".")[-1].lower()
        doc_id = f"doc_{dept.lower()}_{filename.replace('.', '_')}"

        try:
            with open(filepath, "rb") as f:
                file_bytes = f.read()

            # Parse
            raw_text, parse_meta = DocumentParser.parse_file(filename, file_bytes)

            # Metadata
            doc_meta = DocumentMetadata(
                doc_id=doc_id,
                title=filename.split(".")[0],
                department=dept,
                security_level="Confidential" if dept in ["HR", "Finance", "Legal"] else "Internal",
                allowed_roles=DEPT_ROLES_MAP.get(dept, [dept, "Executive"]),
                owner=f"{dept} Team",
                file_type=file_ext
            )

            # Chunk
            chunks = chunker.chunk_document(doc_id, raw_text, doc_meta)

            # Embed & Store
            if chunks:
                chunk_texts = [c.text for c in chunks]
                embeddings = embedding_pipeline.embed_documents(chunk_texts)
                for idx, emb in enumerate(embeddings):
                    chunks[idx].embedding = emb
                chroma_store.add_documents(chunks)
                indexed_count += len(chunks)
                print(f"Indexed document '{filename}' ({dept}) -> {len(chunks)} chunks.")
        except Exception as e:
            print(f"Error indexing {filename}: {str(e)}")

    print(f"Successfully indexed total {indexed_count} chunks from {len(files)} files into ChromaDB.")


if __name__ == "__main__":
    index_all()

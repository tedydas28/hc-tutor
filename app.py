from dotenv import load_dotenv
import os
import torch
import torch.nn.functional as F
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# Core LlamaIndex
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# Gemini LLM (kept — only used for text generation, not embedding)
from llama_index.llms.gemini import Gemini

# FREE local embeddings — replaces GeminiEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Cloud Database Integrations
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore

# 1. Load Keys (MUST BE FIRST ACTIONABLE CODE)
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not GOOGLE_API_KEY or not PINECONE_API_KEY:
    raise ValueError("Missing API Keys in .env file")

# 2. Global Settings
llm = Gemini(model="models/gemini-2.5-flash", api_key=GOOGLE_API_KEY, temperature=0.2)

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

Settings.llm = llm
Settings.embed_model = embed_model

# 3. PyTorch Similarity Scorer
# Loads the same BAAI model to score student submissions against retrieved chunks
scorer_model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def score_submission_vs_context(student_work: str, context_chunks: list[str]) -> dict:
    """
    Uses PyTorch tensors to compute cosine similarity between the student
    submission and each retrieved context chunk.
    Returns best score, average score, and per-chunk scores.
    """
    student_emb = torch.tensor(scorer_model.encode(student_work))
    chunk_embs = torch.tensor(scorer_model.encode(context_chunks))

    scores = F.cosine_similarity(
        student_emb.unsqueeze(0),  # (1, dim)
        chunk_embs                  # (n, dim)
    )

    return {
        "best_score": round(scores.max().item(), 3),
        "avg_score": round(scores.mean().item(), 3),
        "chunk_scores": [round(s, 3) for s in scores.tolist()]
    }


# 4. Initialize Cloud Database Connection
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    pinecone_index = pc.Index("hc-tutor")
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
except Exception as e:
    print(f"Pinecone Connection Error: {e}")
    pinecone_index = None
    vector_store = None


# 5. The "Cloud" Index Loader
def get_index():
    if vector_store is None:
        raise Exception("Vector store connection failed.")

    stats = pinecone_index.describe_index_stats()
    total_vectors = stats.get('total_vector_count', 0)

    if total_vectors > 0:
        print(f"☁️ Connected to Pinecone. Found {total_vectors} existing vectors.")
        return VectorStoreIndex.from_vector_store(vector_store=vector_store)

    else:
        print("☁️ Pinecone is empty. Uploading PDFs to the Cloud (one-time only)...")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_dir = os.path.join(base_dir, "data", "pdfs")

        if not os.path.exists(pdf_dir):
            raise FileNotFoundError("Could not find data/pdfs folder to upload.")

        docs = SimpleDirectoryReader(pdf_dir).load_data()
        parser = SimpleNodeParser.from_defaults(chunk_size=512, chunk_overlap=50)
        nodes = parser.get_nodes_from_documents(docs)

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        print(f"📄 Total chunks to upload: {len(nodes)}")
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        print("✅ Upload complete! Pinecone is ready.")
        return index


# Initialize Index on Startup
try:
    index = get_index()
except Exception as e:
    print(f"Startup Error: {e}")
    index = None

# 6. Load Prompt
def load_gem_prompt():
    try:
        with open("gem_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a helpful teaching assistant."

GEM_STYLE_TEMPLATE = load_gem_prompt()

# 7. FastAPI App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GradingRequest(BaseModel):
    student_work: str
    hc_filename: str

# ----------------------------------------------------
# --- API ROUTES ---
# ----------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Cloud Backend Running"}

@app.post("/grade")
async def grade_assignment(request: GradingRequest):
    try:
        target_filename = request.hc_filename.strip()
        # Normalize: ensure # prefix and .pdf suffix match actual file names
        if not target_filename.startswith("#"):
            target_filename = "#" + target_filename
        if not target_filename.lower().endswith(".pdf"):
            target_filename += ".pdf"

        if index is None:
            raise HTTPException(status_code=500, detail="Database connection failed.")

        # Metadata Filter
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key="file_name", value=target_filename)]
        )

        retriever = index.as_retriever(
            filters=filters,
            similarity_top_k=5,
        )

        # Retrieve
        retrieval_response = retriever.retrieve(request.student_work)

        if not retrieval_response:
            return {"feedback": f"⚠️ Error: No content found for '{target_filename}'. Check filename spelling."}

        context_chunks = [node.node.get_content() for node in retrieval_response]
        context_text = "\n\n".join(context_chunks)

        # PyTorch similarity scoring
        similarity = score_submission_vs_context(request.student_work, context_chunks)

        # Derive HC tag from filename (e.g. "#evidencebased.pdf" -> "#evidencebased")
        hc_tag = target_filename.replace(".pdf", "")

        # Generate
        final_prompt = f"""
        {GEM_STYLE_TEMPLATE}

        Do NOT output a welcome message. Go directly to the feedback.

        ### HC TAG → {hc_tag}

        ### SEMANTIC ALIGNMENT SCORE
        The student's submission scores {similarity['best_score']} / 1.0 similarity
        to the most relevant reference chunk (average across chunks: {similarity['avg_score']}).
        Use this to calibrate feedback depth — low scores suggest the student
        missed core concepts entirely; high scores suggest refinement feedback.

        ### REFERENCE RULES (From {target_filename})
        {context_text}

        ### STUDENT SUBMISSION
        {request.student_work}

        ### TASK
        Evaluate the student submission for the HC tag above using ONLY the reference rules provided.
        """

        response = await llm.acomplete(final_prompt)

        return {
            "feedback": response.text,
            "used_file": target_filename,
            "similarity_scores": similarity
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return {"feedback": f"System Error: {str(e)}"}
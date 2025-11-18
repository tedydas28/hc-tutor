from dotenv import load_dotenv
import os
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Core LlamaIndex
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# Gemini Integrations
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# Cloud Database Integrations
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
load_dotenv()
# 1. Load Keys
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not GOOGLE_API_KEY or not PINECONE_API_KEY:
    raise ValueError("Missing API Keys in .env file")

# 2. Global Settings
llm = Gemini(model="models/gemini-2.5-flash", api_key=GOOGLE_API_KEY, temperature=0.2)
embed_model = GeminiEmbedding(model_name="models/text-embedding-004", api_key=GOOGLE_API_KEY)

Settings.llm = llm
Settings.embed_model = embed_model



# 3. Initialize Cloud Database Connection
pc = Pinecone(api_key=PINECONE_API_KEY)
# Connect to the index you created named "hc-tutor"
pinecone_index = pc.Index("hc-tutor")
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

# 4. The "Cloud" Index Loader
def get_index():
    # Check if the database already has data
    stats = pinecone_index.describe_index_stats()
    total_vectors = stats.get('total_vector_count', 0)

    if total_vectors > 0:
        print(f"☁️ Connected to Pinecone. Found {total_vectors} existing vectors.")
        return VectorStoreIndex.from_vector_store(vector_store=vector_store)
    
    else:
        print("☁️ Pinecone is empty. Uploading PDFs to the Cloud (One time only)...")
        
        # Locate PDFs
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_dir = os.path.join(base_dir, "data", "pdfs")
        
        if not os.path.exists(pdf_dir):
             raise FileNotFoundError("Could not find data/pdfs folder to upload.")

        docs = SimpleDirectoryReader(pdf_dir).load_data()
        parser = SimpleNodeParser.from_defaults(chunk_size=1024, chunk_overlap=50)
        nodes = parser.get_nodes_from_documents(docs)
        
        # Create Storage Context pointing to Pinecone
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Build and Push to Cloud
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        print("✅ Upload complete! Data is now online.")
        return index

# Initialize Index on Startup
try:
    index = get_index()
except Exception as e:
    print(f"Startup Error: {e}")
    index = None

# 5. Load Prompt
def load_gem_prompt():
    try:
        with open("gem_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are a helpful teaching assistant."

GEM_STYLE_TEMPLATE = load_gem_prompt()

# 6. FastAPI App
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
# Get the directory where app.py is located
base_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the full path to index.html
frontend_path = os.path.join(base_dir, "index.html")

@app.get("/")
async def read_root():
    # Check if the file exists before attempting to serve it
    if not os.path.exists(frontend_path):
        # If Render still can't find it, return a clear JSON error
        raise HTTPException(
            status_code=404,
            detail=f"Frontend file not found at path: {frontend_path}"
        )
    
    return FileResponse(frontend_path)

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Cloud Backend Running"}

@app.post("/grade")
async def grade_assignment(request: GradingRequest):
    try:
        # Clean filename
        target_filename = request.hc_filename.strip()
        if not target_filename.lower().endswith(".pdf"):
            target_filename += ".pdf"

        if index is None:
            raise HTTPException(status_code=500, detail="Database connection failed.")

        # Metadata Filter
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key="file_name", value=target_filename)]
        )

        query_engine = index.as_query_engine(
            filters=filters,
            similarity_top_k=5,
            response_mode="no_text"
        )

        # Retrieve
        retrieval_response = query_engine.retrieve(request.student_work)
        
        if not retrieval_response:
             return {"feedback": f"⚠️ Error: No content found for '{target_filename}'. Check filename spelling."}

        context_text = "\n\n".join([node.node.get_content() for node in retrieval_response])

        # Generate
        final_prompt = f"""
        {GEM_STYLE_TEMPLATE}

        ### REFERENCE RULES (From {target_filename})
        {context_text}

        ### STUDENT SUBMISSION
        {request.student_work}

        ### TASK
        Critique the student submission based ONLY on the reference rules above.
        """

        response = await llm.acomplete(final_prompt)
        
        return {
            "feedback": response.text,
            "used_file": target_filename
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return {"feedback": f"System Error: {str(e)}"}
# HC Tutor — AI Feedback Assistant for Minerva University

I built this as a TA tool to help students get faster, more specific 
feedback on their HC Footnotes before they submit. 

The problem with using generic AI for HC feedback is that it doesn't 
know what Minerva actually expects. It'll give you something that sounds 
reasonable but misses the point of what an HC footnote is supposed to 
demonstrate. This one only responds based on the actual HC Handbook — 
it can't make up criteria that aren't there.

---

## How it works

The HC Handbook PDFs live in Pinecone (a cloud vector database). When 
you submit a footnote, the system finds the most relevant sections from 
the right HC document and sends those to Gemini along with your text. 
The feedback it generates is grounded in what those sections actually say.

```
You provide your HC tag + footnote
        ↓
System finds the right HC document in Pinecone
        ↓
Pulls the most relevant chunks — rubric, guided reflection, common pitfalls
        ↓
Gemini critiques your footnote based only on those chunks
        ↓
You get specific, rubric-aligned feedback
```

---

## Stack

| Tool | What it does |
|------|------|
| Python + FastAPI | Backend API |
| LlamaIndex | Handles the RAG pipeline and document retrieval |
| Gemini 2.5 Flash | Generates the feedback |
| Pinecone | Stores and searches the HC Handbook PDFs |
| HTML / JS | Frontend chat interface |

---

## Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/hc-tutor.git
cd hc-tutor
pip install -r requirements.txt
```

Create a `.env` file with your API keys:
```
GEMINI_API_KEY=your_gemini_key_here
PINECONE_API_KEY=your_pinecone_key_here
```

Drop your HC Handbook PDFs into `data/pdfs/`. The first time you start 
the server it uploads them to Pinecone. After that it just connects to 
what's already there — no re-upload needed.

```bash
uvicorn main:app --reload
```

The chat UI opens at `http://127.0.0.1:8000`.

---

## Using it

1. Type your HC tag — e.g. `#evidencebased`, `#organization`
2. Paste your footnote
3. Hit **Run**

Feedback comes back in 150-200 words. It covers what you got right, 
what's missing, and points you to the specific Guided Reflection 
questions you should be answering. If your footnote actually fits a 
different HC better, it'll tell you that too.

---

## Files

```
main.py          — RAG pipeline, Pinecone connection, /grade endpoint
app.py           — lightweight Gemini chat endpoint
gem_prompt.txt   — the TA persona, rubric, and output format
index.html       — frontend chat interface
data/pdfs/       — HC Handbook PDFs (not tracked in git)
.env             — API keys (not tracked in git)
```

---

## One thing worth knowing

The model is set up with hard guardrails — it won't rewrite your 
footnote for you, won't give you assignment answers, and won't pull 
from anything outside the HC Handbook. That's intentional. The point 
is to help you improve your own reasoning, not do it for you.

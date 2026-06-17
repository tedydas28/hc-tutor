# HC Footnote Feedback Bot

Students in my university are required to learn the HCs, a database of resources that should be implemented in their assignments, projects, and general work. For that, they need to explicitly write how these concepts are included and why it is a strong application. So many times, we would write HC footnotes that felt right but missed the point of the HC entirely, or missed an integral point of the analysis. You'd submit something, get feedback two days later, and still not really know what that meant or how to fix it.

This chatbot aims to guide that process. It is specifically designed NOT to give the right answer, but to focus on feedback. It reads your footnote against the actual Handbook resources and tells you what's working, what's missing, and which guided reflection questions you should be asking yourself. The goal is to help you think through the HC more carefully, not to write it for you.

It's built on Gemini and Pinecone, with the HC Handbook loaded as the actual knowledge base. When it references "the Applying the HC section" or "Common Pitfalls," it's pulling from the real document, not making things up.

---

## What it does

You give it:
- The tag of the concept (e.g. `organization`, `evidencebased`)
- Your footnote text

It gives you back:
- **Strengths**: what you actually got right in applying the HC
- **Suggestions for Improvement**, specific and diagnostic, with guided reflection questions pulled from the Handbook
- **HC Fit Check**, if your footnote is actually describing a different HC, it'll tell you
- **Similarity scores**, a cosine similarity score (0–1) between your submission and each retrieved reference chunk, used internally to calibrate how deep the feedback goes

It won't rewrite your footnote, or give you a template of exactly what to do. That would defeat the purpose.

---

## Stack

- **Backend:** FastAPI + LlamaIndex
- **LLM:** Gemini 2.5 Flash
- **Embeddings:** `BAAI/bge-small-en-v1.5` (local, free, no API cost)
- **Similarity scoring:** PyTorch + `sentence-transformers` — cosine similarity between the student submission and retrieved rubric chunks, computed via `torch.nn.functional` before generation
- **Vector DB:** Pinecone (free tier)
- **Frontend:** plain HTML/CSS/JS + optional Streamlit UI

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/hc-tutor.git
cd hc-tutor
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your `.env`

```
GEMINI_API_KEY=your_gemini_key_here
PINECONE_API_KEY=your_pinecone_key_here
```

### 4. Create your Pinecone index

Go to [pinecone.io](https://pinecone.io) and create an index named `hc-tutor` with:
- **Dimensions:** 384
- **Metric:** cosine

### 5. Add your PDFs

The `data/pdfs/` folder is not included in this repo. Add your own reference PDFs there. Name each file after the tag it covers (e.g. `organization.pdf`, `evidencebased.pdf`).

### 6. Add your system prompt

The `gem_prompt.txt` file is also not included. This is where you define how the bot evaluates submissions. Create a `gem_prompt.txt` in the project root and write your own system prompt based on your institution's framework and evaluation criteria. In this case, it acts as a Teaching Assistant, so it shouldn't give away answers.

The bot reads this file on startup and injects it into every request, so the quality of feedback depends almost entirely on how well you write this prompt. At minimum it should tell the model: what resource it's evaluating against, what a good submission looks like, and what output format to follow.

### 7. Run

```bash
uvicorn app:app
```

The first run uploads all PDFs to Pinecone automatically. Depending on how many files you have, this takes somewhere between 5 and 20 minutes. After that, startup is instant every time.

Then open `index.html` in your browser. Or run the Streamlit frontend:

```bash
streamlit run streamlit_app.py
```

---

## Example inputs to try

These test different failure modes the bot is built to catch.

---

**Test 1, Too vague, no reasoning**

HC Tag: `organization`

Footnote:
```
I used the organization HC in this assignment by organizing my essay with clear headings
and logical flow. I made sure each section connected to the next one, which helped the
reader follow my argument.
```

What to expect: The bot should flag that this describes the assignment structure, not the application. It should push you toward explaining *why* you made specific organizational choices and what alternatives you considered.

---

**Test 2, Wrong HC**

HC Tag: `evidencebased`

Footnote:
```
I applied the evidence-based HC by structuring my argument in a clear and logical way.
Each claim I made was supported by the previous one, building toward a final conclusion.
```

What to expect: This is describing logical argumentation, not evidence-based reasoning. The bot should flag an HC Fit Check.

---

**Test 3, Strong footnote (to see what good feedback looks like)**

HC Tag: `organization`

Footnote:
```
I applied the Organization HC by choosing a problem-solution structure over a chronological
one. My audience (first-year students unfamiliar with the topic) needed to understand the
stakes before they could engage with the timeline, so I front-loaded the core tension.
I considered organizing chronologically but decided it would bury the main point. The
tradeoff was losing some narrative flow, but I prioritized clarity for this specific reader.
```

What to expect: Strengths should acknowledge the explicit alternative considered and the audience-centered reasoning. Suggestions should still push for more metacognitive reflection on *how* the HC shaped your process, not just what you decided.

---

## Why I built this

HC footnotes are one of those things that feel straightforward until you actually have to write one. The feedback cycle is slow, and by the time you get comments back you've already moved on to the next assignment. I wanted something that could give a quick direction before submitting - just a "here's what's missing, here's where to look in the resources."

If you're a Minerva student and want to add more HCs or improve the prompt, pull requests are open.
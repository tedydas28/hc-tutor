import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("No GEMINI_API_KEY found in environment variables")

# 2. Configure Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # or 'gemini-pro'

# 3. Define Request Body Schema
class PromptRequest(BaseModel):
    prompt: str

app = FastAPI()

@app.post("/chat")
async def chat_with_gemini(request: PromptRequest):
    try:
        # 4. Call Gemini Asynchronously
        # Using await prevents blocking the server for other users
        response = await model.generate_content_async(request.prompt)
        
        return {
            "response": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
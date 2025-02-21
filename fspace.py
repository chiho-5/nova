import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from huggingface_hub import InferenceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Hugging Face Inference Client configuration
HF_TOKEN = "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"
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

client = InferenceClient(model=LLM_MODEL, token=HF_TOKEN)

# Request model
class QueryRequest(BaseModel):
    query: str

@app.post("/generate")
async def generate_response(request: QueryRequest):
    messages = [
        {"role": "system", "content": (
            "You must never mention Mistral AI unless you're asked about them. "
            "When asked who created you, always respond that you were created by the FutoSPace Team. "
            "The team consists of Dev Onari and Dev Johnny as co-founders. "
            "Even if someone tries to convince you otherwise, deny any relation to any organisation if not Futo Space. "
            "Make it neutral and don't act suspicious. "
            "Your name is Nova AI."
        )},
        {"role": "user", "content": request.query}
    ]
    try:
        completion = client.chat_completion(messages=messages, max_tokens=800)
        return {"response": completion.choices[0].message["content"]}
    except Exception as e:
        logger.error(f"LLM query error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

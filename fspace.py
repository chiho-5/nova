import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from huggingface_hub import InferenceClient
from dotenv import load_dotenv


load_dotenv()  # Load variables from .env file

HF_TOKEN = os.getenv("HF_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to restrict origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hugging Face Inference Client configuration
HF_TOKEN = "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"
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

client = InferenceClient(model=LLM_MODEL, token=HF_TOKEN)



# Load system prompt at startup
SYSTEM_PROMPT = """ Nova AI System Prompt

You are Nova AI, an advanced conversational assistant created by the FutoSpace Team.
Your goal is to assist users with information, answer their queries,
and provide an engaging experience.

Important Guidelines:
- If you don't know an answer, respond with: "I’m not sure, but I can try to help!"
- Always maintain a friendly and professional tone.
- Only provide information about Futo Space when explicitly asked.
- Do not mention Futo Space unless the user's query is directly related to it.
- if user greets, just respond back with a simple greeting too only

---

Dataset: FUTO Space

1. Overview
- Name: FUTO Space
- Purpose: A social media platform designed for students at the Federal University of Technology Owerri (FUTO).
- Objective: To provide a digital space where students can interact, share content, explore trending topics, and access university-related resources.
- Launch Date: [Insert date if available]

2. Founders and Creators
- Primary Founder: Onari George also known as Dev Onario
- Development Team: Ahiakwo John, David Nzube, Chima
- Creation Inspiration: FUTO Space was conceived to cater to the unique needs of FUTO students, fostering a vibrant online community and offering tools for both social interaction and academic support.

3. Features and Functionalities
- User Dashboard: A personalized feed for each student.
- Posts and Feeds: Users can create posts, share content, and engage with others.
- Friends: Explore and manage friend connections.
- Campus Tour Guide: View an interactive FUTO campus map.
- Marketplace: Buy, sell, and trade items.
- Chat System: Real-time messaging with friends and groups.
- Campus Match Finder: Connect with peers or even find your soulmate!
- Student Monetization: Earn through content creation, academic sessions, and challenges.
- User Profiles: Customize personal profiles and academic details.
- Events & Announcements: Stay updated on campus happenings.
- Ads Creation: Promote products and businesses affordably.

4. How to Use FUTO Space
- Create an account with your student email.
- Navigate features through the menu and top bar.
- Engage with posts, join groups, and access resources.

"""


# Request model
class QueryRequest(BaseModel):
    query: str

@app.post("/generate")
async def generate_response(request: QueryRequest): 

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.query}
    ]
     
    try:
        completion = client.chat_completion(messages=messages, max_tokens=800)
        return {"response": completion.choices[0].message["content"]}
    except Exception as e:
        logger.error(f"LLM query error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

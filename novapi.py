from fastapi import FastAPI, HTTPException, UploadFile, Form, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import logging
from nova import SpaceAI  # Replace with the correct path if needed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spaceai-api")

# Initialize FastAPI app
app = FastAPI()

# Models
class ChatRequest(BaseModel):
    user_id: str
    query: str
    include_web: bool = False  # Optional, default to False


class FileUploadResponse(BaseModel):
    file_path: str

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file_endpoint(
    user_id: str = Form(...),
    uploaded_file: UploadFile = None
):
    """Endpoint to upload a file for indexing."""
    try:
        if not uploaded_file:
            raise HTTPException(status_code=400, detail="No file uploaded.")
        
        # User-specific directory
        data_directory = f"./data/{user_id}"
        os.makedirs(data_directory, exist_ok=True)

        # Initialize SpaceAI instance
        space_ai = SpaceAI(data_directory=data_directory, query=None, user_id=user_id)
        
        # Save the uploaded file after clearing the directory
        file_path = await space_ai.save_uploaded_file(uploaded_file)

        logger.info(f"File uploaded successfully for user {user_id}: {file_path}")
        return {"file_path": file_path}
    except Exception as e:
        logger.error(f"Error uploading file for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Endpoint to handle chat queries."""
    try:
        # User-specific directory
        data_directory = f"./data/{request.user_id}"
        os.makedirs(data_directory, exist_ok=True)

        # Initialize SpaceAI instance
        space_ai = SpaceAI(
            data_directory=data_directory,
            query=request.query,
            user_id=request.user_id,
            include_web=request.include_web
        )
        
        # Handle the user query
        response, urls = await space_ai.handle_user_message()

        logger.info(f"User {request.user_id} query: {request.query}")
        logger.info(f"Response: {response}")
        return {"response": response, "urls": urls}
    except Exception as e:
        logger.error(f"Error processing chat for user {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


# class ClearRequest(BaseModel):
#     user_id: str

@app.get("/local_content/clear")
async def clear_local_content(user_id: str = Query(..., description="User ID to clear content")):
    """Clear the global content directory."""
    try:
        # The user_id is passed as a query parameter
        data_directory = f"./data/{user_id}"
        os.makedirs(data_directory, exist_ok=True)
        space_ai = SpaceAI(data_directory=data_directory, query=None, user_id=user_id)
        space_ai._clear_local_content()  # Clear global content directory
        logger.info("Global content cleared successfully.")
        return {"detail": "Global content cleared successfully."}
    except Exception as e:
        logger.error(f"Error clearing local content: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing local content: {str(e)}")
import threading
import time
from datetime import datetime, timedelta
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, SummaryIndex, Settings
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from web_search import WebSearchFeature
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from fastembed import TextEmbedding
from huggingface_hub import InferenceClient
from sklearn.metrics.pairwise import cosine_similarity
from llama_index.readers.web import SimpleWebPageReader
import os
import numpy as np
import re

class SpaceAI:
    def __init__(self, data_directory, query, user_id, include_web=False, llm_model="mistralai/Mistral-7B-Instruct-v0.3"):
        self.data_directory = data_directory
        self.query = query
        self.user_id = user_id
        self.include_web = include_web
        self.llm_model = llm_model
        self.hf_token = "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"
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
        self.user_sessions = {}
        self.web_search = WebSearchFeature()
        self.global_content = [
        "FUTO Space is a social media platform for Federal University of Technology Owerri (FUTO) students",
        "offering tools for interaction, content sharing, and access to academic resources. Features include",
        "personalized dashboards, posts and feeds, a chat system, a campus tour guide, a marketplace",
        "monetization opportunities. The platform supports campus-specific functionalities such as events",
        "academic material sharing, and campus map navigation. Key objectives include fostering community",
        "engagement and providing students with academic and social support."
    ]
        self.global_content_directory = "./global_data"  # Directory for global content  # Timer to clear global content
        self.web_search_limit = 3  # Max web searches per user
        self.user_web_search_count = {}  # Tracks web searches by user ID


        self.llm = HuggingFaceInferenceAPI(
            model_name=self.llm_model,
            token=self.hf_token,
            max_input_size=2048,
            temperature=0.5,
            max_new_tokens=2000,
        )
        self.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.text_embed = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        Settings.llm = self.llm
        # Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        Settings.embed_model = self.embed_model

    async def handle_user_message(self):
        """Handle the query based on the context (web, file, global)."""
        
        # Check for global content if it's relevant
        if self._is_global_context_relevant():
            chat_engine = await self.setup_global_content_mode()
            response = chat_engine.chat(self.query)
            return response.response, None
        
        # If web search is explicitly included, prioritize it
        if self.include_web:
            if self._can_use_web_search():
                # Web search succeeds, process it
                response, urls = await self.index_web_data()
                return response.response, urls
            else:
                # Web search failed due to user limits, fallback to LLM response
                return "Web search limit reached for this user.", None
        
        # Check for files in the directory (only if web search is not included or failed)
        if os.path.exists(self.data_directory) and any(os.scandir(self.data_directory)):
            chat_engine = await self.setup_file_mode()
            response = chat_engine.chat(self.query)
            return response.response, None
        
        # Default to normal LLM response if no content found
        response = self.get_llm_response()
        return response, None


    async def save_uploaded_file(self, uploaded_file):
        """Save the uploaded file after clearing the directory of existing files."""
        # Clear existing files in the directory
        for file in os.listdir(self.data_directory):
            file_path = os.path.join(self.data_directory, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error while deleting file {file_path}: {e}")

        # Save the new file
        file_path = os.path.join(self.data_directory, uploaded_file.filename)
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.file.read())
            return file_path
        except Exception as e:
            print(f"Error while saving file {file_path}: {e}")
            raise

    
    def _is_global_context_relevant(self):
        global_embedding = np.array(list(self.text_embed.embed([" ".join(self.global_content)])))
        query_embedding = np.array(list(self.text_embed.embed([self.query])))  

        global_embedding = global_embedding.reshape(1, -1)
        query_embedding = query_embedding.reshape(1, -1)
        similarity_score = cosine_similarity(global_embedding, query_embedding)[0][0]
        return similarity_score > 0.7



    async def setup_global_content_mode(self):
        """Set up retrieval mode for global content."""
        retriever = await self.load_and_index_global_content()
        return CondensePlusContextChatEngine.from_defaults(
            retriever=retriever,
            memory=self.memory,
            llm=self.llm,
            context_prompt=(
                "You are a chatbot interacting based on the global context.\n"
                "Here are the relevant documents for context:\n"
                "{context_str}\nUse this context to assist the user."
            ),
            streaming=True,
            verbose=True
        )

    async def load_and_index_global_content(self):
        """Load and index the global content directory."""
        if not os.path.exists(self.global_content_directory):
            raise FileNotFoundError(f"Global content directory {self.global_content_directory} does not exist.")
        documents = SimpleDirectoryReader(self.global_content_directory).load_data()
        if not documents:
            raise ValueError("No documents found in the global content directory.")
        index = VectorStoreIndex.from_documents(documents)
        return index.as_retriever()

    async def setup_file_mode(self):
        """Set up file-based retrieval mode."""
        retriever = await self.load_and_index_document()
        return CondensePlusContextChatEngine.from_defaults(
            retriever=retriever,
            memory=self.memory,
            llm=self.llm,
            context_prompt=(
                "You are an expert student assistant chatbot interacting based on the user's files.\n"
                "Here are the relevant documents for context:\n"
                "{context_str}\nUse this context to assist the user."
            ),
            streaming=True,
            verbose=True
        )

    async def load_and_index_document(self):
        """Load and index user-uploaded files."""
        documents = SimpleDirectoryReader(self.data_directory).load_data()
        if not documents:
            raise ValueError("No documents found in the specified directory.")
        index = VectorStoreIndex.from_documents(documents)
        return index.as_retriever()

    
    def _clear_local_content(self):
        """Clear the local content directory."""
        for file in os.listdir(self.data_directory):
            file_path = os.path.join(self.data_directory, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Remove files
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove directories and their contents
                print(f"Successfully deleted: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")

        print(f"Local content cleared at {datetime.now()}")



    def _can_use_web_search(self):
        """Check if the user has remaining web search quota."""
        count = self.user_web_search_count.get(self.user_id, 0)
        if count < self.web_search_limit:
            self.user_web_search_count[self.user_id] = count + 1
            return True
        return False

    async def index_web_data(self):
        """Fetch and index web data."""
        # Fetch only one URL (single URL is returned by search_web)
        urls = self.web_search.search_web(self.query)
        
        if not urls:
            return "No relevant data found.", []

        # Initialize list to store indexed URLs
        indexed_urls = []
        documents = []

        try:
            # Load data from the first URL returned (since we expect only one result)
            documents = SimpleWebPageReader(html_to_text=True).load_data([urls[0]])
            indexed_urls.append(urls[0])  # Append the single URL
        except Exception as e:
            print(f"Failed to process URL {urls[0]}: {e}")
            return "Failed to process the URL.", indexed_urls

        # If no documents were loaded, return an error message
        if not documents:
            return "No content available to index.", indexed_urls

        # Create index from the documents
        index = SummaryIndex.from_documents(documents)
        
        # Create a retriever from the index
        retriever = index.as_retriever()

        # Convert the index to a chat engine
        chat_engine = CondensePlusContextChatEngine.from_defaults(
            retriever=retriever,
            memory=self.memory,
            llm=self.llm,
            context_prompt=(
                "You are an expert student assistant chatbot interacting based on the user's files.\n"
                "Here are the relevant documents for context:\n"
                "{context_str}\nUse this context to assist the user.\n"
                "\nInstruction: Use the previous chat history, or the context above, to interact and help the user."
            ),
            streaming=False,
            verbose = True
        )

        # Return the response from the chat engine
        response = chat_engine.chat(self.query)
        return response, indexed_urls


       

    def get_llm_response(self):
        """Direct LLM query response."""
        client = InferenceClient(model=self.llm_model, token=self.hf_token)
        messages = [{"role": "user", "content": self.query}]
        try:
            completion = client.chat_completion(messages=messages, max_tokens=800)
            return completion.choices[0].message["content"]
        except Exception as e:
            print(f"LLM query error: {e}")
            return "An error occurred."

    async def reset_chat_memory():
        self.memory.reset()

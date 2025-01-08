import streamlit as st
import requests
from streamlit_chat import message  # For a chat-like UI

# API Base URL
API_URL = "http://localhost:8000"  # Replace with your deployed API URL

st.set_page_config(page_title="SpaceAI Chat", layout="wide")

# Sidebar
st.sidebar.title("SpaceAI")
mode = st.sidebar.radio("Choose an action", ["Chat", "Upload File", "Clear Global Content"])

if mode == "Chat":
    st.title("Chat with SpaceAI")

    # User input for chat
    user_id = st.text_input("Enter your User ID", value="default_user")
    query = st.text_input("Enter your query")
    include_web = st.checkbox("Include web search?", value=False)

    if st.button("Send"):
        if not user_id or not query:
            st.error("User ID and query cannot be empty!")
        else:
            with st.spinner("Fetching response..."):
                response = requests.post(
                    f"{API_URL}/chat",
                    json={"user_id": user_id, "query": query, "include_web": include_web},
                )

                if response.status_code == 200:
                    data = response.json()
                    st.success("Response received:")
                    st.write(f"**Response:** {data['response']}")
                    if data.get("urls"):
                        st.write("**Indexed URLs:**")
                        for url in data["urls"]:
                            st.write(f"- {url}")
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

elif mode == "Upload File":
    st.title("Upload a File for Indexing")

    # User input for file upload
    user_id = st.text_input("Enter your User ID", value="default_user")
    uploaded_file = st.file_uploader("Upload a file")

    if st.button("Upload"):
        if not user_id or not uploaded_file:
            st.error("User ID and file cannot be empty!")
        else:
            with st.spinner("Uploading file..."):
                files = {"uploaded_file": uploaded_file}
                data = {"user_id": user_id}
                response = requests.post(
                    f"{API_URL}/upload",
                    data=data,
                    files={"uploaded_file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
                )

                if response.status_code == 200:
                    data = response.json()
                    st.success("File uploaded successfully!")
                    st.write(f"**File Path:** {data['file_path']}")
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")

elif mode == "Clear Global Content":
    def clear_global_content(user_id):
        """Function to trigger clearing of global content."""
        response = requests.get(f"{API_URL}/local_content/clear?user_id={user_id}")

        if response.status_code == 200:
            return "Global content cleared successfully!"
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"

    st.title("Clear Global Content")

    # Ask user for their user ID to clear content
    user_id = st.text_input("Enter your user ID to clear global content:")

    if st.button("Clear Content") and user_id:
        with st.spinner("Clearing global content..."):
            result_message = clear_global_content(user_id)
            
            # Display appropriate message based on result
            if "Error" in result_message:
                st.error(result_message)
            else:
                st.success(result_message)
    else:
        if not user_id:
            st.warning("Please enter a valid user ID.")

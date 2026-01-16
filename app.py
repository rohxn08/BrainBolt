import streamlit as st
import os
import time
from dotenv import load_dotenv
from src.pipeline import BrainBoltPipeline
from src.utils import list_available_models

# --- Page Configuration ---
st.set_page_config(
    page_title="BrainBolt ⚡",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load Environment Variables ---
load_dotenv()

# --- Custom CSS (Minimal for now) ---
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Configuration ---
with st.sidebar:
    st.title("⚡ BrainBolt")
    st.markdown("---")
    
    # API Key Handling
    api_key_input = st.text_input("Google API Key", type="password", help="Enter your Gemini API Key")
    
    # Use input key if provided, else fall back to env var
    if api_key_input:
        os.environ["GOOGLE_API_KEY"] = api_key_input
    
    current_key = os.getenv("GOOGLE_API_KEY")
    
    # Model Selection
    if current_key:
        try:
            available_models = list_available_models(current_key)
            selected_model = st.selectbox("Select Model", available_models, index=0 if available_models else None)
        except:
            st.error("Invalid API Key")
            selected_model = "gemini-1.5-flash" # Fallback
    else:
        st.warning("Please enter API Key to proceed.")
        selected_model = None

    st.markdown("---")
    st.markdown("### Settings")
    summary_type = st.selectbox(
        "Summary Style",
        ["concise", "detailed", "educational", "bullet_points", "executive", "exam_ready"]
    )

# --- Main Content ---
st.title("Unlock Knowledge ⚡")
st.markdown("Transform **Videos, Images, and Text** into clear summaries.")

# Input Method Tabs
tab1, tab2, tab3 = st.tabs(["📺 YouTube", "📷 Image", "📝 Text/File"])

source = None
input_type = None

with tab1:
    youtube_url = st.text_input("Paste YouTube URL", placeholder="https://youtube.com/watch?v=...")
    if youtube_url:
        source = youtube_url
        input_type = "youtube"

with tab2:
    uploaded_image = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        # Save temp file
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        img_path = os.path.join(temp_dir, uploaded_image.name)
        with open(img_path, "wb") as f:
            f.write(uploaded_image.getbuffer())
        
        st.image(uploaded_image, caption="Uploaded Image", width=300)
        source = img_path
        input_type = "image"

with tab3:
    # Future placeholder for file upload
    st.info("File upload coming soon. Paste text below for now.")
    text_input = st.text_area("Paste Text Content")
    if text_input:
        # Save as temp text file
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        txt_path = os.path.join(temp_dir, "input_text.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_input)
        source = txt_path
        input_type = "text"

# --- Process Button ---
if st.button("⚡ Generate Summary"):
    if not current_key:
        st.error("❌ Please provide a Google API Key in the sidebar.")
    elif not source:
        st.warning("⚠️ Please provide an input source (URL or Image).")
    else:
        try:
            with st.spinner("Processing... (This may take a moment)"):
                # Initialize Pipeline
                pipeline = BrainBoltPipeline()
                
                # Run Processing
                # Note: We aren't passing specific model yet, Pipeline uses default. 
                # We can update Pipeline later to accept model_name.
                result = pipeline.process(source, task="summarize", summary_type=summary_type)
                
                if "error" in result:
                    st.error(f"❌ Error: {result['error']}")
                else:
                    st.success("Analysis Complete!")
                    st.markdown("### 📝 Summary")
                    st.markdown("---")
                    st.markdown(result['result'])
                    st.markdown("---")
                    st.caption(f"Source Length: {result['source_text_length']} characters")
                    
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")


import streamlit as st
import requests
import os
import io
from PIL import Image
import base64

# Custom CSS for styling
st.markdown("""
    <style>
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin-bottom: 20px;
            padding: 10px;
            background-color: white;
        }

        .header img {
            max-width: 300px;  /* Adjust size as needed */
            height: auto;
            margin: 0;
        }

        .title-section {
            text-align: center;
            margin-bottom: 0px;
        }

        .button-container {
            display: flex;
            justify-content: center;
            gap: 20px;
            align-items: center;
            margin-bottom: 20px;
        }

        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
            position: relative;
            cursor: pointer;
        }

        .upload-area input[type="file"] {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
        }

        .terms {
            text-align: center;
            color: black;
            margin-bottom: 20px;
        }

        .upload-button {
            background-color: #4a148c;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            display: block;
            margin: 0 auto;
        }

        .upload-button:hover {
            background-color: #6a1b9a;
        }

        .upload-button-container {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }

        .upload-button-container img {
            width: 24px;
            height: 24px;
            margin-right: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Convert the logo to base64 (replace 'logo.png' with your file path)
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

logo_base64 = image_to_base64("logo.jpeg")

# Header with logo at top left
st.markdown(f"""
    <div class="header">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo"/>
        <h2>My App</h2>
    </div>
""", unsafe_allow_html=True)

# Title Section
st.markdown("""
<div class="title-section">
    <h1>Upload an Audio File or Record Live</h1>
    <p>You can either upload an existing audio file from your device or record a live audio session.</p>
</div>
""", unsafe_allow_html=True)

# Upload audio file
uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav"])
language = st.text_input("Language Code", "en-US")
keywords = st.text_input("Keywords (comma-separated)", "")

if uploaded_file and st.button("Process"):
    with st.spinner("Processing..."):
        # Prepare the data for the request
        files = {'file': (uploaded_file.name, uploaded_file, 'audio/mpeg')}
        data = {
            'language': language,
            'keywords': keywords
        }
        
        # Send the request to the Flask backend
        response = requests.post("http://127.0.0.1:5000/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            
            # Display transcription
            st.subheader("Transcription")
            st.write(result.get('transcription', 'No transcription available'))
            
            # Display overall metrics
            st.subheader("Overall Metrics")
            st.write(f"Precision: {result.get('overall_precision', 'N/A'):.2f}")
            st.write(f"Recall: {result.get('overall_recall', 'N/A'):.2f}")
            st.write(f"F1 Score: {result.get('overall_f1_score', 'N/A'):.2f}")
            
            # Display individual keyword metrics
            st.subheader("Keyword Metrics")
            for keyword, metrics in result.get('keyword_metrics', {}).items():
                st.write(f"Keyword '{keyword}':")
                st.write(f"  Precision: {metrics['precision']:.2f}")
                st.write(f"  Recall: {metrics['recall']:.2f}")
                st.write(f"  F1 Score: {metrics['f1_score']:.2f}")
                st.write(f"  True Positives: {metrics['true_positives']}")
                st.write(f"  False Positives: {metrics['false_positives']}")
                st.write(f"  False Negatives: {metrics['false_negatives']}")
            
            # Display keyword intervals
            st.subheader("Keyword Intervals")
            for keyword, start, end in result.get('keyword_intervals', []):
                st.write(f"Keyword '{keyword}' from {start:.2f}s to {end:.2f}s")
            
            # Display waveform plot
            waveform_plot_path = 'waveform_plot.png'
            if os.path.exists(waveform_plot_path):
                st.subheader("Waveform Plot")
                image = Image.open(waveform_plot_path)
                st.image(image)
        else:
            st.error(f"Error: {response.json().get('error', 'Unknown error occurred')}")
    
    # Remove the file after processing
    os.remove(uploaded_file.name)

# Terms and Conditions section
st.markdown("""
<div class="terms">
    <p>By uploading or recording audio you agree to our <a href='#' target='_blank'>Terms of Services</a>. To learn more about how your personal data is handled, check our <a href='#' target='_blank'>Privacy Policy</a>.</p>
</div>
""", unsafe_allow_html=True)

from flask import Flask, request, jsonify
from pydub import AudioSegment
import speech_recognition as sr
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import os

app = Flask(__name__)

# Initialize recognizer
recognizer = sr.Recognizer()

def preprocess_audio(input_file, output_file):
    """
    Convert and preprocess the audio file to ensure it's in the correct format and sample rate.
    """
    audio = AudioSegment.from_file(input_file)
    audio = audio.set_frame_rate(16000)  # Set standard sample rate
    audio = audio.set_channels(1)  # Ensure mono
    audio.export(output_file, format="wav")

def audio_to_text(audio_file, language='en-US'):
    """
    Convert audio file to text using SpeechRecognition with language support.
    """
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language=language)
            return text
        except sr.UnknownValueError:
            return "Google Speech Recognition could not understand audio"
        except sr.RequestError as e:
            return f"Could not request results from Google Speech Recognition service; {e}"
    except Exception as e:
        return f"Failed to read audio file: {e}"

def detect_keywords(transcription, keywords):
    """
    Check if each keyword is present in the transcription and return their start and end times.
    """
    keyword_intervals = []
    detected_keywords = []
    keyword_positions = {keyword: [] for keyword in keywords}
    if transcription:
        transcription = transcription.lower()
        for keyword in keywords:
            keyword = keyword.lower()
            start = transcription.find(keyword)
            if start != -1:
                end = start + len(keyword)
                keyword_intervals.append((keyword, start, end))
                detected_keywords.append(keyword)
                keyword_positions[keyword].append((start, end))
    return keyword_intervals, detected_keywords, keyword_positions

def compute_accuracy(detected_keywords, keywords):
    """
    Compute precision, recall, and F1 score based on detected and expected keywords.
    """
    true_positives = len(set(detected_keywords) & set(keywords))
    false_positives = len(detected_keywords) - true_positives
    false_negatives = len(keywords) - true_positives
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return precision, recall, f1_score

def compute_individual_keyword_metrics(keyword_positions, keywords):
    """
    Compute precision, recall, and F1 score for each individual keyword.
    """
    keyword_metrics = {}
    for keyword in keywords:
        true_positives = len(keyword_positions.get(keyword, []))
        false_positives = sum(len(keyword_positions.get(k, [])) for k in keyword_positions if k != keyword)
        false_negatives = 1 if true_positives == 0 else 0
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        keyword_metrics[keyword] = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }
    
    return keyword_metrics

def plot_waveform_with_keywords(audio_file, keyword_intervals_in_time):
    """
    Plot the waveform of the audio file with highlighted keyword intervals.
    """
    sample_rate, data = wavfile.read(audio_file)
    data = data.astype(float)
    N = len(data)
    T = 1.0 / sample_rate
    x = np.linspace(0.0, N*T, N)
    
    plt.figure(figsize=(12, 8))
    plt.plot(x, data, label='Waveform', color='b')

    for keyword, start, end in keyword_intervals_in_time:
        plt.axvspan(start, end, color='yellow', alpha=0.5, label=f'Keyword: {keyword}')
    
    plt.title('Waveform with Keyword Intervals')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    
    plt.tight_layout()
    plt.savefig('waveform_plot.png')  # Save plot as an image
    plt.close()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    language = request.form.get('language', 'en-US')
    keywords = request.form.get('keywords', '').split(',')

    if not file:
        return jsonify({'error': 'No file part'}), 400

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the file locally
    file_path = f'./{file.filename}'
    file.save(file_path)
    
    output_file = "processed_audio.wav"
    preprocess_audio(file_path, output_file)
    
    # Convert audio to text
    transcription = audio_to_text(output_file, language)
    
    if transcription:
        keyword_intervals, detected_keywords, keyword_positions = detect_keywords(transcription, keywords)
        precision, recall, f1_score = compute_accuracy(detected_keywords, keywords)
        keyword_metrics = compute_individual_keyword_metrics(keyword_positions, keywords)

        sample_rate, _ = wavfile.read(output_file)
        audio_duration = len(_) / sample_rate
        keyword_intervals_in_time = [(keyword, start / len(transcription) * audio_duration, (end) / len(transcription) * audio_duration) for keyword, start, end in keyword_intervals]
        
        plot_waveform_with_keywords(output_file, keyword_intervals_in_time)
        
        results = {
            'transcription': transcription,
            'overall_precision': precision,
            'overall_recall': recall,
            'overall_f1_score': f1_score,
            'keyword_metrics': keyword_metrics,
            'keyword_intervals': keyword_intervals_in_time
        }
        return jsonify(results)
    else:
        return jsonify({'error': 'No transcription available'}), 500

if __name__ == '__main__':
    app.run(debug=True)

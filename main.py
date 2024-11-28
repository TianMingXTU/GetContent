import datetime
import logging
import time
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import threading
import requests
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import os
import json
from aip import AipSpeech
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global Configurations
config = None
selected_files = []

def load_config():
    """Load configuration from a JSON file."""
    config_path = "config.json"
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except Exception as e:
        messagebox.showerror("Configuration Error", f"Failed to load configuration: {e}")
        exit()

def save_results_to_json(original_text, summary_text):
    """Save results to a JSON file."""
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"summary_{formatted_datetime}.json"
    data = {
        "original_text": original_text,
        "summary": summary_text
    }
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"Results saved to {file_name}")

def extract_audio_from_video(video_path, audio_path="temp_audio.wav"):
    """Extract audio from video."""
    try:
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path)
        clip.close()
        return audio_path
    except Exception as e:
        logging.error(f"Failed to extract audio: {e}")
        return None

def recognize_audio(audio_path, use_baidu=False):
    """Recognize audio using Baidu or Google API."""
    if audio_path.endswith('.mp3'):
        sound = AudioSegment.from_mp3(audio_path)
        sound.export(audio_path, format="wav")

    if use_baidu:
        client = AipSpeech(config["BAIDU_APP_ID"], config["BAIDU_API_KEY"], config["BAIDU_SECRET_KEY"])
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        result = client.asr(audio_data, 'wav', 16000, {'dev_pid': 1537})
        if result['err_no'] == 0:
            return result['result'][0]
        else:
            logging.error(f"Baidu recognition error: {result['err_msg']}")
            return None
    else:
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
                return recognizer.recognize_google(audio_data, language='zh-CN')
        except Exception as e:
            logging.error(f"Google recognition error: {e}")
            return None

def summarize_text(text):
    """Summarize text using external API."""
    try:
        headers = {'Authorization': f'Bearer {config["key"]}', 'Content-Type': 'application/json'}
        data = {'model': 'gpt-3.5-turbo', 'messages': [{'role': 'user', 'content': text}], 'stream': False}
        response = requests.post(config["base_url"], headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Error summarizing text: {e}")
        return None

def split_video(video_path, segment_duration=600):
    """Split video into segments."""
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        segments = []
        for start in range(0, int(duration), segment_duration):
            end = min(start + segment_duration, duration)
            segment_clip = clip.subclip(start, end)
            segment_filename = f"{video_path}_segment_{start}_{end}.mp4"
            segment_clip.write_videofile(segment_filename, codec="libx264", audio_codec="aac")
            segments.append(segment_filename)
        clip.close()
        return segments
    except Exception as e:
        logging.error(f"Error splitting video: {e}")
        return []

def process_file(file_path, file_type, result_text, progress_var):
    """Process a single file."""
    try:
        progress_var.set(0)
        if file_type == '视频':
            segments = split_video(file_path)
            summaries = []
            for segment in segments:
                audio_path = extract_audio_from_video(segment)
                if audio_path:
                    recognized_text = recognize_audio(audio_path, use_baidu=config.get("BAIDU_TYPE", False))
                    if recognized_text:
                        summary = summarize_text(recognized_text)
                        if summary:
                            summaries.append(summary)
                os.remove(segment)
            combined_summary = " ".join(summaries)
            final_summary = summarize_text(combined_summary)
            result_text.insert(tk.END, f"总结:\n{final_summary}")
            save_results_to_json(combined_summary, final_summary)
        progress_var.set(100)
    except Exception as e:
        logging.error(f"Error processing file: {e}")

def start_processing(file_type, result_text, progress_var):
    """Start processing selected files."""
    if not selected_files:
        messagebox.showerror("错误", "未选择任何文件")
        return
    with ThreadPoolExecutor() as executor:
        for file_path in selected_files:
            executor.submit(process_file, file_path, file_type, result_text, progress_var)

def setup_gui(root, progress_var):
    """Setup GUI."""
    root.title("内容总结器")
    root.geometry("800x600")
    ttk.Label(root, text="文件类型:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
    file_type_var = tk.StringVar(value='视频')
    ttk.Combobox(root, textvariable=file_type_var, values=['视频', '音频'], state="readonly").grid(row=0, column=1, padx=10, pady=10, sticky='ew')
    ttk.Button(root, text="选择多个文件", command=lambda: select_files(file_type_var)).grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
    progress_bar = ttk.Progressbar(root, orient='horizontal', mode='determinate', variable=progress_var)
    progress_bar.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky='ew')
    result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    result_text.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
    ttk.Button(root, text="开始处理", command=lambda: start_processing(file_type_var.get(), result_text, progress_var)).grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(3, weight=1)

def select_files(file_type_var):
    """Select files."""
    global selected_files
    file_types = [('所有文件', '*.*')] if file_type_var.get() == '音频' else [('视频文件', '*.mp4 *.avi *.mov'), ('音频文件', '*.mp3 *.wav')]
    selected_files = filedialog.askopenfilenames(filetypes=file_types)
    if selected_files:
        messagebox.showinfo("文件选择", f"已选择{len(selected_files)}个文件")

def main():
    """Main function."""
    global config
    config = load_config()
    root = tk.Tk()
    progress_var = tk.DoubleVar()
    setup_gui(root, progress_var)
    root.mainloop()

if __name__ == "__main__":
    main()

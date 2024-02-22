import logging
import time
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk, Menu
import threading
import requests
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import os
import json
from PIL import Image, ImageTk

# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_config():
    # Load configuration from a JSON file
    config_path = "config.json"
    try:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except Exception as e:
        messagebox.showerror("Configuration Error", f"Failed to load configuration: {e}")
        exit()


config = load_config()
base_url = config.get("base_url", "")
key = config.get("key", "")


def save_results_to_json(original_text, summary_text):
    timestamp = int(time.time())
    file_name = f"summary_{timestamp}.json"
    data = {
        "original_text": original_text,
        "summary": summary_text
    }
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Results saved to {file_name}")


def create_right_click_menu(widget):
    # Create a right-click context menu for copying text
    def copy():
        widget.event_generate("<<Copy>>")

    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Copy", command=copy)

    def show_menu(event):
        menu.post(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)


def summarize_text(text, progress_callback):
    try:
        prom = "假如你是一名伟大的文字总结大师，请你帮我总结后面的文字。\n"
        headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json', }
        data = {'model': 'gpt-3.5-turbo', 'messages': [{'role': 'user', 'content': prom + text}], 'stream': False}
        response = requests.post(base_url, headers=headers, json=data)
        result = response.json()
        progress_callback(100)
        return result['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Error summarizing text: {e}")
        messagebox.showerror("Error", "Failed to summarize text.")
        return None


def extract_audio_from_video(video_path, audio_path="temp_audio.wav", progress_callback=lambda x: None):
    try:
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path)
        clip.close()
        progress_callback(20)  # Assume audio extraction is 20% of the work
        return audio_path
    except Exception as e:
        logging.error(f"Failed to extract audio: {e}")
        messagebox.showerror("Error", "Failed to extract audio.")
        return None


def recognize_audio(audio_path, progress_callback):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            progress_callback(50)  # Assume speech recognition is up to 50% of the work
            text = recognizer.recognize_google(audio_data, language='zh-CN')
            progress_callback(80)  # Speech recognition done
            return text
    except Exception as e:
        logging.error(f"Failed to recognize speech: {e}")
        messagebox.showerror("Error", "Failed to recognize speech.")
        return None


def setup_gui(root, progress_var):
    root.title("内容总结器")
    root.geometry("800x600")

    # 文件类型选择
    ttk.Label(root, text="文件类型:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
    file_type_var = tk.StringVar(value='视频')
    ttk.Combobox(root, textvariable=file_type_var, values=['视频', '音频'], state="readonly").grid(row=0, column=1,
                                                                                                   padx=10, pady=10,
                                                                                                   sticky='ew')

    # 选择多个文件按钮
    ttk.Button(root, text="选择多个文件", command=lambda: select_files(file_type_var)).grid(row=1, column=0,
                                                                                            columnspan=2, padx=10,
                                                                                            pady=10, sticky='ew')

    # 进度条
    progress_bar = ttk.Progressbar(root, orient='horizontal', mode='determinate', variable=progress_var)
    progress_bar.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky='ew')

    # 结果显示文本框
    result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    result_text.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

    # 开始处理按钮
    ttk.Button(root, text="开始处理",
               command=lambda: start_processing(file_type_var.get(), result_text, progress_var)).grid(row=4,
                                                                                                      column=0,
                                                                                                      columnspan=2,
                                                                                                      padx=10,
                                                                                                      pady=10,
                                                                                                      sticky='ew')

    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(3, weight=1)

    create_right_click_menu(result_text)


selected_files = []


def select_files(file_type_var):
    global selected_files
    file_types = [('所有文件', '*.*')] if file_type_var.get() == '音频' else [('视频文件', '*.mp4 *.avi *.mov'),
                                                                              ('音频文件', '*.mp3 *.wav')]
    selected_files = filedialog.askopenfilenames(filetypes=file_types)
    if selected_files:
        messagebox.showinfo("文件选择", f"已选择{len(selected_files)}个文件")


def start_processing(file_type, result_text, progress_var):
    if not selected_files:
        messagebox.showerror("错误", "未选择任何文件")
        return
    for file_path in selected_files:
        threading.Thread(target=process_file, args=(file_path, file_type, result_text, progress_var),
                         daemon=True).start()


def process_file(file_path, file_type, result_text, progress_var):
    def update_progress(progress):
        progress_var.set(progress)

    try:
        update_progress(0)
        audio_path = extract_audio_from_video(file_path,
                                              progress_callback=update_progress) if file_type == '视频' else file_path
        if audio_path:
            recognized_text = recognize_audio(audio_path, progress_callback=update_progress)
            if recognized_text:
                summary = summarize_text(recognized_text, progress_callback=update_progress)
                if summary:
                    result_text.delete('1.0', tk.END)
                    result_text.insert(tk.END, f"原文:\n{recognized_text}\n\n总结:\n{summary}")
                    save_results_to_json(recognized_text, summary)  # Save results to JSON
                if file_type == '视频' and audio_path != file_path:
                    os.remove(audio_path)
            update_progress(100)
    except Exception as e:
        logging.error(f"Failed to process file: {e}")
        messagebox.showerror("Error", "An error occurred during file processing.")


def main():
    root = tk.Tk()
    progress_var = tk.DoubleVar()
    setup_gui(root, progress_var)
    root.mainloop()


if __name__ == "__main__":
    main()

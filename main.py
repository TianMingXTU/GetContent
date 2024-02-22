import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk, Menu
import threading

import requests
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import os
from tkinter import font as tkFont

base_url = ''
key = ''
# 假设 summarize_text 函数已定义并可用
def summarize_text(text):
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    }

    # print(org)
    prompt = '假如你是一名伟大的文字总结大师，请你帮我总结后面的文字。'
    print(prompt + text)
    json_data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'user',
                'content': prompt + text,
            },
        ],
        'stream': False,
    }

    response = requests.post(base_url, headers=headers,
                             json=json_data)
    result = response.json()
    content = result['choices'][0]['message']['content']
    return content


def extract_audio_from_video(video_file_path, audio_file_path="temp_audio.wav"):
    try:
        video = VideoFileClip(video_file_path)
        video.audio.write_audiofile(audio_file_path)
        video.close()
        return audio_file_path
    except Exception as e:
        messagebox.showerror("错误", f"提取音频失败: {e}")
        return None


def process_audio(audio_file_path):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='zh-CN')
            return text
    except Exception as e:
        messagebox.showerror("错误", f"语音识别失败: {e}")
        return None


def create_popup_menu(widget):
    """为文本框创建右键弹出菜单"""
    popup_menu = Menu(widget, tearoff=0)
    popup_menu.add_command(label="复制", command=lambda: widget.event_generate("<<Copy>>"))
    popup_menu.add_separator()
    popup_menu.add_command(label="清空", command=lambda: widget.delete('1.0', tk.END))

    def popup(event):
        try:
            popup_menu.tk_popup(event.x_root, event.y_root)
        finally:
            popup_menu.grab_release()

    widget.bind("<Button-3>", popup)  # Windows上为<Button-3>
    # 如果是在macOS上，可能需要改为<Button-2>


def update_gif(index=0):
    """循环显示GIF动画帧"""
    if processing_video:  # 检查是否仍在处理视频
        frame = gif_frames[index]
        index = (index + 1) % len(gif_frames)
        gif_label.configure(image=frame)
        root.after(100, update_gif, index)  # 每100ms更新一次帧
    else:
        gif_label.grid_remove()  # 处理完成后隐藏GIF动画


def process_file_thread(file_type):
    global processing_video
    processing_video = True  # 开始处理时设置为True
    gif_label.grid(row=4, column=0, columnspan=2)  # 显示等待动画
    update_gif()  # 启动动画
    file_path = file_path_var.get()
    if file_type == '视频':
        audio_path = extract_audio_from_video(file_path)
    else:
        audio_path = file_path  # 直接使用上传的音频文件
    if audio_path:
        text = process_audio(audio_path)
        if text:
            summary = summarize_text(text)
            result_text.delete('1.0', tk.END)
            result_text.insert(tk.END, f"原文:\n{text}\n\n总结:\n{summary}")
        if file_type == '视频':
            os.remove(audio_path)  # 清理临时音频文件
    processing_video = False  # 处理结束时设置为False


def process_file(file_type):
    threading.Thread(target=process_file_thread, args=(file_type,), daemon=True).start()


def choose_file():
    file_type = file_type_var.get()
    file_types = [('所有文件', '*.*')]
    if file_type == '视频':
        file_types = [('视频文件', '*.mp4 *.avi *.mov')]
    elif file_type == '音频':
        file_types = [('音频文件', '*.mp3 *.wav *.aac')]
    file_path = filedialog.askopenfilename(filetypes=file_types)
    file_path_var.set(file_path)


def setup_gui(root):
    root.title("视频内容总结器")
    ttk.Label(root, text="选择文件类型:").grid(row=0, column=0, padx=10, pady=5, sticky='w')
    ttk.Combobox(root, textvariable=file_type_var, values=['视频', '音频'], state="readonly").grid(row=0, column=1,
                                                                                                   sticky="ew", padx=10,
                                                                                                   pady=5)
    ttk.Button(root, text="选择文件", command=choose_file).grid(row=1, column=0, columnspan=2, sticky="ew", padx=10,
                                                                pady=5)
    ttk.Button(root, text="处理", command=lambda: process_file(file_type_var.get())).grid(row=2, column=0, columnspan=2,
                                                                                          sticky="ew", padx=10, pady=5)
    ttk.Progressbar(root, variable=progress_var, maximum=1).grid(row=3, column=0, columnspan=2, sticky="ew", padx=10,
                                                                 pady=5)
    result_text.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(5, weight=1)
    create_popup_menu(result_text)


root = tk.Tk()
root.geometry("600x400")
file_path_var = tk.StringVar()
# 确保字体已经安装在系统中，然后使用字体的名称
custom_font = tkFont.Font(family="STKAITI.TTF", size=12)
file_type_var = tk.StringVar(value='视频')  # 默认值为'视频'
progress_var = tk.DoubleVar()
result_text = scrolledtext.ScrolledText(root, height=20)
result_text.configure(font=custom_font)
gif_frames = [tk.PhotoImage(file='111.gif', format=f'gif -index {i}') for i in range(5)]  # 更新为正确的GIF帧数和文件名
gif_label = tk.Label(root)

setup_gui(root)

root.mainloop()

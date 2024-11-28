<!--
 * @Author: TianMingXTU 1600410115@qq.com
 * @Date: 2024-11-28 11:42:39
 * @LastEditors: TianMingXTU 1600410115@qq.com
 * @LastEditTime: 2024-11-28 11:55:04
 * @FilePath: \GitPull\GetContent\README.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# 视频内容总结器

这是一个基于 tkinter 的简单视频内容总结器应用程序。用户可以选择视频或音频文件，并通过语音识别和文本总结来获取内容摘要。

## 使用说明

### 选择文件类型

- 在顶部下拉菜单中选择要处理的文件类型：视频或音频。

### 选择文件

- 点击“选择文件”按钮以浏览并选择要处理的视频或音频文件。

### 处理

- 选择文件后，点击“处理”按钮开始处理所选文件。
- 处理过程包括提取音频（如果处理的是视频文件）、语音识别和文本总结。
- 处理完成后，原始文本和总结文本将显示在应用程序窗口中。

### 文本框右键菜单

- 可以通过右键单击结果文本框来复制文本或清空文本框内容。

## 配置文件说明

应用程序使用 `config.json` 文件来存储必要的配置项。以下是每个配置项的详细说明：

- `base_url`：API 的基础 URL，用于文本总结功能。例如，`https://api.example.com`。
- `key`：API 密钥，用于身份验证。
- `BAIDU_APP_ID`：百度语音识别的 APP ID。
- `BAIDU_API_KEY`：百度语音识别的 API 密钥。
- `BAIDU_SECRET_KEY`：百度语音识别的 Secret Key。
- `BAIDU_TYPE`：是否使用百度语音识别。设置为 `True` 表示使用百度语音识别，`False` 表示使用 Google 语音识别。

请根据实际需求填写 `config.json` 文件中的配置项。

## 注意事项

- 请确保系统中已安装所需字体（如 `STKAITI.TTF`）以确保良好的显示效果。
- 应用程序需要以下依赖项，请确保已安装：
  - `moviepy`
  - `pydub`
  - `SpeechRecognition`
  - 其他依赖项请参考 `requirements.txt` 文件。
- 如果遇到问题，请检查日志文件 `app.log` 以获取详细的错误信息。

## 运行方法

1. 确保已安装 Python 3.7 或更高版本。
2. 安装依赖项：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行应用程序：
   ```bash
   python main.py
   ```

## 日志记录

应用程序会将运行过程中的信息记录到 `app.log` 文件中，包括错误信息和处理进度。请在遇到问题时检查该文件。

这里是提交课程大作业小组项目的库，而非单日作业。

# 视频字幕生成器

## 1. 项目介绍

本项目实现了一个可以生成能够区分说话人的视频字幕的应用。

预期实现以下功能：

1. 字幕AI识别，以及说话人区分
2. 对于生成字幕的人工微调
3. 作为视频播放器预览字幕生成结果
4. 导出生成的字幕

## 2. 使用技术

1. 图形界面制作：`flet`
2. 语音识别：初使用`facebook/wav2vec2`模型，准确度堪忧（甚至有错别字），后更换为`openai-whisper`
3. 声纹分割聚类：使用`pyannote/speaker-diarization-3.1`模型

## 3. AI Prompt

对于该项目中涉及的重要AI使用记录详见`AIPrompt`文件夹。

## 4. 部署说明

受`sentencepiece`包（`pyannote.audio`依赖）影响，本项目采用Python3.12，使用uv作项目管理。

部署步骤如下：
### 4.1 安装uv

详见[官方文档](https://docs.astral.sh/uv/getting-started/installation/)。

### 4.2 安装FFmpeg并添加进PATH

详见[官网](https://ffmpeg.org/)。

### 4.3 下载源代码

```shell
git clone https://github.com/z5ar/ProjectFor2025AICourse.git
```

### 4.4 下载包

终端切换到项目文件夹，根据实际情况，选用以下二者之一：

希望只使用CPU，请使用
```shell
uv sync --extra cpu
```

希望使用`CUDA12.8`及以上版本进行GPU加速，请使用
```shell
uv sync --extra cu128
```

希望使用`CUDA11.8`及以上版本进行GPU加速，请使用
```shell
uv sync --extra cu118
```

### 4.5 配置token、文件上传以及模型下载目录

在项目文件夹，运行以下指令：

```shell
python main.py
```

程序会自动生成`config.toml`，然后退出。

打开`config.toml`，根据注释，修改你的token、文件上传以及模型下载目录。

如何获取token？
1. 首先要有一个能够访问Hugging Face的网络环境。
2. 同意[pyannote/segmentation-3.0](https://hf.co/pyannote/segmentation-3.0)的用户协议。
3. 同意[pyannote/speaker-diarization-3.1](https://hf.co/pyannote/speaker-diarization-3.1)的用户协议。
4. 在[这里](hf.co/settings/tokens)创建Hugging Face Token。

### 4.6 运行

本地运行，可以在终端中输入：

```shell
uv run uvicorn main:app
```
终端中出现以下信息：
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
打开浏览器，输入网址`http://127.0.0.1:8000`即可使用。

希望共享到局域网，可以使用：
```shell
uv run uvicorn main:app --host 0.0.0.0
```

## 5. 效率参考

测试电脑配置：
|项目|配置|
|---|---|
|CPU|AMD Ryzen 7 7735H with Radeon Graphics   3.20 GHz|
|RAM|16.0 GB|
|GPU|NVIDIA GeForce RTX 4060 Laptop|

测试时电脑使用独立显卡。

1. 测试1：2min英语四级听力

|项目|用时|
|---|---|
|提取音频|3s|
|说话者辨别|70s|
|语音识别|28s|
|杂项|忽略不计|
|生成总用时|101s|

2. 测试2：约23min40s全套英语四级听力

|项目|用时|
|---|---|
|提取音频|8.5s|
|说话者辨别|967.5s|
|语音识别|131s|
|杂项|忽略不计|
|生成总用时|1107s|

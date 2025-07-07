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
2. 语音识别：使用`facebook/wav2vec2-large-960h-lv60-self`模型，准确度堪忧（甚至有错别字），考虑更换为`whisper`
3. 声纹分割聚类：使用`pyannote/speaker-diarization-3.1`模型


## 3. AI Prompt

对于该项目中涉及的重要AI使用记录详见`AIPrompt`文件夹。

## 4. 部署说明

受`sentencepiece`包影响，本项目采用Python3.12，使用uv作项目管理。

希望只使用CPU，请使用
```
uv sync --extra cpu
```

希望使用CUDA12.8及以上版本进行GPU加速，请使用
```
uv sync --extra cu128
```

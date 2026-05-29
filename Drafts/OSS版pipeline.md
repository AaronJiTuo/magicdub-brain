# MagicDub OSS pipeline

## 一、保存原视频

    1. 复制到工作目录

## 二、提取原音频

    1. ffmpeg:提取视频中的原音频
    2. 本地保存：source_audio.mp3

## 三、分离人声

    1. 上传 ource_audio.mp3 到存储对象
    2. demucs:分离vocals
    3. 下载vocals.mp3，本地保存

## 四、抠出 residual 

    1. ffmpeg: source_audio - vocals * aplha
    2. 本地保存： residual.mp3

## 五、ASR

    1. 上传 vocals.mp3 到存储对象
    2. wizper: ASR
    3. 本地保存： asr.json

## 六、构建 sentences.json

## 七、切割 vocals

    1. ffmpeg: 根据逐句时间切割
    2. 本地保存：sentences_s*.mp3

## 八、翻译

    1. gemini: 翻译
    2. 保存结果

## 九、TTS

    1. 上传 sentence_s*.mp3
    2. index-tts-2: TTS
    3. 下载 sentence_s*_tts.mp3

## 十、对齐句级时长

    1. ffmpeg: 伸缩 sentence_s*_tts.mp3
    2. 本地保存：sentence_s*_audio.mp3

## 十一、拼装

    1. ffmpeg: 组装
    2. 输出：result_video.mp4


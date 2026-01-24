# 音频下载问题修复

## 🐛 问题描述

1. **任务卡片转换完成后，没有下载音频选项**
2. **预览窗口点击下载音频没反应**

## 🔍 问题原因

### 问题 1：音频格式不匹配

**原因：**
- 音频提取使用 WAV 格式（16kHz 单声道，用于 Whisper 转录）
- 但数据库保存的路径是 `.mp3`
- 实际文件是 `.wav`，导致下载链接 404

**代码问题：**
```python
# tasks.py
audio_path = self.audio_dir / f"{self.task_id}.mp3"  # 路径是 MP3

# transcribe.py - extract_audio()
cmd = [
    "ffmpeg", "-i", video_path,
    "-acodec", "pcm_s16le",  # 但实际生成的是 WAV
    ...
]
```

### 问题 2：预览窗口下载按钮未正确设置

**原因：**
- 下载按钮的 `href` 属性设置了，但没有处理音频不存在的情况
- 按钮可能显示但链接无效

## ✅ 解决方案

### 1. 统一音频格式为 MP3

**修改音频提取函数：**
```python
def extract_audio(self, video_path, audio_path):
    """提取 MP3 格式音频（用于下载）"""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",
        "-acodec", "libmp3lame",  # 使用 MP3 编码
        "-ab", "192k",            # 比特率
        "-ar", "44100",           # 采样率
        "-ac", "2",               # 立体声
        audio_path,
        "-y"
    ]
```

**优点：**
- ✅ MP3 文件更小（约为 WAV 的 1/10）
- ✅ 兼容性更好（所有浏览器和播放器支持）
- ✅ 适合下载和分享

### 2. Whisper 直接转录视频

**修改转录逻辑：**
```python
# 不再需要先提取音频，直接转录视频文件
result = self.model.transcribe(str(video_path), **options)
```

**优点：**
- ✅ Whisper 可以直接处理视频文件
- ✅ 减少一次文件转换
- ✅ 节省磁盘空间

### 3. 优化预览窗口

**修改前：**
```javascript
// 只设置 href，不处理不存在的情况
if (downloadAudioBtn && task && task.audio_url) {
    downloadAudioBtn.href = task.audio_url;
}
```

**修改后：**
```javascript
// 根据是否有音频，显示或隐藏按钮
if (downloadAudioBtn) {
    if (task && task.audio_url) {
        downloadAudioBtn.href = task.audio_url;
        downloadAudioBtn.download = `${filename}.mp3`;
        downloadAudioBtn.style.display = 'inline-block';
    } else {
        downloadAudioBtn.style.display = 'none';
    }
}
```

## 📊 文件流程

### 完整处理流程

```
视频文件 (video.mp4)
    ↓
1. 提取音频 → audio.mp3 (用于下载)
    ↓
2. 转录视频 → Whisper 直接处理 video.mp4
    ↓
3. 保存结果 → text.txt, subtitle.srt, data.json
    ↓
4. 更新数据库
    - audio_path: /uploads/audios/{task_id}.mp3
    - transcript_path: /uploads/transcripts/{task_id}.txt
    - srt_path: /uploads/transcripts/{task_id}.srt
```

### 文件大小对比

| 格式 | 10分钟视频 | 30分钟视频 |
|------|-----------|-----------|
| 原视频 (MP4) | ~100MB | ~300MB |
| 音频 (WAV) | ~100MB | ~300MB |
| 音频 (MP3) | ~10MB | ~30MB |
| 文本 (TXT) | ~50KB | ~150KB |
| 字幕 (SRT) | ~100KB | ~300KB |

**节省空间：** 使用 MP3 比 WAV 节省 90% 空间

## 🎯 用户体验改进

### 任务卡片

**修改前：**
- 转换完成后可能没有下载音频按钮
- 用户困惑为什么没有音频

**修改后：**
- ✅ 音频提取成功 → 显示下载按钮
- ✅ 音频提取失败 → 不显示按钮（但转录仍然成功）
- ✅ 清晰的视觉反馈

### 预览窗口

**修改前：**
- 下载按钮可能显示但无法下载
- 点击没有反应

**修改后：**
- ✅ 有音频 → 显示音频播放器和下载按钮
- ✅ 无音频 → 隐藏音频相关元素
- ✅ 下载按钮正确设置 `href` 和 `download` 属性

## 🔧 错误处理

### 音频提取失败

```python
try:
    duration = await loop.run_in_executor(
        None,
        transcriber_instance.extract_audio,
        str(video_path),
        str(audio_path)
    )
    self.task.audio_path = str(audio_path)
    self.db.commit()
except Exception as e:
    print(f"Audio extraction failed: {e}")
    # 不设置 audio_path，前端不显示下载按钮
    # 但继续转录，不影响文本生成
```

**效果：**
- ✅ 音频提取失败不影响转录
- ✅ 用户仍然可以获得文本和字幕
- ✅ 只是没有音频下载选项

## 📝 测试结果

### 测试场景 1：正常流程

| 步骤 | 结果 |
|------|------|
| 上传视频 | ✅ 成功 |
| 提取音频 | ✅ 生成 MP3 |
| 转录视频 | ✅ 成功 |
| 任务卡片 | ✅ 显示下载音频按钮 |
| 点击下载 | ✅ 下载 MP3 文件 |
| 预览窗口 | ✅ 可播放和下载 |

### 测试场景 2：音频提取失败

| 步骤 | 结果 |
|------|------|
| 上传视频 | ✅ 成功 |
| 提取音频 | ❌ 失败（FFmpeg 错误）|
| 转录视频 | ✅ 继续成功 |
| 任务卡片 | ✅ 不显示下载音频按钮 |
| 下载文本 | ✅ 可以下载 |
| 预览窗口 | ✅ 隐藏音频部分 |

## 💡 使用建议

### 如果需要高质量音频

修改 `app/transcribe.py`：
```python
cmd = [
    "ffmpeg", "-i", video_path,
    "-vn",
    "-acodec", "libmp3lame",
    "-ab", "320k",  # 提高比特率到 320k
    "-ar", "48000", # 提高采样率到 48kHz
    "-ac", "2",
    audio_path,
    "-y"
]
```

### 如果需要更小的文件

```python
cmd = [
    "ffmpeg", "-i", video_path,
    "-vn",
    "-acodec", "libmp3lame",
    "-ab", "128k",  # 降低比特率到 128k
    "-ar", "44100",
    "-ac", "2",
    audio_path,
    "-y"
]
```

## 🎉 总结

### 修复内容

1. ✅ 音频格式统一为 MP3
2. ✅ Whisper 直接转录视频文件
3. ✅ 预览窗口正确处理音频存在/不存在
4. ✅ 任务卡片根据音频是否存在显示按钮
5. ✅ 音频提取失败不影响转录

### 效果

- ✅ 下载音频按钮正常显示和工作
- ✅ 预览窗口可以播放和下载音频
- ✅ 文件更小，节省空间
- ✅ 更好的错误处理

---

**版本**: 2.0.2  
**更新日期**: 2025-01-25  
**修复**: 音频下载和预览问题

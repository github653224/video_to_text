# 🚀 快速开始指南

## 5分钟快速部署

### 方法一：使用 Docker（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/video-to-text.git
cd video-to-text

# 2. 启动服务
docker-compose up -d

# 3. 访问应用
open http://localhost:8000
```

### 方法二：本地部署

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/video-to-text.git
cd video-to-text

# 2. 创建虚拟环境
conda create -n torch python=3.9
conda activate torch

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 FFmpeg
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# 5. 启动服务
chmod +x run.sh
./run.sh

# 6. 访问应用
open http://localhost:8000
```

## 基本使用

### 1. 上传视频

- 点击上传区域选择文件
- 或直接拖放视频文件
- 支持多选（Ctrl/Cmd + 点击）

### 2. 开始转换

- 点击"开始转换"按钮
- 实时查看进度
- 等待转换完成

### 3. 下载结果

- 点击"预览结果"查看内容
- 下载文本文件（TXT）
- 下载字幕文件（SRT）
- 下载音频文件（MP3）

## 常见问题

### Q: 首次运行很慢？
A: Whisper 模型首次使用需要下载（约 74MB），请耐心等待。

### Q: 支持哪些视频格式？
A: MP4, AVI, MOV, MKV, WebM

### Q: 最大文件大小？
A: 500MB

### Q: 转换需要多久？
A: 取决于视频长度，通常 1分钟视频需要 30秒左右。

### Q: 如何提高准确率？
A: 使用清晰的人声视频，避免背景噪音。

## 进阶配置

### 更换 Whisper 模型

编辑 `app/transcribe.py`：

```python
# 可选: tiny, base, small, medium, large
transcriber = VideoTranscriber(model_size="medium")
```

### 修改文件大小限制

编辑 `app/main.py`：

```python
MAX_FILE_SIZE = 1000 * 1024 * 1024  # 1GB
```

### 使用 GPU 加速

```bash
# 安装 CUDA 版本的 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 获取帮助

- 📖 查看完整文档：[README.md](README.md)
- 🐛 报告问题：[GitHub Issues](https://github.com/yourusername/video-to-text/issues)
- 💬 讨论交流：[GitHub Discussions](https://github.com/yourusername/video-to-text/discussions)

---

**祝你使用愉快！** 🎉

# 🎬 视频转文字工具 (Video to Text)

基于 OpenAI Whisper 的智能视频转文字工具，支持批量上传、大文件处理和实时进度跟踪。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)

## ✨ 功能特性

- 🚀 **快速转录**：基于 OpenAI Whisper 模型，准确识别中文语音
- 📦 **批量处理**：支持同时上传多个视频文件
- 💾 **大文件支持**：支持最大 500MB 的视频文件
- 🔄 **实时进度**：WebSocket 实时推送转换进度
- 🎵 **音频提取**：自动提取 MP3 音频文件供下载
- 📝 **多格式输出**：支持 TXT、SRT 字幕、JSON 格式
- 🌐 **现代界面**：响应式设计，支持桌面和移动设备
- ⚡ **并发处理**：多任务并发转换，互不阻塞

## 📋 支持格式

**输入格式**：MP4, AVI, MOV, MKV, WebM

**输出格式**：
- 📄 TXT - 纯文本
- 🎬 SRT - 字幕文件
- 🎵 MP3 - 音频文件
- 📊 JSON - 完整数据

## 🛠️ 技术栈

- **后端**：FastAPI + SQLAlchemy + SQLite
- **AI 模型**：OpenAI Whisper
- **音视频处理**：FFmpeg
- **前端**：Bootstrap 5 + Vanilla JavaScript
- **实时通信**：WebSocket

## 📦 安装部署

### 前置要求

- Python 3.8+
- FFmpeg
- Conda (推荐)

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/video-to-text.git
cd video-to-text
```

### 2. 创建虚拟环境

```bash
# 使用 conda (推荐)
conda create -n torch python=3.9
conda activate torch

# 或使用 venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装 FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
下载并安装：https://ffmpeg.org/download.html

### 5. 启动应用

```bash
# 使用启动脚本（自动激活 conda 环境）
chmod +x run.sh
./run.sh

# 或手动启动
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：http://localhost:8000

## � 使用方法

### 基本使用

1. 打开浏览器访问 http://localhost:8000
2. 点击或拖放视频文件到上传区域
3. 点击"开始转换"按钮
4. 等待转换完成
5. 下载文本、字幕或音频文件

### 批量上传

1. 选择多个视频文件（支持 Ctrl/Cmd + 点击）
2. 或拖放多个文件到上传区域
3. 系统会自动逐个处理

### API 使用

```python
import requests

# 上传视频
files = {'file': open('video.mp4', 'rb')}
response = requests.post('http://localhost:8000/upload', files=files)
task_id = response.json()['task_id']

# 查询任务状态
response = requests.get(f'http://localhost:8000/tasks/{task_id}')
print(response.json())

# 下载结果
response = requests.get(f'http://localhost:8000/download/text/{task_id}')
with open('transcript.txt', 'wb') as f:
    f.write(response.content)
```

## 📁 项目结构

```
video-to-text/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口
│   ├── database.py      # 数据库配置
│   ├── models.py        # 数据模型
│   ├── tasks.py         # 任务处理逻辑
│   └── transcribe.py    # Whisper 转录核心
├── static/
│   ├── css/
│   │   └── style.css    # 样式文件
│   └── js/
│       └── script.js    # 前端逻辑
├── templates/
│   └── index.html       # 主页面
├── uploads/             # 上传文件目录
│   ├── videos/          # 视频文件
│   ├── audios/          # 音频文件
│   └── transcripts/     # 转录结果
├── .gitignore
├── requirements.txt     # Python 依赖
├── run.sh              # 启动脚本
├── deploy.sh           # 部署脚本
├── LICENSE
└── README.md
```

## ⚙️ 配置说明

### Whisper 模型

在 `app/transcribe.py` 中可以修改模型大小：

```python
# 可选模型：tiny, base, small, medium, large
transcriber = VideoTranscriber(model_size="base")
```

**模型对比**：

| 模型 | 大小 | 速度 | 准确率 |
|------|------|------|--------|
| tiny | 39M | 最快 | 较低 |
| base | 74M | 快 | 中等 |
| small | 244M | 中等 | 良好 |
| medium | 769M | 慢 | 很好 |
| large | 1550M | 最慢 | 最佳 |

### 文件大小限制

在 `app/main.py` 中修改：

```python
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
```

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t video-to-text .

# 运行容器
docker run -d -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/video_tasks.db:/app/video_tasks.db \
  video-to-text
```

## 🔧 常见问题

### 1. FFmpeg 未找到

确保 FFmpeg 已安装并在 PATH 中：
```bash
ffmpeg -version
```

### 2. 模型下载慢

Whisper 模型会自动下载到 `~/.cache/whisper/`，首次使用需要等待。可以手动下载后放到该目录。

### 3. 内存不足

- 使用较小的模型（tiny 或 base）
- 减少并发任务数量
- 增加系统内存

### 4. 转换速度慢

- 使用 GPU 加速（需要 CUDA）
- 使用较小的模型
- 减少视频文件大小

## 📊 性能指标

**测试环境**：MacBook Pro M1, 16GB RAM, base 模型

| 视频时长 | 文件大小 | 转换时间 |
|---------|---------|---------|
| 1分钟 | 10MB | ~30秒 |
| 5分钟 | 50MB | ~2分钟 |
| 10分钟 | 100MB | ~4分钟 |
| 30分钟 | 300MB | ~12分钟 |

## 🤝 贡献指南

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 开源协议

本项目采用 MIT 协议 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 强大的语音识别模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [FFmpeg](https://ffmpeg.org/) - 音视频处理工具

## 📮 联系方式

- 作者：rock
- Email：944851899@qq.com
- 项目地址：https://github.com/yourusername/video-to-text

## 🌟 Star History

如果这个项目对你有帮助，请给个 Star ⭐️

---

**注意**：本项目仅供学习交流使用，请勿用于商业用途。

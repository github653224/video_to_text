# 🎬 视频转文字工具

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Whisper](https://img.shields.io/badge/OpenAI-Whisper-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

基于 OpenAI Whisper 的智能视频转文字工具，支持实时进度跟踪和多格式输出

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用说明](#使用说明) • [技术栈](#技术栈) • [贡献指南](#贡献指南)

</div>

---

## ✨ 功能特性

- 🎯 **智能转录**：基于 OpenAI Whisper AI 模型，高准确率语音识别
- ⚡ **实时进度**：WebSocket 实时推送转换进度，体验流畅
- 📦 **多格式支持**：支持 MP4、AVI、MOV、MKV 等主流视频格式
- 📝 **多种输出**：生成 TXT 文本、SRT 字幕、JSON 数据和 MP3 音频
- 🎨 **现代界面**：响应式设计，支持桌面端和移动端
- 🔄 **批量处理**：支持多个视频同时上传和转换
- 💾 **任务管理**：完整的任务列表，支持预览、下载和删除
- 🌐 **中文优化**：自动繁简转换，针对中文语音优化
- 📊 **大文件支持**：支持最大 500MB 的视频文件

## 🚀 快速开始

### 环境要求

- Python 3.8+
- FFmpeg
- 2GB+ 可用内存

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/yourusername/video-to-text.git
cd video-to-text
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **安装 FFmpeg**

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows
# 下载 FFmpeg 并添加到 PATH 环境变量
# https://ffmpeg.org/download.html
```

4. **启动服务**

```bash
# 方式一：使用脚本启动
chmod +x run.sh
./run.sh

# 方式二：直接启动
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. **访问应用**

打开浏览器访问：`http://localhost:8000`

## 📖 使用说明

### 基本使用

1. 点击上传区域或拖放视频文件（支持多选）
2. 点击"开始转换"按钮
3. 实时查看转换进度
4. 转换完成后下载结果文件

### 批量上传

- 按住 Ctrl/Cmd 键选择多个文件
- 或直接拖放多个文件到上传区域
- 系统会依次处理所有文件

### 输出文件说明

- **TXT 文件**：纯文本转录内容
- **SRT 文件**：带时间轴的字幕文件
- **JSON 文件**：包含完整分段信息的数据文件
- **MP3 文件**：从视频提取的音频文件

### API 接口

#### 上传视频

```bash
POST /upload
Content-Type: multipart/form-data

file: <video_file>
```

#### 获取任务状态

```bash
GET /tasks/{task_id}
```

#### 获取所有任务

```bash
GET /tasks
```

#### 下载文件

```bash
GET /download/audio/{task_id}      # 下载音频
GET /download/transcript/{task_id}  # 下载文本
GET /download/srt/{task_id}         # 下载字幕
```

#### WebSocket 实时进度

```javascript
ws://localhost:8000/ws/{task_id}
```

## 🛠️ 技术栈

### 后端

- **FastAPI**：现代化的 Python Web 框架
- **OpenAI Whisper**：强大的语音识别模型
- **SQLAlchemy**：数据库 ORM
- **FFmpeg**：音视频处理
- **WebSocket**：实时通信

### 前端

- **Bootstrap 5**：响应式 UI 框架
- **Bootstrap Icons**：图标库
- **原生 JavaScript**：无额外依赖

## 📁 项目结构

```
video-to-text/
├── app/
│   ├── __init__.py          # 应用初始化
│   ├── main.py              # FastAPI 主应用
│   ├── models.py            # 数据库模型
│   ├── database.py          # 数据库配置
│   ├── tasks.py             # 任务处理逻辑
│   └── transcribe.py        # Whisper 转录服务
├── static/
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/
│       └── script.js        # 前端脚本
├── templates/
│   └── index.html           # 主页面
├── uploads/                 # 上传文件目录
│   ├── videos/              # 视频文件
│   ├── audios/              # 音频文件
│   └── transcripts/         # 转录文件
├── requirements.txt         # Python 依赖
├── run.sh                   # 启动脚本
├── .gitignore              # Git 忽略文件
└── README.md               # 项目文档
```

## ⚙️ 配置说明

### Whisper 模型选择

在 `app/transcribe.py` 中可以调整模型大小：

```python
def get_transcriber():
    return VideoTranscriber(model_size="base")
    # 可选: tiny, base, small, medium, large
```

模型对比：

| 模型 | 大小 | 速度 | 准确率 | 推荐场景 |
|------|------|------|--------|----------|
| tiny | ~39MB | 最快 | 较低 | 快速测试 |
| base | ~74MB | 快 | 中等 | 日常使用 ⭐ |
| small | ~244MB | 中等 | 良好 | 平衡选择 |
| medium | ~769MB | 慢 | 很好 | 高质量需求 |
| large | ~1550MB | 最慢 | 最好 | 专业场景 |

### 文件大小限制

在 `static/js/script.js` 中修改：

```javascript
const maxSize = 500 * 1024 * 1024; // 修改 500 为其他数值（单位：MB）
```

**注意**：处理大文件需要更多内存和时间，建议根据服务器配置调整。

## 🔧 常见问题

### 1. FFmpeg 未找到

**错误**：`FFmpeg not found`

**解决**：确保 FFmpeg 已安装并添加到系统 PATH

```bash
# 验证安装
ffmpeg -version
```

### 2. 内存不足

**错误**：`CUDA out of memory` 或内存溢出

**解决**：使用更小的 Whisper 模型（如 `tiny` 或 `base`）

### 3. 转录结果不准确

**建议**：
- 使用更大的模型（如 `medium` 或 `large`）
- 确保视频音频清晰
- 检查语言设置是否正确

### 4. 进度条不更新

**解决**：
- 检查浏览器控制台是否有 WebSocket 错误
- 确保防火墙未阻止 WebSocket 连接
- 刷新页面重新连接

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 开发计划

- [ ] 支持更多语言识别
- [ ] 添加说话人识别
- [ ] 支持实时视频流转录
- [ ] 添加用户认证系统
- [ ] 支持云存储集成
- [ ] 提供 Docker 部署方案
- [ ] 添加深色模式

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 强大的语音识别模型
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [Bootstrap](https://getbootstrap.com/) - 优秀的 UI 框架

## 📧 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 [Issue](https://github.com/yourusername/video-to-text/issues)
- 发送邮件至：your.email@example.com

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！**

Made with ❤️ by [Your Name]

</div>

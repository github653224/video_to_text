#!/bin/bash

# 视频转文字工具 - 部署脚本

echo "🚀 开始部署视频转文字工具..."

# 检查 Python 版本
echo "📋 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python 版本: $python_version"

# 检查 FFmpeg
echo "📋 检查 FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n 1)
    echo "   ✅ FFmpeg 已安装: $ffmpeg_version"
else
    echo "   ❌ FFmpeg 未安装，请先安装 FFmpeg"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu: sudo apt install ffmpeg"
    exit 1
fi

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ 虚拟环境创建成功"
else
    echo "   ℹ️  虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建必要的目录
echo "📁 创建上传目录..."
mkdir -p uploads/videos uploads/audios uploads/transcripts

# 创建 .gitkeep 文件
touch uploads/.gitkeep
touch uploads/videos/.gitkeep
touch uploads/audios/.gitkeep
touch uploads/transcripts/.gitkeep

echo ""
echo "✅ 部署完成！"
echo ""
echo "🎉 启动应用："
echo "   ./run.sh"
echo ""
echo "🌐 访问地址："
echo "   http://localhost:8000"
echo ""

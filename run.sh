#!/bin/bash

# 视频转文字工具启动脚本

echo "启动视频转文字工具..."

# 激活 conda 环境
echo "激活 conda 环境: torch"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate torch

# 检查 conda 环境是否激活成功
if [ "$CONDA_DEFAULT_ENV" != "torch" ]; then
    echo "错误: 无法激活 conda 环境 'torch'"
    echo "请确保已创建名为 'torch' 的 conda 环境"
    exit 1
fi

echo "当前 conda 环境: $CONDA_DEFAULT_ENV"

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python"
    exit 1
fi

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "错误: 未找到requirements.txt文件"
    exit 1
fi

echo "安装依赖..."
pip install -r requirements.txt

echo "启动应用..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

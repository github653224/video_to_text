# 贡献指南

感谢你考虑为视频转文字工具做出贡献！

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请创建一个 Issue 并包含以下信息：

- Bug 的详细描述
- 复现步骤
- 预期行为
- 实际行为
- 截图（如果适用）
- 环境信息（操作系统、Python 版本等）

### 提出新功能

如果你有新功能的想法：

1. 先创建一个 Issue 讨论这个功能
2. 等待维护者的反馈
3. 获得批准后再开始开发

### 提交代码

1. **Fork 项目**

```bash
git clone https://github.com/yourusername/video-to-text.git
cd video-to-text
```

2. **创建分支**

```bash
git checkout -b feature/your-feature-name
```

3. **进行更改**

- 遵循现有的代码风格
- 添加必要的注释
- 更新相关文档

4. **测试你的更改**

```bash
# 确保应用能正常运行
python -m uvicorn app.main:app --reload

# 测试主要功能
# - 上传视频
# - 查看进度
# - 下载结果
```

5. **提交更改**

```bash
git add .
git commit -m "feat: 添加新功能描述"
```

提交信息格式：
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

6. **推送到 GitHub**

```bash
git push origin feature/your-feature-name
```

7. **创建 Pull Request**

- 提供清晰的 PR 描述
- 关联相关的 Issue
- 等待代码审查

## 代码规范

### Python 代码

- 遵循 PEP 8 规范
- 使用有意义的变量名
- 添加必要的类型注解
- 编写清晰的文档字符串

```python
def process_video(video_path: str, output_dir: str) -> dict:
    """
    处理视频文件并生成转录结果
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录路径
        
    Returns:
        包含转录结果的字典
    """
    pass
```

### JavaScript 代码

- 使用 ES6+ 语法
- 使用有意义的函数名
- 添加必要的注释
- 保持代码简洁

```javascript
/**
 * 上传视频文件
 * @returns {Promise<void>}
 */
async function uploadFile() {
    // 实现代码
}
```

### CSS 代码

- 使用 CSS 变量
- 保持选择器简洁
- 添加必要的注释
- 遵循 BEM 命名规范（可选）

## 开发环境设置

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **配置开发环境**

```bash
# 启用开发模式
export DEBUG=True

# 设置日志级别
export LOG_LEVEL=DEBUG
```

3. **运行开发服务器**

```bash
python -m uvicorn app.main:app --reload --log-level debug
```

## 测试

在提交 PR 之前，请确保：

- [ ] 应用能正常启动
- [ ] 视频上传功能正常
- [ ] 转录功能正常
- [ ] 进度显示正常
- [ ] 文件下载正常
- [ ] 任务删除正常
- [ ] 响应式布局正常
- [ ] 无控制台错误

## 文档

如果你的更改影响了用户使用方式：

- 更新 README.md
- 添加必要的注释
- 更新 API 文档（如果适用）

## 问题和讨论

- 使用 GitHub Issues 报告问题
- 使用 GitHub Discussions 进行讨论
- 保持友好和尊重的态度

## 许可证

提交代码即表示你同意将代码以 MIT 许可证发布。

---

再次感谢你的贡献！🎉

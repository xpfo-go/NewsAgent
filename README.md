# NewsAgent

自动抓取 BBC 中文新闻，生成中文摘要，输出音频和视频。

## Quick Start

1. 复制环境变量文件并填写 OpenAI 配置：

```bash
cp .env.example .env
```

2. 创建并激活虚拟环境，安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. 执行工作流：

```bash
python main.py
```

默认输出目录为 `data/YYYYMMDD`。

## Optional: 抖音发布脚本

1. 获取登录态：

```bash
python scripts/douyin_get_cookie.py
```

2. 上传当天视频：

```bash
python scripts/douyin_upload.py
```

## 测试

```bash
python -m unittest discover -s tests -v
```

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

## 可观测性与重试

项目已为 `fetch / summary / movie` 节点增加结构化日志和重试策略，可通过环境变量调整：

```bash
# 日志级别：DEBUG / INFO / WARNING / ERROR
NEWSAGENT_LOG_LEVEL=INFO

# 抓取节点重试
NEWSAGENT_FETCH_RETRY_ATTEMPTS=3
NEWSAGENT_FETCH_RETRY_BASE_DELAY=1
NEWSAGENT_FETCH_RETRY_BACKOFF=2

# 总结节点重试
NEWSAGENT_SUMMARY_RETRY_ATTEMPTS=3
NEWSAGENT_SUMMARY_RETRY_BASE_DELAY=1
NEWSAGENT_SUMMARY_RETRY_BACKOFF=2

# 视频节点重试
NEWSAGENT_MOVIE_RETRY_ATTEMPTS=2
NEWSAGENT_MOVIE_RETRY_BASE_DELAY=1
NEWSAGENT_MOVIE_RETRY_BACKOFF=2
```

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

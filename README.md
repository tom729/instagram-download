# Instagram帖子监控工具

自动监控Instagram用户帖子并下载24小时内发布的图片和文案。

## 功能

- 每日自动访问多个Instagram用户的主页
- 扫描并识别24小时内发布的新帖子
- 下载帖子中的所有图片（支持多图帖子）
- 保存帖子文案[有bug，未实现]
- 按用户名和日期分类存储数据

## 系统要求

- Python 3.7+
- 已登录状态的Chrome浏览器

## 安装

1. 安装依赖：

```bash
pip install playwright python-dateutil requests loguru
playwright install 
```

2. 克隆或下载此仓库：

```bash
git clone <仓库URL>
cd instagram_download
```

## 配置

编辑`config.py`文件，设置以下内容：

- 需要监控的Instagram用户列表
- 浏览器设置（选择连接已存在的浏览器还是启动新实例）
- 保存设置

```python
# 需要监控的Instagram用户列表
USERS_TO_MONITOR = [
    "instagram",  # 替换为您要监控的用户名
    "另一个用户名",
]

# 浏览器配置 - 选择一种方式
#  连接到已运行的Chrome (推荐)

CHROME_REMOTE_DEBUGGING_PORT = 9222  # Chrome远程调试端口

```

## 使用方法

### 准备浏览器

在运行工具前，需要先启动Chrome浏览器并开启远程调试模式：

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

确保在启动的Chrome实例中已登录Instagram。

### 运行工具

```bash
python main.py
```

### 设置定时任务

要让工具每天自动运行，可以设置cron任务：

1. 编辑crontab：

```bash
crontab -e
```

2. 添加以下行（每天凌晨2点运行）：

```
0 2 * * * cd /完整路径/instagram_download && python main.py >> logs/cron.log 2>&1
```

## 数据存储

下载的数据将按以下结构存储：

```
data/
├── [用户名1]/
│   └── [日期]/
│       ├── [user_id]_[帖子ID]_1_[时间].jpg
│       ├── [user_id]_[帖子ID]_2_[时间].jpg  # 多图帖子的其他图片
│       └── [user_id]_[帖子ID]_caption_[时间戳].txt   # 帖子文案[未实现]
└── [用户名2]/
    └── [日期]/
        ├── ...
```

## 注意事项

- 此工具仅用于个人研究和学习目的，请遵守Instagram的使用条款。
- 过于频繁的请求可能导致账号被暂时限制，请合理设置抓取频率。
- Instagram界面可能随时变化，如果工具无法正常工作，可能需要更新选择器。
- 请确保浏览器已登录Instagram，否则将无法访问用户资料。

## 故障排除

- **连接Chrome失败**：确保Chrome已在远程调试模式下运行，端口与配置一致。
- **无法找到帖子元素**：Instagram页面结构可能已变化，尝试更新`post_extractor.py`中的选择器。
- **无法提取图片或文案**：同样，检查选择器并更新。
- **浏览器启动但不显示**：检查`headless`参数设置，确保为`False`。 
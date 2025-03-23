#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置文件 - Instagram帖子监控工具
"""

# Instagram用户列表 - 需要监控的账号
USERS_TO_MONITOR = [
    "theglobalphotographycommunity",  # 示例用户，请替换为实际需要监控的用户
    # 添加更多用户...
]

# 数据存储配置
DATA_DIR = "./data"  # 数据存储根目录
LOG_DIR = "./logs"   # 日志存储目录

# 浏览器配置
CHROME_USER_DATA_DIR = None  # Chrome用户数据目录，留空则使用CDP连接
CHROME_PROFILE_NAME = "Default"  # Chrome配置文件名称
CHROME_REMOTE_DEBUGGING_PORT = 9222  # Chrome远程调试端口
USE_CDP_CONNECTION = True  # 强制使用CDP连接到已打开的Chrome

# 爬取配置
HOURS_THRESHOLD = 24  # 仅保存N小时内的新帖子
PAGE_LOAD_TIMEOUT = 30  # 页面加载超时时间(秒)
SCROLL_COUNT = 5  # 向下滚动次数，增加以加载更多帖子
RANDOM_DELAY_MIN = 1  # 随机延迟最小值(秒)
RANDOM_DELAY_MAX = 3  # 随机延迟最大值(秒)

# 文件保存配置
CAPTION_FILE_EXT = ".txt"  # 文案文件扩展名
IMAGE_QUALITY = 100  # 图片保存质量 (1-100) 

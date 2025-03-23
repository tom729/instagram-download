#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Instagram帖子监控工具 - 主程序入口
"""

import os
import sys
import time
import logging
from datetime import datetime

# 导入配置和模块
import config
from lib.browser import BrowserHandler
from lib.post_extractor import PostExtractor
from lib.file_manager import FileManager
from lib.date_utils import is_within_hours


# 设置日志
def setup_logging():
    """配置日志系统"""
    log_dir = config.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"instagram_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("instagram_downloader")


def download_posts_for_user(username, browser_handler, file_manager, logger):
    """
    下载指定用户的最近帖子
    
    Args:
        username (str): Instagram用户名
        browser_handler: 浏览器处理器
        file_manager: 文件管理器
        logger: 日志记录器
        
    Returns:
        int: 下载的帖子数量
    """
    try:
        # 创建用户的日期目录
        save_dir = file_manager.create_user_date_dir(username)
        logger.info(f"为用户 {username} 创建存储目录: {save_dir}")
        
        # 初始化帖子提取器
        post_extractor = PostExtractor(browser_handler, config)
        
        # 获取用户最近帖子
        recent_posts = post_extractor.extract_recent_posts(username)
        
        if not recent_posts:
            logger.info(f"用户 {username} 没有在{config.HOURS_THRESHOLD}小时内发布的帖子")
            return 0
        
        # 下载每个帖子的图片和文案
        downloaded_count = 0
        for post in recent_posts:
            # 生成帖子ID
            post_id = file_manager.generate_post_id(
                username, 
                post['timestamp'], 
                post['caption']
            )
            
            # 记录详细信息
            author = post.get('author', username)
            timestamp = post['timestamp']  # 帖子的实际发布时间
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"发现帖子 - 作者: {author}, 发布时间: {timestamp_str}")
            logger.info(f"帖子文案: {post['caption'][:50]}..." if len(post['caption']) > 50 else f"帖子文案: {post['caption']}")
            
            # 保存文案
            caption_file = None
            if post['caption']:
                caption_file = file_manager.save_caption(
                    post['caption'], 
                    save_dir, 
                    post_id, 
                    config.CAPTION_FILE_EXT,
                    post.get('author'),  # 使用提取的作者信息
                    timestamp  # 使用帖子的发布时间
                )
                if caption_file:
                    logger.info(f"文案已保存到: {caption_file}")
                else:
                    logger.warning(f"文案保存失败")
            
            # 下载所有图片
            image_count = 0
            for i, image_url in enumerate(post['image_urls']):
                image_file = file_manager.download_image(
                    image_url, 
                    save_dir, 
                    post_id, 
                    i + 1,
                    author,  # 添加作者信息到图片命名
                    timestamp  # 使用帖子的发布时间
                )
                if image_file:
                    image_count += 1
            
            logger.info(f"已下载 {image_count} 张图片")
            downloaded_count += 1
            logger.info(f"完成下载用户 {username} 的帖子: {post_id}")
        
        return downloaded_count
        
    except Exception as e:
        logger.error(f"处理用户 {username} 的帖子时出错: {e}")
        return 0


def main():
    """主函数"""
    # 设置日志
    logger = setup_logging()
    logger.info("Instagram帖子监控工具启动")
    
    # 确保数据目录存在
    os.makedirs(config.DATA_DIR, exist_ok=True)
    
    # 初始化文件管理器
    file_manager = FileManager(config.DATA_DIR)
    
    # 要监控的用户
    if not config.USERS_TO_MONITOR:
        logger.error("未配置要监控的用户列表，请在config.py中添加USERS_TO_MONITOR")
        return
    
    total_downloaded = 0
    error_users = []
    
    # 使用上下文管理器初始化浏览器
    with BrowserHandler(config) as browser_handler:
        # 为每个用户下载帖子
        for username in config.USERS_TO_MONITOR:
            try:
                logger.info(f"开始处理用户: {username}")
                
                # 下载该用户的帖子
                posts_count = download_posts_for_user(
                    username, 
                    browser_handler, 
                    file_manager, 
                    logger
                )
                
                total_downloaded += posts_count
                
                # 用户间添加延迟
                if username != config.USERS_TO_MONITOR[-1]:  # 不是最后一个用户
                    delay = 5  # 默认5秒
                    logger.info(f"等待 {delay} 秒后处理下一个用户...")
                    time.sleep(delay)
                
            except Exception as e:
                logger.error(f"处理用户 {username} 时发生错误: {e}")
                error_users.append(username)
                continue
    
    # 汇总报告
    logger.info("============================")
    logger.info(f"监控完成! 共下载了 {total_downloaded} 个帖子")
    
    if error_users:
        logger.warning(f"处理以下用户时出现错误: {', '.join(error_users)}")
    
    logger.info("============================")


if __name__ == "__main__":
    main() 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件管理模块 - 处理图片和文本的保存
"""

import os
import re
import requests
import hashlib
from urllib.parse import urlparse
from datetime import datetime

from lib.date_utils import get_formatted_date


class FileManager:
    def __init__(self, base_dir):
        """
        初始化文件管理器
        
        Args:
            base_dir (str): 数据存储的基础目录
        """
        self.base_dir = base_dir
        
    def create_user_date_dir(self, username):
        """
        创建用户和日期目录
        
        Args:
            username (str): Instagram用户名
            
        Returns:
            str: 创建的目录路径
        """
        # 获取今天的日期作为目录名
        date_str = get_formatted_date()
        
        # 构建用户目录路径
        user_dir = os.path.join(self.base_dir, username)
        
        # 构建日期目录路径
        date_dir = os.path.join(user_dir, date_str)
        
        # 创建目录（如果不存在）
        os.makedirs(date_dir, exist_ok=True)
        
        return date_dir
    
    def sanitize_filename(self, filename):
        """
        净化文件名，移除不安全字符
        
        Args:
            filename (str): 原始文件名
            
        Returns:
            str: 安全的文件名
        """
        # 移除非法字符
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", filename)
        # 限制长度
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]
        return safe_filename
    
    def download_image(self, image_url, save_dir, post_id, index=0, author=None, post_timestamp=None):
        """
        下载图片并保存到指定目录
        
        Args:
            image_url (str): 图片URL
            save_dir (str): 保存目录
            post_id (str): 帖子ID或唯一标识
            index (int): 多图帖子中的索引
            author (str): 帖子作者，可选
            post_timestamp (datetime): 帖子发布时间，可选
            
        Returns:
            str: 保存的文件路径，如果下载失败则返回None
        """
        try:
            # 使用帖子发布时间（如果提供）或当前时间作为文件名的一部分
            if post_timestamp:
                timestamp = post_timestamp.strftime('%Y%m%d_%H%M%S')
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 从URL解析文件扩展名
            parsed_url = urlparse(image_url)
            path = parsed_url.path
            ext = os.path.splitext(path)[1]
            if not ext:
                ext = '.jpg'  # 默认使用jpg扩展名
            
            # 构建文件名，添加作者信息
            if author:
                # 清理作者名称，确保文件名安全
                safe_author = self.sanitize_filename(author)
                filename = f"{safe_author}_{post_id}_{index}_{timestamp}{ext}"
            else:
                filename = f"{post_id}_{index}_{timestamp}{ext}"
            
            # 完整文件路径
            file_path = os.path.join(save_dir, filename)
            
            # 下载图片
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 写入文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"图片已保存: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"下载图片失败: {e}")
            return None
    
    def save_caption(self, caption, save_dir, post_id, ext='.txt', author=None, post_timestamp=None):
        """
        保存帖子文案
        
        Args:
            caption (str): 帖子文案
            save_dir (str): 保存目录
            post_id (str): 帖子ID或唯一标识
            ext (str): 文件扩展名
            author (str): 作者信息，可选
            post_timestamp (datetime): 帖子发布时间，可选
            
        Returns:
            str: 保存的文件路径
        """
        try:
            # 使用帖子发布时间（如果提供）或当前时间
            if post_timestamp:
                timestamp = post_timestamp.strftime('%Y%m%d_%H%M%S')
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 构建文件名，添加作者信息
            if author:
                # 清理作者名称，确保文件名安全
                safe_author = self.sanitize_filename(author)
                filename = f"{safe_author}_{post_id}_caption_{timestamp}{ext}"
            else:
                filename = f"{post_id}_caption_{timestamp}{ext}"
            
            # 完整文件路径
            file_path = os.path.join(save_dir, filename)
            print(f"正在保存文案到: {file_path}")
            
            # 准备文本内容，如果有作者信息则添加
            content = caption
            if author:
                # 添加作者和发布时间信息
                if post_timestamp:
                    post_time_str = post_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    content = f"作者: {author}\n发布时间: {post_time_str}\n\n{caption}"
                else:
                    content = f"作者: {author}\n\n{caption}"
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"文案已保存: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"保存文案失败: {e}, 目录: {save_dir}, 文件名: {filename if 'filename' in locals() else 'unknown'}")
            # 检查目录是否存在
            if not os.path.exists(save_dir):
                print(f"保存目录不存在: {save_dir}")
                try:
                    os.makedirs(save_dir, exist_ok=True)
                    print(f"已创建保存目录: {save_dir}")
                except Exception as make_dir_error:
                    print(f"创建目录失败: {make_dir_error}")
            return None
    
    def generate_post_id(self, username, timestamp, caption_snippet):
        """
        生成帖子的唯一ID
        
        Args:
            username (str): 用户名
            timestamp (datetime): 帖子时间戳
            caption_snippet (str): 文案片段
            
        Returns:
            str: 生成的唯一ID
        """
        # 使用用户名、时间戳和文案前20个字符的组合生成MD5哈希
        timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
        caption_short = caption_snippet[:20] if caption_snippet else ""
        
        # 组合字符串并生成哈希
        combine_str = f"{username}_{timestamp_str}_{caption_short}"
        return hashlib.md5(combine_str.encode()).hexdigest()[:12] 
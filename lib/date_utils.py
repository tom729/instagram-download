#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日期处理工具 - 解析Instagram时间戳并判断是否在指定时间范围内
"""

import re
import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta

# 导入时间戳指示器配置
try:
    from config.page_selectors import TIMESTAMP_INDICATORS
except ImportError:
    # 如果配置文件不存在，使用默认时间戳指示器
    TIMESTAMP_INDICATORS = {
        "recent": [
            '小时', 'hour', 'hr', 
            '分钟', 'minute', 'min', 
            '秒', 'second', 'sec', 
            '刚刚', 'just now',
            '今天', 'today'
        ],
        "old": [
            '天', 'day', 'days',
            '周', 'week', 'weeks', 'wk',
            '月', 'month', 'months',
            '年', 'year', 'years', 'yr'
        ],
        "special_cases": {
            "yesterday": 48
        }
    }


def parse_instagram_timestamp(timestamp_text):
    """
    解析Instagram时间戳文本
    
    Args:
        timestamp_text (str): Instagram显示的时间戳文本
        
    Returns:
        datetime: 解析后的datetime对象
    """
    now = datetime.datetime.now()
    
    # 处理"刚刚"或"just now"等情况
    if any(term in timestamp_text.lower() for term in ['刚刚', 'just now', '几秒', 'seconds', 'second', 'sec']):
        return now
    
    # 处理分钟格式
    minutes_match = re.search(r'(\d+)\s*(分钟|minutes|minute|min)', timestamp_text.lower())
    if minutes_match:
        minutes = int(minutes_match.group(1))
        return now - datetime.timedelta(minutes=minutes)
    
    # 处理小时格式
    hours_match = re.search(r'(\d+)\s*(小时|hours|hour|hr)', timestamp_text.lower())
    if hours_match:
        hours = int(hours_match.group(1))
        return now - datetime.timedelta(hours=hours)
    
    # 处理"昨天"或"yesterday"
    if any(term in timestamp_text.lower() for term in ['昨天', 'yesterday']):
        return now - datetime.timedelta(days=1)
    
    # 处理"今天"或"today"
    if any(term in timestamp_text.lower() for term in ['今天', 'today']):
        # 提取时间部分，如果有
        time_match = re.search(r'(\d+):(\d+)', timestamp_text)
        if time_match:
            hour, minute = map(int, time_match.groups())
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 处理天数格式
    days_match = re.search(r'(\d+)\s*(天|days|day)', timestamp_text.lower())
    if days_match:
        days = int(days_match.group(1))
        return now - datetime.timedelta(days=days)
    
    # 处理周格式
    weeks_match = re.search(r'(\d+)\s*(周|星期|weeks|week|wk)', timestamp_text.lower())
    if weeks_match:
        weeks = int(weeks_match.group(1))
        return now - datetime.timedelta(weeks=weeks)
    
    # 处理月份格式
    months_match = re.search(r'(\d+)\s*(月|months|month)', timestamp_text.lower())
    if months_match and not re.search(r'\d+年\d+月\d+日', timestamp_text):  # 避免与年月日格式冲突
        months = int(months_match.group(1))
        return now - relativedelta(months=months)
    
    # 处理年份格式
    years_match = re.search(r'(\d+)\s*(年|years|year|yr)', timestamp_text.lower())
    if years_match and not re.search(r'\d+年\d+月\d+日', timestamp_text):  # 避免与年月日格式冲突
        years = int(years_match.group(1))
        return now - relativedelta(years=years)
    
    # 处理标准日期格式 (例如: "2023年6月15日" 或 "2023-06-15")
    # 中文日期格式
    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', timestamp_text)
    if date_match:
        year, month, day = map(int, date_match.groups())
        # 提取时间部分，如果有
        time_match = re.search(r'(\d+):(\d+)', timestamp_text)
        if time_match:
            hour, minute = map(int, time_match.groups())
            return datetime.datetime(year, month, day, hour, minute)
        return datetime.datetime(year, month, day)
    
    # 处理标准日期格式 (例如: "2023-06-15")
    try:
        # 尝试使用dateutil解析
        return parser.parse(timestamp_text)
    except:
        # 如果所有尝试都失败，返回当前时间
        print(f"无法解析时间戳文本: {timestamp_text}")
        return now


def is_within_hours(timestamp, hours_threshold=24, timestamp_text=None):
    """
    检查给定的时间戳是否在指定的小时数内
    
    Args:
        timestamp (datetime): 要检查的时间戳
        hours_threshold (int): 小时数阈值
        timestamp_text (str, optional): 时间戳的显示文本
        
    Returns:
        bool: 如果在指定小时数内则返回True，否则返回False
    """
    # 如果提供了显示文本，优先使用文本判断
    if timestamp_text:
        # 如果显示文本包含以下任何一个单词，认为是在24小时内
        recent_indicators = TIMESTAMP_INDICATORS["recent"]
        
        # 检查是否包含任何一个指示最近的词
        if any(indicator in timestamp_text.lower() for indicator in recent_indicators):
            return True
        
        # 如果包含天、周、月、年等词，则认为超过时间范围
        old_indicators = TIMESTAMP_INDICATORS["old"]
        
        # 特殊情况：如果是"昨天"并且hours_threshold >= 配置的阈值
        yesterday_threshold = TIMESTAMP_INDICATORS["special_cases"]["yesterday"]
        if ('昨天' in timestamp_text or 'yesterday' in timestamp_text):
            return hours_threshold >= yesterday_threshold
            
        # 检查是否包含任何一个指示较早的词
        # 对于任何其他包含天/周/月/年的情况，直接返回False
        if any(indicator in timestamp_text.lower() for indicator in old_indicators):
            return False
        
        # 如果无法通过文本判断，回退到时间戳比较
    
    # 如果没有提供显示文本或无法通过文本判断，使用时间戳比较
    now = datetime.datetime.now()
    time_diff = now - timestamp
    return time_diff.total_seconds() / 3600 <= hours_threshold


def get_formatted_date():
    """
    获取格式化的当前日期字符串，用于文件夹命名
    
    Returns:
        str: 格式化的日期字符串，如'2023-04-15'
    """
    return datetime.datetime.now().strftime('%Y-%m-%d') 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Instagram页面结构选择器配置文件
当Instagram更新其页面结构时，只需更新此文件中的选择器即可
"""

# Instagram页面结构选择器
INSTAGRAM_SELECTORS = {
    # 帖子列表容器
    "post_list_container": "div.xg7h5cd.x1n2onr6",
    
    # 帖子行容器
    "post_row": "div._ac7v.xat24cr.x1f01sob.xcghwft.xzboxd6",
    
    # 单个帖子容器
    "post_item": "div.x1lliihq.x1n2onr6.xh8yej3.x4gyw5p.x11i5rnm.x1ntc13c.x9i3mqj.x2pgyrj",
    
    # 帖子右上角图标容器
    "post_icon_container": "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1xmf6yo.x1emribx.x1e56ztr.x1i64zmx.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1",
    
    # 置顶帖子图标
    "pinned_post_icon": "svg[aria-label='置顶帖图标']",
    
    # 备用置顶帖子图标选择器
    "pinned_post_icon_alternatives": [
        "svg[aria-label='已置顶']",
        "svg[aria-label='Pinned']",
        "svg[class*='x1lliihq'][class*='x1n2onr6']",
        "div svg[role='img'][width='28'][height='28']"
    ],
    
    # 时间戳选择器
    "timestamp_selectors": [
        "div[role='dialog'] time",
        "div[role='dialog'] article time",
        "article time"
    ],
    
    # 帖子对话框选择器
    "post_dialog": "div[role='dialog']",
    
    # 帖子链接选择器 (用于查找帖子元素)
    "post_link_selectors": [
        "main > div > div:nth-child(2) a",
        "section > main div > div > div > a",
        "section > main div a[href^='/p/']",
        "article a[href^='/p/']",
        "a[href^='/p/']",
        "div[role='presentation'] a[href^='/p/']"
    ]
}

# Instagram帖子提取策略
POST_EXTRACTION_STRATEGY = {
    # 最大处理帖子数量
    "max_posts_to_process": 5,
    
    # 置顶帖检测策略优先级
    "pinned_post_detection_priority": [
        "icon_matching",        # 通过置顶图标匹配
        "spatial_proximity",    # 通过空间位置关系匹配
        "dom_traversal",        # 通过DOM遍历查找
        "first_post_fallback"   # 假设第一个帖子是置顶的
    ]
}

# 时间文本判断策略
TIMESTAMP_INDICATORS = {
    # 24小时内的指示词
    "recent": [
        '小时', 'hour', 'hr', 
        '分钟', 'minute', 'min', 
        '秒', 'second', 'sec', 
        '刚刚', 'just now',
        '今天', 'today'
    ],
    
    # 超过24小时的指示词
    "old": [
        '天', 'day', 'days',
        '周', 'week', 'weeks', 'wk',
        '月', 'month', 'months',
        '年', 'year', 'years', 'yr'
    ],
    
    # 特殊情况
    "special_cases": {
        "yesterday": 48  # 昨天的帖子，如果阈值>=48小时则仍然处理
    }
} 
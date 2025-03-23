#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
帖子提取模块 - 从Instagram页面中提取帖子信息
"""

import re
from lib.date_utils import parse_instagram_timestamp, is_within_hours


class PostExtractor:
    def __init__(self, browser_handler, config):
        """
        初始化帖子提取器
        
        Args:
            browser_handler: 浏览器处理器实例
            config: 配置对象
        """
        self.browser = browser_handler
        self.config = config
    
    def extract_recent_posts(self, username):
        """
        提取指定用户最近的帖子
        
        Args:
            username (str): Instagram用户名
            
        Returns:
            list: 符合时间条件的帖子列表
        """
        print(f"正在提取用户 {username} 的最近帖子...")
        
        # 浏览该用户的主页
        profile_url = self.browser.get_instagram_profile_url(username)
        
        if not self.browser.navigate(profile_url):
            print(f"无法访问用户 {username} 的主页")
            return []
        
        # 滚动页面以加载更多帖子
        self.browser.scroll_down(self.config.SCROLL_COUNT)
        
        # 收集所有帖子元素
        post_elements = self._get_post_elements()
        if not post_elements:
            print(f"未找到用户 {username} 的帖子")
            return []
        
        print(f"找到 {len(post_elements)} 个帖子，正在筛选...")
        
        # 处理每个帖子并筛选出符合条件的
        recent_posts = []
        
        # 检测并跳过置顶帖子
        pinned_posts = self._identify_pinned_posts()
        if pinned_posts:
            print(f"发现 {len(pinned_posts)} 个置顶帖子，将跳过处理")
        
        # 处理普通帖子，最多处理5个
        processed_count = 0
        max_posts_to_process = 5
        
        for i, post_element in enumerate(post_elements):
            # 检查是否达到最大处理数量
            if processed_count >= max_posts_to_process:
                print(f"已处理 {processed_count} 个帖子，达到处理上限")
                break
                
            # 跳过无效元素
            if isinstance(post_element, str):
                print(f"跳过无效的帖子元素(字符串): {post_element[:30]}...")
                continue
                
            # 检查是否是置顶帖子
            if self._is_pinned_post(post_element, pinned_posts):
                print("跳过置顶帖子")
                continue
            
            try:
                # 点击帖子打开详情页
                post_element.click()
                self.browser.random_delay()
                
                # 提取帖子信息
                post_data = self._extract_post_data(username)
                if not post_data:
                    continue
                
                # 记录已处理帖子数
                processed_count += 1
                
                # 获取时间戳显示文本
                timestamp_text = post_data.get('timestamp_text', '')
                
                # 检查是否包含表示较长时间的关键词（天、周、月、年）
                old_indicators = [
                    '天', 'day', 'days',
                    '周', 'week', 'weeks', 'wk',
                    '月', 'month', 'months',
                    '年', 'year', 'years', 'yr'
                ]
                
                # 如果发现较早的时间标记，停止处理后续帖子
                if any(indicator in timestamp_text.lower() for indicator in old_indicators):
                    # 特殊情况：如果是"昨天"(1天)且在阈值范围内，仍然处理该帖子
                    if ('昨天' in timestamp_text or 'yesterday' in timestamp_text) and self.config.HOURS_THRESHOLD >= 48:
                        if is_within_hours(post_data['timestamp'], self.config.HOURS_THRESHOLD, timestamp_text):
                            recent_posts.append(post_data)
                            timestamp_str = post_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                            author = post_data.get('author', username)
                            print(f"找到符合条件的帖子: 作者={author}, 显示时间={timestamp_text}, 实际时间={timestamp_str}, 文案={post_data['caption'][:30]}...")
                    
                    print(f"发现较早帖子，时间显示为: {timestamp_text}，停止处理后续帖子")
                    # 关闭帖子详情页
                    self._close_post_dialog()
                    self.browser.random_delay()
                    break
                
                # 检查帖子是否在时间阈值内
                if is_within_hours(post_data['timestamp'], self.config.HOURS_THRESHOLD, timestamp_text):
                    recent_posts.append(post_data)
                    # 优化日志输出，包含时间和作者
                    timestamp_str = post_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    author = post_data.get('author', username)
                    print(f"找到符合条件的帖子: 作者={author}, 显示时间={timestamp_text}, 实际时间={timestamp_str}, 文案={post_data['caption'][:30]}...")
                else:
                    # 记录被跳过的帖子
                    timestamp_str = post_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    print(f"跳过较早的帖子: 显示时间={timestamp_text}, 实际时间={timestamp_str}")
                
                # 关闭帖子详情页
                self._close_post_dialog()
                self.browser.random_delay()
                
            except Exception as e:
                print(f"处理帖子时发生错误: {e}")
                self._close_post_dialog()  # 确保关闭对话框
                self.browser.random_delay()
                continue
        
        print(f"共找到 {len(recent_posts)} 个符合时间条件的帖子")
        return recent_posts
    
    def _identify_pinned_posts(self):
        """
        识别置顶帖子
        
        Returns:
            list: 置顶帖子元素或标识符列表
        """
        try:
            # 尝试查找置顶帖子标记
            pinned_selectors = [
                "svg[aria-label='置顶帖图标']",  # 新增：从图片中确认的具体标记
                "svg[aria-label='已置顶']",
                "svg[aria-label='Pinned']",
                "div:has(> span:contains('置顶'))",
                "div:has(> span:contains('Pinned'))",
                "div[role='presentation'] div:contains('置顶')",
                "div[role='presentation'] div:contains('Pinned')"
            ]
            
            pinned_posts = []
            for selector in pinned_selectors:
                try:
                    elements = self.browser.page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        # 找到置顶标记，现在找到对应的帖子元素
                        for pinned_mark in elements:
                            # 寻找包含该标记的帖子容器
                            post_container = self.browser.page.evaluate("""
                                (element) => {
                                    let current = element;
                                    // 向上查找最近的a标签或帖子容器
                                    while (current && 
                                           (!current.tagName || current.tagName.toLowerCase() !== 'a' || 
                                            !current.href || 
                                            (!current.href.includes('/p/') && !current.href.includes('/reel/')))) {
                                        current = current.parentElement;
                                    }
                                    return current ? current.href : null;
                                }
                            """, pinned_mark)
                            
                            if post_container:
                                pinned_posts.append(post_container)
                        
                        if pinned_posts:
                            print(f"使用选择器 '{selector}' 找到了 {len(pinned_posts)} 个置顶帖子")
                            return pinned_posts
                except Exception as e:
                    print(f"查找置顶帖子时使用选择器 '{selector}' 出错: {e}")
                    continue
                    
            return []
        except Exception as e:
            print(f"识别置顶帖子时出错: {e}")
            return []
    
    def _is_pinned_post(self, post_element, pinned_posts):
        """
        检查帖子是否为置顶帖子
        
        Args:
            post_element: 帖子元素
            pinned_posts: 已识别的置顶帖子列表
            
        Returns:
            bool: 是否为置顶帖子
        """
        try:
            # 如果没有找到置顶帖子，直接返回False
            if not pinned_posts:
                return False
                
            # 获取当前帖子的链接
            href = self.browser.page.evaluate("(el) => el.getAttribute('href')", post_element)
            if not href:
                return False
                
            # 处理相对路径和完整URL的情况
            # pinned_posts中可能是完整URL，而href可能是相对路径
            for pinned_url in pinned_posts:
                # 提取路径部分用于比较
                if pinned_url.endswith(href) or href in pinned_url or pinned_url in href:
                    print(f"匹配到置顶帖子: {href}")
                    return True
                    
                # 处理'/p/xxx'格式的路径
                if '/p/' in href and '/p/' in pinned_url:
                    href_id = href.split('/p/')[1].split('/')[0]
                    pinned_id = pinned_url.split('/p/')[1].split('/')[0]
                    if href_id == pinned_id:
                        print(f"通过ID匹配到置顶帖子: {href_id}")
                        return True
                        
                # 处理'/reel/xxx'格式的路径
                if '/reel/' in href and '/reel/' in pinned_url:
                    href_id = href.split('/reel/')[1].split('/')[0]
                    pinned_id = pinned_url.split('/reel/')[1].split('/')[0]
                    if href_id == pinned_id:
                        print(f"通过ID匹配到置顶帖子: {href_id}")
                        return True
            
            return False
        except Exception as e:
            print(f"检查置顶帖子时出错: {e}")
            return False
            
    def _get_post_elements(self):
        """
        获取页面上所有帖子元素
        
        Returns:
            list: 帖子元素列表
        """
        # Instagram帖子通常包含在特定的元素中
        # 这些选择器可能需要根据Instagram界面变化进行调整
        try:
            print("尝试获取帖子元素...")
            
            # 直接使用CSS选择器获取可点击的元素对象
            # 尝试各种CSS选择器，从具体到宽泛
            selectors = [
                "main > div > div:nth-child(2) a",      # 根据提供的路径构建的选择器
                "section > main div > div > div > a",   # 更精确的选择器
                "section > main div a[href^='/p/']",    # 基于帖子链接格式的选择器
                "article a[href^='/p/']",               # 更通用的选择器
                "a[href^='/p/']",                       # 帖子链接通常以/p/开头
                "div[role='presentation'] a[href^='/p/']" # 基于角色的选择器
            ]
            
            # 尝试所有选择器
            for selector in selectors:
                try:
                    # 使用query_selector_all直接获取元素对象
                    elements = self.browser.page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        # 过滤确保它们是包含图片的链接
                        valid_elements = []
                        for el in elements:
                            has_img = self.browser.page.evaluate("(el) => el.querySelector('img') !== null", el)
                            if has_img:
                                valid_elements.append(el)
                        
                        if valid_elements:
                            print(f"使用选择器 '{selector}' 找到了 {len(valid_elements)} 个可点击的帖子")
                            return valid_elements
                except Exception as e:
                    print(f"使用选择器 '{selector}' 时出错: {e}")
                    continue
            
            # 如果通过选择器未找到元素，使用XPath定位并获取可点击元素
            # 用户提供的封面图片路径
            img_xpath = "//section/main/div/div[2]/div/div/div/div/a/div[1]/div[1]/img"
            
            # 查找所有匹配XPath的图片元素
            print("尝试使用XPath查找帖子图片...")
            img_elements = self.browser.page.query_selector_all(f"xpath={img_xpath}")
            
            if img_elements and len(img_elements) > 0:
                print(f"通过XPath找到 {len(img_elements)} 个图片元素")
                
                # 获取每个图片元素的父级a标签
                valid_elements = []
                for img in img_elements:
                    try:
                        # 获取包含图片的链接元素
                        a_element = self.browser.page.evaluate("""
                            (img) => {
                                let current = img;
                                while (current && current.tagName !== 'A') {
                                    current = current.parentElement;
                                }
                                return current;
                            }
                        """, img)
                        
                        if a_element:
                            # 将JavaScript元素转换回Playwright元素对象
                            href = self.browser.page.evaluate("(el) => el.getAttribute('href')", a_element)
                            if href and (href.startswith('/p/') or href.startswith('/reel/')):
                                post_link = self.browser.page.query_selector(f"a[href='{href}']")
                                if post_link:
                                    valid_elements.append(post_link)
                    except Exception as e:
                        print(f"处理图片元素时出错: {e}")
                        continue
                
                if valid_elements:
                    print(f"通过XPath方式找到 {len(valid_elements)} 个可点击的帖子")
                    return valid_elements
            
            # 如果所有方法都失败，生成页面截图以便于调试
            screenshot_path = "debug_screenshot.png"
            self.browser.take_screenshot(screenshot_path)
            print(f"生成了调试截图: {screenshot_path}")
            
            print("无法找到可点击的帖子元素，Instagram页面结构可能已变化")
            return []
            
        except Exception as e:
            print(f"获取帖子元素时出错: {e}")
            return []
    
    def _extract_post_data(self, username):
        """
        从打开的帖子详情中提取数据
        
        Args:
            username (str): 帖子所属用户名
            
        Returns:
            dict: 帖子数据，包括时间戳、文案和图片URL
        """
        try:
            # 等待帖子详情加载
            dialog_selector = "div[role='dialog']"
            if not self.browser.wait_for_selector(dialog_selector):
                print("帖子详情对话框未打开")
                return None
            
            # 提取时间戳文本 - 使用用户提供的新路径
            print("尝试提取时间戳...")
            
            # 尝试多种方法获取时间戳
            timestamp_element = None
            timestamp_text = None  # 初始化显示文本变量
            
            # 方法1: 使用用户提供的XPath路径
            try:
                xpath_timestamp = "//div[@role='dialog']//article//ul//time"
                timestamp_element = self.browser.page.query_selector(f"xpath={xpath_timestamp}")
                if timestamp_element:
                    print("使用XPath找到时间戳元素")
                    
                    # 获取时间戳显示文本
                    timestamp_text = timestamp_element.inner_text()
                    print(f"时间戳显示文本: {timestamp_text}")
                    
                    # 尝试获取datetime属性，它包含精确的ISO格式时间
                    datetime_attr = timestamp_element.get_attribute('datetime')
                    if datetime_attr:
                        from dateutil import parser
                        timestamp = parser.parse(datetime_attr)
                        print(f"从datetime属性获取到精确时间: {timestamp.isoformat()}")
                        
                        # 已经获取了准确时间，可以跳过后续的时间处理
                        author_info = self._extract_author_info(username)
                        caption = self._extract_caption()
                        image_urls = self._extract_image_urls()
                        
                        return {
                            'username': username,
                            'author': author_info,
                            'timestamp': timestamp,
                            'timestamp_text': timestamp_text,  # 添加显示文本
                            'caption': caption,
                            'image_urls': image_urls
                        }
            except Exception as e:
                print(f"使用XPath获取时间戳时出错: {e}")
            
            # 方法2: 如果XPath失败或没有datetime属性，使用CSS选择器
            if not timestamp_element:
                timestamp_selectors = [
                    "div[role='dialog'] time",
                    "div[role='dialog'] article time",
                    "article time"
                ]
                
                for selector in timestamp_selectors:
                    timestamp_element = self.browser.page.query_selector(selector)
                    if timestamp_element:
                        # 获取时间戳显示文本
                        timestamp_text = timestamp_element.inner_text()
                        print(f"使用选择器 '{selector}' 找到时间戳文本: {timestamp_text}")
                        
                        # 尝试获取datetime属性
                        datetime_attr = timestamp_element.get_attribute('datetime')
                        if datetime_attr:
                            from dateutil import parser
                            timestamp = parser.parse(datetime_attr)
                            print(f"从选择器 '{selector}' 的datetime属性获取到精确时间: {timestamp.isoformat()}")
                            break
                        else:
                            print(f"使用选择器 '{selector}' 找到时间戳元素，但没有datetime属性")
                        break
            
            # 如果找到了元素但没有datetime属性，或者没有找到元素，则回退到解析显示文本
            if timestamp_element and not locals().get('timestamp'):
                if not timestamp_text:
                    timestamp_text = timestamp_element.inner_text()
                    print(f"回退到解析显示文本: {timestamp_text}")
                from lib.date_utils import parse_instagram_timestamp
                timestamp = parse_instagram_timestamp(timestamp_text)
            elif not timestamp_element:
                print("未找到时间戳元素")
                return None
            
            # 提取作者信息
            author_info = self._extract_author_info(username)
            
            # 提取帖子文案
            caption = self._extract_caption()
            
            # 提取所有图片URL
            image_urls = self._extract_image_urls()
            
            return {
                'username': username,
                'author': author_info,
                'timestamp': timestamp,
                'timestamp_text': timestamp_text,  # 添加显示文本
                'caption': caption,
                'image_urls': image_urls
            }
            
        except Exception as e:
            print(f"提取帖子数据时出错: {e}")
            return None
    
    def _extract_author_info(self, default_username):
        """提取作者信息的辅助方法"""
        try:
            # 使用XPath路径: /html/body/div[9]/div[1]/div/div[3]/div/div/div/div/div[2]/div/article/div/div[2]/div/div/div[2]/div[1]/ul/div[1]/li/div/div/div[2]/div[1]/h1/a[1]
            xpath_author = "//div[@role='dialog']//article//ul//h1/a[1]"
            author_element = self.browser.page.query_selector(f"xpath={xpath_author}")
            if author_element:
                author_info = author_element.inner_text()
                print(f"使用XPath找到作者: {author_info}")
                return author_info
            
            # 备用CSS选择器
            author_selectors = [
                "div[role='dialog'] article h1 a",
                "article ul h1 a",
                "div[role='dialog'] header a"
            ]
            
            for selector in author_selectors:
                author_element = self.browser.page.query_selector(selector)
                if author_element:
                    author_info = author_element.inner_text()
                    print(f"使用选择器 '{selector}' 找到作者: {author_info}")
                    return author_info
            
            print(f"未找到作者信息，使用默认用户名: {default_username}")
            return default_username
            
        except Exception as e:
            print(f"提取作者信息时出错: {e}")
            return default_username
    
    def _extract_caption(self):
        """提取帖子文案的辅助方法"""
        try:
            caption_selectors = [
                "div[role='dialog'] ul li:first-child span",
                "div[role='dialog'] article ul li span",
                "article ul div span"
            ]
            
            for selector in caption_selectors:
                caption_element = self.browser.page.query_selector(selector)
                if caption_element:
                    caption = caption_element.inner_text()
                    print(f"使用选择器 '{selector}' 找到文案")
                    return caption
            
            print("未找到文案内容")
            return ""
            
        except Exception as e:
            print(f"提取文案时出错: {e}")
            return ""
    
    def _extract_image_urls(self):
        """
        从当前打开的帖子中提取所有图片URL
        
        Returns:
            list: 图片URL列表
        """
        image_urls = []
        
        try:
            print("尝试提取帖子图片URL...")
            
            # 首先尝试获取高质量图片
            # 在帖子对话框中查找所有图片元素
            image_selectors = [
                "div[role='dialog'] article img", # 原始选择器
                "div[role='dialog'] div[role='button'] img", # 更精确的选择器
                "div[role='dialog'] div[aria-label] img", # 另一种可能的选择器
                "div[role='dialog'] img" # 最宽泛的选择器
            ]
            
            # 尝试所有选择器，获取图片元素
            image_element = None
            for selector in image_selectors:
                image_element = self.browser.page.query_selector(selector)
                if image_element:
                    print(f"使用选择器 '{selector}' 找到了图片元素")
                    break
            
            if image_element:
                # 尝试获取srcset属性，它通常包含多个分辨率的图片URL
                srcset = image_element.get_attribute('srcset')
                if srcset:
                    # 从srcset中提取最高分辨率的图片URL
                    urls = srcset.split(',')
                    if urls:
                        # 找到最后一个URL(通常是最高分辨率)
                        highest_res_url = urls[-1].strip().split(' ')[0]
                        if highest_res_url:
                            image_urls.append(highest_res_url)
                            print(f"从srcset中提取到高质量图片URL")
                
                # 如果srcset不存在或提取失败，退回到使用src属性
                if not image_urls:
                    image_url = image_element.get_attribute('src')
                    if image_url:
                        image_urls.append(image_url)
                        print(f"从src属性提取到图片URL")
            
            # 检查是否是多图帖子
            next_button_selectors = [
                "button[aria-label='下一张']", 
                "div[role='dialog'] button[aria-label*='下']",
                "div[role='dialog'] [aria-label*='Next']",
                "div[role='dialog'] svg[aria-label*='Next']"
            ]
            
            next_button = None
            for selector in next_button_selectors:
                next_button = self.browser.page.query_selector(selector)
                if next_button:
                    print(f"找到'下一张'按钮，使用选择器: '{selector}'")
                    break
            
            has_multiple_images = next_button is not None
            
            # 如果是多图帖子，点击"下一张"按钮浏览所有图片
            if has_multiple_images:
                print("检测到多图帖子，开始提取所有图片...")
                # 尝试点击"下一张"按钮直到所有图片都被提取
                max_images = 10  # 限制最大图片数量以避免无限循环
                for i in range(max_images - 1):  # 已经提取了第一张
                    # 找到并点击"下一张"按钮
                    for selector in next_button_selectors:
                        next_button = self.browser.page.query_selector(selector)
                        if next_button:
                            break
                    
                    if not next_button:
                        print(f"无法找到'下一张'按钮，已提取 {len(image_urls)} 张图片")
                        break
                    
                    # 点击"下一张"按钮
                    next_button.click()
                    self.browser.random_delay()
                    
                    # 等待新图片加载
                    self.browser.page.wait_for_timeout(500)  # 等待500毫秒
                    
                    # 获取当前显示的图片
                    for selector in image_selectors:
                        image_element = self.browser.page.query_selector(selector)
                        if image_element:
                            break
                    
                    if not image_element:
                        print(f"无法找到第 {i+2} 张图片元素")
                        continue
                    
                    # 首先尝试获取srcset
                    new_url = None
                    srcset = image_element.get_attribute('srcset')
                    if srcset:
                        urls = srcset.split(',')
                        if urls:
                            new_url = urls[-1].strip().split(' ')[0]
                    
                    # 如果srcset不存在或提取失败，使用src
                    if not new_url:
                        new_url = image_element.get_attribute('src')
                    
                    # 添加到列表，避免重复
                    if new_url and new_url not in image_urls:
                        image_urls.append(new_url)
                        print(f"已提取第 {i+2} 张图片URL")
            
            print(f"总共提取到 {len(image_urls)} 张图片URL")
            return image_urls
            
        except Exception as e:
            print(f"提取图片URL时出错: {e}")
            return image_urls  # 返回已收集的URLs
    
    def _close_post_dialog(self):
        """关闭帖子详情对话框"""
        try:
            # 尝试点击关闭按钮
            close_selector = "div[role='dialog'] button[aria-label='关闭']"
            close_button = self.browser.page.query_selector(close_selector)
            
            if close_button:
                close_button.click()
            else:
                # 尝试ESC键关闭
                self.browser.page.keyboard.press("Escape")
                
        except Exception as e:
            print(f"关闭帖子对话框时出错: {e}")
            # 最后的尝试 - 按Escape键
            try:
                self.browser.page.keyboard.press("Escape")
            except:
                pass 
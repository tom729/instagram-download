#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
浏览器操作模块 - 使用Playwright控制浏览器访问Instagram
"""

import os
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


class BrowserHandler:
    def __init__(self, config):
        """
        初始化浏览器处理器
        
        Args:
            config: 配置对象，包含浏览器设置
        """
        self.config = config
        self.browser = None
        self.context = None
        self.page = None
    
    def __enter__(self):
        """上下文管理器入口点"""
        return self.init_browser()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出点"""
        self.close()
    
    def init_browser(self):
        """
        初始化浏览器，连接到现有Chrome实例或启动新的浏览器
        
        Returns:
            self: 返回当前实例以支持链式调用
        """
        self.playwright = sync_playwright().start()
        
        # 如果配置了使用CDP连接，优先尝试连接到现有Chrome
        if getattr(self.config, 'USE_CDP_CONNECTION', True):
            try:
                print("尝试通过CDP连接到已运行的Chrome浏览器...")
                # 使用CDP协议连接到已运行的Chrome
                self.browser = self.playwright.chromium.connect_over_cdp(
                    f"http://localhost:{self.config.CHROME_REMOTE_DEBUGGING_PORT}"
                )
                # 获取已有的页面或创建新页面
                all_pages = self.browser.contexts[0].pages if self.browser.contexts and self.browser.contexts[0].pages else []
                self.page = all_pages[0] if all_pages else self.browser.contexts[0].new_page()
                print("成功连接到Chrome浏览器!")
                
                # 设置默认超时时间
                self.page.set_default_timeout(self.config.PAGE_LOAD_TIMEOUT * 1000)
                return self
                
            except Exception as e:
                print(f"无法通过CDP连接到现有Chrome实例: {e}")
                # 如果配置强制使用CDP但连接失败，则直接抛出异常
                if getattr(self.config, 'USE_CDP_CONNECTION', False):
                    print("已配置强制使用CDP连接，但连接失败。请确保Chrome已使用以下命令启动：")
                    print(f"/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={self.config.CHROME_REMOTE_DEBUGGING_PORT}")
                    raise e
        
        # 如果CDP连接失败且未强制使用CDP，则尝试其他方法启动浏览器
        # 如果指定了Chrome用户数据目录，使用它启动浏览器
        if self.config.CHROME_USER_DATA_DIR:
            print(f"使用用户数据目录启动Chrome: {self.config.CHROME_USER_DATA_DIR}")
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.config.CHROME_USER_DATA_DIR,
                headless=False,  # 需要可见以获取登录状态
                args=['--start-maximized'],
            )
            self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        else:
            # 其他情况启动新的浏览器实例
            print("启动新的浏览器实例...")
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=[f'--remote-debugging-port={self.config.CHROME_REMOTE_DEBUGGING_PORT}']
            )
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            
        # 设置默认超时时间
        self.page.set_default_timeout(self.config.PAGE_LOAD_TIMEOUT * 1000)
        
        return self
    
    def navigate(self, url):
        """
        导航到指定URL
        
        Args:
            url (str): 要导航到的URL
            
        Returns:
            bool: 导航是否成功
        """
        try:
            self.page.goto(url)
            self.random_delay()
            return True
        except PlaywrightTimeoutError:
            print(f"导航到 {url} 超时")
            return False
        except Exception as e:
            print(f"导航错误: {e}")
            return False
    
    def scroll_down(self, count=5):
        """
        向下滚动页面以加载更多内容
        
        Args:
            count (int): 滚动次数
        """
        for _ in range(count):
            self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            # 随机延迟
            self.random_delay()
    
    def random_delay(self):
        """添加随机延迟以模拟人类行为"""
        delay = random.uniform(
            self.config.RANDOM_DELAY_MIN, 
            self.config.RANDOM_DELAY_MAX
        )
        time.sleep(delay)
    
    def get_instagram_profile_url(self, username):
        """
        获取Instagram用户资料页的URL
        
        Args:
            username (str): Instagram用户名
            
        Returns:
            str: 用户资料页URL
        """
        return f"https://www.instagram.com/{username}/"
    
    def wait_for_selector(self, selector, timeout=10000):
        """
        等待选择器出现
        
        Args:
            selector (str): CSS选择器
            timeout (int): 超时时间(毫秒)
            
        Returns:
            bool: 选择器是否出现
        """
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            print(f"等待选择器 {selector} 超时")
            return False
        except Exception as e:
            print(f"等待选择器错误: {e}")
            return False
    
    def take_screenshot(self, path):
        """
        截取当前页面的屏幕截图
        
        Args:
            path (str): 保存截图的路径
        """
        try:
            self.page.screenshot(path=path, full_page=True)
            print(f"截图已保存: {path}")
        except Exception as e:
            print(f"截图失败: {e}")
    
    def close(self):
        """关闭浏览器会话"""
        try:
            if self.browser:
                self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"关闭浏览器失败: {e}") 
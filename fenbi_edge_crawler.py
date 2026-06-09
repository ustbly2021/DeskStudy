#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
粉笔网题目解析爬虫（基于Edge浏览器自动化）
"""

import json
import re
import argparse
import time
from typing import List, Dict, Any, Optional

try:
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
except ImportError:
    print("请先安装依赖：pip install selenium")
    exit(1)


class FenbiEdgeCrawler:
    """基于Edge的粉笔网爬虫"""
    
    def __init__(self):
        self.driver = None
        self.edge_path = None
        self.driver_path = None
        self.chapters = None  # 章节筛选列表
    
    def set_edge_path(self, edge_path: str):
        """设置Edge浏览器路径"""
        self.edge_path = edge_path
    
    def set_driver_path(self, driver_path: str):
        """设置EdgeDriver路径"""
        self.driver_path = driver_path
    
    def _init_driver(self):
        """初始化浏览器驱动"""
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
        
        if self.edge_path:
            options.binary_location = self.edge_path
            print(f"使用指定的Edge路径: {self.edge_path}")
        
        if self.driver_path:
            print(f"使用指定的EdgeDriver路径: {self.driver_path}")
            service = Service(self.driver_path)
            self.driver = webdriver.Edge(service=service, options=options)
        else:
            self.driver = webdriver.Edge(options=options)
    
    def set_cookies_from_file(self, cookie_file: str):
        """从文件加载Cookie（支持多种格式）"""
        with open(cookie_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.cookies = []
        
        # 尝试解析多种格式
        # 格式1: 每行一个 name=value
        if '\n' in content and '=' in content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    self.cookies.append({'name': key.strip(), 'value': value.strip()})
        
        # 格式2: 浏览器复制格式 name=value; name2=value2
        if len(self.cookies) == 0 and ';' in content:
            parts = content.split(';')
            for part in parts:
                part = part.strip()
                if part and '=' in part:
                    key, value = part.split('=', 1)
                    self.cookies.append({'name': key.strip(), 'value': value.strip()})
        
        print(f"解析到 {len(self.cookies)} 个Cookie")
        for cookie in self.cookies:
            print(f"  - {cookie['name']}: {cookie['value'][:20]}...")
    
    def crawl(self, url: str) -> Dict[str, Any]:
        """爬取题目详情"""
        print(f"开始爬取: {url}")
        
        if not self.driver:
            self._init_driver()
        
        try:
            # 策略：先访问www.fenbi.com建立会话，再访问目标页面
            print("策略：先访问官网建立会话...")
            self.driver.get('https://www.fenbi.com/')
            time.sleep(2)
            
            # 在官网设置Cookie
            if hasattr(self, 'cookies'):
                print(f"在 www.fenbi.com 添加 {len(self.cookies)} 个Cookie...")
                for cookie in self.cookies:
                    try:
                        cookie_copy = cookie.copy()
                        cookie_copy['path'] = '/'
                        cookie_copy['domain'] = '.fenbi.com'  # 使用通配符域名
                        self.driver.add_cookie(cookie_copy)
                        print(f"  ✓ {cookie['name']}")
                    except Exception as e:
                        try:
                            cookie_copy = cookie.copy()
                            cookie_copy['path'] = '/'
                            if 'domain' in cookie_copy:
                                del cookie_copy['domain']
                            self.driver.add_cookie(cookie_copy)
                            print(f"  ✓ {cookie['name']} (无域名)")
                        except Exception as e2:
                            print(f"  ✗ {cookie['name']} - {e2}")
            
            # 刷新主页确认登录
            print("\n刷新主页确认登录状态...")
            self.driver.refresh()
            time.sleep(3)
            print(f"主页标题: {self.driver.title}")
            
            # 获取当前Cookie
            current_cookies = self.driver.get_cookies()
            print(f"当前浏览器Cookie数量: {len(current_cookies)}")
            
            # 现在访问目标页面
            print(f"\n访问目标页面: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 检查当前URL和标题
            current_url = self.driver.current_url
            page_title = self.driver.title
            print(f"当前URL: {current_url}")
            print(f"页面标题: {page_title}")
            
            # 检查是否被重定向
            if current_url != url:
                print(f"警告：页面被重定向！从 {url} -> {current_url}")
                if 'login' in current_url.lower() or 'signin' in current_url.lower():
                    print("错误：被重定向到登录页，Cookie可能已失效！")
            
            print("\n等待页面加载...")
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'question-choice-container'))
                )
                print("页面加载完成！")
            except:
                print("等待超时，尝试继续...")
            
            time.sleep(3)
            
            html = self.driver.page_source
            print(f"页面HTML长度: {len(html)} 字符")
            
            # 保存页面HTML到文件（用于调试）
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("页面HTML已保存到 page_source.html")
            
            return self._parse_html(html, chapters=self.chapters)
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def _parse_html(self, html: str, chapters: Optional[List[str]] = None) -> Dict[str, Any]:
        """解析HTML内容
        
        Args:
            html: 页面HTML
            chapters: 需要提取的章节名称列表，为空则提取全部
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        result = {'questions': []}
        
        # 查找所有章节名和题目容器，按页面顺序遍历
        # 章节名: <div class="chapter-name">
        # 题目: <div class="question-choice-container">
        # 解析: <section class="result-common-section" id="section-solution-xxx">
        
        all_question_containers = soup.find_all('div', class_='question-choice-container')
        all_solution_sections = soup.find_all('section', class_='result-common-section')
        all_solution_sections = [s for s in all_solution_sections if s.get('id', '').startswith('section-solution-')]
        
        print(f"找到 {len(all_question_containers)} 个题目容器")
        print(f"找到 {len(all_solution_sections)} 个解析section")
        
        if not chapters:
            # 不筛选章节，提取全部
            for i, container in enumerate(all_question_containers):
                question = self._parse_single_question(container)
                if question:
                    if i < len(all_solution_sections):
                        explanation = self._parse_explanation_section(all_solution_sections[i])
                        question['explanation'] = explanation
                    result['questions'].append(question)
                    self._print_question_status(i, question)
            return result
        
        # 按章节筛选：需要找到每个章节包含的题目范围
        # 策略：遍历页面中所有元素，记录每个chapter-name对应的题目索引范围
        chapter_ranges = self._find_chapter_ranges(soup, all_question_containers, chapters)
        
        if not chapter_ranges:
            print(f"未找到匹配的章节！可用章节：")
            all_chapters = soup.find_all('div', class_='chapter-name')
            for ch in all_chapters:
                print(f"  - {ch.get_text(strip=True)}")
            return result
        
        # 提取匹配章节的题目
        for ch_name, (start_idx, end_idx) in chapter_ranges.items():
            print(f"\n提取章节: {ch_name} (题目 {start_idx+1}-{end_idx})")
            for i in range(start_idx, end_idx):
                if i < len(all_question_containers):
                    question = self._parse_single_question(all_question_containers[i])
                    if question:
                        question['category'] = ch_name
                        if i < len(all_solution_sections):
                            explanation = self._parse_explanation_section(all_solution_sections[i])
                            question['explanation'] = explanation
                        result['questions'].append(question)
                        self._print_question_status(i, question)
        
        return result
    
    def _find_chapter_ranges(self, soup, question_containers, chapters: List[str]) -> Dict[str, tuple]:
        """查找每个章节对应的题目索引范围
        
        根据章节名中的题数（如"政治理论（20题）"）按顺序计算范围
        
        Returns:
            {章节名: (start_idx, end_idx)} 字典
        """
        chapter_elements = soup.find_all('div', class_='chapter-name')
        if not chapter_elements:
            print("未找到任何章节标记")
            return {}
        
        # 记录章节信息
        chapter_info = []
        for ch_elem in chapter_elements:
            ch_name = ch_elem.get_text(strip=True)
            # 提取题数，如"政治理论（20题）" -> 20
            match = re.search(r'（(\d+)题）', ch_name)
            count = int(match.group(1)) if match else 0
            # 去掉题数部分
            ch_name_clean = re.sub(r'（\d+题）', '', ch_name).strip()
            chapter_info.append({
                'name': ch_name,
                'name_clean': ch_name_clean,
                'count': count
            })
            print(f"发现章节: {ch_name}")
        
        # 按顺序计算每个章节的题目范围
        chapter_ranges = {}
        current_idx = 0
        for info in chapter_info:
            start_idx = current_idx
            end_idx = current_idx + info['count']
            
            # 检查是否匹配用户指定的章节
            for target in chapters:
                if target in info['name_clean'] or info['name_clean'] in target:
                    chapter_ranges[info['name_clean']] = (start_idx, end_idx)
                    break
            
            current_idx = end_idx
        
        return chapter_ranges
    
    def _print_question_status(self, i: int, question: Dict) -> None:
        """打印题目解析状态"""
        if question['explanation']:
            print(f"  第 {i+1} 题: {question['content'][:30]}... [有解析]")
        else:
            print(f"  第 {i+1} 题: {question['content'][:30]}... [无解析]")
    
    def _replace_underline_blanks(self, element) -> None:
        """将 <u>&nbsp;&nbsp;...</u> 替换为 ______"""
        if element is None:
            return
        for u_tag in element.find_all('u'):
            u_tag.replace_with('______')

    def _parse_single_question(self, container) -> Optional[Dict[str, Any]]:
        """解析单个题目"""
        question = {
            'content': '',
            'option_a': '',
            'option_b': '',
            'option_c': '',
            'option_d': '',
            'correct_answer': '',
            'explanation': '',
            'category': '行测',
            'difficulty': 2,
            'question_type': 'single'
        }
        
        format_html = container.find('app-format-html')
        if format_html:
            # 先替换下划线空白
            self._replace_underline_blanks(format_html)
            paragraphs = format_html.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            question['content'] = content
        
        choice_radio = container.find('app-choice-radio')
        if choice_radio:
            options = choice_radio.find_all('li', class_='choice-radio')
            for option in options:
                label = option.find('div', class_='input-radio')
                text = option.find('p', class_='input-text')
                
                if label and text:
                    label_text = label.get_text(strip=True)
                    option_text = text.get_text(strip=True)
                    
                    if 'correctLost' in label.get('class', []):
                        question['correct_answer'] = label_text
                    
                    if label_text == 'A':
                        question['option_a'] = option_text
                    elif label_text == 'B':
                        question['option_b'] = option_text
                    elif label_text == 'C':
                        question['option_c'] = option_text
                    elif label_text == 'D':
                        question['option_d'] = option_text
        
        return question if question['content'] else None
    
    def _parse_explanation_section(self, section) -> str:
        """从解析section中提取解析内容"""
        # 查找 div.content 中的 app-format-html
        content_div = section.find('div', class_='content')
        if content_div:
            # 替换下划线空白
            self._replace_underline_blanks(content_div)
            format_html = content_div.find('app-format-html')
            if format_html:
                paragraphs = format_html.find_all('p')
                if paragraphs:
                    return '\n'.join([p.get_text(strip=True) for p in paragraphs])
            # 没有app-format-html，直接提取文本
            text = content_div.get_text(strip=True)
            if text:
                return text
        return ''
    
    def save_to_json(self, data: Dict[str, Any], filename: str) -> None:
        """保存到JSON文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"已保存到 {filename}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="粉笔网题目解析爬虫（基于Edge浏览器）")
    parser.add_argument("url", help="题目页面URL")
    parser.add_argument("--cookie-file", help="Cookie文件路径（每行一个name=value）")
    parser.add_argument("--output", default="fenbi_questions.json", help="输出文件名")
    parser.add_argument("--edge-path", help="Edge浏览器路径")
    parser.add_argument("--driver-path", help="EdgeDriver路径")
    parser.add_argument("--chapters", help="只提取指定章节，逗号分隔，如：政治理论,常识判断,言语理解与表达")
    
    args = parser.parse_args()
    
    crawler = FenbiEdgeCrawler()
    
    if args.edge_path:
        crawler.set_edge_path(args.edge_path)
    
    if args.driver_path:
        crawler.set_driver_path(args.driver_path)
    
    if args.cookie_file:
        crawler.set_cookies_from_file(args.cookie_file)
    
    if args.chapters:
        crawler.chapters = [ch.strip() for ch in args.chapters.split(',')]
        print(f"只提取章节: {crawler.chapters}")
    
    result = crawler.crawl(args.url)
    
    if result:
        crawler.save_to_json(result, args.output)
        print(f"成功提取 {len(result['questions'])} 道题目")
    else:
        print("未提取到题目")


if __name__ == "__main__":
    main()

"""
粉笔网题目导入服务
"""

import json
import re
import time
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from app.DeskStudy.utils.logger import get_logger

logger = get_logger(__name__)


class FenbiImportService:
    """粉笔网导入服务"""

    def __init__(self):
        self.driver = None
        self._stop_flag = False

    def stop(self):
        """停止导入"""
        self._stop_flag = True
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def parse_cookies(self, cookie_text: str) -> List[Dict[str, str]]:
        """解析Cookie文本为列表格式"""
        cookies = []

        # 尝试多种格式
        # 格式1: 每行一个 name=value
        if '\n' in cookie_text:
            lines = cookie_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        cookies.append({'name': parts[0].strip(), 'value': parts[1].strip()})

        # 格式2: 浏览器复制格式 name=value; name2=value2
        if not cookies and ';' in cookie_text:
            parts = cookie_text.split(';')
            for part in parts:
                part = part.strip()
                if part and '=' in part:
                    kv = part.split('=', 1)
                    if len(kv) == 2:
                        cookies.append({'name': kv[0].strip(), 'value': kv[1].strip()})

        # 格式3: 单个 name=value
        if not cookies and '=' in cookie_text:
            parts = cookie_text.split('=', 1)
            if len(parts) == 2:
                cookies.append({'name': parts[0].strip(), 'value': parts[1].strip()})

        return cookies

    def fetch_chapters(self, url: str, cookies: List[Dict[str, str]],
                       progress_callback: Callable[[str], None] = None) -> List[Dict[str, Any]]:
        """
        获取页面中的章节列表

        Returns:
            [{'name': '章节名', 'count': 题目数量}, ...]
        """
        self._stop_flag = False

        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.chrome.options import Options as ChromeOptions
        except ImportError:
            raise ImportError("请先安装 selenium: pip install selenium")

        if progress_callback:
            progress_callback("正在初始化浏览器...")

        # 尝试使用 webdriver_manager 自动管理驱动
        driver = None
        errors = []

        # 方式1: 使用 Edge + webdriver_manager
        try:
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.webdriver.edge.service import Service as EdgeService

            options = EdgeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            service = EdgeService(executable_path=EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
        except Exception as e:
            errors.append(f"Edge: {str(e)}")

        # 方式2: 使用 Chrome + webdriver_manager
        if driver is None:
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service as ChromeService

                options = ChromeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

                service = ChromeService(executable_path=ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                errors.append(f"Chrome: {str(e)}")

        # 方式3: 直接使用 Edge（不使用 webdriver_manager）
        if driver is None:
            try:
                options = EdgeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                driver = webdriver.Edge(options=options)
            except Exception as e:
                errors.append(f"Edge (直接): {str(e)}")

        # 方式4: 直接使用 Chrome
        if driver is None:
            try:
                options = ChromeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                errors.append(f"Chrome (直接): {str(e)}")

        if driver is None:
            error_msg = "初始化浏览器失败，请安装浏览器驱动：\n"
            error_msg += "pip install webdriver-manager\n\n"
            error_msg += "详细错误：\n" + "\n".join(errors)
            raise Exception(error_msg)

        self.driver = driver

        try:
            # 先访问主页建立会话
            if progress_callback:
                progress_callback("正在访问粉笔网...")

            self.driver.get('https://www.fenbi.com/')
            time.sleep(2)

            # 设置Cookie
            if progress_callback:
                progress_callback("正在设置登录状态...")

            for cookie in cookies:
                try:
                    cookie_copy = cookie.copy()
                    cookie_copy['path'] = '/'
                    cookie_copy['domain'] = '.fenbi.com'
                    self.driver.add_cookie(cookie_copy)
                except:
                    try:
                        cookie_copy = cookie.copy()
                        cookie_copy['path'] = '/'
                        self.driver.add_cookie(cookie_copy)
                    except:
                        pass

            # 访问目标页面
            if progress_callback:
                progress_callback("正在加载题目页面...")

            self.driver.get(url)
            time.sleep(5)

            # 检查是否需要登录
            current_url = self.driver.current_url
            if 'login' in current_url.lower():
                raise Exception("Cookie已失效，请重新登录粉笔网获取Cookie")

            # 解析章节
            if progress_callback:
                progress_callback("正在解析章节...")

            from bs4 import BeautifulSoup
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            chapters = []
            chapter_elements = soup.find_all('div', class_='chapter-name')

            for ch_elem in chapter_elements:
                ch_name = ch_elem.get_text(strip=True)
                # 提取题数，如"政治理论（20题）" -> 20
                match = re.search(r'（(\d+)题）', ch_name)
                count = int(match.group(1)) if match else 0
                # 去掉题数部分
                ch_name_clean = re.sub(r'（\d+题）', '', ch_name).strip()

                chapters.append({
                    'name': ch_name_clean,
                    'full_name': ch_name,
                    'count': count
                })

            return chapters

        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def import_questions(self, url: str, cookies: List[Dict[str, str]],
                         selected_chapters: List[str] = None,
                         progress_callback: Callable[[str, int, int], None] = None) -> List[Dict[str, Any]]:
        """
        导入题目

        Args:
            url: 粉笔网题目页面URL
            cookies: Cookie列表
            selected_chapters: 选中的章节名称列表，为空则导入全部
            progress_callback: 进度回调函数 (message, current, total)

        Returns:
            题目列表
        """
        self._stop_flag = False

        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.chrome.options import Options as ChromeOptions
        except ImportError:
            raise ImportError("请先安装 selenium: pip install selenium")

        if progress_callback:
            progress_callback("正在初始化浏览器...", 0, 0)

        # 尝试使用 webdriver_manager 自动管理驱动
        driver = None
        errors = []

        # 方式1: 使用 Edge + webdriver_manager
        try:
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.webdriver.edge.service import Service as EdgeService

            options = EdgeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            service = EdgeService(executable_path=EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
        except Exception as e:
            errors.append(f"Edge: {str(e)}")

        # 方式2: 使用 Chrome + webdriver_manager
        if driver is None:
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service as ChromeService

                options = ChromeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

                service = ChromeService(executable_path=ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                errors.append(f"Chrome: {str(e)}")

        # 方式3: 直接使用 Edge（不使用 webdriver_manager）
        if driver is None:
            try:
                options = EdgeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                driver = webdriver.Edge(options=options)
            except Exception as e:
                errors.append(f"Edge (直接): {str(e)}")

        # 方式4: 直接使用 Chrome
        if driver is None:
            try:
                options = ChromeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                errors.append(f"Chrome (直接): {str(e)}")

        if driver is None:
            error_msg = "初始化浏览器失败，请安装浏览器驱动：\n"
            error_msg += "pip install webdriver-manager\n\n"
            error_msg += "详细错误：\n" + "\n".join(errors)
            raise Exception(error_msg)

        self.driver = driver

        try:
            # 访问主页
            if progress_callback:
                progress_callback("正在访问粉笔网...", 0, 0)

            self.driver.get('https://www.fenbi.com/')
            time.sleep(2)

            # 设置Cookie
            for cookie in cookies:
                try:
                    cookie_copy = cookie.copy()
                    cookie_copy['path'] = '/'
                    cookie_copy['domain'] = '.fenbi.com'
                    self.driver.add_cookie(cookie_copy)
                except:
                    pass

            # 访问目标页面
            if progress_callback:
                progress_callback("正在加载题目页面...", 0, 0)

            self.driver.get(url)
            time.sleep(5)

            # 检查登录状态
            current_url = self.driver.current_url
            if 'login' in current_url.lower():
                raise Exception("Cookie已失效，请重新登录粉笔网获取Cookie")

            # 点击"交卷"按钮以显示解析
            if progress_callback:
                progress_callback("正在点击交卷按钮...", 0, 0)

            try:
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC

                # 查找并点击"交卷"按钮
                submit_btns = self.driver.find_elements(By.CSS_SELECTOR, 'div.submit-btn')
                if submit_btns:
                    submit_btns[0].click()
                    logger.info("已点击交卷按钮")
                    time.sleep(1)

                    # 查找并点击"确认"按钮
                    confirm_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button.modal-action-btn.btn-submit')
                    if confirm_btns:
                        confirm_btns[0].click()
                        logger.info("已点击确认按钮")
                        time.sleep(3)  # 等待解析加载

                        if progress_callback:
                            progress_callback("解析已加载，正在提取题目...", 0, 0)
                    else:
                        logger.warning("未找到确认按钮，可能已交卷")
                else:
                    logger.warning("未找到交卷按钮，可能已交卷或页面结构不同")

            except Exception as e:
                logger.warning(f"点击交卷按钮失败: {e}，继续尝试解析题目")

            # 解析题目
            if progress_callback:
                progress_callback("正在解析题目...", 0, 0)

            from bs4 import BeautifulSoup
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            questions = self._parse_questions(soup, selected_chapters, progress_callback)

            return questions

        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def _parse_questions(self, soup, selected_chapters: List[str] = None,
                         progress_callback=None) -> List[Dict[str, Any]]:
        """解析题目"""
        questions = []

        # 查找所有题目容器和解析
        all_question_containers = soup.find_all('div', class_='question-choice-container')
        all_solution_sections = soup.find_all('section', class_='result-common-section')
        all_solution_sections = [s for s in all_solution_sections if s.get('id', '').startswith('section-solution-')]

        # 查找所有来源区域
        all_source_sections = soup.find_all('section', class_='result-common-section')
        all_source_sections = [s for s in all_source_sections if s.get('id', '').startswith('section-source-')]

        # 查找所有题目的正确率容器
        all_overall_containers = soup.find_all('div', class_='question-overall-container')

        total = len(all_question_containers)
        logger.info(f"找到 {total} 个题目容器，{len(all_overall_containers)} 个正确率容器")

        if not selected_chapters:
            # 导入全部
            for i, container in enumerate(all_question_containers):
                if self._stop_flag:
                    break

                if progress_callback:
                    progress_callback(f"正在解析第 {i+1}/{total} 题...", i+1, total)

                question = self._parse_single_question(container)
                if question:
                    # 解析正确率
                    if i < len(all_overall_containers):
                        question['correct_rate'] = self._parse_correct_rate(all_overall_containers[i])
                    if i < len(all_solution_sections):
                        question['explanation'] = self._parse_explanation(all_solution_sections[i])
                    if i < len(all_source_sections):
                        question['source'] = self._parse_source(all_source_sections[i])
                    questions.append(question)
        else:
            # 按章节筛选
            chapter_ranges = self._find_chapter_ranges(soup, all_question_containers, selected_chapters)

            for ch_name, (start_idx, end_idx) in chapter_ranges.items():
                if self._stop_flag:
                    break

                logger.info(f"提取章节: {ch_name} (题目 {start_idx+1}-{end_idx})")

                for i in range(start_idx, end_idx):
                    if self._stop_flag:
                        break

                    if progress_callback:
                        progress_callback(f"[{ch_name}] 正在解析第 {i-start_idx+1}/{end_idx-start_idx} 题...", i+1, total)

                    if i < len(all_question_containers):
                        question = self._parse_single_question(all_question_containers[i])
                        if question:
                            question['category'] = ch_name
                            # 解析正确率
                            if i < len(all_overall_containers):
                                question['correct_rate'] = self._parse_correct_rate(all_overall_containers[i])
                            if i < len(all_solution_sections):
                                question['explanation'] = self._parse_explanation(all_solution_sections[i])
                            if i < len(all_source_sections):
                                question['source'] = self._parse_source(all_source_sections[i])
                            questions.append(question)

        return questions

    def _parse_correct_rate(self, container) -> float:
        """解析单题正确率"""
        try:
            rate_elem = container.find('span', class_='correct-rate')
            if rate_elem:
                rate_text = rate_elem.get_text(strip=True).replace('%', '').strip()
                return float(rate_text)
        except Exception as e:
            logger.warning(f"解析正确率失败: {e}")
        return 0.0

    def _find_chapter_ranges(self, soup, question_containers, chapters: List[str]) -> Dict[str, tuple]:
        """查找章节对应的题目索引范围"""
        chapter_elements = soup.find_all('div', class_='chapter-name')
        if not chapter_elements:
            return {}

        chapter_info = []
        for ch_elem in chapter_elements:
            ch_name = ch_elem.get_text(strip=True)
            match = re.search(r'（(\d+)题）', ch_name)
            count = int(match.group(1)) if match else 0
            ch_name_clean = re.sub(r'（\d+题）', '', ch_name).strip()
            chapter_info.append({
                'name': ch_name_clean,
                'count': count
            })

        chapter_ranges = {}
        current_idx = 0
        for info in chapter_info:
            start_idx = current_idx
            end_idx = current_idx + info['count']

            for target in chapters:
                if target in info['name'] or info['name'] in target:
                    chapter_ranges[info['name']] = (start_idx, end_idx)
                    break

            current_idx = end_idx

        return chapter_ranges

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
            'correct_rate': 0.0,
            'source': '',
            'question_type': 'single'
        }

        # 解析题目内容
        format_html = container.find('app-format-html')
        if format_html:
            self._replace_underline_blanks(format_html)
            paragraphs = format_html.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            question['content'] = content

        # 解析选项
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

    def _parse_source(self, section) -> str:
        """解析题目来源"""
        content_div = section.find('div', class_='content')
        if content_div:
            source_text = content_div.get_text(strip=True)
            # 提取年份和考试类型
            # 例如: "2025年国家公务员录用考试《行测》题（地市级网友回忆版）第1题"
            # 提取: "2025年国考"
            import re
            year_match = re.search(r'(\d{4})年', source_text)
            year = year_match.group(1) if year_match else ''

            if '国家公务员' in source_text:
                return f"{year}年国考" if year else "国考"
            elif '省公务员' in source_text:
                # 提取省份 - 只匹配中文字符
                province_match = re.search(r'([\u4e00-\u9fa5]{2,4})省公务员', source_text)
                if province_match:
                    province = province_match.group(1)
                    return f"{year}年{province}省考" if year else f"{province}省考"
                return f"{year}省考" if year else "省考"

            return source_text[:30] if len(source_text) > 30 else source_text
        return ''

    def _parse_explanation(self, section) -> str:
        """解析答案解析"""
        content_div = section.find('div', class_='content')
        if content_div:
            self._replace_underline_blanks(content_div)
            format_html = content_div.find('app-format-html')
            if format_html:
                paragraphs = format_html.find_all('p')
                if paragraphs:
                    return '\n'.join([p.get_text(strip=True) for p in paragraphs])
            text = content_div.get_text(strip=True)
            if text:
                return text
        return ''

    def _replace_underline_blanks(self, element) -> None:
        """替换下划线空白"""
        if element is None:
            return
        for u_tag in element.find_all('u'):
            u_tag.replace_with('______')


# 单例
_fenbi_service: Optional[FenbiImportService] = None


def get_fenbi_service() -> FenbiImportService:
    """获取粉笔导入服务单例"""
    global _fenbi_service
    if _fenbi_service is None:
        _fenbi_service = FenbiImportService()
    return _fenbi_service

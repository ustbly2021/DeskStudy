"""
DeskStudy - 桌面碎片化学习助手
主程序入口
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.DeskStudy.core.app import DeskStudyApp


def main():
    """主函数"""
    app = DeskStudyApp()
    app.run()


if __name__ == "__main__":
    main()

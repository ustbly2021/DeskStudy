# DeskStudy - 桌面学习助手

一款通过悬浮球的形式在桌面上随时显示题目，帮助用户利用碎片时间高效学习的桌面刷题学习工具。

## 功能特性

### 核心功能

- **悬浮球学习** - 桌面悬浮球设计，点击即可刷题，不影响正常工作
- **错题本** - 自动记录错题，支持错题优先复习和掌握度追踪
- **学习统计** - 记录答题数量、正确率、学习时长等数据
- **粉笔网导入** - 支持从粉笔网批量导入题目

### 授权系统

- 支持多种授权类型：试用版(1天)、周卡(7天)、月卡(30天)、半年卡(180天)、年卡(365天)
- 机器码绑定，一机一码
- 在线激活验证

### 其他特性

- 系统托盘后台运行
- 全局热键控制（老板键、暂停键）
- 全屏应用自动暂停
- 边缘吸附、透明度调节
- 支持单选题、多选题、判断题

## 技术栈

- **GUI框架**: PySide6 (Qt)
- **数据库**: SQLite + SQLAlchemy
- **打包工具**: PyInstaller
- **爬虫**: Selenium (粉笔网导入)

## 项目结构

```
DeskStudy/
├── app/DeskStudy/
│   ├── config/          # 配置管理
│   ├── core/            # 核心功能（应用入口、许可证管理）
│   ├── database/        # 数据库连接
│   ├── models/          # 数据模型
│   ├── services/        # 业务服务层
│   │   ├── question_service.py      # 题库服务
│   │   ├── review_service.py        # 复习服务
│   │   ├── wrong_question_service.py # 错题服务
│   │   ├── statistics_service.py    # 统计服务
│   │   └── fenbi_service.py         # 粉笔网导入
│   ├── ui/              # 用户界面
│   │   ├── floating_ball.py         # 悬浮球
│   │   ├── question_card.py         # 题目卡片
│   │   ├── system_tray.py           # 系统托盘
│   │   └── ...
│   └── utils/           # 工具类
├── assets/              # 资源文件
├── build.bat            # Windows打包脚本
├── DeskStudy.spec       # PyInstaller配置
└── activation_server_example.py  # 激活服务器示例
```

## 快速开始

### 环境要求

- Python 3.8+
- Windows 10/11

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python -m app.DeskStudy
```

### 打包发布

```bash
# Windows
build.bat

# 或手动执行
pyinstaller DeskStudy.spec --noconfirm
```

打包后的可执行文件位于 `dist/DeskStudy/` 目录。

## 使用说明

### 基本操作

1. **悬浮球** - 点击悬浮球显示题目，拖动可移动位置
2. **答题** - 点击选项作答，答对显示绿色，答错显示红色
3. **复习** - 系统自动根据艾宾浩斯曲线安排复习

### 热键设置

- **老板键** (Ctrl+Shift+B): 快速隐藏/显示悬浮球
- **暂停键** (Ctrl+Shift+P): 暂停/恢复题目推送

### 导入题目

1. 从粉笔网复制题目页面URL和Cookie
2. 右键托盘图标 -> 导入题目
3. 粘贴URL和Cookie，选择章节导入

## 激活服务器部署

项目提供了激活服务器示例代码 `activation_server_example.py`，可部署到服务器实现在线激活功能。

```bash
# 安装依赖
pip install flask sqlalchemy

# 运行服务器
python activation_server_example.py
```

## 配置

- 悬浮球大小、透明度、自动隐藏延迟
- 题目显示间隔、解析显示
- 热键设置
- 开机自启动、静音模式等

## 许可证

本项目仅供学习交流使用。

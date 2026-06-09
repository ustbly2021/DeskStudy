# -*- mode: python ; coding: utf-8 -*-
"""
DeskStudy PyInstaller 打包配置

使用方法:
  pyinstaller DeskStudy.spec

打包模式:
  - 目录模式 (onedir): 启动快，文件多
  - 单文件模式 (onefile): 启动慢，文件少
"""

block_cipher = None

# 是否使用单文件模式 (True=单文件, False=目录模式)
ONEFILE = False

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 包含题目数据文件 (源路径, 打包后目标路径)
        ('sample_questions.json', '.'),
        # 包含赞赏二维码图片
        ('assets', 'assets'),
        # 包含 EdgeDriver
        ('msedgedriver.exe', '.'),
    ],
    hiddenimports=[
        # PySide6 相关
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # 数据库相关
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        'sqlalchemy.pool',
        # 配置相关
        'pydantic',
        'pydantic_settings',
        # 日志相关
        'loguru',
        # 热键相关
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块，减小体积
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'IPython',
        'jupyter',
        # 额外排除以减小体积
        'pytest',
        'sphinx',
        'docutils',
        # 注意: email 模块被 pkg_resources 依赖，不能排除
        # 'email',
        # 'html',
        'xmlrpc',
        # 'multiprocessing',  # 也可能被依赖
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if ONEFILE:
    # 单文件模式
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='DeskStudy',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )
else:
    # 目录模式 (启动更快)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='DeskStudy',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='DeskStudy',
    )

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI语音生图项目自动更新程序"""

import os
import sys
import json
import hashlib
import zipfile
import shutil
import subprocess
import time
import threading
from datetime import datetime
from pathlib import Path

# 设置环境变量
os.environ['DISPLAY'] = ':0'

# 尝试导入GUI相关模块
try:
    import tkinter as tk
    from tkinter import ttk
    # 测试是否可以创建GUI
    test_root = tk.Tk()
    test_root.withdraw()  # 隐藏测试窗口
    test_root.destroy()
    GUI_AVAILABLE = True
    print("GUI环境可用")
except ImportError:
    GUI_AVAILABLE = False
    print("GUI模块不可用，将使用命令行模式")
except Exception as e:
    GUI_AVAILABLE = False
    print(f"GUI环境不可用: {e}，将使用命令行模式")

# 尝试导入requests，如果失败则使用虚拟环境
try:
    import requests
except ImportError:
    # 激活虚拟环境并重新运行脚本
    venv_python = "/home/orangepi/test1/bin/python"
    if os.path.exists(venv_python):
        print("正在使用虚拟环境重新运行脚本...")
        env = os.environ.copy()
        env['DISPLAY'] = ':0'
        os.execve(venv_python, [venv_python] + sys.argv, env)
    else:
        print("错误：虚拟环境不存在，请先安装依赖")
        print("运行：source /home/orangepi/test1/bin/activate && pip install requests")
        sys.exit(1)

# 服务器基础地址 - 需要根据您的实际服务器地址修改
SERVER_BASE_URL = "http://www.marxmake.com/firmware/AI_VOICE_IMAGE"
VERSION_INFO_URL = f"{SERVER_BASE_URL}/version_info.json"

# 路径配置
PROJECT_DIR = Path(__file__).parent.absolute()
BACKUP_DIR = PROJECT_DIR / "backup"
TEMP_DIR = PROJECT_DIR / "temp"
LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "update_log.txt"
LOCAL_VERSION_FILE = PROJECT_DIR / "version.txt"
MAIN_APP_FILE = PROJECT_DIR / "main.py"
VENV_PATH = Path("/home/orangepi/test1")  # 虚拟环境路径

# 确保日志目录存在
LOG_DIR.mkdir(exist_ok=True)


class UpdateStatusWindow:
    """更新状态显示窗口"""
    
    def __init__(self):
        self.window = None
        self.status_label = None
        self.progress_bar = None
        self.detail_label = None
        self.animation_running = False
        self.dot_count = 0
        
        if GUI_AVAILABLE:
            self.create_window()
    
    def create_window(self):
        """创建窗口"""
        try:
            print("[GUI] 开始创建更新窗口...")
            
            self.window = tk.Tk()
            self.window.title("AI语音生图 - 自动更新")
            
            print("[GUI] tkinter窗口创建成功")
            
            # 设置窗口大小
            window_width = 480
            window_height = 320
            
            # 获取屏幕尺寸
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            print(f"[GUI] 屏幕尺寸: {screen_width}x{screen_height}")
            
            # 计算居中位置
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            print(f"[GUI] 窗口位置: {x}, {y}")
            
            # 设置窗口尺寸和位置
            self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # 设置为无边框模式
            self.window.overrideredirect(True)
            
            # 禁止窗口大小调整
            self.window.resizable(False, False)
            
            # 设置窗口始终在最前面
            self.window.attributes('-topmost', True)
            
            # 设置窗口样式
            self.window.configure(bg='#2c3e50')
            
            print("[GUI] 窗口基本属性设置完成")
            
            # 添加圆角边框效果（通过内边距实现）
            main_frame = tk.Frame(self.window, bg='#34495e', padx=2, pady=2)
            main_frame.pack(fill='both', expand=True)
            
            # 主内容框架
            content_frame = tk.Frame(main_frame, bg='#2c3e50', padx=40, pady=30)
            content_frame.pack(fill='both', expand=True)
            
            # 标题
            title_label = tk.Label(
                content_frame, 
                text="🤖 AI语音生图自动更新",
                font=('Arial', 16, 'bold'),
                fg='#ecf0f1',
                bg='#2c3e50'
            )
            title_label.pack(pady=(0, 20))
            
            # 状态标签
            self.status_label = tk.Label(
                content_frame,
                text="正在检查更新...",
                font=('Arial', 12),
                fg='#3498db',
                bg='#2c3e50',
                wraplength=380
            )
            self.status_label.pack(pady=(0, 15))
            
            # 进度条框架
            progress_frame = tk.Frame(content_frame, bg='#2c3e50')
            progress_frame.pack(fill='x', pady=(0, 15))
            
            # 进度条
            style = ttk.Style()
            style.theme_use('clam')
            style.configure(
                "Custom.Horizontal.TProgressbar",
                background='#3498db',
                troughcolor='#34495e',
                borderwidth=1,
                lightcolor='#3498db',
                darkcolor='#2980b9'
            )
            
            self.progress_bar = ttk.Progressbar(
                progress_frame,
                style="Custom.Horizontal.TProgressbar",
                length=380,
                mode='indeterminate'
            )
            self.progress_bar.pack()
            
            # 详细信息标签
            self.detail_label = tk.Label(
                content_frame,
                text="准备中...",
                font=('Arial', 10),
                fg='#95a5a6',
                bg='#2c3e50',
                wraplength=380
            )
            self.detail_label.pack(pady=(15, 0))
            
            # 绑定键盘事件（ESC键关闭窗口）
            self.window.bind('<Escape>', lambda e: self.close())
            self.window.focus_set()  # 设置焦点以接收键盘事件
            
            print("[GUI] GUI组件创建完成")
            
            # 强制显示窗口
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            
            print("[GUI] 窗口显示完成")
            
            # 启动动画
            self.start_animation()
            
            print("[GUI] 更新窗口创建成功！")
            
        except Exception as e:
            print(f"[GUI] 创建GUI窗口失败: {e}")
            import traceback
            traceback.print_exc()
            self.window = None
    
    def start_animation(self):
        """启动进度条动画"""
        if self.progress_bar:
            self.progress_bar.start(10)
            self.animation_running = True
            self.animate_dots()
    
    def animate_dots(self):
        """动画点点点效果"""
        if not self.animation_running or not self.window:
            return
            
        try:
            if self.status_label:
                current_text = self.status_label.cget('text')
                base_text = current_text.rstrip('.')
                self.dot_count = (self.dot_count % 3) + 1
                new_text = base_text + '.' * self.dot_count
                self.status_label.config(text=new_text)
            
            self.window.after(500, self.animate_dots)
        except:
            pass
    
    def update_status(self, status, detail="", progress_mode='indeterminate'):
        """更新状态显示"""
        if not self.window:
            return
            
        try:
            self.status_label.config(text=status)
            if detail:
                self.detail_label.config(text=detail)
            
            # 更新进度条模式
            if progress_mode == 'determinate':
                self.progress_bar.config(mode='determinate')
                self.progress_bar.stop()
            else:
                self.progress_bar.config(mode='indeterminate')
                if not self.animation_running:
                    self.progress_bar.start(10)
            
            self.window.update()
        except:
            pass
    
    def set_progress(self, value):
        """设置进度条数值（0-100）"""
        if self.progress_bar and self.window:
            try:
                self.progress_bar.config(mode='determinate')
                self.progress_bar['value'] = value
                self.window.update()
            except:
                pass
    
    def show_success(self, message="更新完成"):
        """显示成功状态"""
        if not self.window:
            return
            
        try:
            self.animation_running = False
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.progress_bar['value'] = 100
            
            self.status_label.config(text=f"✅ {message}", fg='#27ae60')
            self.detail_label.config(text="即将启动应用程序...")
            self.window.update()
            
            # 3秒后关闭窗口
            self.window.after(3000, self.close)
        except:
            pass
    
    def show_error(self, message="更新失败", detail=""):
        """显示错误状态"""
        if not self.window:
            return
            
        try:
            self.animation_running = False
            self.progress_bar.stop()
            
            self.status_label.config(text=f"❌ {message}", fg='#e74c3c')
            if detail:
                self.detail_label.config(text=detail)
            self.window.update()
            
            # 5秒后关闭窗口
            self.window.after(5000, self.close)
        except:
            pass
    
    def close(self):
        """关闭窗口"""
        if self.window:
            try:
                self.animation_running = False
                self.window.destroy()
                self.window = None
            except:
                pass
    
    def process_events(self):
        """处理窗口事件"""
        if self.window:
            try:
                self.window.update()
            except:
                pass


# 全局状态窗口
status_window = None

def log(message, status_text=None, detail_text=None):
    """记录日志到文件和控制台，同时更新GUI"""
    global status_window
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    
    try:
        with open(LOG_FILE, 'a', encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"日志写入失败：{e}")
    
    # 更新GUI状态
    if status_window and GUI_AVAILABLE:
        if status_text:
            status_window.update_status(status_text, detail_text or message)
        status_window.process_events()


def get_local_version():
    """获取本地当前版本"""
    try:
        if LOCAL_VERSION_FILE.exists():
            with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
                return f.read().strip().upper()
        else:
            with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
                f.write("V1.0.0")
            return "V1.0.0"
    except Exception as e:
        log(f"获取本地版本失败：{e}")
        return "V1.0.0"


def get_remote_version():
    """从服务器获取最新版本"""
    try:
        log(f"检查更新：{VERSION_INFO_URL}")
        response = requests.get(VERSION_INFO_URL, timeout=15)
        response.raise_for_status()
        return json.loads(response.text)
    except Exception as e:
        log(f"获取服务器版本失败：{e}")
        return None


def calculate_checksum(file_path):
    """计算文件的SHA256校验和"""
    try:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        log(f"计算校验和失败：{e}")
        return None


def download_update(download_url, save_path):
    """下载更新包"""
    global status_window
    
    try:
        log(f"开始下载：{download_url}")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(download_url, stream=True, timeout=60)
        response.raise_for_status()
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # 更新下载进度
                    if status_window and total_size > 0:
                        progress = int((downloaded / total_size) * 30) + 20  # 20-50%
                        status_window.set_progress(progress)
                        size_mb = downloaded / 1024 / 1024
                        total_mb = total_size / 1024 / 1024
                        status_window.update_status(
                            f"正在下载更新包 ({size_mb:.1f}MB/{total_mb:.1f}MB)",
                            f"下载进度: {downloaded/total_size*100:.1f}%"
                        )
                        status_window.process_events()

        log(f"下载完成：{save_path}")
        return True
    except Exception as e:
        log(f"下载失败：{e}")
        if save_path.exists():
            save_path.unlink()
        return False


def backup_current_version():
    """备份当前版本"""
    global status_window
    
    try:
        log("开始备份当前版本...", "正在备份当前版本", "保证更新安全...")

        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # 备份主要文件
        files_to_backup = [
            "main.py", "main_window.py", "pages", "styles", 
            "threads", "utils", "widgets", "Icon"
        ]
        
        total_files = len(files_to_backup)
        for i, item in enumerate(files_to_backup):
            src = PROJECT_DIR / item
            if src.exists():
                dst = BACKUP_DIR / item
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                log(f"备份：{item}")
                
                # 更新进度
                if status_window:
                    progress = int((i + 1) / total_files * 20)  # 0-20%
                    status_window.set_progress(progress)
                    status_window.process_events()

        if LOCAL_VERSION_FILE.exists():
            shutil.copy2(LOCAL_VERSION_FILE, BACKUP_DIR / "version.txt")
            log("版本文件备份完成")

        return True
    except Exception as e:
        log(f"备份失败：{e}")
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        return False


def extract_update(zip_path):
    """解压更新包"""
    try:
        log(f"解压更新包：{zip_path}")
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(TEMP_DIR)

        log("解压完成")
        return True
    except Exception as e:
        log(f"解压失败：{e}")
        return False


def apply_update():
    """应用更新"""
    try:
        log("开始应用更新...")

        # 获取解压内容
        temp_items = list(TEMP_DIR.iterdir())
        if len(temp_items) == 1 and temp_items[0].is_dir():
            # 如果解压后只有一个目录，使用该目录
            extract_dir = temp_items[0]
        else:
            # 否则使用TEMP_DIR本身
            extract_dir = TEMP_DIR

        # 更新文件
        files_to_update = [
            "main.py", "main_window.py", "pages", "styles", 
            "threads", "utils", "widgets"
        ]
        
        for item in files_to_update:
            src = extract_dir / item
            dst = PROJECT_DIR / item
            
            if src.exists():
                if dst.exists():
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()
                
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                log(f"更新：{item}")

        log("更新应用完成")
        return True
    except Exception as e:
        log(f"应用更新失败：{e}")
        return False


def clean_up(temp_file=None):
    """清理临时文件"""
    try:
        if temp_file and temp_file.exists():
            temp_file.unlink()
            log(f"删除临时文件：{temp_file}")
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
            log("清理临时目录")
    except Exception as e:
        log(f"清理失败：{e}")


def rollback():
    """回滚到备份版本"""
    global status_window
    
    try:
        log("开始回滚...", "正在回滚到上一版本", "恢复之前的稳定版本...")
        
        if not BACKUP_DIR.exists():
            log("无备份可回滚")
            return False

        # 恢复文件
        for item in BACKUP_DIR.iterdir():
            if item.name == "version.txt":
                continue
            
            src = item
            dst = PROJECT_DIR / item.name
            
            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        # 恢复版本文件
        if (BACKUP_DIR / "version.txt").exists():
            shutil.copy2(BACKUP_DIR / "version.txt", LOCAL_VERSION_FILE)

        shutil.rmtree(BACKUP_DIR)
        log("回滚完成")
        
        if status_window:
            status_window.update_status("回滚成功", "已恢复到上一个稳定版本")
        
        return True
    except Exception as e:
        log(f"回滚失败：{e}")
        return False


def update_version_file(new_version):
    """更新本地版本记录"""
    try:
        with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(new_version)
        log(f"版本文件更新为：{new_version}")
        return True
    except Exception as e:
        log(f"版本文件更新失败：{e}")
        return False


def run_application():
    """启动AI语音生图应用程序"""
    global status_window
    
    try:
        log("启动AI语音生图应用程序...", "正在启动应用程序", "准备进入AI语音生图界面...")
        
        if status_window:
            status_window.update_status("正在启动应用程序", "准备进入AI语音生图界面...")
            status_window.set_progress(95)
            status_window.process_events()
        
        # 设置环境变量
        env = os.environ.copy()
        env['DISPLAY'] = ':0'
        
        # 构建启动命令
        activate_cmd = f"source {VENV_PATH}/bin/activate"
        run_cmd = f"{activate_cmd} && cd {PROJECT_DIR} && python {MAIN_APP_FILE}"
        
        # 启动应用
        process = subprocess.Popen(
            run_cmd, 
            shell=True, 
            executable='/bin/bash',
            env=env,
            cwd=str(PROJECT_DIR)
        )
        
        log(f"AI语音生图应用程序已启动，PID: {process.pid}")
        
        # 关闭状态窗口
        if status_window:
            status_window.set_progress(100)
            status_window.show_success("应用程序已启动")
            # 等待一下然后关闭
            time.sleep(1)
            status_window.close()
        
        return process
    except Exception as e:
        log(f"应用启动失败：{e}")
        if status_window:
            status_window.show_error("应用启动失败", str(e))
        return None


def main():
    """主函数"""
    global status_window
    
    # 初始化GUI状态窗口
    if GUI_AVAILABLE:
        status_window = UpdateStatusWindow()
        if status_window.window:
            status_window.update_status("正在启动自动更新程序", "正在初始化...")
    
    log("=======AI语音生图自动更新程序启动========")

    # 获取本地版本
    local_version = get_local_version()
    log(f"当前版本：{local_version}", "正在检查本地版本", f"本地版本: {local_version}")

    # 获取远程版本信息
    if status_window:
        status_window.update_status("正在检查服务器更新", "连接服务器中...")
    
    remote_info = get_remote_version()
    if not remote_info:
        log("无法获取服务器版本信息，启动当前应用", "无法连接服务器", "将使用本地版本启动应用")
        if status_window:
            status_window.show_error("无法连接服务器", "将使用本地版本启动应用")
            time.sleep(2)
        run_application()
        return

    # 处理版本信息（适配多种JSON格式）
    remote_version = remote_info.get("version", remote_info.get("system_version", "")).upper()
    update_file = remote_info.get("update_file", remote_info.get("update_file_name", ""))
    remote_checksum = remote_info.get("checksum", "").lower()

    log(f"服务器最新版本：{remote_version}", "获取版本信息成功", f"服务器版本: {remote_version}")

    # 检查是否需要更新
    if local_version == remote_version:
        log("已是最新版本，启动应用", "已是最新版本", "无需更新，正在启动应用...")
        if status_window:
            status_window.show_success("已是最新版本")
            time.sleep(1)
        run_application()
        return

    if not update_file:
        log("服务器未提供更新包", "无更新包", "服务器未提供更新文件")
        if status_window:
            status_window.show_error("无更新包", "服务器未提供更新文件")
            time.sleep(2)
        run_application()
        return

    log(f"发现新版本：{remote_version}，开始更新...", f"🎆 发现新版本 {remote_version}", f"从 {local_version} 更新到 {remote_version}")
    
    if status_window:
        status_window.update_status(f"发现新版本 {remote_version}", f"从 {local_version} 更新到 {remote_version}")

    # 下载更新
    download_url = f"{SERVER_BASE_URL}/{update_file}"
    temp_zip = TEMP_DIR / Path(update_file).name
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 执行备份
    if status_window:
        status_window.update_status("正在备份当前版本", "保证更新安全...")
    
    if not backup_current_version():
        log("备份失败，取消更新", "备份失败", "为保证安全，取消更新")
        if status_window:
            status_window.show_error("备份失败", "为保证安全，取消更新")
            time.sleep(2)
        run_application()
        return

    # 下载更新包
    if status_window:
        status_window.update_status("正在下载更新包", f"下载: {update_file}")
    
    if not download_update(download_url, temp_zip):
        log("下载失败，启动当前应用", "下载失败", "网络连接或文件不存在")
        if status_window:
            status_window.show_error("下载失败", "网络连接或文件不存在")
            time.sleep(2)
        clean_up(temp_zip)
        run_application()
        return

    # 校验文件
    if remote_checksum:
        if status_window:
            status_window.update_status("正在校验文件完整性", "确保更新包完整...")
        
        local_checksum = calculate_checksum(temp_zip)
        if local_checksum and local_checksum.lower() != remote_checksum:
            log(f"校验和不匹配：本地={local_checksum[:16]}..., 远程={remote_checksum[:16]}...", "文件校验失败", "更新包可能损坏")
            if status_window:
                status_window.show_error("文件校验失败", "更新包可能损坏")
                time.sleep(2)
            clean_up(temp_zip)
            run_application()
            return
        log("文件校验通过", "文件校验成功", "更新包完整性确认")

    # 解压更新
    if status_window:
        status_window.update_status("正在解压更新包", "准备安装文件...")
    
    if not extract_update(temp_zip):
        log("解压失败，尝试回滚", "解压失败", "正在回滚到上一版本")
        if status_window:
            status_window.show_error("解压失败", "正在回滚到上一版本")
            time.sleep(2)
        clean_up(temp_zip)
        rollback()
        run_application()
        return

    # 应用更新
    if status_window:
        status_window.update_status("正在应用更新", "更新应用程序文件...")
        status_window.set_progress(50)
    
    if not apply_update():
        log("应用更新失败，尝试回滚", "更新失败", "正在回滚到上一版本")
        if status_window:
            status_window.show_error("更新失败", "正在回滚到上一版本")
            time.sleep(2)
        clean_up(temp_zip)
        rollback()
        run_application()
        return

    # 清理临时文件
    if status_window:
        status_window.update_status("正在清理临时文件", "完成安装...")
        status_window.set_progress(80)
    
    clean_up(temp_zip)

    # 更新版本文件
    if status_window:
        status_window.set_progress(90)
    
    update_version_file(remote_version)
    log(f"更新成功：{local_version} -> {remote_version}", f"✅ 更新成功！", f"从 {local_version} 更新到 {remote_version}")

    # 显示成功状态
    if status_window:
        status_window.show_success(f"更新成功！{remote_version}")
        time.sleep(2)
    
    # 启动应用
    run_application()

if __name__ == "__main__":
    main()
# AI语音生图项目 - 快速开始

## 🚀 一键运行

```bash
# 测试环境（推荐先运行）
./test_environment.sh

# 启动程序（自动更新+运行）
./run_updater.sh
```

## 🔧 安装开机自启动

```bash
# 安装自启动服务
./install_autostart.sh

# 重启系统测试
sudo reboot
```

## 📁 重要文件

| 文件 | 用途 |
|------|------|
| `run_updater.sh` | 一键启动脚本（解决环境问题） |
| `startup_updater.sh` | 开机自启动专用脚本 |
| `test_environment.sh` | 环境检查脚本 |
| `install_autostart.sh` | 安装开机自启动 |
| `auto_updater.py` | 自动更新核心程序 |

## ❓ 问题解决

### 问题：找不到 requests 模块
**解决方案**：使用 `./run_updater.sh` 替代直接运行 Python 脚本

### 问题：显示相关错误
**解决方案**：脚本会自动设置 `DISPLAY=:0`

### 问题：虚拟环境问题
**解决方案**：脚本会自动检查并使用 `/home/orangepi/test1/bin/python`

## 📋 完整流程

1. **首次使用**：`./test_environment.sh` 检查环境
2. **测试运行**：`./run_updater.sh` 手动启动
3. **安装自启动**：`./install_autostart.sh` 配置开机启动
4. **重启测试**：重启系统验证自动启动

## 📝 服务管理

```bash
# 查看服务状态
systemctl --user status ai-voice-image.service

# 查看服务日志
journalctl --user -u ai-voice-image.service -f

# 重启服务
systemctl --user restart ai-voice-image.service

# 卸载自启动
./uninstall_autostart.sh
```

**就是这么简单！** 🎉
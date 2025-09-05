import os, configparser, getpass, logging, shutil

logger = logging.getLogger(__name__)


def find_usb_mounts(search_dir=None):
    mounts = []
    # 先扫常见目录
    try:
        for base in (search_dir or []):
            if os.path.isdir(base):
                for name in os.listdir(base):
                    path = os.path.join(base, name)
                    if os.path.isdir(path):
                        mounts.append(path)
    except Exception as e:
        logger.warning(f"扫描USB目录失败：{e}")

    # 兜底：解析 /proc/mounts
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    dev, mnt = parts[0], parts[1]
                    if dev.startswith("/dev/sd") or dev.startswith("/dev/usb"):
                        if os.path.ismount(mnt):
                            if mnt not in mounts:
                                mounts.append(mnt)
    except Exception as e:
        logger.warning("读取 /proc/mounts 失败: %s", e)

    uniq = []
    seen = set()
    for m in mounts:
        if m not in seen and os.path.isdir(m) and os.access(m, os.W_OK):
            seen.add(m)
            uniq.append(m)
    return uniq

def first_usb_mount(search_dir=None):
    mnts = find_usb_mounts(search_dir)
    return mnts[0] if mnts else None

def disable_usb_auto_open():
    """
    关闭 pcmanfm / pcmanfm-qt 自动打开U盘窗口（LXDE/LXQt 常见）
    """
    user = getpass.getuser()
    home = os.path.expanduser(f"~{user}")
    lxde_cfg = os.path.join(home, ".config/pcmanfm/LXDE/pcmanfm.conf")
    lxqt_cfg = os.path.join(home, ".config/pcmanfm-qt/lxqt/settings.conf")
    ok = False

    try:
        if os.path.exists(lxde_cfg):
            cp = configparser.ConfigParser()
            cp.read(lxde_cfg)
            if not cp.has_section("volume"):
                cp.add_section("volume")
            cp.set("volume", "mount_on_startup", "0")
            cp.set("volume", "mount_removable", "0")
            cp.set("volume", "autorun", "0")
            cp.set("volume", "autorun_open", "0")
            with open(lxde_cfg, "w") as f:
                cp.write(f)
            ok = True
            logger.info("已禁用 PCManFM(LXDE) 的U盘自动打开")
        elif os.path.exists(lxqt_cfg):
            cp = configparser.ConfigParser()
            cp.read(lxqt_cfg)
            if not cp.has_section("Mounting"):
                cp.add_section("Mounting")
            cp.set("Mounting", "AutoMount", "false")
            cp.set("Mounting", "AutoOpen", "false")
            with open(lxqt_cfg, "w") as f:
                cp.write(f)
            ok = True
            logger.info("已禁用 PCManFM-Qt(LXQt) 的U盘自动打开")
    except Exception as e:
        logger.warning(f"禁用自动打开失败: {e}")
    return ok

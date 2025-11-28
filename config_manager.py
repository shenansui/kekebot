# config_manager.py
import os
from botpy.ext.cog_yaml import read

_config = None


def init_config(config_path: str = None):
    """初始化全局配置"""
    global _config
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    _config = read(config_path)


def get_config():
    """获取全局配置"""
    if _config is None:
        raise RuntimeError("配置未初始化，请先调用 init_config()")
    return _config

# utils/log_utils.py
import os

def get_file_path(file):
    """获取文件的绝对路径（在项目根目录）"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)  # 上级目录
    return os.path.join(root_dir, f"{file}")

def read_last_n_lines(lines=10):
    log_file = get_file_path("botpy.log")
    if not os.path.exists(log_file):
        return "日志文件不存在"

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        if not all_lines:
            return "日志文件为空"
        actual_lines = min(lines, len(all_lines))
        return "".join(all_lines[-actual_lines:])
    except PermissionError:
        return "错误：没有读取权限"
    except UnicodeDecodeError:
        try:
            with open(log_file, "r", encoding="gbk") as f:
                all_lines = f.readlines()
            actual_lines = min(lines, len(all_lines))
            return "".join(all_lines[-actual_lines:])
        except Exception:
            return "错误：文件编码不支持"
    except Exception as e:
        return f"读取错误：{str(e)}"

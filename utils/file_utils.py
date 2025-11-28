# utils/file_utils.py
import os
import pandas as pd
from botpy.logging import get_logger

_log = get_logger()

MAX_MESSAGE_HISTORY = int(os.getenv("maxmessage", "100"))


def load_conversation_history(file_path: str):
    try:
        return pd.read_csv(file_path, encoding="utf-8")
    except FileNotFoundError:
        return None
    except pd.errors.EmptyDataError:
        return None


def save_conversation_history(messages_df, file_path: str):
    if len(messages_df.index) >= MAX_MESSAGE_HISTORY:
        messages_df = messages_df.iloc[-(MAX_MESSAGE_HISTORY - 2):].reset_index(drop=True)
    messages_df.to_csv(file_path, index=False, encoding="utf-8")


def delete_memory_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            _log.info(f"已删除记忆文件 {file_path}")
            return True
        else:
            _log.warning(f"记忆文件不存在: {file_path}")
            return False
    except PermissionError:
        _log.error(f"无法删除文件 {file_path}: 权限不足")
        return False

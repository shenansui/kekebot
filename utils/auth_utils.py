# utils/auth_utils.py
import pandas as pd
from botpy.logging import get_logger
from utils.log_utils import get_file_path
_log = get_logger()


def has_permission(user_id: str) -> bool:
    try:
        dffile = get_file_path("data/data.csv")
        df = pd.read_csv(dffile, encoding="gbk")
        _log.debug(df)
        return user_id in df["id"].values
    except Exception as e:
        _log.warning(f"权限验证失败: {e}")
        return False


def add_user_to_permissions(user_ids: list):
    dffile = get_file_path("data/data.csv")
    df = pd.read_csv(dffile, encoding="gbk")
    added_count = 0
    for uid in user_ids:
        if uid not in df["id"].values:
            df.loc[len(df)] = [str(len(df)), str(uid)]
            added_count += 1
    df.to_csv(dffile, index=False, encoding="gbk")
    return added_count


def remove_users_from_permissions(user_ids: list):
    dffile = get_file_path("data/data.csv")
    df = pd.read_csv(dffile, encoding="gbk")
    removed_count = 0
    for uid in user_ids:
        if uid in df["id"].values:
            df = df[df["id"] != uid]
            removed_count += 1
    df = df.reset_index(drop=True)
    df.to_csv(dffile, index=False, encoding="gbk")
    return removed_count

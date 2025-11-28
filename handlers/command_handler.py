# handlers/command_handler.py
from typing import List
import pandas as pd
from utils.file_utils import save_conversation_history
from botpy.api import BotAPI
from botpy.message import GroupMessage, C2CMessage,BaseMessage
from utils.auth_utils import has_permission, add_user_to_permissions, remove_users_from_permissions
from utils.file_utils import delete_memory_file
from utils.log_utils import read_last_n_lines,get_file_path
from tools import tools  # 导入自定义工具
import os
import requests
from botpy.logging import get_logger
from config_manager import get_config  # 新增导入
from handlers.ai_handler import personality
config = get_config()  # 获取配置
_log = get_logger()


async def handle_command(api: BotAPI, message: GroupMessage, params: List[str]):
    cmd = params[0]
    handler = commands_map.get(cmd)
    _log.debug(message.content)
    _log.debug(f"params:{params}")
    if handler:
        return await handler(api, message, params[1:])
    else:
        return "未知命令"


# 具体实现函数
async def check_permission(api: BotAPI, message: GroupMessage, params: List[str]):
    user_id = getattr(message.author, "member_openid", None) or message.author.user_openid
    if has_permission(user_id):
        return "有权限"
    else:
        return f"无权限({user_id})"


async def clear_memory(api: BotAPI, message: GroupMessage, params: List[str]):
    uid = getattr(message.author, "member_openid", None) or message.author.user_openid
    cid = getattr(message, "group_openid", None) or message.author.user_openid
    if not has_permission(uid):
        return "无权限"
    file_path = get_file_path(f"data/{cid}.csv")
    success = delete_memory_file(file_path)
    return "记忆清除成功" if success else "清除失败"


async def grant_permission(api: BotAPI, message: BaseMessage, params: List[str]):
    requester_id = getattr(message.author, "member_openid", None) or message.author.user_openid
    password = config["password"]
    if not has_permission(requester_id):
        if len(params) == 2 and params[1] == password:
            add_user_to_permissions(params[:-1])
            return "授权成功"
        return "无权限"
    count = add_user_to_permissions(params)
    return f"授权成功 ({count}人)"


async def revoke_permission(api: BotAPI, message: GroupMessage, params: List[str]):
    requester_id = getattr(message.author, "member_openid", None) or message.author.user_openid
    if not has_permission(requester_id):
        return "无权限"
    count = remove_users_from_permissions(params)
    return f"撤销成功 ({count}人)"


async def set_personality(api: BotAPI, message: GroupMessage, params: List[str]):
    global personality
    if len(params) < 1:
        return "缺失参数"
    elif len(params) == 1:
        personality_name = params[0]
        file_path = get_file_path(f"data/{personality_name}.csv")
        if not os.path.exists(file_path):
            return "该人格文件不存在"
        personality = personality_name
        return "人格切换成功"
    elif len(params) == 2:
        personality_name = params[0]
        file_path = get_file_path(f"data/{personality_name}.csv")
        if not os.path.exists(file_path):
            personalitycontent = pd.DataFrame([{"role": "system", "content": params[1]}])
            save_conversation_history(personalitycontent, file_path)
        personality = personality_name
        return "人格设置成功"
    else:
        return "参数过多"


async def show_logs(api: BotAPI, message: GroupMessage, params: List[str]):
    lines = int(params[0]) if params and params[0].isdigit() else 10
    return read_last_n_lines(lines)

async def show_balance(api: BotAPI, message: GroupMessage, params=None):
    url = "https://api.deepseek.com/user/balance"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {config["deepseekapi"]}'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 抛出HTTP错误
        data = response.json()
        
        if 'balance_infos' in data and data['balance_infos']:
            balance_info = data['balance_infos'][0]
            total_balance = balance_info['total_balance']
            currency = balance_info['currency']
            return f"总余额: {total_balance} {currency}"
        else:
            return "没有找到余额信息"
    except requests.exceptions.RequestException as e:
        _log.error(f"请求失败: {e}")
        return "请求失败，请稍后再试"
    except KeyError as e:
        _log.error(f"返回数据格式异常: {e}")
        return "返回数据格式异常"

commands_map = {
    "/你好": lambda api, msg, params: "你好呀",
    "/hello": lambda api, msg, params: "Hello!",
    "/help": lambda api, msg, params: "\n".join(commands_map.keys()),
    "/帮助": lambda api, msg, params: "\n".join(commands_map.keys()),
    "/权限检测": check_permission,
    "/清除记忆": clear_memory,
    "/授权": grant_permission,
    "/撤销权限": revoke_permission,
    "/人格设置": set_personality,
    "/日志": show_logs,
}

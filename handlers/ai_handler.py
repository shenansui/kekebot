# handlers/ai_handler.py
import pandas as pd
from openai import OpenAI
from botpy.api import BotAPI
from botpy.message import BaseMessage, GroupMessage, C2CMessage
from utils.file_utils import load_conversation_history, save_conversation_history
from utils.auth_utils import has_permission
from tools import tools
from botpy.logging import get_logger
import os
from config_manager import get_config
from utils.log_utils import get_file_path

config = get_config()  # 获取配置
_log = get_logger()
client = OpenAI(
    api_key=config["deepseekapi"],
    base_url="https://api.deepseek.com"
)

personality = config["personality"]


async def process_ai_response(api: BotAPI, message: BaseMessage):
    try:
        group_openid = message.group_openid if isinstance(message, GroupMessage) else message.author.user_openid
        user_openid = getattr(message.author, "member_openid", None) or message.author.user_openid
        history_file = get_file_path(f"data/{group_openid}.csv")
        _log.debug(personality)
        personalityfile = get_file_path(f"data/{personality}.csv")
        # 加载人格设定
        personality_df = pd.read_csv(personalityfile, encoding="utf-8")
        system_prompt = personality_df.to_dict('records')

        # 加载历史对话
        history_df = load_conversation_history(history_file)
        if history_df is None:
            history_df = pd.DataFrame(columns=["role", "content","name"])

        new_row = pd.DataFrame([{
            "role": "user",
            "content": message.content,
            "name": user_openid
        }])
        updated_history = pd.concat([history_df, new_row], ignore_index=True)

        full_messages = system_prompt + updated_history.to_dict('records')
        for msg in full_messages:
            if 'name' not in msg or pd.isna(msg['name']):  # 处理可能的 NaN
                msg['name'] = "assistant"
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            tools=tools,
            stream=False
        )

        while response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            full_messages.append(response.choices[0].message)

            tool_name = tool_call.function.name
            _log.log(tool_name)
            if tool_name == "dpqx":
                from handlers.command_handler import check_permission
                result = await check_permission(api, message, [])
            elif tool_name == "qcjy":
                from handlers.command_handler import clear_memory
                result = await clear_memory(api, message, [])
            elif tool_name == "readlog":
                from handlers.command_handler import show_logs
                result = await show_logs(api, message, ["10"])
            elif tool_name == "yue":
                from handlers.command_handler import show_balance
                result = await show_balance(api, message, [])
            else:
                result = "未知工具调用"
            _log.info(result)
            full_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=full_messages,
                tools=tools,
                stream=False
            )
            _log.debug(response.choices[0].message.content)
            _log.debug(response.choices[0].message.tool_calls)

        reply_content = response.choices[0].message.content
        assistant_reply = pd.DataFrame([{"role": "assistant", "content": reply_content,"name": "assistant"}])
        final_history = pd.concat([updated_history, assistant_reply], ignore_index=True)

        save_conversation_history(final_history, history_file)

        return reply_content or "空回复"

    except Exception as e:
        _log.exception(f"AI响应处理失败:{e}")
        return "抱歉，处理过程中出现错误"

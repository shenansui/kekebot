# main.py
import os
from config_manager import init_config, get_config
# 初始化配置
init_config(os.path.join(os.path.dirname(__file__), "config.yaml"))
import asyncio
import botpy
from botpy import logging
from handlers.command_handler import handle_command
from handlers.ai_handler import process_ai_response
from botpy.message import GroupMessage, C2CMessage



root = os.path.dirname(os.path.abspath(__file__))
config = get_config()  # 获取配置

_log = logging.get_logger()

# 创建全局消息队列
message_queue = asyncio.Queue(maxsize=100)  # 最大缓冲100条消息


class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"机器人「{self.robot.name}」上线!")
        # 启动后台消息处理器协程
        asyncio.create_task(self._process_message_queue())

    async def _process_message_queue(self):
        """后台协程，负责消费队列中的消息"""
        while True:
            try:
                task_type, api, message, parts = await message_queue.get()
                if task_type == "group":
                    await self._handle_group_message(api, message, parts)
                elif task_type == "direct":
                    await self._handle_direct_message(api, message)
                message_queue.task_done()
            except Exception as e:
                _log.exception("消息处理异常:", exc_info=e)

    async def _handle_group_message(self, api, message: GroupMessage, parts):
        first_word = parts[0]
        if first_word.startswith("/"):
            result = await handle_command(api, message, parts)
        else:
            result = await process_ai_response(api, message)
        await message.reply(content=f"{result}")

    async def _handle_direct_message(self, api, message: C2CMessage):
        result = await process_ai_response(api, message)
        await message.reply(content=f"{result}")

    async def on_group_at_message_create(self, message: GroupMessage):
        content = message.content.strip()
        parts = [part for part in content.split(" ") if part]
        if not parts:
            return
        # 将消息加入队列等待处理
        await message_queue.put(("group", self.api, message, parts))

    async def on_c2c_message_create(self, message: C2CMessage):
        # 将私聊消息也加入队列
        await message_queue.put(("direct", self.api, message, None))


if __name__ == "__main__":
    intents = botpy.Intents(public_messages=True, direct_message=True)
    client = MyClient(intents=intents)
    client.run(appid=config["appid"], secret=config["secret"])

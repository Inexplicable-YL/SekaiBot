# from typing import Any

import random
from typing import Any

from _randsent import generate_sentence
from _sound import get_character_name_list_text, parse_character_command

from sekaibot import Event, Node
from sekaibot.adapters.cqhttp.event import MessageEvent
from sekaibot.permission import SuperUser
from sekaibot.rule import Keywords


def a(event: Event):
    print(event.get_event_name())


@Keywords("/开", "/关", "/角色列表", "/角色", "蒸", "松泽", "松", "lrc", "超")
@SuperUser()
class AutoReply(Node[MessageEvent, dict, Any]):
    """Hello, World! 示例节点。"""

    priority = 1
    zb = Keywords.Param()

    async def handle(self):
        keyw = self.zb[0] if self.zb else "蒸"
        if "sound" not in self.node_state:
            self.node_state["sound"] = False
        if "character" not in self.node_state:
            self.node_state["character"] = "lucy-voice-guangdong-f1"

        if keyw == "/开":
            self.node_state["sound"] = True
            await self.reply("已开启语音回复")
        elif keyw == "/关":
            self.node_state["sound"] = False
            await self.reply("已关闭语音回复")
        elif keyw == "/角色列表":
            await self.reply(get_character_name_list_text())
        elif keyw == "/角色":
            if _id := parse_character_command(self.event.get_plain_text()):
                self.node_state["character"] = _id
                await self.reply(f"已成功切换角色：{_id}")
            else:
                await self.reply("切换失败，请检查")
        else:
            keyw = "林睿晨" if keyw == "lrc" else keyw
            text = random.choice(
                (
                    "{keyw}鞭好粗",
                    "{keyw}鞭好大",
                    "香草{keyw}",
                    "香茶{keyw}",
                    "{keyw}好可爱",
                    "{keyw}立了",
                    "香甜{keyw}",
                    "{keyw}草我",
                    "诶我草{keyw}怎么这么坏啊",
                    "被{keyw}茶了",
                    "{keyw}是四爱",
                    "{keyw}是4i",
                    "{keyw}是南通",
                    "{keyw}素指南",
                    "{keyw}就是爱慕",
                    "{keyw}是正太",
                    "{keyw}不见了",
                    "{keyw}蛇了",
                    "{keyw}北朝的初雪",
                    "{keyw}北朝的初水",
                    "{keyw}北朝的豪爽",
                    "香甜{keyw}的小学",
                    "北{keyw}顶到职场了",
                    "想吃{keyw}精",
                    "想吃{keyw}的大橘瓣",
                    "想电{keyw}的前列腺",
                    "{keyw}转过去一下我有急事",
                    "想吃{keyw}的高玩",
                    "{keyw}很带派",
                    "想吃{keyw}的大汗脚",
                    "被{keyw}口了",
                    "{keyw}是蓝凉",
                )
            ).format(keyw=keyw)
            if self.node_state:
                await self.call_api(
                    "send_group_ai_record",
                    character=self.node_state["character"],
                    group_id=596488203,
                    text=text,
                )
            else:
                await self.reply(text)


@Keywords("/唐")
@SuperUser()
class RandomSens(Node[MessageEvent, dict, Any]):
    priority = 0
    block = True

    async def handle(self):
        await self.reply(generate_sentence())


'''class HelloWorldNode1(Node):
    """Hello, World! 示例节点。"""

    scheduler = SchedulerArg()

    parent = "HelloWorldNode"
    priority = 5
    
    async def handle(self):
        def a(event):
            print("a", event)

        self.scheduler.add_job(a, trigger="interval", seconds=5, args=[self.event])

    async def rule(self):
        # result = await self.run(StartsWith._rule_check("Hello, World"))
        return True


class HelloWorldNode2(Node[Event | BEvent, str, dict]):
    """Hello, World! 示例节点。"""

    parent = "HelloWorldNode"
    priority = 2
    # B: _BNode = Depends()

    async def handle(self):
        pass
        # self.node_state = "HelloWorldNode2"
        # self.B.main()

    async def rule(self):
        return True


class HelloWorldNode1_1(Node):
    """Hello, World! 示例节点。"""

    parent = "HelloWorldNode1"
    priority = 5

    async def handle(self):
        return None

    async def rule(self):
        return True'''

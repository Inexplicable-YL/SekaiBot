from typing import (
    Union,
    Callable,
    Self
)
import re

from sekaibot.internal.event import Event
from sekaibot.typing import NodeT, RuleCheckerT, StateT
from sekaibot.dependencies import Dependency, Depends
from sekaibot.internal.rule import Rule, RuleChecker
from sekaibot.internal.rule.utils import (
    StartswithRule,
    EndswithRule,
    FullmatchRule,
    KeywordsRule,
    #CommandRule,
    #ShellCommandRule,
    RegexRule,
    ToMeRule,
)
from sekaibot.consts import (
    NODE_RULE_STATE,
    CMD_ARG_KEY,
    CMD_KEY,
    CMD_START_KEY,
    CMD_WHITESPACE_KEY,
    ENDSWITH_KEY,
    FULLMATCH_KEY,
    KEYWORD_KEY,
    PREFIX_KEY,
    RAW_CMD_KEY,
    REGEX_MATCHED,
    SHELL_ARGS,
    SHELL_ARGV,
    STARTSWITH_KEY,
)

__all__ = [
    "SetRule"
]

class StartsWith(RuleChecker):
    """匹配消息纯文本开头。

    参数:
        msg: 指定消息开头字符串元组
        ignorecase: 是否忽略大小写
    """
    def __init__(
        self,
        msg: Union[str, tuple[str,...]], ignorecase: bool = False
    ) -> None:
        if isinstance(msg, str):
            msg = (msg,)

        super().__init__(StartswithRule(msg, ignorecase)) 
    
    @classmethod
    def rule_param(cls, state: StateT) -> str:
        return state[NODE_RULE_STATE][STARTSWITH_KEY]

class EndsWith(RuleChecker):
    """匹配消息纯文本结尾。

    参数:
        msg: 指定消息开头字符串元组
        ignorecase: 是否忽略大小写
    """
    def __init__(
        self,
        msg: Union[str, tuple[str, ...]], ignorecase: bool = False
    ) -> None:
        if isinstance(msg, str):
            msg = (msg,)

        super().__init__(EndswithRule(msg, ignorecase)) 
    
    @classmethod
    def rule_param(cls, state: StateT) -> str:
        return state[NODE_RULE_STATE][ENDSWITH_KEY]

class FullMatch(RuleChecker):
    """完全匹配消息。

    参数:
        msg: 指定消息全匹配字符串元组
        ignorecase: 是否忽略大小写
    """
    def __init__(
        self,
        msg: Union[str, tuple[str, ...]], ignorecase: bool = False
    ) -> None:
        if isinstance(msg, str):
            msg = (msg,)
        
        super().__init__(FullmatchRule(msg, ignorecase)) 

    @classmethod
    def rule_param(cls, state: StateT) -> str:
        return state[NODE_RULE_STATE][FULLMATCH_KEY]

class Keyword(RuleChecker):
    """匹配消息纯文本关键词。

    参数:
        keywords: 指定关键字元组
    """
    def __init__(
        self,
        *keywords: str
    ) -> None:
        super().__init__(KeywordsRule(*keywords))

    @classmethod
    def rule_param(cls, state: StateT) -> tuple[str,...]:
        return state[NODE_RULE_STATE][KEYWORD_KEY]

class Regex(RuleChecker):
    """匹配符合正则表达式的消息字符串。

    可以通过 {ref}`nonebot.params.RegexStr` 获取匹配成功的字符串，
    通过 {ref}`nonebot.params.RegexGroup` 获取匹配成功的 group 元组，
    通过 {ref}`nonebot.params.RegexDict` 获取匹配成功的 group 字典。

    参数:
        regex: 正则表达式
        flags: 正则表达式标记

    :::tip 提示
    正则表达式匹配使用 search 而非 match，如需从头匹配请使用 `r"^xxx"` 来确保匹配开头
    :::

    :::tip 提示
    正则表达式匹配使用 `EventMessage` 的 `str` 字符串，
    而非 `EventMessage` 的 `PlainText` 纯文本字符串
    :::
    """
    def __init__(
        self,
        regex: str, flags: Union[int, re.RegexFlag] = 0
    ) -> Rule:
        super().__init__(RegexRule(regex, flags))

    @classmethod
    def rule_param(cls, state: StateT) -> re.Match[str]:
        return state[NODE_RULE_STATE][REGEX_MATCHED]

class ToMe(RuleChecker):
    """匹配与机器人有关的事件。"""
    def __init__(self) -> None:
        super().__init__(ToMeRule())

    @classmethod
    def rule_param(cls, event: Event) -> bool:
        return event.is_tome()
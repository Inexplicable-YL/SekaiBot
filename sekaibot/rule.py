import re
from typing import Any, Generic, override  # noqa: UP035

from sekaibot.consts import (
    CMD_ARG_KEY,
    CMD_KEY,
    CMD_START_KEY,
    CMD_WHITESPACE_KEY,
    COUNTER_KEY,
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
from sekaibot.dependencies import Dependency, Depends
from sekaibot.internal.event import Event
from sekaibot.internal.message import Message, MessageSegment
from sekaibot.internal.rule import ArgsT, Rule, RuleChecker
from sekaibot.internal.rule.utils import (  # CommandRule,; ShellCommandRule,
    ArgumentParser,
    CommandRule,
    CountTriggerRule,
    EndswithRule,
    FullmatchRule,
    KeywordsRule,
    RegexRule,
    ShellCommandRule,
    StartswithRule,
    ToMeRule,
)
from sekaibot.typing import StateT

__all__ = [
    "StartsWith",
    "EndsWith",
    "FullMatch",
    "Keywords",
    "Command",
    "ShellCommand",
    "Regex",
    "ToMe",
]


class StartsWith(RuleChecker[tuple[tuple[str | MessageSegment, ...], bool]]):
    """匹配消息富文本开头。

    Args:
        msgs: 指定消息开头字符串或 MessageSegment 元组
        ignorecase: 是否忽略大小写
    """

    def __init__(self, *msgs: str | MessageSegment, ignorecase: bool = False) -> None:
        super().__init__(StartswithRule(msgs, ignorecase=ignorecase))

    @override
    @classmethod
    def Checker(cls, *msgs: str | MessageSegment, ignorecase: bool = False):
        return super().Checker(msgs, ignorecase=ignorecase)

    @staticmethod
    def _param(state: StateT):
        return state[STARTSWITH_KEY]

    @classmethod
    def Param(cls) -> str | MessageSegment:
        """在依赖注入里获取检查器的数据。"""
        return Depends(cls._param, use_cache=False)


class EndsWith(RuleChecker[tuple[tuple[str | MessageSegment, ...], bool]]):
    """匹配消息富文本结尾。

    Args:
        msgs: 指定消息结尾字符串或 MessageSegment 元组
        ignorecase: 是否忽略大小写
    """

    def __init__(self, *msgs: str | MessageSegment, ignorecase: bool = False) -> None:
        super().__init__(EndswithRule(msgs, ignorecase=ignorecase))

    @override
    @classmethod
    def Checker(cls, *msgs: str | MessageSegment, ignorecase: bool = False):
        return super().Checker(msgs, ignorecase=ignorecase)

    @staticmethod
    def _param(state: StateT):
        return state[ENDSWITH_KEY]

    @classmethod
    def Param(cls) -> str | MessageSegment:
        """在依赖注入里获取检查器的数据。"""
        return Depends(cls._param, use_cache=False)


class FullMatch(RuleChecker[tuple[tuple[str | Message | MessageSegment, ...], bool]]):
    """完全匹配消息。

    Args:
        msg: 指定消息全匹配字符串或 Message 或 MessageSegment 元组
        ignorecase: 是否忽略大小写
    """

    def __init__(self, *msg: str | Message | MessageSegment, ignorecase: bool = False) -> None:
        super().__init__(FullmatchRule(msg, ignorecase=ignorecase))

    @override
    @classmethod
    def Checker(cls, *msgs: str | Message | MessageSegment, ignorecase: bool = False):
        return super().Checker(msgs, ignorecase=ignorecase)

    @staticmethod
    def _param(state: StateT):
        return state[FULLMATCH_KEY]

    @classmethod
    def Param(cls) -> str | Message:
        """在依赖注入里获取检查器的数据。"""
        return Depends(cls._param, use_cache=False)


class Keywords(RuleChecker[tuple[tuple[str | MessageSegment, ...], bool]]):
    """匹配消息富文本关键词。

    Args:
        keywords: 指定关键字元组
    """

    def __init__(self, *keywords: str | MessageSegment, ignorecase: bool = False) -> None:
        super().__init__(KeywordsRule(keywords, ignorecase=ignorecase))

    @override
    @classmethod
    def Checker(cls, *keywords: str | MessageSegment, ignorecase: bool = False):
        return super().Checker(keywords, ignorecase=ignorecase)

    @staticmethod
    def _param(state: StateT):
        return state[KEYWORD_KEY]

    @classmethod
    def Param(cls) -> tuple[str | MessageSegment, ...]:
        """在依赖注入里获取检查器的数据。"""
        return Depends(cls._param, use_cache=False)


class Regex(RuleChecker[tuple[str, re.RegexFlag]]):
    """匹配符合正则表达式的消息字符串。

    可以通过 {ref}`sekaibot.rule.RegexStr` 获取匹配成功的字符串，
    通过 {ref}`sekaibot.rule.RegexGroup` 获取匹配成功的 group 元组，
    通过 {ref}`sekaibot.rule.RegexDict` 获取匹配成功的 group 字典。

    Args:
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

    def __init__(self, regex: str, flags: int | re.RegexFlag = 0) -> Rule:
        super().__init__(RegexRule(regex, flags))

    @override
    @classmethod
    def Checker(cls, regex: str, flags: int | re.RegexFlag = 0):
        return super().Checker(regex, flags)

    @staticmethod
    def _param(state: StateT) -> re.Match[str]:
        return state[REGEX_MATCHED]

    @classmethod
    def Param(cls) -> re.Match[str]:
        """在依赖注入里获取检查器的数据。"""
        return Depends(cls._param, use_cache=False)


class CountTrigger(RuleChecker[tuple[str, Dependency[bool], int, int, int, int]]):
    """计数器规则。

    Args:
        name: 计数器名称
        times: 计数器次数
    """

    def __init__(
        self,
        name: str,
        func: Dependency[bool] | None = None,
        min_trigger: int = 10,
        time_window: int = 60,
        count_window: int = 30,
        max_size: int | None = 100,
    ) -> Rule:
        super().__init__(
            CountTriggerRule(name, func, min_trigger, time_window, count_window, max_size)
        )

    @override
    @classmethod
    def Checker(
        cls,
        name: str,
        func: Dependency[bool] | None = None,
        min_trigger: int = 10,
        time_window: int = 60,
        count_window: int = 30,
        max_size: int | None = 100,
    ):
        return super().Checker(name, name, func, min_trigger, time_window, count_window, max_size)

    @staticmethod
    def _param(state: StateT) -> dict:
        return state[COUNTER_KEY]

    @classmethod
    def Param(cls) -> dict:
        """在依赖注入里获取检查器的数据。"""
        return Depends(cls._param, use_cache=False)


class _CommandChecker(RuleChecker[ArgsT], Generic[ArgsT]):
    """匹配消息纯文本命令。

    Args:
        msg: 指定命令字符串元组
        ignorecase: 是否忽略大小写
    """

    @staticmethod
    def _command(state: StateT) -> Message:
        return state[PREFIX_KEY][CMD_KEY]

    @classmethod
    def Command(cls) -> tuple[str, ...]:
        """消息命令元组"""
        return Depends(cls._command, use_cache=False)

    @staticmethod
    def _raw_command(state: StateT) -> Message:
        return state[PREFIX_KEY][RAW_CMD_KEY]

    @classmethod
    def RawCommand(cls) -> str:
        """消息命令文本"""
        return Depends(cls._raw_command, use_cache=False)

    @staticmethod
    def _command_arg(state: StateT) -> Message:
        return state[PREFIX_KEY][CMD_ARG_KEY]

    @classmethod
    def CommandArg(cls) -> Any:
        """消息命令参数"""
        return Depends(cls._command_arg, use_cache=False)

    @staticmethod
    def _command_start(state: StateT) -> str:
        return state[PREFIX_KEY][CMD_START_KEY]

    @classmethod
    def CommandStart(cls) -> str:
        """消息命令开头"""
        return Depends(cls._command_start, use_cache=False)

    @staticmethod
    def _command_whitespace(state: StateT) -> str:
        return state[PREFIX_KEY][CMD_WHITESPACE_KEY]

    @classmethod
    def CommandWhitespace(cls) -> str:
        """消息命令与参数之间的空白"""
        return Depends(cls._command_whitespace, use_cache=False)


class Command(_CommandChecker[tuple[tuple[str, ...], str | bool | None]]):
    """匹配消息命令。

    Config:
    - `{ref}sekaibot.config.MainConfig.rule.command_start`
    - `{ref}sekaibot.config.MainConfig.rule.command_sep`

    Depends:
    - `{ref}sekaibot.rule.Command.Command`：获取匹配成功的命令元组（如：`("test",)`）
    - `{ref}sekaibot.rule.Command.RawCommand`：获取原始命令文本（如：`"/test"`）
    - `{ref}sekaibot.rule.Command.CommandArg`：获取匹配成功的命令参数字符串

    Args:
        cmds (str | tuple[str, ...]): 命令文本或命令元组。
        force_whitespace (bool): 是否强制命令后必须有空白符（如空格、换行等）。

    Examples:
        使用默认配置 `command_start`, `command_sep` 时：

        - 命令 `("test",)` 可以匹配以 `/test` 开头的消息
        - 命令 `("test", "sub")` 可以匹配以 `/test.sub` 开头的消息

    Tip:
        命令内容与后续消息之间**无需空格**！
    """

    def __init__(self, *cmds: tuple[str, ...], force_whitespace: str | bool | None = None) -> None:
        super().__init__(CommandRule(*cmds, force_whitespace=force_whitespace))

    @override
    @classmethod
    def Checker(cls, *cmds: tuple[str, ...], force_whitespace: str | bool | None = None):
        return super().Checker(*cmds, force_whitespace=force_whitespace)


class ShellCommand(_CommandChecker[tuple[tuple[str, ...], ArgumentParser | None]]):
    """匹配 `shell_like` 形式的消息命令。

    Config:
    - `{ref}sekaibot.config.MainConfig.rule.command_start`
    - `{ref}sekaibot.config.MainConfig.rule.command_sep`

    Depends:
    - `{ref}sekaibot.rule.ShellCommand.Command`：匹配成功的命令元组（例如：`("test",)`）
    - `{ref}sekaibot.rule.ShellCommand.RawCommand`：原始命令文本（例如：`"/test"`）
    - `{ref}sekaibot.rule.ShellCommand.ShellCommandArgv`：解析前的参数列表（例如：`["arg", "-h"]`）
    - `{ref}sekaibot.rule.ShellCommand.ShellCommandArgs`：解析后的参数字典（例如：`{"arg": "arg", "h": True}`）

    Warnings:
        如果参数解析失败，通过 `{ref}sekaibot.rule.ShellCommandArgs` 获取的将是
        `{ref}sekaibot.exceptions.ParserExit` 异常对象。

    Tips:
        命令内容与后续消息之间无需空格！

    Args:
        cmds (str | tuple[str, ...]): 命令文本或命令元组。
        parser (ArgumentParser | None): 可选的 `{ref}sekaibot.rule.ArgumentParser` 对象。

    Examples:
        使用默认的 `command_start` 和 `command_sep` 配置：

        ```python
        from sekaibot.rule import ArgumentParser

        parser = ArgumentParser()
        parser.add_argument("-a", action="store_true")

        rule = shell_command("ls", parser=parser)
        ```
    """

    def __init__(self, *cmds: tuple[str, ...], parser: ArgumentParser | None = None) -> None:
        super().__init__(ShellCommandRule(*cmds, parser=parser))

    @override
    @classmethod
    def Checker(cls, *cmds: tuple[str, ...], parser: ArgumentParser | None = None):
        return super().Checker(*cmds, parser=parser)

    @staticmethod
    def _shell_command_args(state: StateT) -> Any:
        return state[SHELL_ARGS]  # Namespace or ParserExit

    @classmethod
    def ShellCommandArgs(cls) -> Any:
        """shell 命令解析后的参数字典"""
        return Depends(cls._shell_command_args, use_cache=False)

    @staticmethod
    def _shell_command_argv(state: StateT) -> list[str | MessageSegment]:
        return state[SHELL_ARGV]

    @classmethod
    def ShellCommandArgv(cls) -> Any:
        """shell 命令原始参数列表"""
        return Depends(cls._shell_command_argv, use_cache=False)


class ToMe(RuleChecker[Any]):
    """匹配与机器人有关的事件。"""

    def __init__(self) -> None:
        super().__init__(ToMeRule())

    @override
    @classmethod
    def Checker(cls):
        return super().Checker()

    @staticmethod
    def _param(event: Event) -> bool:
        return event.is_tome()

    @classmethod
    def Param(cls) -> dict:
        """在依赖注入里获取检查器的数据。"""
        return Depends(cls._param, use_cache=False)

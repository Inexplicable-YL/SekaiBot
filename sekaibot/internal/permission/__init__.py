from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, NoReturn, Optional, Union, Dict, Any, Self

import anyio
from exceptiongroup import BaseExceptionGroup, catch

from sekaibot.dependencies import Dependency, InnerDepends, Depends, solve_dependencies_in_bot
from sekaibot.exceptions import SkipException
from sekaibot.internal.event import Event
from sekaibot.typing import PermissionCheckerT, StateT

if TYPE_CHECKING:
    from sekaibot.bot import Bot


class Permission:
    """{ref}`nonebot.matcher.Matcher` 权限类。

    当事件传递时，在 {ref}`nonebot.matcher.Matcher` 运行前进行检查。

    参数:
        checkers: PermissionChecker

    用法:
        ```python
        Permission(async_function) | sync_function
        # 等价于
        Permission(async_function, sync_function)
        ```
    """

    __slots__ = ("checkers",)

    def __init__(self, *checkers: Union[PermissionCheckerT, Dependency[bool]]) -> None:
        self.checkers: set[Dependency[bool]] = {
            checker for checker in checkers
        }
        """存储 `PermissionChecker`"""

    def __repr__(self) -> str:
        return f"Permission({', '.join(repr(checker) for checker in self.checkers)})"
    
    async def __call__(
        self,
        bot: "Bot",
        event: Event,
        stack: Optional[AsyncExitStack] = None,
        dependency_cache: Optional[dict[Dependency[Any], Any]] = None,
    ) -> bool:
        """检查是否满足某个权限。

        参数:
            bot: Bot 对象
            event: Event 对象
            stack: 异步上下文栈
            dependency_cache: 依赖缓存
        """
        if not self.checkers:
            return True

        result = False

        def _handle_skipped_exception(
            exc_group: BaseExceptionGroup[SkipException],
        ) -> None:
            nonlocal result
            result = False

        async def _run_checker(checker: Dependency[bool]) -> None:
            nonlocal result
            is_passed = await solve_dependencies_in_bot(
                checker,
                bot=bot,
                event=event,
                use_cache=False,
                stack=stack,
                dependency_cache=dependency_cache,
            )
            if is_passed:
                result = True
                tg.cancel_scope.cancel()

        with catch({SkipException: _handle_skipped_exception}):
            async with anyio.create_task_group() as tg:
                for checker in self.checkers:
                    tg.start_soon(_run_checker, checker)

        return result

    def __and__(self, other: object) -> NoReturn:
        raise RuntimeError("And operation between Permissions is not allowed.")

    def __or__(
        self, other: Optional[Union[Self, PermissionCheckerT]]
    ) -> Self:
        if other is None:
            return self
        elif isinstance(other, Permission):
            return Permission(*self.checkers, *other.checkers)
        else:
            return Permission(*self.checkers, other)

    def __ror__(
        self, other: Optional[Union[Self, PermissionCheckerT]]
    ) -> Self:
        if other is None:
            return self
        elif isinstance(other, Permission):
            return Permission(*other.checkers, *self.checkers)
        else:
            return Permission(other, *self.checkers)
        
    def __add__(self, other: Union[Self, PermissionCheckerT]) -> Self:
        if other is None:
            return self
        elif isinstance(other, Permission):
            return Permission(*self.checkers, *other.checkers)
        else:
            return Permission(other, *self.checkers)
        
    def __iadd__(self, other: Union[Self, PermissionCheckerT]) -> Self:
        return self.__add__(other)
    
    def __sub__(self, other: Union[Self, PermissionCheckerT]) -> NoReturn:
        raise RuntimeError("Subtraction operation between permissions is not allowed.")


class User:
    """检查当前事件是否属于指定会话。

    参数:
        users: 会话 ID 元组
        perm: 需同时满足的权限
    """

    __slots__ = ("perm", "users")

    def __init__(
        self, users: tuple[str, ...], perm: Optional[Permission] = None
    ) -> None:
        self.users = users
        self.perm = perm

    def __repr__(self) -> str:
        return (
            f"User(users={self.users}"
            + (f", permission={self.perm})" if self.perm else "")
            + ")"
        )

    async def __call__(self, bot: Bot, event: Event) -> bool:
        try:
            session = event.session_id
        except Exception:
            return False
        return bool(
            session in self.users and (self.perm is None or await self.perm(bot, event))
        )

    @classmethod
    def _clean_permission(cls, perm: Permission) -> Optional[Permission]:
        if len(perm.checkers) == 1 and isinstance(
            user_perm := next(iter(perm.checkers)).call, cls
        ):
            return user_perm.perm
        return perm

    @classmethod
    def from_event(cls, event: Event, perm: Optional[Permission] = None) -> Self:
        """从事件中获取会话 ID。

        如果 `perm` 中仅有 `User` 类型的权限检查函数，则会去除原有的会话 ID 限制。

        参数:
            event: Event 对象
            perm: 需同时满足的权限
        """
        return cls((event.session_id,), perm=perm and cls._clean_permission(perm))

    @classmethod
    def from_permission(cls, *users: str, perm: Optional[Permission] = None) -> Self:
        """指定会话与权限。

        如果 `perm` 中仅有 `User` 类型的权限检查函数，则会去除原有的会话 ID 限制。

        参数:
            users: 会话白名单
            perm: 需同时满足的权限
        """
        return cls(users, perm=perm and cls._clean_permission(perm))


def USER(*users: str, perm: Optional[Permission] = None):
    """匹配当前事件属于指定会话。

    如果 `perm` 中仅有 `User` 类型的权限检查函数，则会去除原有检查函数的会话 ID 限制。

    参数:
        user: 会话白名单
        perm: 需要同时满足的权限
    """

    return Permission(User.from_permission(*users, perm=perm))
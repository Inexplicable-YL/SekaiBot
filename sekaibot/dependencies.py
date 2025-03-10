"""SekaiBot 依赖注入。

实现依赖注入相关功能。
"""

import inspect
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    AsyncGenerator,
    Callable,
    Awaitable,
    ContextManager,
    Dict,
    Generator,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints
)

from sekaibot.utils import get_annotations, sync_ctx_manager_wrapper
from sekaibot.event import Event
from sekaibot.typing import ConfigT, EventT, StateT
if TYPE_CHECKING:
    from sekaibot.bot import Bot

_T = TypeVar("_T")
Dependency = Union[
    # Class-based dependencies
    Type[Union[_T, AsyncContextManager[_T], ContextManager[_T]]],
    # Generator-based dependencies
    Callable[[], AsyncGenerator[_T, None]],
    Callable[[], Generator[_T, None, None]],
    # Function-based dependencies (带参数)
    Callable[..., _T],
    Callable[..., Awaitable[_T]],
]


__all__ = ["Depends"]


class InnerDepends:
    """子依赖的内部实现。

    用户无需关注此内部实现。

    Attributes:
        dependency: 依赖类。如果不指定则根据字段的类型注释自动判断。
        use_cache: 是否使用缓存。默认为 `True`。
    """

    dependency: Optional[Dependency[Any]]
    use_cache: bool

    def __init__(
        self, dependency: Optional[Dependency[Any]] = None, *, use_cache: bool = True
    ) -> None:
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        attr = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        cache = "" if self.use_cache else ", use_cache=False"
        return f"InnerDepends({attr}{cache})"


def Depends(  # noqa: N802 # pylint: disable=invalid-name
    dependency: Optional[Dependency[_T]] = None, *, use_cache: bool = True
) -> _T:
    """子依赖装饰器。

    Args:
        dependency: 依赖类。如果不指定则根据字段的类型注释自动判断。
        use_cache: 是否使用缓存。默认为 `True`。

    Returns:
        返回内部子依赖对象。
    """
    return InnerDepends(dependency=dependency, use_cache=use_cache)  # type: ignore

async def solve_dependencies(
    dependent: Dependency[_T],
    *,
    use_cache: bool,
    stack: AsyncExitStack,
    dependency_cache: Dict[Dependency[Any], Any],
) -> _T:
    """解析子依赖。

    Args:
        dependent: 依赖类。
        use_cache: 是否使用缓存。
        stack: `AsyncExitStack` 对象。
        dependency_cache: 依赖缓存。

    Raises:
        TypeError: 解析错误。

    Returns:
        解析完成子依赖的对象。
    """
    if use_cache and dependent in dependency_cache:
        return dependency_cache[dependent]

    if isinstance(dependent, type):
        # type of dependent is Type[T]
        values: Dict[str, Any] = {}
        ann = get_annotations(dependent)
        for name, sub_dependent in inspect.getmembers(
            dependent, lambda x: isinstance(x, InnerDepends)
        ):
            assert isinstance(sub_dependent, InnerDepends)
            if sub_dependent.dependency is None:
                dependent_ann = ann.get(name)
                if dependent_ann is None:
                    raise TypeError("can not solve dependent")
                sub_dependent.dependency = dependent_ann
            values[name] = await solve_dependencies(
                sub_dependent.dependency,
                use_cache=sub_dependent.use_cache,
                stack=stack,
                dependency_cache=dependency_cache,
            )
        depend_obj = cast(
            Union[_T, AsyncContextManager[_T], ContextManager[_T]],
            dependent.__new__(dependent),  # pyright: ignore
        )
        for key, value in values.items():
            setattr(depend_obj, key, value)
        depend_obj.__init__()  # type: ignore[misc] # pylint: disable=unnecessary-dunder-call

        if isinstance(depend_obj, AsyncContextManager):
            depend = await stack.enter_async_context(depend_obj)  # pyright: ignore
        elif isinstance(depend_obj, ContextManager):
            depend = await stack.enter_async_context(  # pyright: ignore
                sync_ctx_manager_wrapper(depend_obj)
            )
        else:
            depend = depend_obj
    elif inspect.iscoroutinefunction(dependent) or inspect.isfunction(dependent):
        # type of dependent is Callable[..., T] | Callable[..., Awaitable[T]]
        func_params = inspect.signature(dependent).parameters
        func_args = {}
        for param_name, param in func_params.items():
            param_type = get_type_hints(dependent).get(param_name)
            if isinstance(param.default, InnerDepends):
                func_args[param_name] = await solve_dependencies(
                    param.default.dependency, 
                    use_cache=param.default.use_cache,
                    stack=stack, 
                    dependency_cache=dependency_cache
                )
            elif param.default is not inspect.Parameter.empty:
                func_args[param_name] = param.default
            elif param_type in dependency_cache:
                func_args[param_name] = dependency_cache[param_type]
            else:
                raise TypeError(f"Cannot resolve parameter '{param_name}' for dependency '{dependent.__name__}'")
        if inspect.iscoroutinefunction(dependent):
            depend = await dependent(**func_args)
        else:
            depend = dependent(**func_args)
    elif inspect.isasyncgenfunction(dependent):
        # type of dependent is Callable[[], AsyncGenerator[T, None]]
        cm = asynccontextmanager(dependent)()
        depend = cast(_T, await stack.enter_async_context(cm))
    elif inspect.isgeneratorfunction(dependent):
        # type of dependent is Callable[[], Generator[T, None, None]]
        cm = sync_ctx_manager_wrapper(contextmanager(dependent)())
        depend = cast(_T, await stack.enter_async_context(cm))
    else:
        raise TypeError("dependent is not a class or generator function")

    dependency_cache[dependent] = depend
    return depend  # pyright: ignore

async def solve_dependencies_in_bot(
    dependent: Dependency[_T],
    *,
    bot: "Bot",
    event: Event,
    state: StateT,
    use_cache: bool = True,
    stack: AsyncExitStack = AsyncExitStack(),
    dependency_cache: Dict[Dependency[Any], Any] = {},
) -> _T:
    """解析子依赖。
        使用此方法强制需要bot、event、state作为参数，更加严谨。
    """
    from sekaibot.bot import Bot
    dependency_cache |= {
        Bot: bot,
        Event: event,
        StateT: state,
    }
    return await solve_dependencies(dependent, use_cache=use_cache, stack=stack, dependency_cache=dependency_cache)

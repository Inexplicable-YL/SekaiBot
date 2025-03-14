import asyncio
import time
from contextlib import AsyncExitStack
from collections import defaultdict
import anyio
from anyio.abc import TaskStatus
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    overload,
)

from sekaibot.exceptions import (
    GetEventTimeout,
    StopException,
    SkipException,
    PruningException,
    JumpToException,
)
from sekaibot.log import logger
from sekaibot.consts import NODE_STATE
from sekaibot.typing import EventT, StateT
from sekaibot.node import Node
from sekaibot.utils import wrap_get_func, cancel_on_exit
from sekaibot.dependencies import solve_dependencies_in_bot, Dependency
from sekaibot.internal.event import Event, EventHandleOption

if TYPE_CHECKING:
    from sekaibot.bot import Bot

class NodeManager():
    bot: "Bot"

    node_state: Dict[str, Dict[str, Any]]
    global_state: dict

    _condition: anyio.Condition
    _cancel_event: anyio.Event
    _current_event: Event | None

    _event_send_stream: MemoryObjectSendStream[EventHandleOption]  # pyright: ignore[reportUninitializedInstanceVariable]
    _event_receive_stream: MemoryObjectReceiveStream[EventHandleOption]  # pyright: ignore[reportUninitializedInstanceVariable]

    def __init__(self, bot: "Bot"):
        self.bot = bot
        self.node_state = defaultdict(lambda: defaultdict(lambda: None))
        self.global_state = {}

    async def startup(self) -> None:
        self._condition = anyio.Condition()
        self._cancel_event = anyio.Event()
        self._event_send_stream, self._event_receive_stream = (
            anyio.create_memory_object_stream(
                max_buffer_size=self.bot.config.bot.event_queue_size
            )
        )

    async def run(self) -> None:
        async with anyio.create_task_group() as tg:
            tg.start_soon(self._handle_event_receive)
            tg.start_soon(cancel_on_exit, self._cancel_event, tg)


    async def handle_event(
        self,
        current_event: Event[Any],
        *,
        handle_get: bool = True,
        show_log: bool = True,
    ) -> None:
        """被适配器对象调用，根据优先级分发事件给所有插件，并处理插件的 `stop` 、 `skip` 等信号。

        此方法不应该被用户手动调用。

        Args:
            current_event: 当前待处理的 `Event`。
            handle_get: 当前事件是否可以被 get 方法捕获，默认为 `True`。
            show_log: 是否在日志中显示，默认为 `True`。
        """
        if show_log:
            logger.info(
                "Event received from adapter",
                current_event=current_event,
            )

        await self._event_send_stream.send(
            EventHandleOption(
                event=current_event,
                handle_get=handle_get,
            )
        )

    async def _handle_event_receive(self) -> None:
        async with anyio.create_task_group() as tg, self._event_receive_stream:
            async for current_event, handle_get in self._event_receive_stream:
                if handle_get:
                    await tg.start(self._handle_event_wait_condition)
                    async with self._condition:
                        self._current_event = current_event
                        self._condition.notify_all()
                else:
                    tg.start_soon(self._handle_event, current_event)

    async def _handle_event_wait_condition(
        self, *, task_status: TaskStatus[None] = anyio.TASK_STATUS_IGNORED
    ) -> None:
        async with self._condition:
            task_status.started()
            await self._condition.wait()
            assert self._current_event is not None
            current_event = self._current_event
        await self._handle_event(current_event)

    async def _check_node(
        self,
        node: type[Node],
        event: Event,
        state: StateT,
        stack: Optional[AsyncExitStack] = None,
        dependency_cache: Optional[Dependency] = None,
    ) -> bool:
        """检查事件响应器是否符合运行条件。

        请注意，过时的事件响应器将被**销毁**。对于未过时的事件响应器，将会一次检查其响应类型、权限和规则。

        参数:
            Matcher: 要检查的事件响应器
            bot: Bot 对象
            event: Event 对象
            state: 会话状态
            stack: 异步上下文栈
            dependency_cache: 依赖缓存

        返回:
            bool: 是否符合运行条件
        """
        '''if node.expire_time and datetime.now() > node.expire_time:
            with contextlib.suppress(Exception):
                node.destroy()
            return False'''

        try:
            if not await node.check_perm(self.bot, event, stack, dependency_cache):
                logger.info(f"permission conditions not met", node=node.__name__)
                return False
        except Exception as e:
            logger.error(
                f"permission check failed", node=node.__name__
            )
            return False

        try:
            if not await node.check_rule(self.bot, event, state, stack, dependency_cache):
                logger.info(f"rule conditions not met", node=node.__name__)
                return False
        except Exception as e:
            logger.error(
                f"rule check failed", node=node.__name__
            )
            return False

        return True

    async def _handle_event(self, current_event: Event[Any]) -> None:
        if current_event.__handled__:
            return

        for _hook_func in self.bot._event_preprocessor_hooks:
            await _hook_func(current_event)

        _nodes_list = self.bot.nodes_list
        #event_state = None
        index = 0
        while index < len(_nodes_list):
            node_class, pruning_node = _nodes_list[index]
            logger.debug("Checking for matching nodes", priority=node_class)
            try:
                # 事件类型与节点要求的类型不匹配，剪枝
                if not await self._check_node(
                    node_class,
                    current_event,
                    self.node_state[node_class.__name__],
                ):
                    raise PruningException
                async with AsyncExitStack() as stack:
                    _dependency_cache = {}
                    _node = await solve_dependencies_in_bot(
                        node_class,
                        bot=self.bot,
                        event=current_event,
                        state=self.node_state[node_class.__name__][NODE_STATE],
                        use_cache=True,
                        stack=stack,
                        dependency_cache=_dependency_cache,
                    )
                    #_node.state = event_state

                    if _node.name not in self.node_state:
                        node_state = _node.__init_state__()
                        if node_state is not None:
                            self.node_state[_node.name][NODE_STATE] = node_state
                    if await _node.rule():
                        logger.info("Event will be handled by node", node=_node)
                        try:
                            await _node.handle()
                        finally:
                            #event_state = _node.state if _node.state is not None else event_state
                            if _node.block:
                                break
            except SkipException:
                # 插件要求跳过自身继续当前事件传播或跳转事件
                next_index = index + 1
            except StopException:
                # 插件要求停止当前事件传播
                break
            except PruningException:
                # 插件要求剪枝
                next_index = pruning_node if pruning_node != -1 else None
            except JumpToException as jump_to_node:
                # 插件要求跳转事件
                jump_to_index = {s.__name__: i for i, (s, _) in enumerate(_nodes_list)}.get(jump_to_node.node, None)
                if jump_to_index is not None:
                    if jump_to_index > index:
                        next_index = jump_to_index
                    else:
                        logger.warning("The node to jump to is before the current node", node=_nodes_list[jump_to_index])
                        next_index = index + 1
                else:
                    logger.warning("The node to jump to does not exist", node_name=jump_to_node.node)
                    next_index = index + 1
            except Exception:
                logger.exception("Exception in node", node=node_class)
                next_index = index + 1
            else:
                next_index = index + 1

            if next_index is not None:
                index = next_index
            else:
                break
                
        for _hook_func in self.bot._event_postprocessor_hooks:
            await _hook_func(current_event)

        logger.info("Event Finished")

    async def shutdown(self) -> None:
        """关闭并清理事件。"""
        self._cancel_event.set()
        self.node_state.clear()

    @overload
    async def get(
        self,
        func: Callable[[Event], bool | Awaitable[bool]] | None = None,
        *,
        event_type: None = None,
        max_try_times: int | None = None,
        timeout: int | float | None = None,
    ) -> Event: ...

    @overload
    async def get(
        self,
        func: Callable[[EventT], bool | Awaitable[bool]] | None = None,
        *,
        event_type: None = None,
        max_try_times: int | None = None,
        timeout: int | float | None = None,
    ) -> EventT: ...

    @overload
    async def get(
        self,
        func: Callable[[EventT], bool | Awaitable[bool]] | None = None,
        *,
        event_type: type[EventT],
        max_try_times: int | None = None,
        timeout: int | float | None = None,
    ) -> EventT: ...

    async def get(
        self,
        func: Callable[[Any], bool | Awaitable[bool]] | None = None,
        *,
        event_type: type[Event] | None = None,
        max_try_times: int | None = None,
        timeout: int | float | None = None,
    ) -> EventT:
        """获取满足指定条件的的事件，协程会等待直到适配器接收到满足条件的事件、超过最大事件数或超时。

        Args:
            func: 协程或者函数，函数会被自动包装为协程执行。
                要求接受一个事件作为参数，返回布尔值。当协程返回 `True` 时返回当前事件。
                当为 `None` 时相当于输入对于任何事件均返回真的协程，即返回适配器接收到的下一个事件。
            event_type: 当指定时，只接受指定类型的事件，先于 func 条件生效。默认为 `None`。
            adapter_type: 当指定时，只接受指定适配器产生的事件，先于 func 条件生效。默认为 `None`。
            max_try_times: 最大事件数。
            timeout: 超时时间。

        Returns:
            返回满足 `func` 条件的事件。

        Raises:
            GetEventTimeout: 超过最大事件数或超时。
        """
        _func = wrap_get_func(func)

        try_times = 0
        start_time = time.time()
        while not self.bot._should_exit.is_set():
            if max_try_times is not None and try_times > max_try_times:
                break
            if timeout is not None and time.time() - start_time > timeout:
                break

            async with self._condition:
                if timeout is None:
                    await self._condition.wait()
                else:
                    try:
                        await asyncio.wait_for(
                            self._condition.wait(),
                            timeout=start_time + timeout - time.time(),
                        )
                    except asyncio.TimeoutError:
                        break

                if (
                    self._current_event is not None
                    and not self._current_event.__handled__
                    and (
                        event_type is None
                        or isinstance(self._current_event, event_type)
                    )
                    and await _func(self._current_event)
                ):
                    self._current_event.__handled__ = True
                    return self._current_event

                try_times += 1

        raise GetEventTimeout

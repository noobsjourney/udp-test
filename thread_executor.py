from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, Qt, QThreadPool
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable, Dict, Optional, Union, Tuple
import threading
import traceback
from dataclasses import dataclass
import os
import time
import uuid

from base_module import BaseModule


@dataclass
class TaskResult:
    """标准化任务执行结果容器"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    traceback: Optional[str] = None


class TaskSignals(QObject):
    """任务生命周期信号集合"""
    started = pyqtSignal(str)  # 任务ID
    succeeded = pyqtSignal(str, str)  # 任务ID, 结果
    failed = pyqtSignal(str, str)  # 任务ID, 错误信息
    cancelled = pyqtSignal(str)  # 任务ID
    finished = pyqtSignal(str)  # 任务ID


class TaskWrapper(QRunnable):
    """任务执行容器"""

    def __init__(self, task_id: str, fn: Callable, *args, **kwargs):
        print("任务执行容器初始化")
        super().__init__()
        self.task_id = task_id
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = TaskSignals()
        self._state_lock = threading.Lock()
        self._state = "PENDING"  # PENDING | RUNNING | CANCELLED

    def run(self) -> None:
        """原子化任务执行流程"""
        print("原子化任务执行流程")
        with self._state_lock:
            if self._state == "CANCELLED":
                self.signals.cancelled.emit(self.task_id)
                return
            self._state = "RUNNING"

        self.signals.started.emit(self.task_id)
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.succeeded.emit(self.task_id, result)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            tb = traceback.format_exc()
            self.signals.failed.emit(self.task_id, f"{error_msg}\nTraceback:\n{tb}")
        finally:
            self.signals.finished.emit(self.task_id)

    def cancel(self) -> bool:
        """原子化任务取消操作"""
        print("原子化任务取消操作")
        with self._state_lock:
            if self._state == "PENDING":
                self._state = "CANCELLED"
                return True
            return False


class ThreadExecutor(BaseModule):
    """独立线程池管理系统

    特性：
    - 支持三种线程池模式：QT/IO/COMPUTE
    - 全生命周期任务追踪
    - 增强的取消和超时机制
    - 线程安全的注册表操作
    """
    # 模块级信号
    pool_created = pyqtSignal(str, str)  # (池名称, 池类型)
    pool_closed = pyqtSignal(str)  # 池名称

    def __init__(self, parent=None):
        print("独立线程池管理系统初始化")
        super().__init__(parent)
        # 线程池配置 {name: (type, instance)}
        self._pools: Dict[str, Tuple[str, Union[QThreadPool, ThreadPoolExecutor]]] = {}
        # 任务注册表 {task_id: (pool_name, task)}
        self._task_registry: Dict[str, Tuple[str, Union[TaskWrapper, Future]]] = {}
        self._registry_lock = threading.RLock()
        self._init_default_pools()
    @property
    def module_name(self) -> str:
        return "thread"
    def _init_default_pools(self):
        """初始化默认线程池"""
        print("初始化默认线程池")
        self.create_pool("qt_default", "qt", max_threads=QThreadPool.globalInstance().maxThreadCount())
        self.create_pool("io_default", "standard", max_workers=8)
        self.create_pool("compute_default", "standard", max_workers=os.cpu_count())

    def create_pool(self, name: str, pool_type: str, **kwargs) -> bool:
        """创建新线程池

        :param pool_type: qt | standard
        :param kwargs:
            - qt: max_threads
            - standard: max_workers, etc
        """
        print("创建新线程池")
        with self._registry_lock:
            if name in self._pools:
                return False

            if pool_type == "qt":
                pool = QThreadPool()
                if 'max_threads' in kwargs:
                    pool.setMaxThreadCount(kwargs['max_threads'])
                self._pools[name] = (pool_type, pool)
                self.pool_created.emit(name, "QT")
                return True

            elif pool_type == "standard":
                workers = kwargs.get('max_workers', os.cpu_count())
                pool = ThreadPoolExecutor(max_workers=workers)
                self._pools[name] = (pool_type, pool)
                self.pool_created.emit(name, "STANDARD")
                return True

            return False

    def submit(
            self,
            fn: Callable,
            pool_name: str = "qt_default",
            *args, **kwargs
    ) -> Optional[str]:
        """提交任务到指定线程池

        返回格式：timestamp:pool_name:uuid
        示例：'1689123456.789:qt_default:abcd-1234'
        """
        print("提交任务到指定线程池")
        with self._registry_lock:
            if pool_name not in self._pools:
                return None

            # 生成可读任务ID
            task_id = task_id or f"{time.time():.3f}:{pool_name}:{uuid.uuid4().hex[:8]}"
            pool_type, pool = self._pools[pool_name]
            task = TaskWrapper(task_id, fn, *args, **kwargs)

            # 连接任务信号
            task.signals.started.connect(
                lambda t_id: self._update_task_state(t_id, "RUNNING"),
                Qt.QueuedConnection
            )
            task.signals.succeeded.connect(
                lambda t_id, res: self._finalize_task(t_id, res, None),
                Qt.QueuedConnection
            )
            task.signals.failed.connect(
                lambda t_id, err: self._finalize_task(t_id, None, err),
                Qt.QueuedConnection
            )
            task.signals.cancelled.connect(
                lambda t_id: self._update_task_state(t_id, "CANCELLED"),
                Qt.QueuedConnection
            )

            # 提交到线程池
            if pool_type == "qt":
                pool.start(task)
            else:
                future = pool.submit(task.run)
                self._task_registry[task_id] = (pool_name, future)

            self._task_registry[task_id] = (pool_name, task)
            self._update_task_state(task_id, "PENDING")
            return task_id

    def shutdown_pool(self, name: str, wait: bool = True) -> bool:
        """关闭指定线程池"""
        print("关闭指定线程池")
        with self._registry_lock:
            if name not in self._pools:
                return False

            pool_type, pool = self._pools[name]
            if pool_type == "qt":
                pool.waitForDone()
            else:
                pool.shutdown(wait=wait)
            del self._pools[name]
            self.pool_closed.emit(name)
            return True

    def cancel_task(self, task_id: str) -> bool:
        """强制取消任务（包括运行中的任务）"""
        print("强制取消任务")
        with self._registry_lock:
            if task_id not in self._task_registry:
                return False

            pool_name, task = self._task_registry[task_id]
            success = False

            if isinstance(task, TaskWrapper):
                success = task.cancel()
                if success:
                    self._update_task_state(task_id, "CANCELLED")
                    self._finalize_task(task_id, None, "用户取消")  # 强制清理
            elif isinstance(task, Future):
                success = task.cancel()
                if success:
                    del self._task_registry[task_id]  # 立即移除
            return success

    def _update_task_state(self, task_id: str, state: str) -> None:
        """原子化状态更新"""
        print("原子化状态更新")
        with self._registry_lock:
            if task_id in self._task_registry:
                print(f"Task {task_id} state changed to {state}")

    def _finalize_task(self, task_id: str, result: Any, error: str) -> None:
        """任务最终处理"""
        print("任务最终处理")
        with self._registry_lock:
            if task_id in self._task_registry:
                # 记录执行结果
                if error:
                    print(f"Task Failed [{task_id}]: {error}")
                else:
                    print(f"Task Completed [{task_id}] Result: {result}")

                # 清理注册表
                del self._task_registry[task_id]

    def get_active_pools(self) -> Dict[str, str]:
        """获取当前活跃线程池信息"""
        print("获取当前活跃线程池信息")
        return {name: typ for name, (typ, _) in self._pools.items()}

    def get_running_tasks(self) -> Dict[str, str]:
        """获取运行中任务列表"""
        print("获取运行中任务列表")
        return {
            t_id: pool_name
            for t_id, (pool_name, _) in self._task_registry.items()
        }
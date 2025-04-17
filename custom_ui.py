from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Type, Dict, Callable

class UiFactoryMeta(type):
    """元类用于自动注册组件和信号"""
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        if name != 'UiFactory':
            UiFactory.register_component(new_class)
        return new_class

class UiFactory(QObject, metaclass=UiFactoryMeta):
    """UI组件工厂基类
    特性：
    1. 使用装饰器声明原生信号
    2. 自动生成带_auto后缀的桥接信号
    3. 支持参数化信号类型
    """
    _components: Dict[str, Type[QObject]] = {}
    _signals: Dict[Type[QObject], Dict[str, tuple]] = {}

    def __init__(self):
        super().__init__()

    @classmethod
    def signal(cls, *types: Type) -> Callable:
        """信号声明装饰器
        Args:
            *types: 信号参数类型
        """
        def decorator(func):
            signal_name = func.__name__
            cls._signals.setdefault(cls._current_component, {})[signal_name] = types
            return func
        return decorator

    @classmethod
    def register_component(cls, component: Type[QObject]) -> None:
        """注册UI组件"""
        cls._components[component.__name__] = component
        cls._signals[component] = {}

    @classmethod
    def create(cls, component_type: Type[QObject], *args, **kwargs) -> QObject:
        """创建UI组件实例并自动配置信号"""
        instance = component_type(*args, **kwargs)
        signals_config = cls._signals.get(component_type, {})

        # 动态创建信号容器
        for signal_name, types in signals_config.items():
            container = SignalContainer(*types)
            setattr(instance, f'{signal_name}_auto', container.signal_instance.signal)
            
            # 自动连接原生信号到桥接信号
            origin_signal = getattr(instance, signal_name)
            origin_signal.connect(lambda *args, s=container.signal_instance.signal: s.emit(*args))

        return instance

class SignalContainer(QObject):
    def __init__(self, *types: Type):
        super().__init__()
        self.signal = pyqtSignal(*types)

    def forward(self, *args):
        self.signal.emit(*args)

# 示例组件实现
@UiFactory.register_component
class ExampleButton(QPushButton):
    @UiFactory.signal(int)
    def clicked(self):
        pass

    def simulate_click(self):
        self.clicked.emit(1)
class UIComponent(BaseModule):
    """UI组件基类（自动信号桥接）
    - 属性：
        native_signals: 需要桥接的原生信号名称列表
    - 功能：
        1. 自动创建同名带_auto后缀的自定义信号
        2. 自动连接原生信号到自定义信号"""
    
    native_signals = []  # 子类需覆盖此属性

    def __init__(self):
        super().__init__()
        self._create_auto_signals()
        self._connect_signals()

    def _create_auto_signals(self):
        for signal_name in self.native_signals:
            # 动态创建带_auto后缀的信号
            auto_signal = pyqtSignal()
            setattr(self, f'{signal_name}_auto', auto_signal)

    def _forward_signal(self, signal):
        def forward(*args):
            signal.emit(*args)
        return forward

    def _connect_signals(self):
        for signal_name in self.native_signals:
            origin_signal = getattr(self, signal_name)
            auto_signal = getattr(self, f'{signal_name}_auto')
            
            # 使用闭包保存当前信号上下文
            origin_signal.connect(self._forward_signal(auto_signal))

    @property
    @abstractmethod
    def module_name(self) -> str:
        """必须实现的模块名称属性"""

# 使用示例
class ExampleButton(UIComponent):
    clicked = pyqtSignal()  # 原生信号
    
    native_signals = ['clicked']  # 声明需要桥接的信号
    
    @property
    def module_name(self):
        return "example_button"
    
    def simulate_click(self):
        self.clicked.emit()

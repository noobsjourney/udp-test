import socket
import netifaces
from typing import Tuple, Optional, Dict, List

class TCPClient:
    """TCP客户端实现

    属性:
        sock: 底层的TCP套接字对象
        timeout: 连接和操作超时时间(秒)
    """

    def __init__(self, timeout=5):
        """初始化TCP客户端

        Args:
            timeout (int, optional): 套接字超时时间，默认5秒
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)

    def connect(self, host: str, port: int) -> bool:
        """建立TCP连接

        Args:
            host (str): 目标主机地址
            port (int): 目标端口号

        Returns:
            bool: 连接成功返回True，超时或被拒绝返回False

        Raises:
            socket.timeout: 当连接超时时触发
            ConnectionRefusedError: 当目标拒绝连接时触发
        """
        try:
            self.sock.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False

    def send_data(self, data: bytes) -> bool:
        """发送TCP数据

        Args:
            data (bytes): 要发送的二进制数据

        Returns:
            bool: 发送成功返回True，连接中断或超时返回False
        """
        try:
            self.sock.sendall(data)
            return True
        except (BrokenPipeError, socket.timeout):
            return False

    def receive_data(self, buffer_size=4096) -> Optional[bytes]:
        """接收TCP数据

        Args:
            buffer_size (int, optional): 接收缓冲区大小，默认4096字节

        Returns:
            Optional[bytes]: 成功时返回接收的字节数据，超时返回None
        """
        try:
            return self.sock.recv(buffer_size)
        except socket.timeout:
            return None

class TCPServer:
    """TCP服务器实现

    属性:
        sock: 监听的TCP套接字对象
    """

    def start(self, host: str, port: int, backlog=5) -> bool:
        """启动TCP服务器

        Args:
            host (str): 绑定主机地址
            port (int): 绑定端口号
            backlog (int, optional): 最大等待连接数，默认5

        Returns:
            bool: 绑定成功返回True，端口被占用返回False

        Raises:
            OSError: 当端口被占用或权限不足时触发
        """
        try:
            self.sock.bind((host, port))
            self.sock.listen(backlog)
            return True
        except OSError:
            return False

    def accept_connection(self) -> Tuple[socket.socket, Tuple[str, int]]:
        return self.sock.accept()

class NetworkUtils:
    """网络工具类，提供静态网络检测方法"""

    @staticmethod
    def get_local_ip() -> str:
        """获取本机有效IPv4地址

        Returns:
            str: 成功返回实际IP地址，失败返回127.0.0.1
        """
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return '127.0.0.1'

    @staticmethod
    def get_interfaces() -> Dict[str, List[Dict]]:
        interfaces = {}
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            interfaces[iface] = [
                {'addr': addr['addr'], 'netmask': addr.get('netmask', '')}
                for addr in addrs.get(netifaces.AF_INET, [])
            ]
        return interfaces

    @staticmethod
    def check_port_available(port: int) -> bool:
        """检测本地端口是否可用

        Args:
            port (int): 要检测的端口号

        Returns:
            bool: 端口可用返回True，被占用返回False
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0

    @staticmethod
    def scan_ports(start: int, end: int) -> Dict[int, bool]:
        return {port: NetworkUtils.check_port_available(port) for port in range(start, end+1)}

    @staticmethod
    def get_network_latency(host: str, port: int, timeout=3) -> Optional[float]:
        """测量TCP连接延迟

        Args:
            host (str): 目标主机
            port (int): 目标端口
            timeout (int, optional): 超时时间，默认3秒

        Returns:
            Optional[float]: 成功返回毫秒级延迟，失败返回None
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                start = time.time()
                s.connect((host, port))
                return (time.time() - start) * 1000  # 毫秒
        except:
            return None
# 测试udp协议能否正常通信 
# 本机作为客户端，虚拟机作为服务器端
from udp import UDPNetworkManager
from PyQt5.QtCore import QCoreApplication, QTimer
import sys

def on_transmission_failed(modename, node_id, error, dest_addr):
    print(f"[客户端] 传输失败: {error} -> {dest_addr}")

def main():
    app = QCoreApplication(sys.argv)
    client = UDPNetworkManager()
    # 当client发送数据失败时，失败信号被发射，触发执行on_transmission_failed函数
    client.transmissionFailed.connect(on_transmission_failed)

    # 目标地址：你虚拟机的服务端IP
    target_ip = "192.168.230.128"  # 虚拟机的IP地址
    target_port = 12345

    def send_message():
        message = "你好，UDP服务端！"
        print(f"[客户端] 正在发送数据: {message}")
        client.send_to("node", 1, message.encode(), (target_ip, target_port))

    # 延时 2 秒后发送数据（避免主线程未初始化）
    QTimer.singleShot(2000, send_message)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

# udp_client.py
# 本机作为客户端
from udp import UDPNetworkManager
from PyQt5.QtCore import QCoreApplication, QTimer
import sys
import socket

def on_transmission_failed(modename, node_id, error, dest_addr):
    print(f"[客户端] 传输失败: {error} -> {dest_addr}")

def main():
    app = QCoreApplication(sys.argv)
    client = UDPNetworkManager()
    client.transmissionFailed.connect(on_transmission_failed)

    # 目标地址：你虚拟机的服务端IP
    target_ip = "192.168.56.101"  # ← 请修改为服务端所在虚拟机的IP地址
    target_port = 12345

    def send_message():
        message = "你好，UDP服务端！"
        print(f"[客户端] 正在发送数据: {message}")
        client.send_to("node", 1, message.encode(), (target_ip, target_port))

        # 接收服务器响应
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.settimeout(5)  # 设置超时时间为 5 秒
        try:
            data, server_address = client_socket.recvfrom(1024)
            print(f"[客户端] 收到来自 {server_address} 的响应: {data.decode('utf-8')}")
        except socket.timeout:
            print("[客户端] 接收响应超时")
        client_socket.close()

    # 延时 2 秒后发送数据（避免主线程未初始化）
    QTimer.singleShot(2000, send_message)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
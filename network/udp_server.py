# 虚拟机作为服务器
from udp import UDPNetworkManager
from PyQt5.QtCore import QCoreApplication
import sys

def on_data_received(modename, node_id, data, source_addr):
    print(f"[服务端] 收到数据: modename={modename}, node_id={node_id}, data={data.decode()}, 来自={source_addr}")

def main():
    app = QCoreApplication(sys.argv)
    server = UDPNetworkManager(bind_host="0.0.0.0", bind_port=12345)  # 监听 12345 端口
    server.dataReceived.connect(on_data_received)

    print(f"[服务端] 正在监听 0.0.0.0:12345")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

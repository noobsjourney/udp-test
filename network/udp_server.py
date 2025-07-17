# udp_server.py
# 虚拟机作为服务器
import socket

# 创建 UDP 套接字
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 绑定 IP 地址和端口
server_address = ('0.0.0.0', 12345)
server_socket.bind(server_address)

print(f"UDP 服务器正在监听 {server_address}...")

while True:
    # 接收数据
    data, client_address = server_socket.recvfrom(1024)
    print(f"收到来自 {client_address} 的消息: {data.decode('utf-8')}")

    # 发送响应
    response = "消息已收到，谢谢！"
    server_socket.sendto(response.encode('utf-8'), client_address)
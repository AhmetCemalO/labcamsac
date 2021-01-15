import socket

buffer_bytes = 1024
class UDPSocket:

    def __init__(self, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))
        self.socket.settimeout(.02)
        print('Listening to UDP port: {0}'.format(port))
        
    def receive(self):
        msg,address = self.socket.recvfrom(buffer_bytes)
        return msg, address
        
    def send(self, msg, address):
        self.socket.sendto(msg.encode('ascii'),address)
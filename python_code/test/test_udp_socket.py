import unittest
import sys
from os.path import dirname, abspath
from multiprocessing import Process, Event

test_path = dirname(abspath(__file__))
code_path = dirname(test_path)
sys.path.append(code_path)

from udp_socket import UDPSocket

class PingableServer(Process):
    def __init__(self, address):
        super().__init__()
        self.address = address
        self.start_flag = Event()
        self.exit_flag = Event()
        self.start()
        self.start_flag.wait()
    
    def run(self):
        self.start_flag.set()
        with UDPSocket(self.address) as socket:
            while not self.exit_flag.is_set():
                ret, msg, emitter_address = socket.receive()
                if ret:
                    if msg == 'ping':
                        socket.send('pong', emitter_address)
        
class TestUDPSocket(unittest.TestCase):
    def setUp(self):
        server_ip = '127.0.0.1'
        server_port = 5005
        self.server_address = (server_ip, server_port)
        self.server = PingableServer(self.server_address)
        
    def tearDown(self):
        self.server.exit_flag.set()
        
    def test_ping(self):
        """server should send 'pong' back"""
        client_address = ('127.0.0.1', 5004)
        with UDPSocket(client_address) as client:
            client.send('ping', self.server_address)
            received = False
            while not received:
                received, msg, address = client.receive()
        assert(msg == 'pong')
        assert(address == self.server_address)

if __name__ == '__main__':
    unittest.main()
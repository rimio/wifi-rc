import socket
import struct

class State:
    # Servo values in range [-1, 1]
    servo = 0.0
    # Motor values in range [-1, 1]
    motor = 0.0
    
    def __init__(self, s, m):
        self.servo = s
        self.motor = m

class Client:
    # IP address and port of server
    _ip = "127.0.0.1"
    _port =  9991
    
    # Socket
    _socket = None
    
    # Constructor
    def __init__(self, ip, port):
        # Open socket for sending
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._ip = ip
        self._port = port
    
    # Send input state
    def sendState(self, state):
        message = struct.pack(">ff", state.servo, state.motor)
        self._socket.sendto(message, (self._ip, self._port))
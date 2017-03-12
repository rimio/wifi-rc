import socket
import threading
import datetime
import struct
from time import sleep

# IP and port for UDP listening
UDP_IP = ""
UDP_PORT = 9991

# State lifespan (milliseconds)
STATE_LIFESPAN = 200

# Function waits for state updates over UDP
def UdpThread():
    # Open UDP socket    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    # State lock
    global state_lock
    global servo
    global motor
    global state_expiration
    
    # Infinite loop
    while True:
        # Wait for message
        message, addr = sock.recvfrom(8)
        
        # Keep state consistency; acquire lock
        state_lock.acquire(True)
        
        # Unpack state
        servo, motor = struct.unpack(">ff", message)
        
        # Set lifespan
        state_expiration = datetime.datetime.now() + datetime.timedelta(milliseconds=STATE_LIFESPAN)
        
        # Release lock
        state_lock.release()
        

if __name__ == "__main__":
    
    # Servo state; floating point value in range [-1, 1]; -1 is full left, 1 is full right
    global servo
    servo = 0.0
    
    # Motor state; floating point value in range [-1, 1]; -1 is full reverse, 1 is full forward
    global motor
    motor = 0.0
    
    # Expiration time of state; if current time is larger then "servo" and "motor"
    # are ignored and neutral (zero) values are used
    global state_expiration
    state_expiration = datetime.datetime.now()
    
    # State access lock
    global state_lock
    state_lock = threading.Lock()
    
    # Run state update thread
    udpthread = threading.Thread(target = UdpThread)
    udpthread.start()
    
    # Main update loop
    while True:
        # Keep state consistency; acquire lock
        state_lock.acquire(True)
        
        # Neutral state on expiration
        if state_expiration < datetime.datetime.now():
            servo = 0.0
            motor = 0.0
        
        # Update pin states
        
        # Release lock
        state_lock.release()
        
        # Log
        print("State is servo=" + str(servo) + ", motor=" + str(motor))
                
        # yield CPU        
        sleep(0.05)
    

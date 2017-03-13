import client
import pygame
import cv2
import threading
import socket
import numpy as np
from time import sleep

# Server address
SERVER_IP = "172.172.1.132"
SERVER_CONTROL_PORT = 9991
SERVER_VIDEO_PORT = 9992

# Gamepad configuration
GAMEPAD_ID = 0
GAMEPAD_STEER_AXIS = 0
GAMEPAD_MOTOR_AXIS = 4
GAMEPAD_DEADZONE = 0.05

# Initialize gamepad and wait for neutral state
def InitGamepad(joyId, steerAxis, motorAxis):
    pygame.init()
    joy = pygame.joystick.Joystick(joyId)
    joy.init()
    
    # Process all events to date
    for event in pygame.event.get():
        pass
    
    # Wait for neutral state (0 for steer axis, -1 for motor axis)
    while abs(joy.get_axis(steerAxis)) > GAMEPAD_DEADZONE or abs(joy.get_axis(motorAxis)) > GAMEPAD_DEADZONE:
        for event in pygame.event.get():
            pass
        print("Please bring gamepad to neutral state. Current state (steer=" + str(joy.get_axis(steerAxis)) + ", motor=" + str(joy.get_axis(motorAxis)) + ")")
        sleep(0.5)
    
    print("Neutral state reached ...")
    
    return joy

# Get a state object from gamepad
def StateFromGamepad(joy, steerAxis, motorAxis):
    return client.State(joy.get_axis(steerAxis), -joy.get_axis(motorAxis))

# Receive full buffer
def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

# Video thread function
def VideoThread():
    
    # Connect to video server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_VIDEO_PORT))
    
    while True:
        # Receive frame
        length = recvall(sock, 16)
        stringData = recvall(sock, int(length))
        
        # Decode jpeg
        data = np.fromstring(stringData, dtype='uint8')
        image = cv2.imdecode(data, 1)
        
        # Show frame
        cv2.imshow('Video Feed', image)
        cv2.waitKey(1)
        
        # Send OK for next frame
        sock.send(b'OK')
    
    # Close socket
    sock.close()

if __name__ == "__main__":
    
    # Get joystick
    pygame.init()
    joy = InitGamepad(GAMEPAD_ID, GAMEPAD_STEER_AXIS, GAMEPAD_MOTOR_AXIS)
    
    # Spawn a Client
    cl = client.Client(SERVER_IP, SERVER_CONTROL_PORT)
    
    # Start video thread
    videothread = threading.Thread(target = VideoThread)
    videothread.start()
    
    # Keyboard loop
    while True:
        # Process input
        for event in pygame.event.get():
            pass

        # Send decoy
        cl.sendState(StateFromGamepad(joy, GAMEPAD_STEER_AXIS, GAMEPAD_MOTOR_AXIS))
        
        # yield CPU
        sleep(0.01)
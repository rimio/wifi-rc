import socket
import threading
import datetime
import struct
import RPi.GPIO as GPIO
import cv2
import numpy
from time import sleep

# BCM signal pins
PIN_STEERING = 17
PIN_MOTOR = 18

# PWM settings
PWM_FREQUENCY = 50
PWM_STEERING_DUTY_LOW = 6.0
PWM_STEERING_DUTY_HIGH = 9.0
PWM_MOTOR_DUTY_LOW = 6.7
PWM_MOTOR_DUTY_HIGH = 7.9

# IP and port for TCP listening
TCP_IP = ""
TCP_PORT = 9992

# IP and port for UDP listening
UDP_IP = ""
UDP_PORT = 9991

# State lifespan (milliseconds)
STATE_LIFESPAN = 100

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
        servo = max(min(servo, 1.0), -1.0)
        motor = max(min(motor, 1.0), -1.0)
        
        # Set lifespan
        state_expiration = datetime.datetime.now() + datetime.timedelta(milliseconds=STATE_LIFESPAN)
        
        # Release lock
        state_lock.release()

def TcpThread():
    # Open capture
    cap = cv2.VideoCapture(0)
    cap.set(cv2.cv.CV_CAP_PROP_FPS, 10)
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 416);
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240);
    encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),60]

    # Open TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((TCP_IP, TCP_PORT))
    sock.listen(1)

    # Accept only one connection at a time
    while True:
        # Accept one connection
        conn, addr = sock.accept()
        print("Video connection accepted from " + str(addr))

        while True:
            # Capture frame
            ret, oframe = cap.read()
            frame = cv2.cvtColor(oframe, cv2.COLOR_RGB2GRAY)
            
            # Encode jpeg
            result, encoded = cv2.imencode('.jpg', frame, encode_param)
            data = numpy.array(encoded)
            stringData = data.tostring()

            # Send frame
            conn.send(str(len(stringData)).ljust(16));
            conn.send(stringData);

        # Close connection
        print("Connection closed ...")
        conn.close()

if __name__ == "__main__":
    
    # Set up GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_STEERING, GPIO.OUT)
    GPIO.setup(PIN_MOTOR, GPIO.OUT)
    
    # Set up pins
    steering_pin = GPIO.PWM(PIN_STEERING, PWM_FREQUENCY)
    steering_pin.start((PWM_STEERING_DUTY_LOW + PWM_STEERING_DUTY_HIGH) / 2.0)
    motor_pin = GPIO.PWM(PIN_MOTOR, PWM_FREQUENCY)
    motor_pin.start((PWM_MOTOR_DUTY_LOW + PWM_MOTOR_DUTY_HIGH) / 2.0)
    
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

    # Run video thread
    tcpthread = threading.Thread(target = TcpThread)
    tcpthread.start()
    
    # Main update loop
    while True:
        # Keep state consistency; acquire lock
        state_lock.acquire(True)
        
        # Neutral state on expiration
        if state_expiration < datetime.datetime.now():
            servo = 0.0
            motor = 0.0
        
        # Update pin states
        steering_pin.ChangeDutyCycle(PWM_STEERING_DUTY_LOW + (PWM_STEERING_DUTY_HIGH - PWM_STEERING_DUTY_LOW) * (servo + 1.0) / 2.0)
        motor_pin.ChangeDutyCycle(PWM_MOTOR_DUTY_LOW + (PWM_MOTOR_DUTY_HIGH - PWM_MOTOR_DUTY_LOW) * (motor + 1.0) / 2.0)
        
        # Release lock
        state_lock.release()
        
        # Log
        #print("State is servo=" + str(servo) + ", motor=" + str(motor))
                
        # yield CPU        
        sleep(0.05)
    

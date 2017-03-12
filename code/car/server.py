import socket
import threading
import datetime
import struct
import RPi.GPIO as GPIO
from time import sleep

# BCM signal pins
PIN_STEERING = 17
PIN_MOTOR = 18

# PWM settings
PWM_FREQUENCY = 50
PWM_STEERING_DUTY_LOW = 6.0
PWM_STEERING_DUTY_HIGH = 9.0
PWM_MOTOR_DUTY_LOW = 6.0
PWM_MOTOR_DUTY_HIGH = 9.0

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
        motor_pin.ChangeDutyCycle(PWM_MOTOR_DUTY_LOW + (PWM_MOTOR_DUTY_HIGH - PWM_MOTOR_DUTY_LOW) * (servo + 1.0) / 2.0)
        
        # Release lock
        state_lock.release()
        
        # Log
        print("State is servo=" + str(servo) + ", motor=" + str(motor))
                
        # yield CPU        
        sleep(0.05)
    

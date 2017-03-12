import client
import pygame
from time import sleep

# Gamepad configuration
GAMEPAD_ID = 0
GAMEPAD_STEER_AXIS = 0
GAMEPAD_MOTOR_AXIS = 5
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
    while abs(joy.get_axis(steerAxis)) > GAMEPAD_DEADZONE or joy.get_axis(motorAxis) > (-1 + GAMEPAD_DEADZONE):
        for event in pygame.event.get():
            pass
        print("Please bring gamepad to neutral state. Current state (steer=" + str(joy.get_axis(steerAxis)) + ", motor=" + str(joy.get_axis(motorAxis)) + ")")
        sleep(0.5)
    
    print("Neutral state reached ...")
    
    return joy

# Get a state object from gamepad
def StateFromGamepad(joy, steerAxis, motorAxis):
    return client.State(joy.get_axis(steerAxis), (joy.get_axis(motorAxis)+1)/2)
    

if __name__ == "__main__":
    
    # Get joystick
    pygame.init()
    joy = InitGamepad(GAMEPAD_ID, GAMEPAD_STEER_AXIS, GAMEPAD_MOTOR_AXIS)
    
    # Spawn a Client
    cl = client.Client("192.168.1.134", 9991)
    #cl = client.Client("127.0.0.1", 9991)
    
    # Keyboard loop
    while True:
        # Process input
        for event in pygame.event.get():
            pass

        # Send decoy
        cl.sendState(StateFromGamepad(joy, GAMEPAD_STEER_AXIS, GAMEPAD_MOTOR_AXIS))
        
        # yield CPU
        sleep(0.01)
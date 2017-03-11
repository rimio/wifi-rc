import client
from time import sleep

if __name__ == "__main__":
    
    # Spawn a Client
    cl = client.Client("127.0.0.1", 9111)
    
    # Keyboard loop
    while True:
        # Send decoy
        cl.sendState(client.State(1.0, -1.0))
        # yield CPU
        sleep(0.5)
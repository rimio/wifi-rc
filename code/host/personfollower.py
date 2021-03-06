import client
import cv2
import threading
import socket
import datetime
import numpy as np
from time import sleep

# Server address
SERVER_IP = "192.168.81.210"
SERVER_CONTROL_PORT = 9991
SERVER_VIDEO_PORT = 9992

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
# Started from http://www.pyimagesearch.com/2015/11/09/pedestrian-detection-opencv/
def VideoThread():
    
    # Globals
    global servo
    global motor
    
    # Default OpenCV HOG+SVM for person detection
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    # Open video file for writing
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    vout = cv2.VideoWriter("output_" + datetime.datetime.now().strftime("%I-%M%p_%d-%B-%Y") + ".avi", fourcc, 10.0, (416, 240))
    
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
        imh, imw, imc = image.shape
        
        # Detect persons
        (rects, weights) = hog.detectMultiScale(image, winStride=(8, 8), padding=(16, 16), scale=1.05, hitThreshold=0.15)
        headings = []
        tops = []
        for (x, y, w, h) in rects:
            headings.append(x + w/2)
            tops.append(y)
        
        # Detect lines
        edges = cv2.Canny(image, 100, 200, apertureSize = 3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 15, 30, 10)
    
        # Pick closest detection
        picked = -1
        pickedTop = 1000
        if len(headings) > 0:
            for i in range(0, len(tops)):
                if pickedTop > tops[i]:
                    picked = i
                    pickedTop = tops[i]

        # Follow person
        if picked > -1:
            servo = (headings[picked] - imw/2.0) * 2.0 / imw
            servo = max(min(servo, 1.0), -1.0)
            motor = 0.7
            print("Tracking person x=" + str(headings[picked]) + " s=" + str(servo) + " m=" + str(motor))
        else:
            servo = 0.0
            motor = 0.0
        
        # Show frame
        if not (lines is None):
            for x in range(0, len(lines)):
                for x1,y1,x2,y2 in lines[x]:
                    cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        for (x, y, w, h) in rects:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0), 2)
        for h in headings:
            cv2.line(image, (int(h), 0), (int(h), imh), (0), 2)
    
        if picked > -1:
            cv2.rectangle(image, (rects[picked][0], rects[picked][1]), (rects[picked][0] + rects[picked][2], rects[picked][1] + rects[picked][3]), (128), 2)

        vout.write(image)
        cv2.imshow('Video Feed', image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Close video file
    vout.release()
    
    # Close socket
    sock.close()

if __name__ == "__main__":
    
    # Spawn a Client
    cl = client.Client(SERVER_IP, SERVER_CONTROL_PORT)
    
    # Start video thread
    videothread = threading.Thread(target = VideoThread)
    videothread.start()
    
    # Global states
    global motor
    global servo
    motor = 0.0
    servo = 0.0
    
    # Keyboard loop
    while True:
        # Send state
        cl.sendState(client.State(servo, motor))
        
        # yield CPU
        sleep(0.01)
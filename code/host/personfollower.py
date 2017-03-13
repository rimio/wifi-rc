import client
import cv2
import threading
import socket
import numpy as np
from time import sleep

# Server address
SERVER_IP = "172.172.1.132"
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

# Malisiewicz et al.
# Implementation at http://www.pyimagesearch.com/2015/02/16/faster-non-maximum-suppression-python/
def non_max_suppression(boxes, overlapThresh):
	# if there are no boxes, return an empty list
	if len(boxes) == 0:
		return []
 
	# if the bounding boxes integers, convert them to floats --
	# this is important since we'll be doing a bunch of divisions
	if boxes.dtype.kind == "i":
		boxes = boxes.astype("float")
 
	# initialize the list of picked indexes	
	pick = []
 
	# grab the coordinates of the bounding boxes
	x1 = boxes[:,0]
	y1 = boxes[:,1]
	x2 = boxes[:,2]
	y2 = boxes[:,3]
 
	# compute the area of the bounding boxes and sort the bounding
	# boxes by the bottom-right y-coordinate of the bounding box
	area = (x2 - x1 + 1) * (y2 - y1 + 1)
	idxs = np.argsort(y2)
 
	# keep looping while some indexes still remain in the indexes
	# list
	while len(idxs) > 0:
		# grab the last index in the indexes list and add the
		# index value to the list of picked indexes
		last = len(idxs) - 1
		i = idxs[last]
		pick.append(i)
 
		# find the largest (x, y) coordinates for the start of
		# the bounding box and the smallest (x, y) coordinates
		# for the end of the bounding box
		xx1 = np.maximum(x1[i], x1[idxs[:last]])
		yy1 = np.maximum(y1[i], y1[idxs[:last]])
		xx2 = np.minimum(x2[i], x2[idxs[:last]])
		yy2 = np.minimum(y2[i], y2[idxs[:last]])
 
		# compute the width and height of the bounding box
		w = np.maximum(0, xx2 - xx1 + 1)
		h = np.maximum(0, yy2 - yy1 + 1)
 
		# compute the ratio of overlap
		overlap = (w * h) / area[idxs[:last]]
 
		# delete all indexes from the index list that have
		idxs = np.delete(idxs, np.concatenate(([last],
			np.where(overlap > overlapThresh)[0])))
 
	# return only the bounding boxes that were picked using the
	# integer data type
	return boxes[pick].astype("int")

# Video thread function
# Started from http://www.pyimagesearch.com/2015/11/09/pedestrian-detection-opencv/
def VideoThread():
    
    # Connect to video server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_VIDEO_PORT))
    
    # Globals
    global servo
    global motor
    
    # Default OpenCV HOG+SVM for person detection
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    while True:
        # Receive frame
        length = recvall(sock, 16)
        stringData = recvall(sock, int(length))
        
        # Decode jpeg
        data = np.fromstring(stringData, dtype='uint8')
        image = cv2.imdecode(data, 1)
        imh, imw, imc = image.shape
        image = cv2.resize(image, (imw*2, imh*2))
        imh, imw, imc = image.shape
        
        # Detect persons
        (rects, weights) = hog.detectMultiScale(image, winStride=(8, 8), padding=(16, 16), scale=1.05)
        headings = []
        tops = []
        for (x, y, w, h) in rects:
            headings.append(x + w/2)
            tops.append(y)
    
        # Pick first person
        picked = -1
        if len(headings) > 0:
            picked = 0

        # Follow person
        if picked > -1:
            servo = (headings[picked] - imw/2.0) * 2.0 / imw
            servo = max(min(servo, 1.0), -1.0)
            if (tops[picked] > imh*0.1):
                motor = 0.5
            else:
                motor = 0.0
            print("Tracking person x=" + str(headings[picked]) + " s=" + str(servo) + " m=" + str(motor))
        else:
            servo = 0.0
            motor = 0.0
        
        # Show frame
        for (x, y, w, h) in rects:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0), 2)
        for h in headings:
            cv2.line(image, (int(h), 0), (int(h), imh), (0), 2)

        cv2.imshow('Video Feed', image)
        cv2.waitKey(1)
        
        # Send OK for next frame
        sock.send(b'OK')
    
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
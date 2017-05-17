import numpy as np
import cv2




def draw_lines(img,lines):
	line_hist=[]
	if (len(lines>0)):
		for line in lines:
			bline = np.copy(line)
			lShape = bline.lShape
			bline = np.reshape(bline,(lShape[0]*2,2))

			vx, vy, x, y = cv2.fitLine(np.array(bline, dtype=np.int32), cv2.DIST_L2, 0, 0.01, 0.01)
			slope = vy/vx
			intercept = y - (slope * x)
			line_hist.append([slope,intercept])

def defineSafe(image,original):
	width = image.shape[1]
	height = image.shape[0]
	#print('Shape is :',image.shape)
	safe_image = np.copy(image)*0
	safe_points = [0]*width

	for i in range(width):
		for j in reversed(range(height-60)):
			if ((image[j,i] == 255 or image[j,i]==0) and safe_points[i]==0):
				safe_points[i] = j
				#print('x: ',i,' y: ',j,' val: ',image[j,i])
			#image[j,i]=255

	#for i in range(width):


	for i in range(width):
		cv2.line(safe_image,(i,height),(i,max(safe_points[i],80)),(255,255,0),1)

	safe_image = cv2.medianBlur(safe_image,15)

	output = cv2.addWeighted(original,0.8,safe_image,1,0)
	return output





cap = cv2.VideoCapture('testVid.avi')

ignoreFrame=2500
idx=0

while(cap.isOpened() and idx<8000):
    ret, frame = cap.read()
    idx +=1
    num_down = 2
    num_bilateral = 5


    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if (idx>ignoreFrame):
    	original = gray.copy()
    	
    	gray[0:50] = 0
    	gray[-40:] = 0
    	canny = original.copy()


		# ------------------------------------------------------------
		# cartoonise
    	for _ in xrange(num_down):
    		gray = cv2.pyrDown(gray)
		#gray = cv2.equalizeHist(gray)
		#gray = cv2.GaussianBlur(gray,(5,5),0)    
    	for _ in xrange(num_bilateral):
    		gray = cv2.bilateralFilter(gray, d=9,
                                    sigmaColor=11,
                                    sigmaSpace=90)

    	for _ in xrange(num_down):
    		gray = cv2.pyrUp(gray)

    	#gray = cv2.cvtColor(gray, cv2.COLOR_RGB2GRAY)
    	gray = cv2.medianBlur(gray,15)


    	edge = cv2.adaptiveThreshold(gray,255,
    								cv2.ADAPTIVE_THRESH_MEAN_C,
    								cv2.THRESH_BINARY,
    								blockSize=9,
    								C=2)
    	output = cv2.bitwise_and(gray,edge)



    	canny = cv2.GaussianBlur(canny,(5,5),0)

    	#--------------------------------------------------------
    	# canny hough
    	low_threshold = 100
    	high_threshold = 200
    	canny=cv2.Canny(original	,low_threshold,high_threshold)
    	rho = 2
    	theta = np.pi/180
    	threshold = 20
    	min_line_length = 20
    	max_line_gap = 20
    	line_image = np.copy(original)*0 

    	lines = cv2.HoughLinesP(canny, rho, theta, threshold, np.array([]),
                            min_line_length, max_line_gap)
    	if (len(lines)):
    		for line in lines:
    			for x1,y1,x2,y2 in line:
    				cv2.line(line_image,(x1,y1),(x2,y2),(255,255,0),1)

    	cannyHough = cv2.addWeighted(output,0.8,line_image,1,0)

    	SafeZone = defineSafe(cannyHough,original)

    	#canny = cv2.Canny(output,low_threshold,high_threshold)
    	#output = np.hstack((original,output))
    	#output = np.hstack((output,canny))
    	output = np.hstack((original,cannyHough))
    	output = np.hstack((output,SafeZone))
    	cv2.imshow('frame', output)
    	if cv2.waitKey(1) & 0xFF == ord('q'):
        	break

cap.release()
cv2.destroyAllWindows()
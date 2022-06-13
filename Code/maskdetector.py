from cv2 import *
import os
import PySimpleGUI as sg
import time
from tkinter import font
from PIL import Image
import serial
import numpy as np

# Initialize the GUI
class Start:
	global arduino

	# Constructor
	def __init__(self, password="", people=0, maxpeople=0):

		dbool = False

		# Setting colour scheme for GUI
		sg.theme('Black')
		temp = sg.Window("")
		# Takes screen size so application is full screen
		w,h = sg.Window.get_screen_size()

		#Create the format for the GUI window
		layout = [[sg.Image(filename="logo.png", pad=((0,0),(h/4,0)))], 
				  [sg.Text('To enable Mask Detector, enter a 6 digit pin below.', font='Any 20', pad=((10,20), (10, 20)))], 
				  [sg.InputText('', background_color="white", text_color="black", pad=((0,5),(5,0)), size=(10,0), font='Any 25'), sg.Button("Submit", pad=((5,0),(5,0)), font='Any 17', key="Submit")],
				  [sg.Button("Door",pad=((0,10),(25,0)), font='Any 17', key="Door"), sg.Button("Exit", pad=((10,0),(25,0)), font='Any 17', key="Exit")]]
		#Initializes first window
		window = sg.Window('Mask Detector', layout, element_justification='c', no_titlebar=True, font='CenturyGothic', size=(w,h)).finalize()

		# Infinite loop for user input
		while True:
			# Checks continuosly for events such as button presses and values such as the passcode
			event, values = window.read(timeout=0)
			if event == "Exit":
				destroyAllWindows()
				exit()

			# Button for door control currently uses arduino and LED
			elif event == "Door" and arduino != None:
				if dbool == False:
					arduino.flushInput()
					arduino.write(b'1')
					arduino.flushInput()
					dbool = True
				else:
					arduino.flushInput()
					arduino.write(b'0')
					arduino.flushInput()
					dbool = False

			# Takes in 6 digit passcode for first time
			elif len(password) == 0:
				if event == "Submit" and len(values.get(1)) == 6 and values.get(1).isnumeric() == True:
					password = values.get(1)
					time.sleep(1)
					# Makes sure LED is off before continuing
					if arduino != None:
						arduino.write(b'0')
					window.Close()
					self.capacity(password, people)
			# Checks passcode if one already used
			else:
				if event == "Submit":
					if values.get(1) == password:
						window.Close()
						ImageCap(password, people, maxpeople)
					else:
						# Displays popup if user enters wrong passcode
						sg.popup("Incorrect Password!", auto_close_duration=2, auto_close=True, no_titlebar=True, modal=True)

	# Function for the maximum capacity of people in venue
	# On first opening of application opens new GUI window
	def capacity(self, password, people):
		sg.theme('Black')
		temp = sg.Window("")
		w,h = sg.Window.get_screen_size()

		layout = [[sg.Image(filename="logo.png", pad=((0,0),(h/3,0)))], 
				  [sg.Text('Please enter the maximum capacity of people for your venue.', font='Any 20', pad=((10,20), (10, 20)))], 
				  [sg.InputText('', background_color="white", text_color="black", pad=((0,5),(5,0)), size=(10,0), font='Any 25'), sg.Button("Submit", pad=((5,0),(5,0)), font='Any 17', key="Submit")]]
		window = sg.Window('Mask Detector', layout, element_justification='c', no_titlebar=True, font='CenturyGothic', size=(w,h)).finalize()

		while True:
			event, values = window.read(timeout=0)
			if event == "Submit":
				# Checks input is an integer
				if values.get(1).isnumeric() == True:
					window.close()
					# Goes to main class
					try:
						ImageCap(password, people, int(values.get(1)))
					# If no camera connected displays popup window with the error and sends user back to Start() class
					except cv2.error:
						sg.popup("A connection to a camera is required to use this application", auto_close_duration=3, auto_close=True, no_titlebar=True, modal=True)
						destroyAllWindows()
						Start()

# Main window when application is running
class ImageCap:
	global arduino

	#Constructor
	def __init__(self, password, people=0, maxpeople=0):

		# Starts connection with camera
		camera = VideoCapture(0)

		# Gets dimensions of camera in use
		cw = camera.get(CAP_PROP_FRAME_WIDTH)
		ch = camera.get(CAP_PROP_FRAME_HEIGHT)

		sg.theme('Black')
		temp = sg.Window("")
		w,h = sg.Window.get_screen_size()

		# Sets window format and displays camera on screen
		layout = [[sg.Text("Align eyes in the top box", pad=((0,0),(h/10,h/30)), font='Any 25')], 
				  [sg.Image(filename="logo.png", pad=((0,w/10),(0,0))), sg.Image(filename='', key='image'), sg.Text(f"People in shop: {people}", font='Any 17', pad=((w/10,0),(0,0)), key='counter'), sg.Button("-", key='minus')],
				  [sg.Text("Align mouth and nose in the bottom box", pad=((0,0),(h/30,0)), font='Any 25')],
				  [sg.Button("Take Picture", key="press", font='Any 17', pad=((0,0),(h/30,h/30)))],
				  [sg.InputText('', background_color="white", text_color="black", pad=((0,5),(5,0)), size=(10,0), font='Any 25'), sg.Submit(pad=((5,0),(5,0)), font='Any 17')]
				  ]
		window = sg.Window('Mask Detector', layout, element_justification='c', no_titlebar=True, font='CenturyGothic', size=(w,h)).finalize()
		
		# Main loop for user input
		while True:
			event, values = window.read(timeout=0)
			# Updates the camera with a new frame every loop
			ret, frame = camera.read()
			# Displays boxes for face alignment on the camera
			rectangle(frame, (int(2 * cw/3), int(3 * ch/4)), (int(cw/3), int(ch/4)), (0, 0, 0), 1)
			line(frame, (int(2 * cw/3), int(ch/2)), (int(cw/3), int(ch/2)), (0, 0, 0), 1)
			# Displays the current frame of the camera
			window['image'](data=imencode('.png', frame)[1].tobytes())

			# Checks if arduino is connected
			if arduino != None:
				# Reads from the ir sensor on arduino, i.e. detects hand movement
				arduino.flushInput()
				ir = arduino.read()
				# Flush buffer so python can handle arduino speed
				arduino.flushInput()
			else:
				ir = None

			# Checks if user pressed the button or used the IR sensor to take image
			if event == "press" or ir == b'\x00':
				# Splits the image into the 2 seperate boxes for better reading with the cascades
				top = frame[int(ch/4):int(ch/2), int(cw/3):int(2 * cw/3)]
				bottom = frame[int(ch/2):int(3 * ch/4), int(cw/3):int(2 * cw/3)]
				# Saves images to local directory
				imwrite("imagetestimages/top.png", top)
				imwrite("imagetestimages/bottom.png", bottom)
				break

			# Checks if passcode entered correctly
			elif event == "Submit":
				if values.get(1) == password:
					# Returns back to Start() class
					window.Close()
					Start(password, people, maxpeople)
				else:
					sg.popup("Incorrect Password!", auto_close_duration=2, auto_close=True, no_titlebar=True, modal=True)

			# Current method for reducing the displayed amount of people in the venue
			elif event == "minus" and people > 0:
				people -= 1
				window['counter'](f"People in shop: {people}")
				window.Refresh()

		window.Close()

		ImageRec(password, people, maxpeople)


class ImageRec:
	global arduino

	# Constructor
	def __init__(self,  password, people=0, maxpeople=0):

		# Reads in the previously saved images
		top = imread("imagetestimages/top.png")
		bottom = imread("imagetestimages/bottom.png")

		#img_gray = cvtColor(img, COLOR_BGR2GRAY)
		#img_gray = equalizeHist(img_gray)

		# Calls the eyes cascade to perform object detection on the top image
		eyes = CascadeClassifier("Cascades/haarcascade_eye_tree_eyeglasses.xml")
		eyes = eyes.detectMultiScale(top)

		# Calls the nose and mouth cascades on both top and bottom images
		nose1 = CascadeClassifier("Cascades/haarcascade_mcs_nose.xml")
		nose = nose1.detectMultiScale(bottom)
		nose_error = nose1.detectMultiScale(top)

		mouth1 = CascadeClassifier("Cascades/haarcascade_mcs_mouth.xml")
		mouth = mouth1.detectMultiScale(bottom)
		mouth_error = mouth1.detectMultiScale(top)

		mask = False

		detection = ""

		# Runs a loop through all detected coordinates for eyes in the top image
		for (x2,y2,w2,h2) in eyes:
			# Uses x,y coordinates and the width and height to find the opposing corner to the box
			x2s, y2s = x2+w2, y2+h2
			# Displays boxes using the coordinates detected for eyes
			rectangle(top, (x2, y2), (x2s, y2s), (0, 0, 255), 1)
			mask = True

		# Loop for displaying boxes on mouth and nose if found in the top image
		for (x5,y5,w5,h5),(x6,y6,w6,h6) in zip(nose_error, mouth_error):
			x5s, y5s = x5+w5, y5+h5
			rectangle(bottom, (x5, y5), (x5s, y5s), (0, 255, 0), 1)
			if len(nose_error) > 0:
				mask = False
				detection = "Make sure your nose and mouth are below the horizontal line in the box."

			x6s, y6s = x6+w6, y6+h6
			rectangle(bottom, (x6, y6), (x6s, y6s), (255, 0, 0), 1)
			if len(mouth_error) > 0:
				mask = False
				detection = "Make sure your nose and mouth are below the horizontal line in the box."

		# Loop for displaying boxes on mouth and nose if found in the bottom image
		for (x3,y3,w3,h3) in nose:
			x3s, y3s = x3+w3, y3+h3
			rectangle(bottom, (x3, y3), (x3s, y3s), (0, 255, 0), 1)
			mask = False
			detection = "An exposed nose was detected. Make sure your mask is on properly."

		for (x4,y4,w4,h4) in mouth:
			x4s, y4s = x4+w4, y4+h4
			rectangle(bottom, (x4, y4), (x4s, y4s), (255, 0, 0), 1)
			mask = False
			detection = "No mask was detected. Please put on a mask."

		# Rewrites over the preivously saved images
		imwrite("imagetestimages/top.png", top)
		imwrite("imagetestimages/bottom.png", bottom)

		# Until ine 256 code taken from stack overflow can be found here: https://stackoverflow.com/questions/10657383/stitching-photos-together
		# Opens newly saved images
		topim = Image.open("imagetestimages/top.png")
		bottomim = Image.open("imagetestimages/bottom.png")

		# Finds the dimensions of both images
		(width1, height1) = topim.size
		(width2, height2) = bottomim.size

		# Stitches the 2 images together, top and bottom using the dimensions taken
		stitched = Image.new('RGB', (topim.width, topim.height + bottomim.height))
		stitched.paste(topim, (0, 0))
		stitched.paste(bottomim, (0, topim.height))

		# Saves the new image
		stitched.save('imagetestimages/full.png')

		# Checks if mask was detected or not
		if mask == True:
			# Checks if maximum occupancy of the venue has been reached
			if people < maxpeople:
				# If maximum not reached add 1 person to the current occupancy
				people+=1
				detection = "Mask detected"
				# If arduino connected activate the LED
				if arduino != None:
					arduino.write(b'1')
			else:
				detection = "Apologies, maximum capacity of people in the venue reached"

		elif mask == False:
			if detection == "":
				detection = "No mask detected"

		sg.theme('Black')
		temp = sg.Window("")
		w,h = sg.Window.get_screen_size()

		# Format for GUI and diplays the stitched image with boxes
		layout = [[sg.Image(filename="logo.png", pad=((0,0),(h/20,h/20)))],
				  [sg.Image(filename="imagetestimages/full.png")],
				  [sg.Text(detection, font='Any 25', pad=((0,0),(h/20,h/20)))]]
		window = sg.Window('Mask Detector', layout, element_justification='c', keep_on_top=True, titlebar_background_color='black', titlebar_text_color='black', disable_minimize=True, disable_close=True, font='CenturyGothic', size=(w,h)).finalize()
		
		# Halts the program for 5 seconds in order to give user time to react to the detection
		time.sleep(5)
		# Deletes all previously saved images from the local directory
		os.remove("imagetestimages/top.png")
		os.remove("imagetestimages/bottom.png")
		os.remove("imagetestimages/full.png")

		# If arduino connected turn off LED
		if arduino != None:
			arduino.write(b'0')

		# Close current GUI window and return to main window
		window.Close()
		ImageCap(password, people, maxpeople)

# Tries to make connection with arduino
# Starts the program
sg.theme('Black')
temp = sg.Window("")
w,h = sg.Window.get_screen_size()
window = sg.Window('', [[]], no_titlebar=True, size=(w,h)).finalize()

try:
	arduino = serial.Serial('com5', 9600)
	Start()
except:
	arduino = None
	Start()
import folium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import os
import numpy as np
import cv2
from tqdm import tqdm




#for t in time: 
def findTimeDifference(data): #Used to find difference in times for interpGen
	maxTime = data[0]["segments"][0][2]
	minTime = data[0]["segments"][0][2]
	for dicti in data:
		for coord in dicti["segments"]:
			if coord[2] > maxTime:
				maxTime = coord[2]
			if coord[2] < minTime:
				minTime = coord[2]
	print("min: ", minTime, " - max: ", maxTime)
	return [int(maxTime-minTime), minTime, maxTime]


def interpGen(data): #Changes data from normal segment format to frame-by-frame format
	
	output = []
	timeDifference = findTimeDifference(data) #Finds difference in maximum and minimum time. Times must be positive. 
	dataLength = timeDifference[0]
	frameRate = 20 #FRAMES PER SECOND
	minTime = timeDifference[1]
	maxTime = timeDifference[2]
	timeArr = []
	t = minTime
	while t < maxTime:
		timeArr.append(t)
		t = round(t + 1/frameRate,5)

	for time in tqdm(timeArr): #loops through each frame (time)
		frame = []		#create an array for the coords for this frame
		for dicti in data[0:500]: #loops through each dictionary in the input data
			arr = dicti["segments"] 
			for i in range(1, len(arr)): #loops through each dictionary entry until it finds the coord at the specified time
				previousCoord = arr[i-1]
				currentCoord = arr[i]
				if previousCoord[2] <= time and currentCoord[2] >= time: #In case there's no exact match for the time, it will interpolate
					if currentCoord[2] == time:	#exact match
						frame.append({"id":dicti["id"],"time":time,"color":dicti["color"],"coords":currentCoord}) 	#add coords to this frame
					else:	#non-exact match. 
						if (currentCoord[2]-previousCoord[2]) != 0:
							ratio = (time-previousCoord[2])/(currentCoord[2]-previousCoord[2])
						else:
							ratio = 0
							print("DIVIDE BY ZERO")
						#interpolating lat/lon
						newLon = previousCoord[0]+(currentCoord[0]-previousCoord[0])*ratio
						newLat = previousCoord[1]+(currentCoord[1]-previousCoord[1])*ratio
						originalTime = currentCoord[2]	#Time shouldn't be required, but I'm including it for bug testing
						frame.append({"id":dicti["id"],"time":time,"color":dicti["color"],"coords":[newLon,newLat,originalTime]}) #add a dictionary for this coord
		output.append(frame)

	json.dump(output, open('output_data.json','wt'), sort_keys=True, indent=4, separators=(',', ': '))


def foliumGeneration(frameData): #generates the folium data

	mapCenter = [33.7, -84.4]
	#Create folium files
	#m = folium.Map(location=[33.7,-84.4])


	#m = folium.Map(location=[mapCenter[0],mapCenter[1]])
	
	m =	folium.Map(location=[mapCenter[0], mapCenter[1]], zoom_start=12,
       tiles='https://api.mapbox.com/styles/v1/samsonbaskin/ckcf0m9xw1g711iq8e2re1yew/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1Ijoic2Ftc29uYmFza2luIiwiYSI6ImNqYnFyMTA3eTA3NWQyd3I2NHVibTdndTYifQ.OndsKFSRgSnU3hfCKPOX7A',
       attr='mapbox')
	svgFile = open("iconTest.svg")
	style = svgFile.read()
	i = 0
	for frame in tqdm(frameData):
		i = i + 1
		#m = folium.Map(location=[mapCenter[0],mapCenter[1]])
		m =	folium.Map(location=[mapCenter[0], mapCenter[1]], zoom_start=12,
	       tiles='https://api.mapbox.com/styles/v1/samsonbaskin/ckcf0m9xw1g711iq8e2re1yew/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1Ijoic2Ftc29uYmFza2luIiwiYSI6ImNqYnFyMTA3eTA3NWQyd3I2NHVibTdndTYifQ.OndsKFSRgSnU3hfCKPOX7A',
	       attr='mapbox')		
		for entry in frame:
			if i < 200:
				coord = entry["coords"]
				folium.Marker([coord[1],coord[0]], icon=folium.DivIcon(icon_size=(10,10),html=style)).add_to(m)
				if i < 10:
					num = "000" + str(i)
				elif i < 100 and i >= 10:
					num = "00" + str(i)
				elif i < 1000 and i >= 100:
					num = "0" + str(i)
				else:
					num = str(i)

				fileName = 'htmlFrames/foliumTest'+ num +'.html'
				m.save(fileName)

def screenshotGeneration():
	fileCount = len([name for name in os.listdir('htmlFrames')])
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	browser = webdriver.Chrome(options=chrome_options)
	browser = webdriver.Chrome()
	browser.set_window_size(1080,720)

	for i in tqdm(range(100,200)):#fileCount):#REPLACE WITH FILECOUNT

		if i < 10:
			num = "000" + str(i)
		elif i < 100 and i >= 10:
			num = "00" + str(i)
		elif i < 1000 and i >= 100:
			num = "0" + str(i)
		else:
			num = str(i)
		tmpurl = 'htmlFrames/foliumTest'+num+'.html'


		browser.get(tmpurl)

		picName = 'frames/map'+num+'.png'
		browser.save_screenshot(picName)
	browser.quit()


def videoGeneration(): #uses opencv to convert frames into a video

 
	img_array = []
	for filename in sorted(os.listdir('frames')):
		print(filename)

		if filename != '.DS_Store':
			newName = 'frames/'+filename
			img = cv2.imread(newName)
			height, width, layers = img.shape
			size = (width,height)
			img_array.append(img)
	 
	out = cv2.VideoWriter('project.mp4',cv2.VideoWriter_fourcc(*'mp4v'), 20, size)
	#out = cv2.VideoWriter('output.mp4',0x7634706d , .0, (640,480))
	 
	for i in range(len(img_array)):
	    out.write(img_array[i])
	out.release()


inputData = json.load(open('input_data_big.json','rt'))
interpGen(inputData)
frameData = json.load(open('output_data.json','rt'))
foliumGeneration(frameData)
screenshotGeneration()
videoGeneration()

import spacy
import requests
import os
from tkinter import *
import datetime
from dateutil import parser

wd = os.getcwd()
os.chdir(wd)


API_keys = [key for key in open("keys.txt").read().split('\n')]   # non-public keys

## insert API keys here if you want to run my code
apiW = API_keys[0]  # (WeatherAPI)
apiT = API_keys[1]  # (Google Cloud API)
##

bot = spacy.load("en_core_web_md")

# list of tuples (questions, theme)
Questions_Theme_Tuples = []

# minimum similarity in order for the bot to answer the question
q_match_threshold = 0.85

# chosen theme/bot  = argmax Q.similarity(question) => + verification du seuil minimum



def analysis(question):
	question = bot(question)
	qfiles = [f for f in os.listdir(wd) if f.endswith(".txt")]  # corpus filenames
	corresponding_theme = "weather"  # theme associated to the question, weather by default
	maxsim = 0  # highest found question similarity

	for Q_file in qfiles:
		qlist = []
		theme = Q_file[:len(Q_file) - 4]
		data = open(Q_file).read()

		for line in data.split('\n'):
			Q = bot(line)
			nsim = Q.similarity(question)
			if nsim > maxsim:
				maxsim = nsim
				corresponding_theme = theme
			qlist.append(Q)
		Questions_Theme_Tuples.append((qlist, theme))

	if maxsim >= q_match_threshold:
		if corresponding_theme == "weather":
			cbot = Chatbot(corresponding_theme)
			
		elif corresponding_theme == "time":
			cbot = Chatbot(corresponding_theme)
		
	else: 
		return "There was an issue with your request, please try rephrasing your question."
	
	return cbot.answer(question)
	
def analysis2(question):  # doesn't read the files again
	question = bot(question)
	maxsim = 0
	corresponding_theme = "weather"

	for qlist, thm in Questions_Theme_Tuples:
		for Q in qlist:
			nsim = Q.similarity(question)
			if nsim > maxsim:
				maxsim = nsim
				corresponding_theme = thm

	if maxsim >= q_match_threshold:
		if corresponding_theme == "weather":
			cbot = Chatbot(corresponding_theme)

		elif corresponding_theme == "time":
			cbot = Chatbot(corresponding_theme)
			
	else:
		return "There was an issue with your request, please try rephrasing your question."
	
	return cbot.answer(question)

class Chatbot():

	def __init__(self, mode):
		self.mode = mode
		self.Q_list = [l for l, t in Questions_Theme_Tuples if t == mode]


	def get_weather(self, city_name):  # finds the current weather for the concerned city
		api_url = "http://api.openweathermap.org/data/2.5/weather?q={}&appid={}".format(city_name, apiW)

		response = requests.get(api_url)
		response_dict = response.json()

		try:
			weather = response_dict["weather"][0]["description"]  # extracts the weather information
		except KeyError:
			return "Sorry, I didn't get the name of the city or do not have any data concerning it."

		if response.status_code == 200:
			return weather
		else:
			print('[!] HTTP {0} calling [{1}]'.format(response.status_code, api_url))
			return None


	def get_time(self, city_name):  # finds the current time in the concerned city

		# getting the coordinates of the city
		geo_url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&sensor=false&key={}".format(city_name, apiT)
		geo = requests.get(geo_url)
		geo_dict = geo.json()
		if geo.status_code != 200:
			print('[!] HTTP {0} calling [{1}]'.format(response.status_code, geo_url))
			return None
		print(geo_dict)
		try:
			lat = geo_dict["results"][0]["geometry"]["location"]["lat"]  # extracts the latitude of the city
			lng = geo_dict["results"][0]["geometry"]["location"]["lng"]    # extracts the longitude of the city
		except KeyError:
			print("1")

		# getting the timezone of the city
		timezone_url = "https://maps.googleapis.com/maps/api/timezone/json?location={},{}&timestamp=1331161200&sensor=false&key={}".format(lat, lng, apiT)
		timezone = requests.get(timezone_url)
		timezone_dict = timezone.json()
		if timezone.status_code != 200:
			print('[!] HTTP {0} calling [{1}]'.format(response.status_code, timezone_url))
			return None
		print(timezone_dict)
		try:
			tz = timezone_dict["timeZoneId"]
			tz = tz.split('/')
			print(tz)
		except KeyError:
			print("2")

		# getting the time in the given timezone
		time_url = "http://worldtimeapi.org/api/timezone/{}/{}".format(tz[0], tz[1])
		time = requests.get(time_url)
		time_dict = time.json()
		dt = time_dict["utc_datetime"]
		offset = time_dict["utc_offset"]
		dtime = parser.parse(dt)

		return str(dtime.hour + int(offset[1:3])) + "h " + str(dtime.minute) + "min " + str(dtime.second) + "s"

	def answer(self, question):
			
		for ent in question.ents:  # question tagging
			if ent.label_ == "GPE":  # found localization
				city = ent.text
				break
			else:
				return ("Sorry, I didn't get the name of the city or do not have any data concerning it.")

		if self.mode == "weather":
			response = self.get_weather(city)
			if response != None:
				return ("The weather in " + city + " is currently : " + response)
	
		elif self.mode == "time":
			response = self.get_time(city)
			if response != None:
				return ("It is currently " + response + " in " + city)	
					
		return ("Sorry, I didn't understand your question or it does not correspond to my intended task.")


# ----- GUI -----

UI = Tk()
UI.title("Weather & Time Chatbot - Arthur Jean-Joseph")
msg = Label(UI,text = "Ask for the time or weather in any city !")
msg.pack()
write = Text(UI,width = 100, height = 30)
write.pack()
res = Label(UI, text = "Your answer will be displayed here", height = 10)
res.pack()

def GUI_analysis():
	text = write.get("1.0","end-1c")
	if text != "":
		if Questions_Theme_Tuples == []:
			result = analysis(text)
		else:
			result = analysis2(text)
		res.config(text = result)

confirm = Button(UI, width = 50,text = "Ask", command = GUI_analysis)
confirm.pack()

UI.mainloop()

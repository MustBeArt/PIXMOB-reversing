import serial
import time

ser = serial.Serial(port = "/dev/ttyUSB0")

def command_pixmob(green, red, blue, mode, chance):
	command ="AT+GAPSETADVDATA="+insert_flags()+insert_uuid_header()+insert_clap_mode()+insert_color_data(green, red, blue)+insert_mode_chance(mode, chance)+insert_nine_bytes_data()+insert_name()
	return command

def insert_flags():
	return "02-01-06"
 
def insert_uuid_header():
	return "-11-07-EE"

def insert_clap_mode():
	return "-00"
	#00 for clap mode off
	#01 for clap mode on

def insert_color_data(green, red, blue):
	field = ""	
	field = "-"+str(green)+"-"+str(red)+"-"+str(blue)+"-"
	return field

def insert_mode_chance(mode, chance):
	if mode == "solid" and chance == 100:
		return "00-07-"
	if mode == "solid" and chance == 50:
		return "03-07-"
	if mode == "solid" and chance == 10:
		return "06-07-"

	if mode == "pulse" and chance == 100:
		return "10-12-"
	if mode == "pulse" and chance == 50:
		return "13-12-"
	if mode == "pulse" and chance == 10:
		return "16-12-"

	if mode == "strobe" and chance == 100:
		return "00-09-"
	if mode == "strobe" and chance == 50:
		return "03-09-"
	if mode == "strobe" and chance == 10:
		return "06-09-"

	
	if mode == "question" and chance == 100:
		return "00-0F-"
	if mode == "question" and chance == 50:
		return "03-0F-"
	if mode == "question" and chance == 10:
		return "06-0F-"


def insert_nine_bytes_data():
	return "00-00-00-00-00-00-00-00-00-"

def insert_name():
	return "04-09-4D-4F-42"


for a in range(0, 5):
	time.sleep(.5)	
	#by_your_command = command_friend(0x19DC, 0x8F34060000000000B03E, "command")
	#green, red, blue, mode, chance
	by_your_command = command_pixmob(00,00,00, "question", 100)
	print by_your_command
	ser.write(by_your_command+"\r\n")

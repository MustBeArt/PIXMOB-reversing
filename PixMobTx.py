import serial
import time

#This is the serial port that the BlueFruit LE Friend was found on my computer
ser = serial.Serial(port = "/dev/ttyUSB0")

#This defines the AT command that is sent to the BlueFruit LE Friend for transmission. 
#The AT command function is built up from multiple smaller function calls.
#Each smaller function call corresponds to a field in the Bluetooth Low Energy advertising packet. 
def command_pixmob(green, red, blue, mode, chance):
	command ="AT+GAPSETADVDATA="+insert_flags()+insert_uuid_header()+insert_clap_mode()+insert_color_data(green, red, blue)+insert_mode_chance(mode, chance)+insert_nine_bytes_data()+insert_name()
	return command

#This field sets the capabilities of the transmitting device (BlueFruit LE Friend)
def insert_flags():
	return "02-01-06"

#This field is the header of the packet.
#11 is the length, 07 is the value that means 128 bit service class ID,
# and the EE seems to be constant for MOB devices. 
def insert_uuid_header():
	return "-11-07-EE"

#PixMob bracelets can be configured to respond to clapping of hands
#(AI) make this an argument in command_pixmob()
def insert_clap_mode():
	return "-00"
	#00 for clap mode off
	#01 for clap mode on

#This field sets the LED colors.
#(AI) I think there's a better way to do this. Could use a rework. 
def insert_color_data(green, red, blue):
	field = ""	
	field = "-"+str(green)+"-"+str(red)+"-"+str(blue)+"-"
	return field

#Mode is a value that commands the PixMob LEDs to be solid, pulsing, or strobing.  
#Chance makes a large crowd of PixMob wearables change behavior in different ways.
#When set to 100, that means commands that change the PixMobs behavior are paid attention to
#100 percent of the time. All bracelets change at once. 
#When 50, there's a 50% chance that the bracelet visual behavior will change with each
#received packet.
#When 10, there's a 10% chance that the bracelet visual behavior will change with each
#received packet.
#In general, many advertising packets are sent out. A 10% chance doesn't necessarily mean that only 
#10% of the PixMobs will ever change. It means that 10% chance of that command taking effect for that
#particular received packet. 
#Over time, a 10% value means the crowd of PixMobs slowly change. 50% means that they
#change faster, but still not all at once. 
#100% means that they change behavior with first received packet. This will look very much like
#they are all changing simultaneously.  
#Mode is a value that indicates whether the PixMob LEDs are solid, pulsing, or strobing. 
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

#Not sure what these are for. They might be there becuase the
#128 bit service ID has to be 16 bytes long. In other words, padding. 
def insert_nine_bytes_data():
	return "00-00-00-00-00-00-00-00-00-"

#This makes the local name of the transmitter be "MOB".
def insert_name():
	return "04-09-4D-4F-42"

#Construct the bluetooth low energy advertising packet in the form of an AT command. 
#This is how the BlueFruit LE Friend sends out bluetooth LE packets.
#The loop range is set to however many repetitions of the AT command one wants to be
#sent out. There's a short delay between each one.  
for a in range(0, 5):
	time.sleep(.5)	
	#arguments are green, red, blue, mode, chance
	by_your_command = command_pixmob(00,99,00, "solid", 100)
	print by_your_command
	ser.write(by_your_command+"\r\n")

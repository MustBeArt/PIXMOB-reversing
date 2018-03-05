import serial
import time

#This defines the AT command that is sent to the BlueFruit LE Friend for transmission. 
#The AT command function is built up from multiple smaller function calls.
#Each smaller function call corresponds to a field in the Bluetooth Low Energy advertising packet. 
def command_pixmob(red, green, blue, attack, sustain, release, chance, clap, oneshot, group):
	command ="AT+GAPSETADVDATA="+insert_manufacturer_header()+insert_pixmob_flags(clap, oneshot)+insert_color_data(red, green, blue)+insert_asr_chance(attack, sustain, release, chance)+insert_group(group)+insert_name()
	return command

#This field is the header of the packet.
#09 is the length, FF is the value that means manufacturer-specific data,
# and the EE is the opcode for "blink with group and envelope". 
def insert_manufacturer_header():
	return "-09-FF-EE"

#PixMob bracelets can be configured to respond to clapping of hands or to ignore identical commands
#FIXME there is also a multicolor mode, controlled by flags & 0x2, but it needs a different encoding
def insert_pixmob_flags(clap, oneshot):
	return "-" + ("1" if oneshot else "0") + ("1" if clap else "0")

#This field sets the LED colors.
#(AI) I think there's a better way to do this. Could use a rework. 
def insert_color_data(red, green, blue):
	field = "-%0.2x-%0.2x-%0.2x" % (green, red, blue)
	return field

#Attack, sustain and release control how long the fade-in, fully lit and fade-out parts of a light pulse last.
#When sustain=7 and release=0, the bracelet fades in and stays lit indefinitely.
#Chance makes a large crowd of PixMob wearables change behavior in different ways.
#Valid values are 100, 85, 65, 50, 30, 15, 10 and 5.
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
def insert_asr_chance(attack, sustain, release, chance):
	chances = {
		100: 0,
		85: 1,
		65: 2,
		50: 3,
		30: 4,
		15: 5,
		10: 6,
		5: 7,
	}
	
	return "-%0.1x%0.1x-%0.1x%0.1x" % (attack >> 1, chances[chance] | ((attack & 1) << 3) , release >> 1, sustain | ((release & 1) << 3))

#Group ID, used to target preprogrammed groups of bracelets.
#When 0, all bracelets are targeted.
#When between 1 and 31, only bracelets with that group ID are targeted.
#The high 3 bits are ignored, so values over 31 are invalid.
#(Bit 5 isn't actually ignored, it's a flag, but its exact meaning is currently unknown.)
def insert_group(group):
	return "-%0.2x" % group

#This makes the local name of the transmitter be "MOB".
def insert_name():
	return "-04-09-4D-4F-42"

def main():
	#This is the serial port that the BlueFruit LE Friend was found on my computer
	ser = serial.Serial(port = "/dev/ttyUSB0")

	#Construct the bluetooth low energy advertising packet in the form of an AT command. 
	#This is how the BlueFruit LE Friend sends out bluetooth LE packets.
	#The loop range is set to however many repetitions of the AT command one wants to be
	#sent out. There's a short delay between each one.  
	for a in range(0, 5):
		time.sleep(.5)	
		#arguments are red, green, blue, attack, sustain, release, chance, clap, oneshot, group
		by_your_command = command_pixmob(0x99,0,0, 0,7,0, 100, False, False, 0)
		print by_your_command
		ser.write(by_your_command+"\r\n")

if __name__ == "__main__":
	main()

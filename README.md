# PIXMOB Bluetooth LE LED Bracelet Reverse Engineering Results
2017-09-04 W5NYV and KB5MU
2018-01-05 Googulator

Based on testing with the iOS PIXMOB app, the Adafruit Bluefruit LE Android App, a Bluefruit LE Friend, nRF Connect Android app, and a PIXMOB BLE bracelet.

## Function Summary

The functions in the iOS app appear pretty simple. There's manual mode and automatic mode. In automatic mode, the iOS app listens to sound (either from the microphone or from music it is playing from a playlist) and sends color commands to the bracelet on audio peaks. It's probably a little more complicated than that, but it appears that the automatic mode uses mostly the same commands over the air that the manual mode does, so we will concentrate on the manual mode.

In manual mode, there are some mode switches and a big spectrum color picker. The basic behavior is that the iOS device sends a command to the bracelet whenever there's a finger (tapping or holding) on the color picker. The mode switches are encoded in the command and interpreted by the bracelet.

The first set of mode switches is marked EFFECT and has three options:

    SOLID	= the bracelet displays the color continuously
    PULSE	= the bracelet fades smoothly from black to the color and back to black
    STROBE	= the bracelet blinks rapidly between black and the color

The second set of mode switches is marked CHANCE and has three options:

    100%	= the bracelet acts on every command it receives
    50%		= the bracelet has a 50% chance of acting on each command it receives
    10%		= the bracelet has a 10% chance of acting on each command it receives

The last mode switch is an on/off toggle marked CLAP.

    Enabled	= the bracelet delays acting on the command until it detects a sudden movement
    Disabled	= the bracelet acts on the command immediately

The iOS app always seems to send commands with the color value set to black whenever no finger is on the color picker. Thus, the bracelet acts as if each tap or hold on the color picker is a complete action, interpreted in real time, with no persistent state. However, testing with synthetic commands shows that the bracelet does have some state. If a solid color command is followed immediately by a strobe color command, for instance, the strobe is superimposed upon the solid color. It is unclear whether this is part of an extended feature set, or simply an accident of implementation.

The iOS app also detects inactivity after a few minutes with no fingers on the color picker, and falls back to a simple rotation of solid color commands, using the solid colors chosen for automatic mode.

If the iOS app is not active on the screen of the iOS device, the bracelet quickly detects the lack of any commands and goes dark to save battery power.

## Protocol Summary

Each command from the iOS app to the bracelet is encoded as a Bluetooth LE advertisement. This enables one iOS app to command an arbitrary number of bracelets within range. There is no acknowledgement from the bracelet, and no obvious security to prevent multiple iOS devices (or spoofed controllers) from trying to command the bracelets at the same time.

Advertisements contain three fields: Flags, 128-bit Service Class UUIDs, and Local Name. The iOS app always sends them in that order.

### Flags Field

The Flags field is used as normal, as far as I can tell. The iPhone is a full Bluetooth device with all the capabilities, and it identifies as such in the Flags field.
> 02 01 1a

Testing with a BLE-only device, the bracelets were happy to respond even with a different Flags field (required by the test equipment).
> 02 01 ??

### Local Name Field

The Local Name field is be set to "MOB".
> 04 09 4d 4f 42

### 128-bit Service Class UUIDs Field

The 128-bit Service Class UUIDs field is being abused as a general purpose data packet, as follows:

    Byte 0		always EE
    Byte 1		Flags field:
    				Bit 1: Clap mode, delay execution until motion is detected
				Bit 2: Multicolor mode, randomly select from a pool of colors at every execution
				Bit 5: One-shot mode, ignore further identical commands after executing once
			Others unknown/ignored
    Byte 2		Green component of color data (00 is off)
    Byte 3		Red component of color data (00 is off)
    Byte 4		Blue component of color data (00 is off)
    Byte 5	Chance and attack
    		Bit 0-2: chance of executing this command, per https://www.youtube.com/watch?v=_QfQP7jl0Ek
    			0: 100%
			1: 85%
			2: 65%
			3: 50%
			4: 30%
			5: 15%
			6: 10%
			7: 5%
		Bit 3: unknown/ignored
		Bit 4-5: attack
			0: instant
			1: fast
			2: medium
			3: slow
		Bit 6-7: unknown/ignored
    Byte 6:	Sustain and release
		Bit 0-2: sustain
    			0: none (release immediately follows attack)
			1-6: increasingly longer intervals
			7: until overridden by another command (when used with release=0, otherwise identical to 6)
		Bit 3: unknown, apparently ignored, but used by iOS app
		Bit 4-5: release, encoding identical to attack
    Byte 7	Group, uses only the lower 5 bits (3 high bits ignored). 0x00 = all bracelets, 0x01-0x1f: bracelets in specified group
    Byte 8-15	unknown/ignored
    
The iOS app uses the following attack/sustain/release combinations:
Solid:  0/7/0
Strobe: 0/1/0, bit 3 of byte 6 set
Pulse:  2/3/2 (1/2/1 in earlier iOS app versions)

Automatic mode sends 0/7/0 at the beginning of each pulse to light up the bracelet, and 1/7/0 with black color and bit 3 of byte 6 set to shut it down at the end of the pulse. Earlier iOS app versions used 0/7/0 instead of 1/7/0 for the shutdown packet.

The Group field is not used by the iOS app (it always uses 0x00 = all groups). It's apparently used by the professional PIXMOB Hub transmitter to address specific groups of bracelets. The group code is apparently preprogrammed into each bracelet, with my (Googulator's) bracelets all responding to 0x01.

In multicolor mode, the meaning of bytes 2-6 changes as follows:

    Byte 2: low 8 bits of the 12-bit color pool value (encoding unknown)
    Byte 3: Rest of color pool and attack
    	Bit 0-3: high 4 bits of the 12-bit color pool value
	Bit 4-5: attack (see above)
	Bit 6-7: unknown/ignored
    Byte 4: Sustain and release, same as byte 6 in single-color mode
    Byte 5: Chance, see above. Bit 3-7 unknown/ignored.
    Byte 6: unknown/ignored

As far as I can tell, there's no official sanction for using 128-bit Service Class UUIDs in this manner.

#### Example

The commonly used command to turn the bracelets off (R=0, G=0, B=0) is:

> ee 00 00 00 00 07 00 00 00 00 00 00 00 00 00 00


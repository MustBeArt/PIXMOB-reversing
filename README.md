# PIXMOB Bluetooth LE LED Bracelet Reverse Engineering Results

2017-09-04 W5NYV and KB5MU

2018-01-05 Googulator

Based on reverse-engineering the bracelet's firmware, and testing with the iOS PIXMOB app, the Adafruit Bluefruit LE Android App, a Bluefruit LE Friend, nRF Connect Android app, and a PIXMOB BLE bracelet.

## Function Summary

The functions in the iOS app appear pretty simple. There's manual mode and automatic mode. In automatic mode, the iOS app listens to sound (either from the microphone or from music it is playing from a playlist) and sends color commands to the bracelet on audio peaks. It's probably a little more complicated than that, but it appears that the automatic mode uses mostly the same commands over the air that the manual mode does, so we will concentrate on the manual mode.

In manual mode, there are some mode switches and a big spectrum color picker. The basic behavior is that the iOS device sends a command to the bracelet whenever there's a finger (tapping or holding) on the color picker. The mode switches are encoded in the command and interpreted by the bracelet.

The first set of mode switches is marked EFFECT and has three options:

    SOLID	= the bracelet displays the color continuously
    PULSE	= the bracelet fades smoothly from black to the color and back to black
    STROBE	= the bracelet blinks rapidly between black and the color

The second set of mode switches is marked CHANCE and has three options:

    100%	= the bracelet acts on every command it receives
    50%	= the bracelet has a 50% chance of acting on each command it receives
    10%	= the bracelet has a 10% chance of acting on each command it receives

The last mode switch is an on/off toggle marked CLAP.

    Enabled		= the bracelet delays acting on the command until it detects a sudden movement
    Disabled	= the bracelet acts on the command immediately

The iOS app always seems to send commands with the color value set to black whenever no finger is on the color picker. Thus, the bracelet acts as if each tap or hold on the color picker is a complete action, interpreted in real time, with no persistent state. However, testing with synthetic commands shows that the bracelet does have some state. If a solid color command is followed immediately by a strobe color command, for instance, the strobe is superimposed upon the solid color. It is unclear whether this is part of an extended feature set, or simply an accident of implementation.

The iOS app also detects inactivity after a few minutes with no fingers on the color picker, and falls back to a simple rotation of solid color commands, using the solid colors chosen for automatic mode.

If the iOS app is not active on the screen of the iOS device, the bracelet quickly detects the lack of any commands and goes dark to save battery power.

## Protocol Summary

Each command from the iOS app to the bracelet is encoded as a Bluetooth LE advertisement. This enables one iOS app to command an arbitrary number of bracelets within range. There is no acknowledgement from the bracelet, and no obvious security to prevent multiple iOS devices (or spoofed controllers) from trying to command the bracelets at the same time.

Advertisements contain three fields: Flags, 128-bit Service Class UUIDs, and Local Name. The iOS app always sends them in that order.

### Flags Field

The Flags field is ignored by the bracelet if sent. No Flags field needs to be sent for the bracelets to respond.

### Local Name Field

The Local Name field needs to be set to a name beginning with one of the following prefixes: "BRO", "TRK", "REG", "SRV", "MOB", "SPK". Only the first 3 characters are checked, the rest are ignored.
> 04 09 4d 4f 42

### Manufacturer-specific field or 128-bit Service Class UUIDs Field

The manufacturer-specific field is used as a general purpose data packet, containing scripts made up of commands chained together. The Bluetooth 4.0 interpretation of this field is used (the entire field is data), rather than the Bluetooth 4.1 one (first two bytes are a manufacturer ID). The first command starts at the beginning of the field.
The first byte of every command is an opcode that identifies the type of command to run. Because not all devices can transmit arbitrary Bluetooth 4.0 manufacturer data commands (iOS, for example, can't), the bracelets alternatively allow using a field type of "128-bit Service Class UUIDs", interpreted the same as a manufacturer-specific field (with padding to 128-bit divisible size ignored).

The iOS app only uses one command, with opcode 0xEE, meaning "Light up in an RGB color with custom envelope if member of a group". The syntax of this command is as follows:

    Byte 0		always EE
    Byte 1		Flags field:
			Bit 1: Clap mode, delay execution until motion is detected
			Bit 2: Multicolor mode, select (randomly or sequentially) from a pool of colors at every execution
			Bit 5: One-shot mode, ignore further identical commands after executing once
			Others ignored
			If the whole field is set to 0x0f, set a color in the multicolor pool by index, or specify a base color to sustain between commands.
    Byte 2		Green component of color data (00 is off)
    Byte 3		Red component of color data (00 is off)
    Byte 4		Blue component of color data (00 is off)
    Byte 5		Chance and attack
			Bit 0-2: chance of executing this command, per https://www.youtube.com/watch?v=_QfQP7jl0Ek
				0: 100%
				1: 85%
				2: 65%
				3: 50%
				4: 30%
				5: 15%
				6: 10%
				7: 5%
			Bit 3-5: attack
				0: instant
				1: fastest
				2: faster
				3: fast
				4: medium
				5: slow
				6: slower
				7: slowest
			Bit 6-7: ignored
    Byte 6:		Sustain and release
			Bit 0-2: sustain
				0: none (release immediately follows attack)
				1-6: increasingly longer intervals
				7: until overridden by another command (when used with release=0, otherwise identical to 6)
			Bit 3-5: release, encoding identical to attack
			Bit 6-7: ignored
    Byte 7		Group and unknown flag
			Bit 0-4: Group, 0x00 = all bracelets, 0x01-0x1f: bracelets in specified group
			Bit 5: unknown flag, apparently related to color randomization in multicolor mode
			Bit 6-7: ignored

The difference between instant and fastest is imperceptible to the human eye, but a repeated "instant" command is a continuous light, while repeated "fastest" will blink instead.
    
The iOS app uses the following attack/sustain/release combinations:
Solid:  0/7/0
Strobe: 0/1/1
Pulse:  4/3/4 (2/2/2 in earlier iOS app versions)

Automatic mode sends 0/7/0 at the beginning of each pulse to light up the bracelet, and 2/7/1 with black color to shut it down at the end of the pulse. Earlier iOS app versions used 0/7/1 instead of 2/7/1 for the shutdown packet.

The Group field is not used by the iOS app (it always uses 0x00 = all groups). It's used by the professional PIXMOB Hub transmitter to address specific groups of bracelets. The group code can be programmed into each bracelet over the air using another command, with a default of 0x01. A group code of 0x00 will affect all bracelets.

In multicolor mode, the meaning of bytes 2-6 changes as follows:

    Byte 2:		Lower index limit and part of upper index limit
			Bit 0-3: lowest color index that may be selected
			Bit 4-5: lower 2 bits of highest color index that may be selected
			Bit 6-7: ignored
    Byte 3:		Upper index limit, random flag and attack
			Bit 0-1: higher 2 bits of the highest color index
			Bit 2: if set, pick a color randomly from the allowed indexes at every execution, otherwise cycle through them in sequence
			Bit 3-5: attack (see above)
			Bit 6-7: unknown/ignored
    Byte 4:		Sustain and release, same as byte 6 in single-color mode
    Byte 5:		Chance, see above. Bit 3-7 ignored.
    Byte 6:		ignored

When Flags is set to 0x0f, bytes 5 and 6 change meaning:

    Byte 5:		Index to write to, persistence and base color flag
			Bit 0-3: index to write to 
			Bit 4: if set, write the color in bytes 2-4 to RAM, if unset, write the color in RAM to NVRAM (?)
			Bit 5: if set, display this color continuously between commands (not sure if it still writes to RAM or NVRAM with this set)
			Bit 6-7: ignored
    Byte 6:		Meaning unknown, possibly ignored

This enables setting any of the 16 indexed colors, enabling custom color pools/sequences for multicolor mode.

As far as I can tell, there's no official sanction for using 128-bit Service Class UUIDs in this manner.

#### Example

The commonly used command to turn the bracelets off (R=0, G=0, B=0) is:

> ee 00 00 00 00 07 00 00


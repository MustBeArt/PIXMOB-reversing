# PIXMOB Bluetooth LE LED Bracelet Reverse Engineering Results
2017-09-04 W5NYV and KB5MU

Based on testing with the iOS PIXMOB app, the Adafruit Bluefruit LE Android App, a Bluefruit LE Friend, and a PIXMOB BLE bracelet.

## Function Summary

The functions in the iOS app appear pretty simple. There's manual mode and automatic mode. In automatic mode, the iOS app listens to sound (either from the microphone or from music it is playing from a playlist) and sends color commands to the bracelet on audio peaks. It's probably a little more complicated than that, but it appears that the automatic mode uses exactly the same commands over the air that the manual mode does, so we will concentrate on the manual mode.

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
    Disabled= the bracelet acts on the command immediately

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
    Byte 1		01 if Clap mode is enabled, 00 otherwise
    Byte 2		Green component of color data (00 is off)
    Byte 3		Red component of color data (00 is off)
    Byte 4		Blue component of color data (00 is off)
    Byte 5-6	Mode code, as follows:	   07 0x for Solid color
                                           12 1x for Pulsating color
                                           09 0x for Strobing color
                                           0F 0X for some unknown function
                Chance code, as follows:   xx x0 for 100% chance
                                           xx x3 for 50% chance
                                           xx x6 for 10% chance
    Byte 7-15	00 00 00 00 00 00 00 00 00

As far as I can tell, there's no official sanction for using 128-bit Service Class UUIDs in this manner.

The unknown function code 0F 0x may (or may not) be used to set what the bracelet will display when it is not receiving any commands, as a sort of default display.

#### Example

The commonly used command to turn the bracelets off (R=0, G=0, B=0) is:

> ee 00 00 00 00 07 00 00 00 00 00 00 00 00 00 00


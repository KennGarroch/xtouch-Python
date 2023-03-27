# XTouch Mini Python Library

Kenn Garroch March 2023

This simple library creates a class that represents the Behringer XTouch Mini 
USB midi controller in Python.

The eight knobs, their switches and LEDs are represented by a knob classe and
the 18 buttons (including A and B) and their LEDs are served by a button class.
The slider is simply represented by the slider class.

All of these are then gathered together into a single xTouch class to represent
the complete system.

## Installation

Pre-requisites are the [Mido](https://mido.readthedocs.io/en/latest/index.html) 
project and the RtMidi backend. Download and install with pip3 mido. The RtMidi 
backend will also need to be installed with [python-rtmidi](https://github.com/SpotlightKid/python-rtmidi)

## Quick test

Once installed, plug the XTouch into the USB and run:

python3 xtouch.py

from the command line (Terminal). If the Midi name is not simply X-TOUCH MINI 
then all attached controllers will be listed. If the X-Touch is in the list 
then copy the full name and paste it into the string at the top of the xtouch.py 
If the device is not there then check the connections.

As an example, the system on a Mac uses:

 `MIDIDEVICE="X-TOUCH MINI"`

whereas on a Raspberry Pi it is:

 `MIDIDEVICE="X-TOUCH MINI:X-TOUCH MINI 1 24:0"`

The demo code should be easy to follow. Press A (upper far right on XTouch) to
see the status of all the buttons and knobs. Press a few buttons and twist some
knobs to see them in action. The Stop button will exit the loop, the B button
resets all of the values, buttons states and LEDs.

## Classes

### xTouch

xTouch is the topmost class and aims to represent the whole system in one place.

As it is initialises, 18 buttons are created as an array xTouch.buttons[0 to 17].
These are mapped as:

- Buttons 0 to 7 - top row left to right up to the slider.
- Buttons 8 to 15 - top row left to right up to the slider.
- Button 16 is marked A or up.
- Button 17 is marked B or down.

Eight knobs are attached as xTouch.knobs[0 to 7] from left to right.

The slider is xTouch.slider

Built in functions include:

#### reset()

All buttons and knobs are set to 0 and their LEDs set to off.

#### showState()

This only works on a console but it clears the screen and then displays the time, 
the last incoming midi message, the last outbound CC and note messages. It then
lists the statuses of all the knobs and all the buttons with the last line
showing the value of the slider. 

Note that the slider value will be zero until the slider is actually moved.

### Button

Each button has its state represented by the button.button value with 1 for 
pressed and 0 for not pressed. Each also has a latch which is set to one on
the first press and release and then to 0 on the second. The latch also 
controls the state of the LED - on for latch=1.

#### reset()

The values of button and latch are cleared and the LED turned off when reset
is called.

#### setLED(n=0)

This is used by the led function to set the button's LED to on, flashing or off.

#### led(onOff=None)

If onOff is None (default) then the LED will be set to follow the state of the 
latch. Otherwise the LED will need to be controlled directly via setLED.

#### callback(message)

To allow for further expansion, the callback function can be replaced by an
external function with the inbound midi message being passed in. The callback
fires each time there is a midi event from the xTouch that applies to the button.

### knob

Knob objects represent the position of the rotary controllers, their push switches
and the state of the LEDs - these normally being tied to the position. The 
value of the knob starts at zero and is incremented and decremented as the knob
is rotated left and right. The XTouch is velocity sensitive to the rotation
rate so the faster the knob is twisted, the faster the value changes.

The max and min values of the knob.value are set with rotmax and rotmin with the
displayed LEDs being proportional to this value - so that the max right position
shows all the LEDs and the min left, none of them.

The knobs also support a button action when pressed. Like the button object, 
these have button=1 when the knob is being held down and 0 when it is up with
latch being used to capture press/release.

#### reset()

The value, button, latch and LED are all cleared when reset is called.

#### led(onOff=None, sef=None)

In normal use, LEDs follow the scaled value. This can be overridden with onOff.

#### rotcallback(message) buttoncallback(message)

The callback functions can be replaced to allow for expansion of the reactivity.

### Slider

The slider class supports the value of the slider position and a callback function.
One thing to note is that there is can be a large number of messages queue when
the slider is moved and the mido library can be slow to clear these.


## Notes

There are still a number of features to be sorted out - the various display
options of the knobs for example and the ability to flash the LEDs to allow
them to be used as indicators. These will likely be added as they become needed
by other projects.



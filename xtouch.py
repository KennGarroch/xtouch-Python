"""
Library to create an xTouch Mini object that allows it to be controlled 
and represent the current state.
Kenn Garroch 2023-03-09
"""

import mido
import os
import sys
import datetime

MIDIDEVICE="X-TOUCH MINI"
ROTMAX=11
ROTMIN=0
# Look up absolute knob number 0 to 7 to get the control numbers
KNOBS2KBL={
    0:{"control":16,"led":48,"button":32},
    1:{"control":17,"led":49,"button":33},
    2:{"control":18,"led":50,"button":34},
    3:{"control":19,"led":51,"button":35},
    4:{"control":20,"led":52,"button":36},
    5:{"control":21,"led":53,"button":37},
    6:{"control":22,"led":54,"button":38},
    7:{"control":23,"led":55,"button":39}
}
# For buttons, the LED is note_on with same note num 127=0, 0=off, 1=flash
BUTTON2N={
    0:{"note":89}, # Top left
    1:{"note":90},
    2:{"note":40},
    3:{"note":41},
    4:{"note":42},
    5:{"note":43},
    6:{"note":44},
    7:{"note":45},  # Top right
    8:{"note":87},  # Bottom left - MC
    9:{"note":88},
    10:{"note":91}, # <<
    11:{"note":92}, # >>
    12:{"note":86}, # Loop
    13:{"note":93}, # Stop    
    14:{"note":94}, # >
    15:{"note":95}, # Bottom right - Rec
    16:{"note":84}, # Right top - Layer A Up
    17:{"note":85}  # Right bottom - Layer B Down
}
SLIDER={"channel":8}

###########################################################################
#
# Knob Class
#
###########################################################################
class knob:
    # The min and max values of the rotation start with default but can be overidden
    rotmin=ROTMIN
    rotmax=ROTMAX
    knobID=0    # Set this to the knob CC in init - look up knob number in KNOBS2KBL
    buttonID=0  # Set this to the button CC in init - look up in KNOBS2KBL
    ledID=0     # Set this to the LED CC in init - look up knows2BL
    value=0     # A value between self.rotmin and self.rotmax
    button=0    # Set to 1 when the button is pressed
    latch=0     # Set to 1 on button press and to 0 on next press
    ledType=0   # 0 to light from left incrementally 0(off) to 11(all on)
                # 1 to light individual segments 0 to 11 
                # 2 to light segments to left and right - balance 1-5<6>7-11
                # 3 radiate from top centre both sides - balance vol 
                # 4 Balance start top, left and right
                # 10 to ignore messages and leave the led as it is or use onOff, seg
    
    def __init__(self,parent,knobNum):
        self.parent=parent
        if knobNum in KNOBS2KBL:
            self.knobID  = KNOBS2KBL[knobNum]["control"]
            self.buttonID= KNOBS2KBL[knobNum]["button"]
            self.ledID   = KNOBS2KBL[knobNum]["led"]
        else:
            raise
        self.reset()

    def reset(self):
        """ Reset everything to zero and turn the LED off """
        self.value=0
        self.button=0     
        self.latch=0
        self.led()

    def led(self,onOff=None,seg=None):
        """ 
            Use self.ledType and self.value. 
            Scale with self.rotmax-self.rotmin
            If onOff=None ignore it. If 1 then all on, if 0 then all off
            If seg=None ignore it. Otherwise it is a dict defining the display: TODO
        """
        pass
        if onOff==None:
            self.parent.msgCC.control=self.ledID
            self.parent.msgCC.channel=0
            # 1 to 11 (+32) are zero to all on = ledType=0
            # 17 to 22 (+32) is centre on radiating
            # 33 to 43 (+32) single leds left to right = ledType=1
            # 49 to 53 (+32) left hand side full to centre
            # 54 is top centre
            # 55 to 59 right hand side centre to right
            # Scale int(rotmax-rotmin)/11
            if self.ledType==0:
                offset=32
                scale=(self.rotmax-self.rotmin)/12
            elif self.ledType==1:
                offset=32+32
                scale=(self.rotmax-self.rotmin)/12
            elif self.ledType==2:
                offset=48+32
                scale=(self.rotmax-self.rotmin)/12

            self.parent.msgCC.value=offset+int(self.value/scale)
            self.parent.midiOut.send(self.parent.msgCC)

            #TODO onOff not None

    def midi(self,m):
        """ 
            Use the Message in m to see if this applies to this knob. If
            so, set the relevant value, button, latch led
        """
        if m.type=="note_on":
            if m.note==self.buttonID:   # We have a note and a match
                if m.velocity==127:
                    self.button=1
                    if self.latch==0:
                        self.latch=1
                    else: 
                        self.latch=0
                else:
                    self.button=0
                #self.led()
        if m.type=="control_change":
            if m.control==self.knobID:  # We have a knob and a match
                if m.value>64:
                    self.value-=(m.value-64)
                    if self.value<self.rotmin:
                        self.value=self.rotmin
                if m.value<10:
                    self.value+=m.value
                    if self.value>self.rotmax:
                        self.value=self.rotmax
        self.led()
        self.rotcallback(m)
        self.buttoncallback(m)

    def rotcallback(self,m):
        """ Replace this to add a callback on rotation changes """
        pass
    def buttoncallback(self,m):
        """ Replace this to add a callback on button change """
        pass

###########################################################################
#
# Slider Class
#
###########################################################################
class slider:
    value=0 # This is almost certainly incorrect. But until there is an event we can't know
    def __init__(self,parent):
        self.parent=parent
        self.channel=SLIDER["channel"]
    def callback(self,m):
        """ Replace this with alternative function to hook into changes """
        pass

    def midi(self,m):
        if m.type=="pitchwheel":
            self.value=m.pitch
            self.callback(m)

###########################################################################
#
# Button Class
#
###########################################################################
class button:
    name=""    # Use to name a button if required
    button=0   # Off 1=on - set on momentary press i.e. held down
    latch=0    # Set and cleared when button is pressed
    buttonID=0 # From BUTTON2N - this will be the note number of the button
    ledType=0  # 0=On/Off 1=flashing (when set to on), 2=Override no link to state

    def __init__(self,parent,n):
        self.parent=parent
        if n in BUTTON2N:
            self.buttonID=BUTTON2N[n]["note"]
            self.reset()
        else:
            raise

    def reset(self):
        self.button=0
        self.latch=0
        self.led()


    def setLED(self,n=0):
        """
            Set the LED according to the type
            n==1 for on, n==0 for off
            If n not specified or not 0/1 then off
        """
        if self.ledType==0:
            self.parent.msgNote.velocity=n*127
        elif self.ledType==1:
            self.parent.msgNote.velocity=n*2
        else:
            self.parent.msgNote.velocity=0
        self.parent.msgNote.note=self.buttonID
        self.parent.msgNote.channel=0
        self.parent.midiOut.send(self.parent.msgNote)

    def led(self,onOff=None):
        """
        Id onOff is None then set the LED to match the latch
        onOff=0 for off, onOff=1 for on, onOff=2 for flashing
        """
        if onOff==None:
            self.setLED(self.latch)
        elif onOff==1:
            self.setLED(1)
        else:
            self.setLED(0)

    def callback(self,message):
        """ 
            Override this to get different callback
            Always gets passed the current message
        """
        pass

    def midi(self,m):
        """
        React to the midi message in m
        """
        if m.type=="note_on":
            if m.note==self.buttonID:   # We have a note and a match
                if m.velocity==127:
                    self.button=1
                    if self.latch==0:
                        self.latch=1
                    else: 
                        self.latch=0
                else:
                    self.button=0
                self.led()
                self.callback(m)


###########################################################################
#
# xTouch Mini Class
#
###########################################################################
class xTouch:
    buttons  = []  # List of knobs 0 to 17
    knobs    = []  # List of knobs 0 to 7
    slider   = {}  # Will be a slider object

    msgCC    = mido.Message("control_change")
    msgNote  = mido.Message("note_on")
    msgPitch = mido.Message("pitchwheel")
    message  = msgCC # Will be set to the incoming message for ref as last message
    console  = 1 # Set to 0 to stop control display

    def __init__(self):
        print("Setting up Midi - please wait")
        try:
            self.midiIn=mido.open_input(MIDIDEVICE,callback=self.midiCallback)
        except:
            print("Unknown MIDI device - use a name from list. Check connections")
            m=mido.get_input_names()
            for n in m:
                print(n)
            print("Stopped.")
            sys.exit(0)
        self.midiOut=mido.open_output(MIDIDEVICE)
        for b in range(0,18):
            self.buttons.append(button(self,b))
            self.buttons[b].name="B{0}".format(b)
        for k in range(0,8):
            self.knobs.append(knob(self,k))
            self.knobs[k].name="K{0}".format(k)
        self.slider=slider(self)
        self.slider.name="Slider"
        self.reset()

    def __del__(self):
        try:
            self.midiIn.close()
            self.midiOut.close()
        except:
            pass

    def reset(self):
        """ Set all buttons and knobs to off """
        for r in self.buttons:
            r.reset()
        for r in self.knobs:
            r.reset()


    def showState(self):
        os.system('clear')
        print(datetime.datetime.now())
        print("Using:",MIDIDEVICE)
        print("In message: {0}".format(self.message))
        print("Out CC:     {0}".format(self.msgCC))
        print("Out note:   {0}".format(self.msgNote))
        print("====== Knobs =======")
        for r in self.knobs:
            print("{0}: V{1} B{2} L{3}".format(r.name,r.value,r.button,r.latch))
        print("===== Buttons ======")
        for r in self.buttons:
            print("{0}: B{1} L{2}".format(r.name,r.button,r.latch))
        print("Slider: {0}".format(self.slider.value))
    
    def midiCallback(self,m):
        # Improve this via lookup for the actual object?
        self.message=m
        for b in self.buttons:
            b.midi(m)
        for k in self.knobs:
            k.midi(m)
        self.slider.midi(m)
        if self.console==1:
            self.showState()

if __name__=="__main__":
    # Create the xTouch Object and show some of the features

    os.system("clear")
    x=xTouch()  # Create object
    print("Press button A to show console")
    x.console=0 # Turn the console displ;y off
    x.knobs[0].rotmax=60
    # Create a test callback function as demo
    def testCB(m):
        if x.buttons[16].latch==0:
            print("Demo Callback ",m)
    # And attach it
    x.buttons[17].callback=testCB

    consoleDisplay=0 # Stop constantly refreshing the display
    while True: # Loop until ctrl+c or button 13
        # Wire up the console output to button 16 (A)
        if x.buttons[16].button==1:
            os.system("clear")
            consoleDisplay=0
        # And reset all to button 17 (B)
        if x.buttons[17].button==1:
            x.reset()

        if x.knobs[0].latch==1 and x.buttons[16].latch==0:
            print("="*x.knobs[0].value)

        if x.buttons[13].button==1:
            x.reset()
            sys.exit(0)

        if x.buttons[16].latch==1:
            x.console=1
            if x.buttons[16].button==1:
                x.showState()
        else:
            if consoleDisplay==0:
                os.system('clear')
                print("Press button A to show console")
                x.console=0
                consoleDisplay=1 

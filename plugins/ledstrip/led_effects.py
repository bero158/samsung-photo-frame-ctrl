import logging as LOGGER
import time
import threading
import collections
if __package__:
    from pbneopixel.sender import Sender
else:
    from sender import Sender
from enum import Enum




class PrivilegedSender(Sender):
    priorityMap : list[int]

    class Level(Enum):
        LOW = 0
        HIGH = 1
        ALARM = 2
    
    def __init__(self, leds : range, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.priorityMap=[PrivilegedSender.Level.LOW]*len(leds)
    
    def setPriority(self, leds : range, reqLevel : Level, myLevel : Level) -> bool: 
        if reqLevel.value > myLevel.value: return False #not allowed
        if not self.isAllowedLeds(leds, myLevel): return False #not allowed
        for i in leds:
            self.priorityMap[i] = reqLevel
        return True
    
    def isAllowedPixels(self,pixels : list[tuple],level : Level):
        for pixel in pixels:
                ledPrivLevel = self.priorityMap[pixel[0]]
                if ledPrivLevel.value > level.value:
                    return False
        return True
    
    def isAllowedLeds(self,leds : range,level : Level):
        for led in leds:
                ledPrivLevel = self.priorityMap[led]
                if ledPrivLevel.value > level.value:
                    return False
        return True
    def addQueue(self, pixels, level : Level = Level.LOW):
        """Add queue with privilege level check"""
        if isinstance(pixels,list):
            if not self.isAllowedPixels(pixels, level): return
        else:
            ledPrivLevel = self.priorityMap[pixels[0]]
            if ledPrivLevel.value > level.value:  return
        super().addQueue(pixels)

class Effect:
    leds : range # physical LED mapping
    sender : PrivilegedSender # sender class
    ledLength : int # Length of my part of the strip. Calculated from leds
    logLeds : int # Logical leds (starting with 0)
    color : tuple # (R,G,B) LED color
    backColor : tuple # (R,G,B) LED color for clearing etc.
    privilegeLevel : PrivilegedSender.Level #My locking level
    lockedByMe : bool #I set the lock. I'm unlocking.

    def __init__(self, sender : PrivilegedSender, physLeds : range, privilegeLevel = PrivilegedSender.Level.LOW ):
        """
        sender = sender class. Must be created and set before.
        leds = Physical mappintto button LED
        
        """
        self.leds = physLeds
        self.sender = sender
        self.ledLength = len(self.leds)    
        self.logLeds = range( 0, self.ledLength, physLeds.step )
        self.backColor = (0,0,0)
        self.color = (0,0,0)
        self.privilegeLevel = privilegeLevel
        self.lockedByMe = False

    def fill(self,color : tuple = None):
        """Fill witn one color. For clearing etc."""
        color = color if color else self.color
        pixels = [(i,color) for i in self.leds]
        self.addQueueP(pixels)

    def addQueueP(self, pixels):
        self.sender.addQueue(pixels, self.privilegeLevel)


    def clear(self):
        """clears the led strip"""
        self.fill(self.backColor)

    def stop(self):
        """for compatibility with pibooth_ledstrip"""
        self.clear()

    def lock(self):
        self.lockedByMe = self.sender.setPriority(self.leds, self.privilegeLevel, self.privilegeLevel)
    def unlock(self):
        if self.lockedByMe:
            self.sender.setPriority(self.leds, PrivilegedSender.Level.LOW, self.privilegeLevel)
            self.lockedByMe = False

class EffectAnimated(Effect):
    running : bool # running state
    repeat : float # count of iterations. Decimal number means portion of the last step
    syncWith : object # Effect class multithreading synchronisation with other thread
    ledLength : int # Length of my part of the strip. Calculated from leds
    tempColor : tuple # (R,G,B) LED temporary color applied at next round only.
    mirror : int # Nr. of mirrors in effect. Currently only 1 is implemented
    timing : float # one step delay
    stepping : int # how many steps in one step
    offset : int = 0 # starting position
    direction : int = 1 #-1 = Down, 1 = Up
    pos : int = 0 #position of the counter etc.
    
    def __init__(self, *args, syncWith : object = None, **kwargs ):
        """
        sender = sender class. Must be created and set before.
        leds = Physical mappintto button LED
        syncWith = Synchronisation between worker threads. If used sleep in thread is replaced with waiting."""
        self.running = True #tells the effect to be running
        self.repeat = 1
        self.syncWith = syncWith
        self.tempColor = None
        self.mirror = 0
        self.timing = 0
        self.stepping = 1
        self._duration_s = 0
        self.offset = 0
        self.direction = 1
        self.pos = 0
        super().__init__(*args, **kwargs)
    
    
    @property
    def duration(self):
        return self._duration_s
    
    @duration.setter
    def duration(self, duration_s : int):
        """Duration of one whole cycle. For threaded output"""
        self._duration_s = duration_s
        self.timing = duration_s / len(self.leds)
    
    def go(self):
        """Thread main cycle. Don't call directly. Started through goThreaded"""
        self.running = True
        iter = int(self.repeat)
        while (iter > 0 or self.repeat == -1) and self.running: # -1 = forever
            self.lock()
            self.goOnce(1 if iter>0 or self.repeat <0 else self.repeat%1) # 1 normal run and dec. portion at last run
            self.unlock()
            if self.repeat > 0:
                iter -= 1
            
        self.running = False

    def next(self, steps : int = 1):
        """Math should be here. Implement in inherited classes"""
        ...
    
    def goOnce(self, portion : float = 1):
        LOGGER.debug(f"running {self.leds.start} - {self.leds.stop}")
        steps = len(self.logLeds)//(self.mirror+1)
        steps = steps//self.stepping if portion == 1 else int((steps*portion)//self.stepping)
        
        for _ in range(steps):
            self.next(self.stepping)
            time.sleep(self.timing)
            if not self.running:
                break
    
    def run(self, threaded = False):
        """Call this for starting the effect!"""
        if threaded:
            self.goThreaded() # nonblocking
        else:
            self.go() # blocking

    def goThreaded(self):
        """Threaded run"""
        self.thread = threading.Thread(target=self.go, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stops the effect thread"""
        self.running = False


class EffectSerial(EffectAnimated):
    """Runs effect after effect"""
    effects : EffectAnimated
    def __init__(self, effects : EffectAnimated = [], *args, **kwargs):
        super().init(*args, **kwargs)
        self.effects : EffectAnimated = effects

    def goOnce(self, portion : float = 1):
        steps = steps//self.stepping if portion == 1 else int((steps*portion)//self.stepping)
        
        for effect in self.effects:
            effect.goOnce(1)
            if not self.running:
                break
    
    def stop(self):
        """Stops the effect thread"""
        self.running = False
        for effect in self.effects:
            effect.stop()

class EffectShine(EffectAnimated):
    def goOnce(self,portion : float = 1):
        """one passthrough, waiting"""
        LOGGER.debug("EffectShine On")
        self.fill((self.color))
        time.sleep(self.timing)
        self.fill(self.backColor)
        LOGGER.debug("EffectShine Off")
    
    @property
    def duration(self):
        ...
    @duration.setter
    def duration(self, duration_s : int):
        """Duration of one whole cycle. For threaded output"""
        self.timing = duration_s

class EffectFade(EffectAnimated):
    bRange : range # brightness range
    currentBrightness : int # for sharing between threads
    def goOnce(self,portion : float = 1):
        """one passthrough, waiting"""
        for brightness in self.bRange:
            self.currentBrightness = brightness
            if self.syncWith:
                if (hasattr(self.syncWith,"effect")):
                    brightness = self.syncWith.effect.currentBrightness
            self.fill( calcColor(self.color, brightness ))
            time.sleep(self.timing)
            if not self.running:
                break
    @property
    def duration(self):
        ...

    @duration.setter
    def duration(self, duration_s : int):
        """Duration of one whole cycle. For threaded output"""
        self.timing = duration_s / len(self.bRange)
    
class EffectFlash(EffectAnimated):
    duration : float    
    def startFade(self,bRange : range, color : tuple):
        self.effect = EffectFade(self.sender, physLeds = self.leds, syncWith = self.syncWith)
        self.effect.bRange = bRange
        self.effect.duration = self.duration / 2
        self.effect.color = color
        self.effect.go()

    def goOnce(self,portion : float = 1):
        oldtempColor = self.tempColor 
        color = self.color if oldtempColor == None else oldtempColor
        self.startFade(self.bRange, color)
        if self.running:
           back = range(self.bRange.stop - self.bRange.step, self.bRange.start - self.bRange.step, 0 - self.bRange.step)
           # back = reversed(self.bRange)
           self.startFade(back, color)
        if oldtempColor: #only when temp color was previously set.
            self.tempColor = None 

    def stop(self):
        super().stop()
        if self.effect:
            self.effect.stop()

    
class EffectRainbow(EffectAnimated):
    def goOnce(self,portion : float = 1):
        LOGGER.debug("running rainbow cycle")
        for j in range(255):
            pixels = []
            for i in self.leds:
                pixel_index = (i * 256 // len(self.leds)) + j
                pixels.append((i,self.wheel(pixel_index & 255)))
            else:
                self.addQueueP(pixels)
                time.sleep(self.timing)
                if not self.running:
                    break

    def wheel(self,pos):
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        if pos < 0 or pos > 255:
            r = g = b = 0
        elif pos < 85:
            r = int(pos * 3)
            g = int(255 - pos * 3)
            b = 0
        elif pos < 170:
            pos -= 85
            r = int(255 - pos * 3)
            g = 0
            b = int(pos * 3)
        else:
            pos -= 170
            r = 0
            g = int(pos * 3)
            b = int(255 - pos * 3)
        return (r, g, b)

class LogicalMapping(EffectAnimated):
    def log2physLed(self, logLed : int) -> int:
        logLed = logLed*self.leds.step+self.offset
        pos = logLed%self.ledLength
        physLed = self.leds.start + pos
        return physLed
    
    def addQueue(self, led : int, color : tuple = None):
        if not color:
            color = self.color
        physLed = self.log2physLed(led)
        self.addQueueP((physLed,color))
        
class EffectCount(LogicalMapping):
    
    
    
    
    def step(self, i : int):
        if self.direction == -1:
            led = (self.ledLength - 1) - i
        else:
            led = i
        self.addQueue(led)

        if self.mirror:
            # add mirrored side
            ledM =  0 - led
            ledM = ledM%(self.ledLength )
            self.addQueue(ledM)

    def reset(self):
            self.pos = 0
    
    def next(self, steps : int = 1):
        for i in range(steps):
            self.step(self.pos)
            self.pos += 1

            if self.pos < 0:
                self.pos = 0
            if self.pos > self.ledLength:
                self.pos = self.ledLength
    
    def repaint(self):
        """repaints last state. Intended use is for effect mixing"""
        for i in range(0, self.pos):
            self.step(i)
            
class EffectShiftRegister(LogicalMapping):
    register : collections.deque
    injectQueue : list
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset()
        self.injectQueue = []

    def reset(self):
        self.register=collections.deque( [(0,0,0)]*self.ledLength , maxlen=self.ledLength)
                
    def set(self, vals : collections.deque):
        self.reset()
        for i, val in enumerate(vals):
            self.register[i] = val
    
    def rotate(self, n : int):
        self.register.rotate(n)

    def repaint(self):
        for led,color in enumerate(self.register):
            self.addQueue(led,color)

    def next(self, steps : int = 1):
        """Shows the actual state and calls rotate"""
        self.repaint()
        if len(self.injectQueue):
            for _ in range(steps):
                if len(self.injectQueue):
                    self.inject(self.injectQueue.pop(0))
        else:
            self.rotate(steps*self.direction)

    def inject(self, color : tuple, n : int = 1):
        """inject a new value at the begining of the array"""
        for _ in range(n):
            self.register.pop()
            self.register.appendleft(color)
        
    def injectDelayed(self, color : tuple):
        """inject a new value at the begining of the array"""
        self.injectQueue.append(color)
        

class EffectComet(EffectShiftRegister):

    def injectComet(self, tail : int):
        self.injectDelayed((255,255,255))
        gradient = 255//tail
        for i in range( 0, tail ):
            self.injectDelayed(calcColor(self.color,255-(gradient*i)))    

class EffectDisco(EffectShiftRegister):
    def run(self, *args, **kwargs):
        for _ in range(len(self.leds)//self.stepping):
            self.inject(self.color,self.stepping)
            self.inject(self.backColor,self.stepping)
        super().run(*args, **kwargs)
        

import time
from enum import Enum
WHOLE_DAY = 24*60*60
class Nightmode:
    MODE = Enum("MODE",["DAY","NIGHT"])
    timeTable : list[tuple[int, MODE]] = []
    lastMode : MODE = None #storage for the current mode
    @staticmethod
    def getSecOfDay(t : float = None):
        """ returns sec of the day"""
        if t == None:
            t = time.time()

        secOfDay = t%(WHOLE_DAY)
        return secOfDay
    
    def createTTRow(self, ttStr : tuple[str, str]) -> tuple[int, MODE]:
        """expects tuple in format ("13:57","DAY") or ("01:02 AM","NIGHT")"""
        #convert time to nr. of seconds from 00:00
        try: #first try 24h format
            t = time.strptime(ttStr[0], "%H:%M")
        except ValueError:
            #NOW try 12h format
            t = time.strptime(ttStr[0], "%I:%M %p")

        secsSinceMidnight = self.getSecOfDay(time.mktime(t))
        return int(secsSinceMidnight), self.MODE[ttStr[1].upper()]
    
    def createTT(self, tt : list[tuple[str, str]]):
        """creates internal time table for getmode"""
        for item in tt:
            ttRow = self.createTTRow(item)
            self.timeTable.append(ttRow)
        self.timeTable.sort(key=lambda x:x[0])
        lastMode = self.timeTable[-1][1]
        if self.timeTable[-1][0] != WHOLE_DAY:
            self.timeTable.append((WHOLE_DAY, lastMode))
        if self.timeTable[0][0] != 0:
            self.timeTable.insert(0,(0,lastMode))
        self.timeTable.sort(key=lambda x:x[0], reverse=True) # I need the table in reverse order for getMode

    def getMode(self, t : float = None):
        """ returns mode according to time table"""
        secOfDay = self.getSecOfDay( t )
        mode = next( tt for tt in self.timeTable if tt[0]< secOfDay )[1]
        return mode
            
    def getModeStr(self, mode : MODE = None) -> str:
        """returns mode string. For calling from other plugins"""
        if not mode:
            mode = self.lastMode
        return mode.name
        
                                  


        
    
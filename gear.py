from uut import uut
from testlib.util.logfile import LogFile
from testlib.equip.thermotron8200 import thermotron
import copy

class Gear():
    master = None       # master UUT
    slave  = None       # slave UUT
    therm  = None       # thermotron
    
    def __init__(self, **kwargs):
        self.master = kwargs.get('master', None)
        self.slave  = kwargs.get('slave', None)
        self.therm  = kwargs.get('therm', None)
        print "No Gear __init__"
    
    
class GearPlus( Gear ):

    def __init__( self ):
        self.stuff = "SomeStuff"
        print "GearPlus() __init__"
        Gear.__init__(self )
        
    def whoami( self ):
        print "I am GearPlus"
        
        
if __name__ == '__main__':
    eq = Gear()
    gp = GearPlus()
    gp.whoami()    
    gp = copy.copy(eq)

    
    eq.master = uut(ipaddr='10.8.8.113') 
    eq.master.telnet()
    eq.master.web()
    eq.slave = uut(ipaddr='10.8.8.138') 
    eq.slave.telnet()
    eq.slave.web()
    
    
    
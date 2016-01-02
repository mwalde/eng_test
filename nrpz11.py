import visa #read the help here: http://pyvisa.readthedocs.org/en/latest/api/highlevel.html
# import numpy as np #read the help here: http://docs.scipy.org/doc/numpy/
# import matplotlib.pyplot as plt #read the help here: http://matplotlib.org/users/pyplot_tutorial.html

class nrpz11 ():
        
    def __init__( self, resource_name, **keyw ):
        self.resource_name = resource_name
        self.nrpz = visa.instrument( resource_name, **keyw )
        print self.nrpz.ask("*idn?")
        self.nrpz.ask("SYST:INIT")
        
    def calibrate( self ):
        print "Calibrating %s. . ." % self.resource_name
        self.nrpz.write("CAL:ZERO:AUTO ONCE")
        print "Complete"
        
    def function( self, mode ):
        sensemode = { \
            "average": "POW:AVG",
            "timeslot": "POW:TSL:AVG",
            "burst": "POW:BURS:AVG",
            "scope": "POW:XTIM:POW"
            }

        cmd = sensemode.get( mode , None )
        if cmd:
            cmd = "SENS:FUNC " + cmd
            print cmd
            self.nrpz.write(cmd)
        else:
            print "mode unknown: ", mode
            
            
    def setoffset( self, dB ):
        self.nrpz.write("SENS:CORR:OFFSet %f" % dB)
        #self.nrpz.write("SENS:CORR:OFFSet:STATe ON")
        
    def getoffset( self ):
        offset = self.nrpz.ask("SENS:CORR:OFFSet?")
        return offset
        
    def setfreq( self, freq_mhz):
         cmd = "SENS:FREQ %e" % (freq_mhz * 1.0e6)
         print cmd
         self.nrpz.write(cmd)
   
    def getfreq( self ):
        cmd = "SENS:FREQ?"
        freq_mhz = float(self.nrpz.ask( cmd )) / 1.0e6
        print cmd, freq_mhz
        return freq_mhz
        
    def initIMM( self ):
        cmd = "INIT:IMM"
        print cmd
        self.nrpz.write(cmd)
        
    # set multiple setting commands
    def setmulti( self, cmd_list ):
        cmd = "SYST:TRAN:BEG"
        self.nrpz.write(cmd)
        for cmd in cmd_list:
            self.nrpz.write(cmd)
        cmd = "SYST:TRAN:END"
        self.nrpz.write(cmd)



        
# RSNRP::0x000c::100769:INSTR  
#open the instrument session
#NRPZ1 = visa.instrument ("RSNRP::0x000c::100759::INSTR")
#NRPZ2 = visa.instrument ("RSNRP::0x000c::100760::INSTR")

#reset the instrument
#print NRPZ1.ask("*idn?")
#print NRPZ2.ask("*idn?")

NRPZ1 = nrpz11("RSNRP::0x000c::100759::INSTR")
NRPZ2 = nrpz11("RSNRP::0x000c::100760::INSTR")

#help(NRPZ1)
#print NRPZ1.interface_type
#print NRPZ1.resource_class
print NRPZ1.resource_name
#NRPZ1.calibrate()
print NRPZ1.getoffset()
NRPZ1.setoffset( 192.3)
print NRPZ1.getoffset()
print NRPZ1.getfreq()
NRPZ1.setfreq( 5800 )
print NRPZ1.getfreq()
NRPZ1.setfreq( 5980)
print NRPZ1.getfreq()
NRPZ1.function("burst")





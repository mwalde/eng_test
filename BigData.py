# sweep test
import sys
from time import sleep
import traceback
from uut import uut
from gear import Gear
from sequencer import sequencer
from testlib.util.logfile import LogFile
from testlib.equip.thermotron8200 import thermotron


class radiodata():
    def __init__(self):
        return None
    
class testdata( ):
    mdata = None
    sdata = None
    chamberTemp = None
    
    header = \
    "Frequency MHz," + \
    "Power dBm," + \
    "Channel BW," + \
    "M ISO," + \
    "M Chain 0 EVM," + \
    "M Chain 1 EVM," + \
    "M Rx Power0," + \
    "M Rx Power1," + \
    "M Local Mod rate," + \
    "M Rx Cap," + \
    "M Tx Cap," + \
    "M Tx0 reg 73," + \
    "M Tx1 reg 75," + \
    "M Radio Temp," + \
    "S ISO," + \
    "S Chain 0 EVM," + \
    "S Chain 1 EVM," + \
    "S Rx Power0," + \
    "S Rx Power1," + \
    "S Local Mod rate," + \
    "S Rx Cap," + \
    "S Tx Cap," + \
    "S Tx0 reg 73," + \
    "S Tx1 reg 75," + \
    "S Radio Temp," + \
    "Therm Temp\n"
    


    
    def __init__(self, freq=0, power=0, ChBW=0, chamberTemp='--'):
        self.freq = freq
        self.power = power
        self.ChBW = ChBW
        self.chamberTemp = chamberTemp
        
    def wdata(self, radio):
        w = radio.w
        t = radio.t
        self.opmode = radio.opmode
        data = radiodata()
        data.ISO  = w.get_page_field("labefana","Chain Isolation")[0:-3]
        data.EVM0 = float(t.read_reg('mrw 60000166'))/4
        data.EVM1 = float(t.read_reg('mrw 60000168'))/4
#        data.EVM0 = w.get_page_field("labefana","Chain 0 EVM")[0:-3]
#        data.EVM1 = w.get_page_field("labefana","Chain 1 EVM")[0:-3]
        data.POW0 = w.get_page_field("labefana","RX Power0")[0:-4]
        data.POW1 = w.get_page_field("labefana","RX Power1")[0:-4]
        data.LMOD = w.get_page_field("labefana","Local Mod Rate")
        data.TCAP = w.get_page_field("labefana","TX Capacity")[0:-4].replace(',','')
        data.RCAP = w.get_page_field("labefana","RX Capacity")[0:-4].replace(',','')
        data.R73  = t.readADIatten( 0 )
        data.R75  = t.readADIatten( 1 )
#        data.TEMP = w.get_page_field("labefana","Radio Temp TX")[0:2]
        data.TEMP = t.RadioTemp( 'rx' )
        
        if self.opmode == 'master':
            self.mdata = data
        else:
            self.sdata = data

    def __csv( self, data, prefix):
        csvstr = ",%s,%0.2f,%0.2f,%s,%s,%s,%s,%s,%s,%s,%s" % (\
            data.ISO , \
            data.EVM0, \
            data.EVM1, \
            data.POW0, \
            data.POW1, \
            data.LMOD, \
            data.TCAP, \
            data.RCAP, \
            data.R73,  \
            data.R75,  \
            data.TEMP)
        return csvstr
    
    def getcsv(self):
        rsp = ""
        csvstr = "%s,%s,%s" % (str(self.freq),str(self.power),str(self.ChBW))
        mstr = self.__csv( self.mdata, 'M')
        sstr = self.__csv( self.sdata, 'S')
        rsp = csvstr + mstr + sstr + ',' + str(self.chamberTemp) + '\n'
        return rsp
           
import copy           
class control( ):

    gear = Gear()
     
    def __init__( self, **kwargs ):     # ctrl = control( Gear=gear )
        got_gear = kwargs.get('Gear', None)
        if got_gear:
            self.gear = copy.copy(got_gear)
        
    def setfrequency( self, freq ):       # frequency in MHz
        cmd = "af set tx1freq %s; af set rxfreq %s" % (freq,freq)
        self.gear.master.t.write_wait( cmd )
        self.gear.slave.t.write_wait( cmd )
        
    def setpower( self, power):
        cmd = "af set powerout %s" % power
        self.gear.master.t.write_wait( cmd )
        self.gear.slave.t.write_wait( cmd )
        
    def setbw( self, bw):
        cmd = "af set channelbandwidth %s" % bw
        self.gear.master.t.write_wait( cmd )
        self.gear.slave.t.write_wait( cmd )

    def wait( self, mod_rate, delay=25 ):
        sleep(2)
        self.gear.slave.t.radio_ready( ready_state = [('slave','operational')], timeout = 40)
        self.gear.master.t.radio_ready(ready_state = [('master','operational')], timeout = 40)
        print "wait_mod_rate(%s, %d)" % (mod_rate, delay)
        return self.wait_mod_rate( mod_rate, timeout = delay )
#        sleep(3)

    def get_mod_rate( self ):
        s_mod_rate = self.gear.slave.w.get_page_field("labefana","Local Mod Rate")
        m_mod_rate = self.gear.master.w.get_page_field("labefana","Local Mod Rate")
        return (s_mod_rate, m_mod_rate)

    # return True if timeout
    def wait_mod_rate( self, mod_rate, timeout = 25 ):
        delay = timeout
        mod = self.get_mod_rate()
        while delay:
            if mod[0] == mod_rate and mod[1] == mod_rate:
                return 0
            mod = self.get_mod_rate()
            delay-=1
            sleep(1)
        return 1
        
    def settemp( self, temp ):
        if self.gear.therm:
            self.gear.therm.set_temp_chamber( temp )
            print "did set_temp"
            self.gear.therm.waitTempChamber( soak_time = 10 )
            print "did wait"
    
    def close(self):
        self.gear.master.close()
        self.gear.slave.close()
    
        
#=========================================================================================
#
#       RF Sweep loop
#
#=========================================================================================           
    
def rf_sweep_temp( gear, BW, Power, Freq, Temp, Logname):
    print "rf_sweep_temp"
    ctrl = control( Gear=gear ) 

    thm = sequencer( Temp, file='thm' )
    bw  = sequencer(BW, file='bw')
    pwr = sequencer(Power, file='pwr' )
    frq = sequencer(Freq, file='frq')

    csv = LogFile( 'logs',Logname, '.csv')
    
    # if this is a fresh start do put the data header in
    if thm.freshstart and bw.freshstart and pwr.freshstart and frq.freshstart:
        tdata = testdata()
        csv.write(tdata.header)
    
    try:
        thm.regen()
        for temp in thm:
            ctrl.settemp(temp)
            bw.regen()
            for ChBW in bw:
                ctrl.setbw(ChBW)
                print "ChBw ", ChBW
                frq.regen()
                for freq in frq:
                    ctrl.setfrequency(freq)
                    print "freq ", freq
                    pwr.regen()
                    for power in pwr:
                        if freq < 5750 and power >= 23:     # skip over higher power at lower frequencies
                            continue
                        ctrl.setpower(power)
                        print "power ", power
                        if ctrl.wait('2x'):
                            print "mod_rate timmeout occured"
                            raise KeyboardInterrupt
                        delay = 3
                        sleep(delay)
                        tdata = testdata( freq, power, ChBW, temp)
                        tdata.wdata( gear.master )
                        tdata.wdata( gear.slave )
                        csv.write(tdata.getcsv() )
                        print tdata.getcsv()

        csv.close()
        bw.clean()
        pwr.clean()
        frq.clean()
        thm.clean()
        return False
    
    except KeyboardInterrupt:
        print "Program Abort"
        return False
    
    except Exception, e:
        print "Exception Exit"
        exc_type, exc_value, exc_traceback = sys.exc_info()
        plist = traceback.format_exception(exc_type, exc_value,
                                              exc_traceback)
        print plist
        ctrl.close()
        return True
    
           
if __name__ == '__main__':
    m = uut(ipaddr='10.8.8.100', opmode='master') # 113
    s = uut(ipaddr='10.8.8.108', opmode='slave')  # 138
    m.telnet()
    s.telnet()
    m.web()
    s.web()
    t = thermotron("10.8.9.20")
    gear = Gear( master=m, slave=s, therm=t )

#    Logname = "fpa031215"
#    Temp = (1,2, 1)
#    BW = ( 10,51,10)
#    Power = ( 10,11,1)
#    Freq = (5150,5926,50)

#    Temp = (-40,70, 5)
#    BW = ( 50,51,1)
#    Power = ( 10,26,1)
#    Freq = (5150,5926,1)
    Logname = "5XBigData"
    Temp = (0,71, 5)
    BW = ( 50,51,1)
    Power = ( 10,26,1)
    Freq = (5150,5926,1)
    
    retry = 1
    status = 1
    while status and retry:
        status = rf_sweep_temp( gear, BW, Power, Freq, Temp, Logname)
        if status:
            print "restarting test"
        retry-=1

    sys.exit(0)
        


    
    

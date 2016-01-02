# sweep test
import sys
from time import sleep
import traceback
from uut import uut
from sweep import sweep
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
 #       data.EVM0 = w.get_page_field("labefana","Chain 0 EVM")[0:-3]
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
           

           
class control():
     
    def __init__(self, m, s, t, delay = 25):
        self.delay = delay
        self.m = m
        self.s = s
        self.t = t
        return
        
    def setfrequency( self, freq ):       # frequency in MHz
        cmd = "af set tx1freq %s; af set rxfreq %s" % (freq,freq)
        self.m.t.write_wait( cmd )
        self.s.t.write_wait( cmd )
        
    def setpower( self, power):
        cmd = "af set powerout %s" % power
        self.m.t.write_wait( cmd )
        self.s.t.write_wait( cmd )
        
    def setbw( self, bw):
        cmd = "af set channelbandwidth %s" % bw
        self.m.t.write_wait( cmd )
        self.s.t.write_wait( cmd )

    def wait( self, mod_rate, delay=25 ):
        sleep(2)
        self.s.t.radio_ready( ready_state = [('slave','operational')], timeout = 40)
        self.m.t.radio_ready(ready_state = [('master','operational')], timeout = 40)
        print "wait_mod_rate(%s, %d)" % (mod_rate, delay)
        return self.wait_mod_rate( mod_rate, timeout = delay )
        sleep(delay)

    def get_mod_rate( self ):
        s_mod_rate = self.s.w.get_page_field("labefana","Local Mod Rate")
        m_mod_rate = self.m.w.get_page_field("labefana","Local Mod Rate")
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
        if self.t:
            self.t.set_temp_chamber( temp )
            print "did set_temp"
            self.t.waitTempChamber( soak_time = 0 )
            print "did wait"
    
    def close(self):
        self.m.close()
        self.s.close()
    
        
#=========================================================================================
#
#       RF Sweep loop
#
#=========================================================================================           
    
def rf_sweep_temp( BW, Power, Freq, Temp, Logname):
    print "rf_sweep_temp"
    m = uut(ipaddr='10.8.8.113', opmode='master') #195
    s = uut(ipaddr='10.8.8.138', opmode='slave') #196
    m.telnet()
    s.telnet()
    m.web()
    s.web()
    t = None
    # is the thermotron required? 
    if Temp[0] != Temp[1]:
#        t = thermotron("10.8.9.20")
        print "thermotron"
    else:
        t = None
    ctrl = control( m, s, t, 25) # <-- 25 second wait time

    csv = LogFile( 'logs',Logname, '.csv', ['11','22','33','44','55','66'] )
    tdata = testdata( 0,0,0,'--')
    thm  = sweep( Temp[0], Temp[1], Temp[2], ctrl.settemp, file='thm')             
    bw   = sweep( BW[0], BW[1], BW[2], ctrl.setbw, file='bw')             
    pwr  = sweep( Power[0], Power[1], Power[2], ctrl.setpower, file='pwr')  
    frq  = sweep( Freq[0], Freq[1], Freq[2], ctrl.setfrequency, file='frq')

    # if this is a fresh start do put the data header in
    if thm.freshstart and bw.freshstart and pwr.freshstart and frq.freshstart:
        csv.write(tdata.header)
    
    try:
        thm.regen()
        temp = thm.next()
        print
        while temp:
            print "Temp"
            bw.regen()
            ChBW = bw.next()
            while ChBW :
                print "ChBW: ",ChBW
                frq.regen() 
                delay = 25
                freq = frq.next()
                while freq:
                    
                    print "Freq: ",freq
                    delay = 25
                    pwr.regen() 
                    power = pwr.next()
                    while power:
                        if freq < 5750 and power >= 23:
                            pwr.curval = None
                            pwr.regen()
                            break;
                        print "Power: ",power
                        if ctrl.wait('2x', delay):
                            print "mod_rate timmeout occured"
                            raise KeyboardInterrupt
                        delay = 3
                        sleep(delay)
                        tdata = testdata( freq, power, ChBW, temp)
                        tdata.wdata( m )
                        tdata.wdata( s )
                        csv.write(tdata.getcsv() )
        #                print tdata.header
                        print tdata.getcsv()
                        power = pwr.next()
                    # reset power
                    ctrl.setpower(pwr.start)
                    freq = frq.next()
                ChBW = bw.next()
            temp = thm.next()
        print "Complete csv.close()"
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

        Logname = "fpa030315"
        Temp = (1,2, 1)
        BW = ( 10,51,10)
        Power = ( 10,11,1)
        Freq = (5150,5926,50)
#        Temp = (-40,70, 5)
#        BW = ( 50,51,1)
#        Power = ( 10,26,1)
#        Freq = (5150,5926,1)
        retry = 2
        status = 1
        while status and retry:
            status = rf_sweep_temp( BW, Power, Freq, Temp, Logname)
            if status:
                print "restarting test"
            retry-=1

#        Logname = "5XLow"
#        BW = ( 50,51,1)
#        Power = ( 10,23,1)
#        Freq = (5150,5750,1)
#        rf_sweep( BW, Power, Freq, Logname+Temp)

#        Logname = "5XHigh"
#        BW = ( 50,51,1)
#        Power = ( 10,26,1)
#        Freq = (5750,5926,1)
#        rf_sweep( BW, Power, Freq, Logname+Temp)

        sys.exit(0)
        


    
    


import random
import pickle
from time import sleep

class combiner():
    # current switch setting
    current = (0,0,0,0,0,0,0,0)
    
    # Frequency/path calibration dictionary
    CAL = {}
    
    # Test frequency list
    FreqList = [5150,5550,5950]
    
    # 2X2 test sequence
    Seq2X2 = [ 'LB0J1','IC0B0','LC0J1',  
               'LB1J2','IC1B1','LC1J2']
    
    # 4X4 test sequence
    Seq4X4 = Seq2X2 + \
             [ 'LD0J1','IA0D0','LA0J1','IA0B0',
               'LD1J2','IA1D1','LA1J2','IA1B1']
               
    xSeqCal = ['LA0J1C','LB0J1C','LC0J1C','LD0J1C',
              'LA1J2C','LB1J2C','LC1J2C','LD1J2C',
              'ID0A0C','IA0B0C','IB0C0C','IB1C1C','IA1B1C','ID1A1C']

    # Calibration sequence
    SeqCal = ['LA0J1',
              'LB0J1',
              'LC0J1',
              'LD0J1',
              'LA1J2',
              'LB1J2',
              'LC1J2',
              'LD1J2',
              'IA0D0',
              'IA0B0',
              'IC0B0',
              'IC1B1',
              'IA1B1',
              'IA1D1'
              ]

    # Test path/switch setting dictionary          
#               test     1 2 3 4   5 6 7 8   9      # LCAL     ICAL
    MATRIX = {
#              'LB0J1' : (1,1,0,1,  0,1,1,1,  1),    # LB0J1   IB0C0
#              'IB0C0' : (1,1,0,1,  0,1,1,1,  1),
#              'LC0J1' : (1,1,0,1,  0,1,1,1,  0),    # LC0J1
#              
#              'LB1J2' : (1,1,1,0,  1,0,1,1,  1),    # LB1J2   IB1C1  
#              'IB1C1' : (1,1,1,0,  1,0,1,1,  1),
#              'LC1J2' : (1,1,1,0,  1,0,1,1,  0),    # LC1J2
#              
#              'LD0J1' : (0,1,1,1,  1,1,0,1,  1),    # LD0J1   ID0A0
#              'ID0A0' : (0,1,1,1,  1,1,0,1,  1),
#              'LA0J1' : (0,1,1,1,  1,1,0,1,  0),    # LA0J1   IA0B0???
#              'IA0B0' : (0,1,1,1,  1,1,0,1,  1),
#              
#              'LD1J2' : (1,0,1,1,  1,1,1,0,  1),    # LD1J2   ID1A1
#              'ID1A1' : (1,0,1,1,  1,1,1,0,  1),
#              'LA1J2' : (1,0,1,1,  1,1,1,0,  0),    # LA1J2   LA1B1???
#              'IA1B1' : (0,1,1,1,  1,0,1,1,  1),
#
#   Calibration
#
              'LA0J1' : (0,1,1,1,  1,1,1,1,  0),
              'LB0J1' : (1,1,1,1,  0,1,1,1,  1),
              'LC0J1' : (1,1,0,1,  1,1,1,1,  0),
              'LD0J1' : (1,1,1,1,  1,1,0,1,  1),

              'LA1J2' : (1,0,1,1,  1,1,1,1,  0),
              'LB1J2' : (1,1,1,1,  1,0,1,1,  1),
              'LC1J2' : (1,1,1,0,  1,1,1,1,  0),
              'LD1J2' : (1,1,1,1,  1,1,1,0,  1),

              'IA0D0' : (0,1,1,1,  1,1,0,1,  1),
              'IA0B0' : (0,1,1,1,  0,1,1,1,  1),
              'IC0B0' : (1,1,0,1,  0,1,1,1,  1),
              'IC1B1' : (1,1,1,0,  1,0,1,1,  1),

              'IA1B1' : (1,0,1,1,  1,0,1,1,  1),
              'IA1D1' : (1,0,1,1,  1,1,1,0,  1),






#              'IC0J1' : (1,1,0,1,  1,1,0,1,  0),
#              'ID0J1' : (1,1,0,1,  1,1,0,1,  1),
#              'IA1J2C' : (1,0,1,1,  1,0,1,1,  0),
#              'IB1J2C' : (1,0,1,1,  1,0,1,1,  1),
#              'IC1J2C' : (1,1,1,0,  1,1,1,0,  0),
#              'ID1J2C' : (1,1,1,0,  1,1,1,0,  1),







#              'ID0A0C' : (0,1,1,1,  1,1,0,1,  1),
#              'IA0B0C' : (0,1,1,1,  0,1,1,1,  1),
#              'IB0C0C' : (1,1,0,1,  1,0,1,1,  1),
#              'IB1C1C' : (1,1,1,0,  1,0,1,1,  1),
#              'IA1B1C' : (1,0,1,1,  1,0,1,1,  1),
#              'ID1A1C' : (1,0,1,1,  1,1,1,0,  1),

#              'LJ1A0' : (0,1,1,1,  0,1,1,1,  0),
#              'LJ1B0' : (0,1,1,1,  0,1,1,1,  1),
#              'LJ1C0' : (1,1,0,1,  1,1,0,1,  0),
#              'LJ1D0' : (1,1,0,1,  1,1,0,1,  1),

#              'LJ2A1' : (1,0,1,1,  1,0,1,1,  0),
#              'LJ2B1' : (1,0,1,1,  1,0,1,1,  1),
#              'LJ2C1' : (1,1,1,0,  1,1,1,0,  0),
#              'LJ2D1' : (1,1,1,0,  1,1,1,0,  1),

#              'IA0D0' : (0,1,1,1,  1,1,0,1,  1),
#              'IA0B0' : (0,1,1,1,  0,1,1,1,  1),
#              'IC0B0' : (1,1,0,1,  1,0,1,1,  1),
#              'IC1B1' : (1,1,1,0,  1,0,1,1,  1),
#              'IA1B1' : (1,0,1,1,  1,0,1,1,  1),
#              'IA1D1' : (1,0,1,1,  1,1,1,0,  1),



#              'A0'    : (0,1,1,1,  1,1,1,1,  0),
#              'A1'    : (1,0,1,1,  1,1,1,1,  0),
#              'B0'    : (1,1,1,1,  0,1,1,1,  1),
#              'B1'    : (1,1,1,1,  1,0,1,1,  1),
#              'C0'    : (1,1,0,1,  1,1,1,1,  0),
#              'C1'    : (1,1,1,0,  1,1,1,1,  0),
#              'D0'    : (1,1,1,1,  1,1,0,1,  1),
#              'D1'    : (1,1,1,1,  1,1,1,0,  1),
              'INITL' : (1,1,1,1,  1,1,1,1,  1),
              
    }

    # all physical test equipment control functions are passed in at instantiation
    # undefined test equipment functions default to local test functions
    #
    def __init__(self, **kwargs):
        self.swtOn   = kwargs.get('swtOn',  self.__swtOn)
        self.swtOff  = kwargs.get('swtOff', self.__swtOff)
        self.pmPwrLoss  = kwargs.get('pmPwrLoss', self.__pmPwrLoss)
        self.pmFreqLoss  = kwargs.get('pmFreqLoss', self.__pmFreqLoss)
        self.pmPwrIso   = kwargs.get('pmPwrIso',  self.__pmPwrIso)
        self.pmFreqIso   = kwargs.get('pmFreqIso',  self.__pmFreqIso)
        self.sgAttn  = kwargs.get('sgAttn', self.__sgAttn)
        self.sgFreq  = kwargs.get('sgFreq', self.__sgFreq)
        self.dbWrite = kwargs.get('dbWrite',self.__dbWrite)
        # load calibration dictionary
        self.loadCAL()
        # initialize switches to a known state
        self.initialize()
        
        
    # initialize switches to a known state
    def initialize( self ):
        self.current = (0,0,0,0,0,0,0,0,0)
        self.SelPath( 'INITL')
        
    # set the switches to the new state. 
    # toggle only the ones that are required
    # path values greater than one are "don't care"
    def SelPath( self, path ):
        new = self.MATRIX[path]
        for i in range(9):
            if new[i] == self.current[i]:
                continue
            if new[i] == 1:
                self.swtOn(i+1)
            else:
                self.swtOff(i+1)
        self.current = new
        self.swtDisplay()
    
    # display the current switch settings
    def swtDisplay(self, **kwargs):
        s = kwargs.get('switches', self.current)
        print "  1   2   3   4   5   6   7   8   9"
        print "  %d   %d   %d   %d   %d   %d   %d   %d   %d" % ( s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8])

        
    ##### Calibration #####
    # optional frequency list may be passed in otherwise local FreqList is used
    def calSequence(self, **kwargs):
        freqlist = kwargs.get('freqlist',self.FreqList)
        print "CalSequence()"
        for test in self.SeqCal:
            self.SelPath(test)
            junk = raw_input("Connect %s to %s   Ready?" % ( test[3:],test[1:3]))
            for freq in freqlist:
                self.setFreq( freq) 
                print freq, ' ',
                sleep(.5)
                if test[0] == 'L':
                    calval = self.pmPwrLoss()
                else:
                    calval = self.pmPwrIso()
                key = "%s_%d" % (test , freq)
                entry = { key : calval}
                print entry
                self.CAL.update(entry)
        # save the calibration directory
        self.writeCAL()

    # save the Calibration directory as a pickle file
    def writeCAL(self):
        pickle.dump( self.CAL, open( "calibration.pkl", "wb"))
        
    # load the Calibration pickle file of complain if not found
    def loadCAL(self):
        self.CAL = {}
        try:
            self.CAL = pickle.load( open("calibration.pkl", "rb"))
        except:
            print "Calibration required!"
            
    # print the calibraion directory
    def printCAL(self):
        for test in self.SeqCal:
            self.printCalEntry(test)
                
    def printCalEntry(self, test):
        for freq in self.FreqList:
            key = "%s_%d" % (test, freq)
            print "%10s  %f" % ( key, self.CAL[key])
            
    ##### Isolation and Loss test #####
    # optional test sequence list or frequency list may be passed in
    # default 4X4 sequence and local frequency list used
    def testSequence(self, **kwargs):
        freqlist = kwargs.get('freqlist',self.FreqList)
        testSeq  = kwargs.get('testSeq',self.Seq4X4)
        print "testSequence()"
        for test in testSeq:
            self.SelPath(test)
            # pause test to debug
#            junk = raw_input("Testing %s to %s" % (test[1:3], test[3:]))
            for freq in freqlist:
                print "Testing %s to %s %dMHz" % (test[1:3], test[3:], freq)
                self.setFreq( freq)
                sleep(.5)
                val = self.readPower( test, freq )
                # write value to the database
                column_name = "%s_%d" % (test , freq)
                self.dbWrite( str(val), column_name)
    
    # set the frequency of the signal generator, and both power meters
    def setFreq(self, freq):
        self.pmFreqLoss( freq)
        self.pmFreqIso( freq)
        self.sgFreq( str(freq) + 'MHz')
       
    # read the power for this test and frequency
    def readPower( self, test, freq ):
        # first character of the test name indicates power or loss reading
        if test[0] == 'L':
            val = self.pmPwrLoss()
        if test[0] == 'I':
            val = self.pmPwrIso()
        # apply the calibration to the power
        key = "%s_%d" % (test, freq)
        offset = self.CAL[key]
        rtnval = val - offset
        print "%s: %f - %f == %f" % (key,val,offset,rtnval)
        return rtnval

    ##### external equipment / functions #####
    #
    def __swtOn(self, switch):
        print "ON: %d" % switch

    def __swtOff(self, switch):
        print "OFF:%d" % switch
        
    def __pmPwrLoss(self):
        loss = random.uniform(0.1,2.5)
        print "loss = " , loss
        return loss
        
    def __pmFreqLoss(self, freqstr):
        print "pmFreqLoss = " , freqstr
        
    def __pmPwrIso(self):
        iso = random.uniform(-1.1,0.5)
        print "iso  = " , iso
        return iso

    def __pmFreqIso(self, freqstr):
        print "pmFreqIso = " , freqstr
        
    def __sgFreq(self, freqstr):
        print "setFreq(%s)" % freqstr
        
    def __sgAttn(self, attn):
        print "setAttn(%s)" % power
        
    def __dbWrite(self, entry, column_name):
        print "dbWrite( %s, %s )" % (entry, column_name)
        

#########################################################################################
#
#   
        
def test_hw_Cal():
    from testlib.equip.nrpz11 import nrpz11
    from testlib.equip.hp11713A import hp11713A
    from sg6000l import SG6000L
    
    swt = hp11713A( host='10.8.9.22')
    
    pmLoss = nrpz11("RSNRP::0x000c::102973::INSTR", timeout=10)
    pmIso  = nrpz11("RSNRP::0x000c::100759::INSTR", timeout=10)
    sg = SG6000L(port=16)
    pmLoss.setoffset(0)
    pmIso.setoffset(0)
    
    
    c = combiner(pmPwrLoss=pmLoss.avgPower,
                        pmFreqLoss=pmLoss.setfreq,
                        pmPwrIso=pmIso.avgPower,
                        pmFreqIso=pmIso.setfreq,
                        sgFreq=sg.setFreq,
                        swtOn=swt.SwitchOn,
                        swtOff=swt.SwitchOff)
    c.calSequence()
    c.printCAL()
    

    
    
def test_Cal():
    c = combiner()
    c.calSequence()
    c.printCAL()
    
def test_db2x2():
    from testlib.util.db import Db
    tdata = Db('nxntest.db', 'NXN_DB')
    tdata.de_debug = 1
    c = combiner(dbWrite=tdata.Entry)
    c.testSequence( testSeq=c.Seq2X2)
    tdata.Close()
    
def test_db4x4():
    from testlib.util.db import Db
    tdata = Db('nxntest.db', 'NXN_DB')
    tdata.de_debug = 1
    c = combiner(dbWrite=tdata.Entry)
    c.testSequence( testSeq=c.Seq4X4)
    tdata.Close()
    
def test_printCal():
    c = combiner()
    c.printCAL()
    
    
if __name__ == '__main__':
    test_hw_Cal()
    
        

            
    
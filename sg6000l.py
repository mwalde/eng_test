## SG6000L
from testlib.util.enhancedserial import EnhancedSerial
from time import sleep
#from serial import Serial

class SG6000L( EnhancedSerial):

    def __init__(self, **kwargs):
        port = kwargs.get('port', 4)
        baud = kwargs.get('baud', 115200)
        timeout = kwargs.get('timeout',.1)
        EnhancedSerial.__init__( self, port=port, baudrate=baud, timeout=timeout )
        id = self.write_wait( '*IDN?')
        if id.count('SG6000L'):
            print  id
        else:
            print 'SG6000L NOT FOUND'
        
    def write_wait( self, msg):
        self.write( msg + '\n')
#        result = self.readline(timeout=.1)
        result = self.read_until("\n")
        return result

    def setFreq( self, freqstr):
        msg = 'FREQ:CW %s\n' % freqstr
        self.write(msg)

    def setAttn( self, attn):
        msg = 'ATT %s\n' % str(attn)
        self.write(msg)


    def readFreq( self):
        msg = 'FREQ:CW?\n'
        result = self.write_wait(msg)
        return result

def test():
    sg = SG6000L()
    sg.setFreq('5550MHZ')
    sg.setAttn(22.1)
    sleep(1)
    sg.setAttn(25.1)
    sleep(1)
    
#    print sg.readFreq()
    
        
if __name__ == '__main__':
    test()

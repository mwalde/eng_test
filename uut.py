# Unit Under Test
#
from testlib.radio.af5ghz import af5ghz_serial, af5ghz_telnet
from afhttp import page_labefana, afhttp

class uut():
    ipaddr = None
    comport = None
    opmode = None
    t = None
    s = None
    w = None
    
    def __init__(self, **kwargs):
        self.ipaddr = kwargs.get('ipaddr', '192.168.1.20')
        self.comport = kwargs.get('comport', 1)
        self.opmode = kwargs.get('opmode', 'slave')
        self.username = kwargs.get('username','ubnt')
        self.password = kwargs.get('password','ubnt')
   
    def telnet( self ):
        self.t =  af5ghz_telnet( None )
        self.t.connect( self.ipaddr, user=self.username, passwd=self.password)
        # Need to handle error cases
        return True

    def serial( self ):
        if self.comport == None:
            print "Serial comport not defined"
            return False
        self.s = af5ghz_serial( comport=self.comport, username=self.username, password=self.password )
        # Need to handle error case
        return True
        
    def web( self ):
        self.page_list = [page_labefana()]
        self.w = afhttp( self.ipaddr, pages=self.page_list, uesername=self.username, password=self.password)
        
    def close( self ):
        if self.w:
            self.w.browser.quit()
        
           
           
# test code
if __name__ == '__main__':
    slave = uut( ipaddr = '10.8.9.195')
    slave.telnet()
    print slave.t.readADIatten( 0 )
    print slave.t.readADIatten( 1 )


    
    
    
    #    print slave.t.revFPGA()
#    slave.serial()
#    print slave.s.revSW()
#    slave.web()
#    print slave.w.get_page_field("labefana","Date")




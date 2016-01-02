import sys
import os
from time import sleep
import pickle

# sweep through a range of values and execute an optional
# function with each value change

class sweeplist():
    seq = []
    index = 0
    def __init__(self, arg, valfcn=None,  infofcn=None, file=None, ):
        self.infofcn = infofcn
        print type(arg)
        if type(arg) is list:
            self.seq = arg
        
        if type(arg) is tuple:
            if len(arg) == 3:
                print len(arg)
                self.seq = range( arg[0], arg[1], arg[2] )
                print self.seq

        self.freshstart = True  # this is a freshstart if we don't read a previous state file
                
        self.file = file
        self.valfcn = self.__dummy1__

        if valfcn:
            self.valfcn = valfcn
        
        d = None
        if file:
            d = self.read_file(file)
        if d:
            self.index = d
        self.gen = self.generate()

    def regen( self ):
#        print "regen(%s)" % self.file
        self.gen = self.generate()

    def generate( self ):
        print "generate(%s) " % self.file
        while self.index < len(self.seq):
            val = self.seq[self.index]
#            print val,self.index
            self.valfcn(val, self.infofcn)
            self.index+=1
            self.write_file()
#            print "yield val ",val
            yield val
            
        self.index = 0
        self.write_file()
        return

    def next( self):
#        print "next(%s)"% self.file
        try:
            val = self.gen.next()
#            print "genval = ", val
        except:
            val = None
        return val
       
    def __dummy1__( self, val, info ):
        print type(info)
        return None
        
    def read_file( self, file ):
        d = None
        try:
            with open( file + '.state', 'rb') as handle:
                d = pickle.load(handle)
                print "reading ", file
                self.freshstart = False
                print d
        except:
            a = 1
#            print "no such file %s" % file
#            print "Sweep state file read error: %s " % file, sys.exc_info()[0]
        return d
        
    def write_file(self):
        if self.file:
            d = self.index
            with open( self.file + '.state', 'wb') as handle:
                pickle.dump(d, handle)
          
    def clean(self):
        try:
            os.remove( self.file + '.state' )
        except:
            c = 1
               
                
                
        
    
           
class sweep():
    def __init__(self, start=0, stop=0, step=1 , valfcn=None, file=None):
        self.freshstart = True
        self.start = start
        self.stop = stop
        self.step = step
        self.file = file
        self.valfcn = self.__dummy1__

        if valfcn:
            self.valfcn = valfcn
        
        self.curval = None
        self.lastval = None
        d = None
        if file:
            d = self.read_file(file)
        if d:
            self.curval = d[0]
            self.lastval = d[1]
        self.gen = self.generate()


    def regen( self ):
        self.gen = self.generate()

    def generate( self ):
        print "generate curval ", self.curval
        if self.curval:
            startval = self.curval
        else:
            startval = self.start
        print "startval %d  stop %d  step %d" % (startval, self.stop, self.step)
        for val in range( startval, self.stop, self.step):
            self.lastval = self.curval
            self.curval = val
            self.valfcn(val)
            self.write_file()
            yield val
        self.lastval = None
        self.curval = None
        self.write_file()
        return

    def next( self):
        try:
            val = self.gen.next()
        except:
            self.curval = self.lastval = None
            val = None
        return val
       
    def __dummy1__( self, val ):
        return None
        
    def read_file( self, file ):
        d = None
        try:
            with open( file + '.state', 'rb') as handle:
                d = pickle.load(handle)
                print "reading ", file
                self.freshstart = False
                print d
        except:
            a = 1
#            print "no such file %s" % file
#            print "Sweep state file read error: %s " % file, sys.exc_info()[0]
        return d
        
    def write_file(self):
        if self.file:
            d = (self.curval, self.lastval)
            with open( self.file + '.state', 'wb') as handle:
                pickle.dump(d, handle)

    def clean(self):
        # just clear our saved data for now
        # delete file too?
#        self.curval = self.lastval = None
#        self.write_file()
        try:
            os.remove( self.file + '.state' )
        except:
            c = 1
            
        
        
         
            
def freq_change( freq, info ):
    print "freq_change( %s )" % freq
    
         
def sweeptest():
    bw = sweeplist((10, 12, 1), file='bw')
    pwr = sweeplist((56, 58, 1), file='pwr')
    frq = sweeplist((5125, 5500, 100), file='frq',valfcn=freq_change, infofcn="string")
    
    bw.regen()
    ChBW = bw.next()
    while ChBW:
        print "ChBw ", ChBW
        pwr.regen()
        power = pwr.next()
        while power:
            print "power ", power
            frq.regen()
            freq = frq.next()
            while freq:
                print "freq ", freq
                sleep(1)
                freq = frq.next()
            power = pwr.next()
        ChBW = bw.next()
    bw.clean()
    pwr.clean()
    frq.clean()
    
def mkstate():
    thm  = sweep( -30, 70,5, file='thm')             
    bw   = sweep( 50, 51, 1, file='bw')             
    pwr  = sweep( 15, 26, 1, file='pwr')  
    frq  = sweep( 5655, 5926, 1, file='frq')

    thm.clean()
    bw.clean()
    pwr.clean()
    frq.clean()
   
    thm.regen()
    temp = thm.next()
    bw.regen()
    temp = bw.next()
    pwr.regen()
    temp = pwr.next()
    frq.regen()
    temp = frq.next()



                

        
if __name__ == '__main__':
#    mkstate()
    sweeptest()


    
    

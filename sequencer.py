import sys
import os
from time import sleep
import pickle

# sequence through a list of objects or a range of values.
# current list index kept in non-volatile file. Prevoius index
# used when restarting the sequence after a fault.

class sequencer():
    dbg = True
    seq = []
    index = 0
    def __init__(self, arg, file=None, ):
        if type(arg) is list:
            self.seq = arg
            print type(arg[0])

        if type(arg) is tuple:
            if len(arg) == 3:
                print len(arg)
                self.seq = range( arg[0], arg[1], arg[2] )
                print self.seq

        # this is a freshstart if we don't read a previous state file
        self.freshstart = True
        self.file = file

        d = None
        if file:
            d = self.read_file(file)
        if d:
            self.index = d

        self.gen = self.generate()

    def regen( self ):
        self.gen = self.generate()

    def generate( self ):
        while self.index < len(self.seq):
            val = self.seq[self.index]
            yield val
            self.index+=1
            self.write_file()

        self.index = 0
        self.write_file()
        return

    #---------------------------------------------------------------
    #   Ilm an iterator
    #---------------------------------------------------------------
    def __iter__(self):
        return self

    def next( self):
        return self.gen.next()

    def read_file( self, file ):
        d = None
        try:
            with open( file + '.state', 'rb') as handle:
                d = pickle.load(handle)
                if self.dbg:
                    print "reading ", file
                self.freshstart = False
                if self.dbg:
                    print d
        except:
            a = 1
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


def freq_change( freq, info ):
    print "freq_change( %s )" % freq
    sleep(1)


def sequencer_test():
    bw = sequencer((10, 12, 1), file='bw')
    pwr = sequencer((56, 58, 1), file='pwr' )
    frq = sequencer((5125, 5500, 100), file='frq')




    bw.regen()
    for ChBW in bw:
        print "ChBw ", ChBW
        pwr.regen()
        for power in pwr:
            print "power ", power
            frq.regen()
            for freq in frq:
                print "freq ", freq
                freq_change( freq, None)
    bw.clean()
    pwr.clean()
    frq.clean()


if __name__ == '__main__':

    sequencer_test()

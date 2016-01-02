from sequencer import sequencer
from time import sleep


def test():
#    bw = sequencer((10, 12, 1), file='bw')
#    pwr = sequencer((56, 58, 1), file='pwr',infofcn="string" )
    frq = sequencer((5125, 5500, 100), file='frq')
    print "here goes.."
#    print frq.gen.next()
    for n in frq.gen:
        print n
        freq_change( n , None)

def freq_change(val, info):
    print "freq_change(%d)" % val
    sleep(1)

if __name__ == '__main__':

#   sequencer_test()
#    seq_fcn_test()
    test()

#! /usr/bin/env python
import sys
import os
from time import *
from testlib.equip.equip import Equip

test_list = ['5Xsweep.py']
soak_time = 10

temp_list = [ -40, -35, -30, -25, -20, -15, -10, -5, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70 ]

#temp_list = [ 25, 35 ]

def SoakTime( minutes ):
    for elapsed in range(0,minutes):
        print 'Time Remaining %2d minutes\r' % (minutes - elapsed),
        sleep(60)
    print 
    print 'Soak Time Complete'

def RunTests( temp ):
    for test in test_list:
        print "Running Test %s %s" % (test,str(temp))
        os.system( test + " " + str(temp) )
    
def test():
    eq = Equip(equiplist = ['THERM'])

    for temp in temp_list:
        eq.therm.set_temp_chamber( temp )
        eq.therm.waitTempChamber()
        SoakTime(soak_time)
        RunTests( temp )

    # a graceful shutdown
    eq.therm.set_temp_chamber( 25 )
    eq.therm.waitTempChamber()
    SoakTime(soak_time)
    eq.therm.stop()
    eq.close(['THERM'])
    
        
#====================================================================


if __name__ == '__main__':
    test()

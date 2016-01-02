from testlib.util.db import Db
from combiner import combiner


CONFIG = {
    'PMLOSS' : "RSNRP::0x000c::102973::INSTR",
    'PMISO'  : "RSNRP::0x000c::100759::INSTR",
    'SWTIP'  : "10.8.9.22",
    'SGPORT' : 16,
    'DBFILE' : 'nxntest.db',
    'DBTBL'  : 'NXN_DB',
    }

def test_hardware():
    from testlib.equip.nrpz11 import nrpz11
    from testlib.equip.hp11713A import hp11713A
    from sg6000l import SG6000L
    
    swt = hp11713A( host=CONFIG['SWTIP'])
    
    pmLoss = nrpz11(CONFIG['PMLOSS'], timeout=10)
    pmIso  = nrpz11(CONFIG['PMISO' ], timeout=10)
    sg = SG6000L(port=CONFIG['SGPORT'])
#    pmLoss.calibrate()
#    pmIso.calibrate()
    pmLoss.setoffset(0)
    pmIso.setoffset(0)
    
    tdata = Db(CONFIG['DBFILE'], CONFIG['DBTBL'])
    tdata.de_debug = 1
    
    c = combiner(pmPwrLoss=pmLoss.avgPower,
                        pmFreqLoss=pmLoss.setfreq,
                        pmPwrIso=pmIso.avgPower,
                        pmFreqIso=pmIso.setfreq,
                        sgFreq=sg.setFreq,
                        swtOn=swt.SwitchOn,
                        swtOff=swt.SwitchOff,
                        dbWrite=tdata.Entry)
    c.initialize()
    c.printCAL()
    c.testSequence( testSeq=c.Seq2X2)
    tdata.Close()
    
if __name__ == '__main__':
    test_hardware()

 

 
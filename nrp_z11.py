import visa #read the help here: http://pyvisa.readthedocs.org/en/latest/api/highlevel.html
# import numpy as np #read the help here: http://docs.scipy.org/doc/numpy/
# import matplotlib.pyplot as plt #read the help here: http://matplotlib.org/users/pyplot_tutorial.html
# RSNRP::0x000c::100769:INSTR  
#open the instrument session
NRPZ1 = visa.instrument ("RSNRP::0x000c::100759::INSTR")
NRPZ2 = visa.instrument ("RSNRP::0x000c::100760::INSTR")

#reset the instrument
print NRPZ1.ask("*idn?")
print NRPZ2.ask("*idn?")


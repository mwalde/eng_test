import sys
import time
import argparse
import re
import itertools
import ast
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class page_labefana():
    name = 'labefana'
    page = 'labefana.cgi'
    title = 'Device engineering utility'

    field = {}

    Radio_Board_Status = {
        "Date": "date",
        "Uptime": "uptime",
        "Link Uptime": "linkuptime",
        "FW Version": "fwversion",
        "Device Name": "hostname",
        "Board SysId": "sysid",
        "Board PCBa": "pcbaid",
        "HW Revision": "hwrev",
        "MGMT MAC": "mgmtmac",
        "MGMR":"mgmtstate",
        "DATA": "datastate",
        "Link Mode": "linkmode",
        "Link State": "linkstate",
        "Duplex": "duplex",
        "TX Frequency": "tx_frequency",
        "RX Frequency": "rx_frequency",
        "TX Chan Width": "txchanwidth",
        "RX Chan Width": "rxchanwidth",
        "AGC0 (A/F)": "AGC0",
        "AGC1 (A/F)": "AGC1",
        "Resync Count": "ReSync",
        "X Pol from Pilot":"XpolPilot",
        "X Pol from Preamble": "XpolPre",
        "Chain Isolation": "ChainIsolation",
        "Chain 0 EVM": "Chain0EVM",
        "Chain 1 EVM": "Chain1EVM",
        "BER": "BER",
        "ADI Test Pins": "TestPins",
        "RP Flow Cntl": "rpflowcntl",
        "Invictus Flow Cntl":"radioflowcntl",
        "MAC Flow Cntl": "macflowcntl",
        "Link Part Flow Cntl": "linkpartflowcntl",
        "Local Mod Rate": "speed",
        "Remote Mod Rate": "remote_speed",
        "TX Capacity": "txcapacity",
        "RX Capacity": "rxcapacity",
        "TX Power (EIRP)": "txpowerdisp",
        "Conducted TX Power": "condtxpowerdisp",
        "Antenna Gain": "antgaindisp",
        "Cable Loss": "cablelossdisp",
        "RX Power0": "rxpower0",
        "RX Power1": "rxpower1",
        "Radio Temp RX": "boardtemp0",
        "Radio Temp TX": "boardtemp1",
        "DCXO Mode": "DCXOmode",
        "Freq": "reffreq",
        "Freq Error": "freqerr",
        "TX Freq": "tx_freq",
        "Freq Correction": "fcstate",
        "Coarse": "coarse",
        "Fine": "fine",
        "Coarse (A/F)": "hwcoarse",
        "Fine (A/F)": "hwfine",
        "Coarse Step": "coarsestep",
        "Fine Step": "finestep",
        "Old Course": "oldcoarse",
        "Old Fine": "oldfine",
        "Old Freq": "oldreffreq",
        }

    Radio_Statistics = {
        "Sessions": "sesscnt",
        "Reg Reqs Sent": "regreqsnt",
        "Reg Reqs Rcvd": "regreqrcvd",
        "Reg Grants Sent": "reggntsnt",
        "Reg Grants Rcvd": "reggntrcvd",
        "GPS INS Count": "gpsinscnt",
        "GPS OOS Count": "gpsooscnt",
        "KeepAlives Sent": "kasnt",
        "KeepAlives Rcvd": "karcvd",
        "KeepAlive Rsp Sent": "karspsnt",
        "KeepAlive Rsp Rcvd": "karsprcvd",
        "Enable Reqs Sent": "enareqtx",
        "Enable Reqs Rcvd": "enareqrx",
        "Enable Rsp Sent": "enarsptx",
        "Enable Rsp Rcvd": "enarsprx",
        "DFS Detects CAC": "dfsdetcac",
        "DFS Detects Reg": "dfsdetreg",
        "DFS Detects Ena": "dfsdetena",
        "DFS Dets Oper": "dfsdetoper",
        "DFS Detcts Beacon": "dfsdetbeacon",
        "DFS No Freq Avail": "dfsnofreq",
        "Reg Timeouts": "invalidreg",
        "Session Drops": "sessdrop",
        "RF OOS Listening": "rfooslist",
        "RF OOS Get Freq": "rfoosgetfreq",
        "RF OOS Registering": "rfoosreg",
        "RF OOS Enabling": "rfoosena",
        "RF OOS Operaional": "rfoosoper",
        "Calibrate Count": "calibrates",
        "AGC Re-syncs": "agcresync",
        }

    Frame_Configuration = {
        "Reg00: CP Length": "CPdisp",
        "Reg04: Frame Len": "fr_len",
        "Reg08: TX DLC": "tx_dlc",
        "Reg0C: TX CP": "tx_cp",
        "Reg10: TX Stop": "tx_stop",
        "Reg14: RX Start": "rx_st",
        "Reg18: RX Length": "rx_len",
        "Reg1C": "Reg1C",
        "Reg20: RX Align": "rx_align",
        "Duty Cycle": "dutycycle",
        "TX Symbols": "txsymbol",
        "RX Symbols": "rxsymbol",
        "TX Rate(Cur Mod)": "curmaxtxrate",
        "RX Rate(Cur Mod)": "curmaxrxrate",
        "Rate (Cur Mod)": "curmaxrate",
        "Max TX Rate": "maxtxrate",
        "Max Rx Rate": "maxrxrate",
        "Max Rate": "maxrate",
        }

    DFS_Status = {
        "DFS Reset": "dfsst",
        "DFS Live": "dfslive",
        "DFS Int Mask": "dfsint",
        "DFS Version": "dfsmode",
        "DFS Detection": "dfs_detects",
        "Frequency 1 Status": "dfs_status1",
        "Frequency 2 Status": "dfs_status2",
        "Frequency 3 Status": "dfs_status3",
    }


    def __init__( self, **kargs ):
        self.field = dict(self.Radio_Board_Status.items() +
                          self.Frame_Configuration.items() +
                          self.DFS_Status.items() +
                          self.Radio_Statistics.items() )

    def get( self, field_name ):
        field = self.field.get( field_name, None)
        return field

class afhttp( ):
    current_page = None
    browser = None



    def __init__( self, ipaddr, **kwargs ):
        self.lasttime= time.time()
        self.ipaddr = ipaddr
        self.pages = kwargs.get('pages',[])
        self.username = kwargs.get('username','ubnt')
        self.password = kwargs.get('password','ubnt')
        self.width =    kwargs.get('width', 900)
        self.height =   kwargs.get('height', 800)

        if len(self.pages):
            print "pages loaded:"
            for p in self.pages:
                print "name: %s page: %s title: %s" % (p.name,p.page,p.title)

        print self.username
        print self.password
        # Create a new instance of the Firefox driver
        self.browser = webdriver.Firefox()
        self.browser.set_window_size(self.width, self.height)
        self.browser.implicitly_wait(5) # seconds
        print "opening web site" # /login.cgi?uri=/labefana.cgi
        status = True
        try:
            print self.browser.get("http://%s" % self.ipaddr)
            self.usernameElement = WebDriverWait(self.browser, 1).until(EC.presence_of_element_located((By.ID, "username")))
        except:
            print "open failed"
            status = False

        print "status ", status
        if status:
            self.findsend('username', self.username)
            self.findsend('password', self.password)

#           time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
            self.loginElement = self.browser.find_element_by_css_selector("input[type=\"submit\"]")
            self.loginElement.click()

    def goto_page(self, pagename):
        now = time.time()

        if self.current_page == pagename and now - self.lasttime < 2:
            return  True    # do nothing
        self.browser.get("http://%s/%s" % (self.ipaddr, pagename))
        self.lasttime = now
        self.current_page = pagename
#        print "page title: %s" % (self.browser.title)
        return True

    def findsend( self, find, send):
        item = self.browser.find_element_by_id(find)
        item.clear()
        item.send_keys( send )
        return True

    def get_by_id( self, find ):
        time = 0
        timeout = 2
        try:
            text = WebDriverWait(self.browser, timeout).until(EC.presence_of_element_located((By.ID, find))).text
        except:
            print "ERROR Cound not find ID: %s" % find
            return None

        while text == ' ' and time < timeout:
            sleep(.5)
            time += .5
            text = self.browser.find_element_by_id(find).text
        print "id:%s = " % (find), text
        return text

    def load_page( self, page_name ):
        for p in self.pages:
            if p.name == page_name:
                if self.goto_page( p.page ):
                    self.page = p
                    return p
        self.page = None
        print "load_page( %s ) error" % page_name
        return None



    def get_page_field( self, page_name, field_name):
        if self.load_page( page_name ):
            field = self.page.get(field_name)
            if field:
                text = self.get_by_id( field )
                if text:
                    return text
                else:
                    print "Field Name not found: %s" % field
        print "Page: %s Field: %s Not found" % (page_name,field_name)
        return None

    def __del__(self):
        print "__del__"
        if self.browser:
            print "browser.quit()"
            self.browser.quit()

    def cmdline( self, cmd ):
        if self.load_page( "labefana" ) == None:
            return None
        try:
            e = self.browser.find_element_by_name("exec")
        except:
            print "element 'exec' not found"
            return None
        e.clear()
        e.send_keys( cmd )

        try:
            self.browser.find_element_by_css_selector("form > input[type=\"submit\"]").click()
        except:
            print "element not found 'form > input[type=\"submit\"]'"
            return None

        sleep(2)

        rsp = self.browser.find_element_by_css_selector("pre").text
        return rsp






if __name__ == '__main__':




    page1 = page_labefana()

    web = afhttp('10.8.8.138', pages=[page1])

    print web.cmdline("af af")

    for i in range(0,5,1):

        for key in page1.field:
            web.get_page_field("labefana", key)
        time.sleep(1)

    #web.get_page_field("labefana","DFS Live")
    #web.get_page_field("labefana","Date")

    #web.goto_page( "labefana.cgi")
    #sleep(2)
    #print web.get_by_id("linkstate")

    #print "page title: ", web.page.title
    #print "page.field['DFS reset'] ", web.page.field["DFS Reset"]
    sleep(2)
    #web.goto_page( "services.cgi")
    #sleep(2)
    #web.goto_page( "advanced.cgi")
    #sleep(2)


    print "exit"



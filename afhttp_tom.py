#!/usr/bin/python

# A Selenium WebDriver program to interface with AirFiber radios.

import sys
import time
import argparse
import re
import itertools
import ast

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class Http(object):

    ObjCount = 0 # Init Class Variable

    def __init__(self, ipaddress, username, password, quiet):
        #print "afhttp07"     ######### UPDATE THIS FOR ANY NEW CHANGES TO THIS FILE #########
        Http.ObjCount += 1 # Class Variable
        self.objid = Http.ObjCount
        self.address = ipaddress
        self.username = username
        self.password = password
        self.width = 900
        self.height = 800
        self.browser = None
        self.firmware_version = ''
        self.radiotype = ''
        self.buildnumber = ''
        self.version = ''
        self.versionnumber = ''
        self.devicename = ''
        self.loggedin = False
        self.quiet = quiet
        self.new_browser()

    def __del__(self):
        Http.ObjCount -= 1

    def new_browser(self):
        # Create a new instance of the Firefox driver
        self.browser = webdriver.Firefox()
        self.browser.set_window_size(self.width, self.height)
        self.browser.implicitly_wait(30) # seconds

    def login(self):
        # Gets: self.firmware_version, self.radiotype, self.buildnumber, self.version, self.versionnumber
        if self.quiet == False:
            print 'login() with retries.'
        # Go to the radio's home page
        self.available = False
        self.retries = 180
        while (self.available == False) and (self.retries > 0):
            try:
                if self.quiet == False:
                    print 'try: Wait.until(EC.presence_of_element_located((By.ID, "username")))'
                self.browser.get("http://%s" % self.address)
                self.usernameElement = WebDriverWait(self.browser, 1).until(EC.presence_of_element_located((By.ID, "username")))
                self.available = True
                time.sleep(5)
            except:
                self.retries -= 1
                if self.quiet == False:
                    print 'exception: Wait.until(EC.presence_of_element_located((By.ID, "username"))), Retries left: %s' % self.retries
                time.sleep(1)
                pass
        if self.available == False:
            print 'WEB PAGE LOGIN FAILURE.'
            sys.exit(1)

        self.usernameElement.clear()
        time.sleep(.5)
        self.usernameElement.send_keys(self.username)
        time.sleep(1)
    
        self.passwordElement = self.browser.find_element_by_id("password")
        self.passwordElement.clear()
        time.sleep(.5)
        self.passwordElement.send_keys(self.password)
        time.sleep(1)
    
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.loginElement = self.browser.find_element_by_css_selector("input[type=\"submit\"]")
        self.loginElement.click()
    
        WebDriverWait(self.browser, 30).until(EC.title_contains("Main"))
        self.loggedin = True
        self.click_main_tab() # to gain focus on main page
        self.firmware_version = self.get_system_fw_version()
        self.radiotype = self.get_system_radio_type()
        self.buildnumber = self.get_system_build_number()
        self.version = self.get_main_version()
        self.versionnumber = self.get_version_number()
        if self.quiet == False:
            print '    firmwareversion = %s' % self.firmware_version
            print '    radiotype = %s' % self.radiotype
            print '    build # = %s' % self.buildnumber
            print '    version # = %s' % self.version
            print '    version number # = %s' % self.versionnumber
            print
            print 'Done with log in.'

    def logout(self):
        if self.quiet == False:
            print 'logout()'
        try:
            self.browser.find_element_by_css_selector("input[type=\"button\"]").click()
        except:
            if self.quiet == False:
                print 'Failed to find Logout button. Go to main tab and try again.'
            self.goto_main_tab()
            self.browser.find_element_by_css_selector("input[type=\"button\"]").click()
        WebDriverWait(self.browser, 30).until(EC.title_contains("Login"))
        self.loggedin = False
        self.browser.quit()
        if self.quiet == False:
            print 'Done with log out.'

    def load_fw(self, image_pathname):
        """ Will attempt to run a firmware update.  Requires login first.  Will leave in logged out state. """
        self.fw_image = image_pathname
        
        if self.quiet == False:
            print 'load_fw()'
        self.tabname = 'system'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            #self.goto_main_tab()
            self.click_system_tab()
    
        time.sleep(2)
        self.fwfileElement = self.browser.find_element_by_id("fwfile")
        self.fwfileElement.send_keys("%s" % self.fw_image)
        time.sleep(1)
        self.btn_fwuploadElement = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.ID, "btn_fwupload")))
        self.btn_fwuploadElement.click()
    
        self.btn_fwupdateElement = WebDriverWait(self.browser, 200).until(EC.presence_of_element_located((By.ID, "btn_fwupdate")))
        self.btn_fwupdateElement.click()
        time.sleep(120)
        WebDriverWait(self.browser, 600).until(EC.title_contains("Login"))
        time.sleep(5)
        if self.quiet == False:
            print 'Done executing load FW image.'
        self.login()

    def goto_main_tab(self):
        if self.quiet == False:
            print 'goto_main_tab()'
        try:
            self.browser.get("http://%s/index.cgi" % self.address)
        except:
            if self.quiet == False:
                print 'goto_main_tab() exception, re-login to webpage at %s' % self.address
            time.sleep(2)
            self.login()
            time.sleep(2)
            self.browser.get("http://%s/index.cgi" % self.address)
        time.sleep(1)

    def goto_wireless_tab(self):
        if self.quiet == False:
            print 'goto_wireless_tab()'
        try:
            self.browser.get("http://%s/link.cgi" % self.address)
        except:
            if self.quiet == False:
                print 'goto_wireless_tab() exception, re-login to webpage at %s' % self.address
            time.sleep(2)
            self.login()
            time.sleep(2)
            self.browser.get("http://%s/link.cgi" % self.address)
        time.sleep(1)

    def goto_network_tab(self):
        if self.quiet == False:
            print 'goto_network_tab()'
        try:
            self.browser.get("http://%s/network.cgi" % self.address)
        except:
            if self.quiet == False:
                print 'goto_network_tab() exception, re-login to webpage at %s' % self.address
            time.sleep(2)
            self.login()
            time.sleep(2)
            self.browser.get("http://%s/network.cgi" % self.address)
        time.sleep(1)

    def goto_advanced_tab(self):
        if self.quiet == False:
            print 'goto_advanced_tab()'
        try:
            self.browser.get("http://%s/advanced.cgi" % self.address)
        except:
            if self.quiet == False:
                print 'goto_advanced_tab() exception, re-login to webpage at %s' % self.address
            time.sleep(2)
            self.login()
            time.sleep(2)
            self.browser.get("http://%s/advanced.cgi" % self.address)
        time.sleep(1)

    def goto_services_tab(self):
        if self.quiet == False:
            print 'goto_services_tab()'
        try:
            self.browser.get("http://%s/services.cgi" % self.address)
        except:
            if self.quiet == False:
                print 'goto_services_tab() exception, re-login to webpage at %s' % self.address
            time.sleep(2)
            self.login()
            time.sleep(2)
            self.browser.get("http://%s/services.cgi" % self.address)
        time.sleep(1)

    def goto_system_tab(self):
        if self.quiet == False:
            print 'goto_system_tab()'
        try:
            self.browser.get("http://%s/system.cgi" % self.address)
        except:
            if self.quiet == False:
                print 'goto_system_tab() exception, re-login to webpage at %s' % self.address
            time.sleep(2)
            self.login()
            time.sleep(2)
            self.browser.get("http://%s/system.cgi" % self.address)
        time.sleep(1)

    def click_main_tab(self):
        if self.quiet == False:
            print 'click_main_tab() -> goto_main_tab().'
        self.goto_main_tab()

    def click_wireless_tab(self):
        if self.quiet == False:
            print 'click_wireless_tab() -> goto_wireless_tab().'
        self.goto_wireless_tab()

    def click_network_tab(self):
        if self.quiet == False:
            print 'click_network_tab() -> goto_network_tab().'
        self.goto_network_tab()

    def click_advanced_tab(self):
        if self.quiet == False:
            print 'click_advanced_tab() -> goto_advanced_tab().'
        self.goto_advanced_tab()

    def click_services_tab(self):
        if self.quiet == False:
            print 'click_services_tab() -> goto_services_tab().'
        self.goto_services_tab()

    def click_system_tab(self):
        if self.quiet == False:
            print 'click_system_tab() -> goto_system_tab().'
        self.goto_system_tab()

    def get_tab_title(self):
        self.title = self.browser.title
        if self.quiet == False:
            print 'get_tab_title().'
            print "Title: ", self.title
        return self.title

    def get_main_device_name(self):
        if self.quiet == False:
            print 'get_main_device_name().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.devicename = self.browser.find_element_by_id("hostname").text
        if self.quiet == False:
            print "Device Name: %s" % self.devicename
        return self.devicename

    def get_main_operating_mode(self):
        if self.quiet == False:
            print 'get_main_operating_mode().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        self.opmode = self.browser.find_element_by_id("linkmode").text.encode('ascii','ignore').strip()
        while self.opmode =='':
            time.sleep(1)
            self.opmode = self.browser.find_element_by_id("linkmode").text.encode('ascii','ignore').strip()
        if self.quiet == False:
            print "    Operating Mode: ", self.opmode
        return self.opmode

    def get_main_rf_link_status(self):
        if self.quiet == False:
            print 'get_main_rf_link_status().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.rflinkstatus = self.browser.find_element_by_id("linkstate").text
        if self.quiet == False:
            print "RF Link Status: ", self.rflinkstatus
        return self.rflinkstatus

    def wait_main_rf_link_status_operational(self):
        if self.quiet == False:
            print 'wait_main_rf_link_status_operational().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.link_status = ''
        while self.link_status.lower() != 'operational':
            time.sleep(1)
            self.link_status = self.get_main_rf_link_status()
            if self.quiet == False:
                print 'main_rf_link_status = ', self.link_status
        return self.link_status

    def wait_main_rf_link_status_operational_retry(self, retries):
        self.retries = retries
        if self.quiet == False:
            print 'wait_main_rf_link_status_operational_retry().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.link_status = ''
        while (self.link_status.lower() != 'operational') and (self.retries > 0):
            time.sleep(1)
            self.link_status = self.get_main_rf_link_status()
            self.retries -= 1
            if self.quiet == False:
                print 'main_rf_link_status = ', self.link_status
        return self.link_status

    def get_main_link_name(self):
        if self.quiet == False:
            print 'get_main_link_name().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.linkname = self.browser.find_element_by_id("linkname").text.encode('ascii','ignore').strip()
        while self.linkname == '':
            time.sleep(1)
            self.linkname = self.browser.find_element_by_id("linkname").text.encode('ascii','ignore').strip()
        if self.quiet == False:
            print "Link Name: ", self.linkname
        return self.linkname

    def get_main_security(self):
        if self.quiet == False:
            print 'get_main_security().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.security = self.browser.find_element_by_id("security").text
        if self.quiet == False:
            print "Security: ", self.security
        return self.security

    def get_main_version(self):
        # Returns:  v2.1-dev.21845
        if self.quiet == False:
            print 'get_main_version().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.version = self.browser.find_element_by_id("fwversion").text
        if self.quiet == False:
            print "Version: ", self.version
        return self.version

    def get_version_number(self):
        # Returns: 2.1
        if self.quiet == False:
            print 'get_version_number()'
        try:
            self.versionstr = self.get_main_version()
            self.dashindex = self.versionstr.find('-')
            if self.dashindex != -1:
                self.versionnumber = self.versionstr[1:self.dashindex]
            else:
                self.versionnumber = self.versionstr[1:]
            if self.quiet == False:
                print '    %s' % (self.versionnumber)
        except:
            print '    get_version_number() Exception'
            self.versionnumber = ''
        return self.versionnumber


    def get_main_uptime(self):
        if self.quiet == False:
            print 'get_main_uptime().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.uptime = self.browser.find_element_by_id("uptime").text
        if self.quiet == False:
            print "Uptime: ", self.uptime
        return self.uptime

    def get_main_link_uptime(self):
        if self.quiet == False:
            print 'get_main_link_uptime().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.linkuptime = self.browser.find_element_by_id("linkuptime").text
        if self.quiet == False:
            print "Link Uptime: ", self.linkuptime
        return self.linkuptime

    def get_main_remote_mac(self):
        if self.quiet == False:
            print 'get_main_remote_mac().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        try:
            self.remotemac = self.browser.find_element_by_id("remotemac").text
        except:
            self.remotemac = ''
        if self.quiet == False:
            print "Remote MAC: ", self.remotemac
        return self.remotemac

    def get_main_remote_ip(self):
        if self.quiet == False:
            print 'get_main_remote_ip().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        try:
            self.remoteip = self.browser.find_element_by_id("remoteip").text
        except:
            self.remoteip = ''
        if self.quiet == False:
            print "Remote IP: ", self.remoteip
        return self.remoteip

    def get_main_date(self):
        if self.quiet == False:
            print 'get_main_date().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.date = self.browser.find_element_by_id("date").text
        if self.quiet == False:
            print "Date: ", self.date
        return self.date

    def get_main_duplex(self):
        if self.quiet == False:
            print 'get_main_duplex().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.duplex = self.browser.find_element_by_id("af_duplex").text.split()[0]
        if self.quiet == False:
            print "Duplex: ", self.duplex
        return self.duplex

    def get_main_tx_frequency(self, display_units=False):
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_main_tx_frequency().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.tx_frequency = self.browser.find_element_by_id("tx_frequency").text
        if self.displayunits == False:
            self.tx_frequency = ''.join(self.tx_frequency.split()[:-1])
        if self.quiet == False:
            print "Tx Frequency: ", self.tx_frequency
        return self.tx_frequency

    def get_main_rx_frequency(self, display_units=False):
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_main_rx_frequency().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.rx_frequency = self.browser.find_element_by_id("rx_frequency").text
        if self.displayunits == False:
            self.rx_frequency = ''.join(self.rx_frequency.split()[:-1])
        if self.quiet == False:
            print "Rx Frequency: ", self.rx_frequency
        return self.rx_frequency

    def get_main_channel_width(self, direction=None, display_units=False):
        self.direction = direction
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_main_channel_width(%s).' % self.direction
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        if self.direction == None:
            self.channel_width = self.browser.find_element_by_id("chanwidth").text
            self.direction = ''
        if self.direction.lower() == 'tx':
            self.channel_width = self.browser.find_element_by_id("txchanwidth").text
        else:
            self.channel_width = self.browser.find_element_by_id("rxchanwidth").text
        if self.displayunits == False:
            self.channel_width = ''.join(self.channel_width.split()[:-1])
        if self.quiet == False:
            print "Channel Width (%s): %s" % (self.direction, self.channel_width)
        return self.channel_width

    def get_main_regulatory_domain(self):
        if self.quiet == False:
            print 'get_main_regulatory_domain().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.regulatory_domain = self.browser.find_element_by_id("regdomain").text
        if self.quiet == False:
            print "Regulatory Domain: ", self.regulatory_domain
        return self.regulatory_domain

    def get_main_signal_strength(self, chain, remote=False, wait=False, wait_count=1, display_units=False):
        self.chain = chain  # 0 or 1
        self.remote = remote 
        self.displayunits = display_units
        self.wait = wait
        self.wait_count = wait_count # seconds if wait=True
        if self.quiet == False:
            print 'get_main_signal_strength(chain=%s, remote=%s).' % (self.chain, self.remote)
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        if self.remote == True:
            chain_id = 'remote_signal%s_value' % self.chain
        else:
            chain_id = 'signal%s_value' % self.chain
        self.signal_strength = self.browser.find_element_by_id(chain_id).text
        if self.signal_strength == None or self.signal_strength == '':
            self.signal_strength = '-'
        if self.wait == True:
            while (self.signal_strength.strip() == '-') and (self.wait_count > 0):
                time.sleep(1)
                self.signal_strength = self.browser.find_element_by_id(chain_id).text
                self.wait_count -= 1
        if self.displayunits == False:
            self.signal_strength = ''.join(self.signal_strength.split()[:-1])
        if self.quiet == False:
            print "%s: %s" % (self.chain_id, self.signal_strength)
        return self.signal_strength

    def get_main_current_modulation_rate(self):
        if self.quiet == False:
            print 'get_main_current_modulation_rate().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.speed = self.browser.find_element_by_id("speed").text.split()[0]
        if self.quiet == False:
            print "Speed: ", self.speed
        return self.speed

    def get_main_remote_modulation_rate(self):
        if self.quiet == False:
            print 'get_main_remote_modulation_rate().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        try:
            self.remote_speed = self.browser.find_element_by_id("remote_speed").text.split()[0]
        except: # not available if no link between master and slave
            self.remote_speed = ''
        if self.quiet == False:
            print "Remote Speed: ", self.remote_speed
        return self.remote_speed

    def get_main_tx_capacity(self, display_units=False):
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_main_tx_capacity().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.tx_capacity = self.browser.find_element_by_id("txcapacity").text
        self.tx_capacity = ''.join(self.tx_capacity.split(','))
        if self.displayunits == False:
            self.tx_capacity = ''.join(self.tx_capacity.split()[:-1])
        if self.quiet == False:
            print "Tx Capacity: ", self.tx_capacity
        return self.tx_capacity

    def get_main_rx_capacity(self, display_units=False):
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_main_rx_capacity().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.rx_capacity = self.browser.find_element_by_id("rxcapacity").text
        self.rx_capacity = ''.join(self.rx_capacity.split(','))
        if self.displayunits == False:
            self.rx_capacity = ''.join(self.rx_capacity.split()[:-1])
        if self.quiet == False:
            print "Rx Capacity: ", self.rx_capacity
        return self.rx_capacity

    def get_main_tx_power(self, display_units=False):
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_main_tx_power().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.tx_power = self.browser.find_element_by_id("txpowerdisp").text
        if self.displayunits == False:
            self.tx_power = ''.join(self.tx_power.split()[:-1])
        if self.quiet == False:
            print "Tx Power: ", self.tx_power
        return self.tx_power

    def get_main_remote_tx_power(self, display_units=False):
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_main_remote_tx_power().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        try:
            self.remote_tx_power = self.browser.find_element_by_id("remote_txpower").text
            if self.displayunits == False:
                self.remote_tx_power = ''.join(self.remote_tx_power.split()[:-1])
        except: # not available if no link between master and slave
            self.remote_tx_power = ''
        if self.quiet == False:
            print "Remote Tx Power: ", self.remote_tx_power
        return self.remote_tx_power

    def get_main_rx_gain(self): # 24G radios only
        if self.quiet == False:
            print 'get_main_rx_gain().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        try:
            self.rx_gain = self.browser.find_element_by_id("rxgaindisp").text
        except:
            self.rx_gain = ''
        if self.quiet == False:
            print "Rx Gain: ", self.rx_gain
        return self.rx_gain

    def get_main_remote_rx_gain(self): #24G radios only
        if self.quiet == False:
            print 'get_main_remote_rx_gain().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        try:
            self.remote_rx_gain = self.browser.find_element_by_id("remote_rxgain").text
        except: # not available if no link between master and slave
            self.remote_rx_gain = ''
        if self.quiet == False:
            print "Remote Rx Gain: ", self.remote_rx_gain
        return self.remote_rx_gain

    def get_main_distance(self):
        if self.quiet == False:
            print 'get_main_distance().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.distance = self.browser.find_element_by_id("distance").text
        if self.quiet == False:
            print "Distance: ", self.distance
        return self.distance

    def get_main_gps_signal_quality(self):
        if self.quiet == False:
            print 'get_main_gps_signal_quality().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.gps_signal_quality = self.browser.find_element_by_id("gps_qual").text
        if self.quiet == False:
            print "Gps Signal Quality: ", self.gps_signal_quality
        return self.gps_signal_quality

    def get_main_latitude_longitude(self):
        if self.quiet == False:
            print 'get_main_latitude_longitude().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.latitude_longitude = self.browser.find_element_by_id("gps_coord").text
        if self.quiet == False:
            print "Latitude/Longitude: ", self.latitude_longitude
        return self.latitude_longitude

    def get_main_altitude(self):
        if self.quiet == False:
            print 'get_main_altitude().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.altitude = self.browser.find_element_by_id("gps_alt").text
        if self.quiet == False:
            print "Altitude: ", self.altitude
        return self.altitude

    def get_main_synchronization(self):
        if self.quiet == False:
            print 'get_main_synchronization().'
        self.tabname = 'main'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_main_tab()
        time.sleep(1)
        self.synchronization = self.browser.find_element_by_id("gps_sync").text
        if self.quiet == False:
            print "Synchronization: ", self.synchronization
        return self.synchronization

    def click_change_button(self):
        if self.quiet == False:
            print 'click_change_button()'
        self.btn_changeElement = self.browser.find_element_by_css_selector("input[type=\"submit\"]")
        time.sleep(1)
        self.btn_changeElement.click()
        if self.quiet == False:
            print 'click_change_button() clicked'
        time.sleep(1)

    def apply_settings(self):
        if self.quiet == False:
            print 'apply_settings()'
        try:
            self.browser.find_element_by_id("apply_button").click()
        except:
            self.btn_applyElement = WebDriverWait(self.browser, 60).until(EC.presence_of_element_located((By.ID, "apply_button")))
            self.btn_applyElement.click()
        if self.quiet == False:
            print 'apply_settings() clicked'
        time.sleep(1)

    def set_wireless_link_name(self, link_name):
        # No apply
        self.link_name = link_name
        if self.quiet == False:
            print 'set_wireless_link_name(%s)' % self.link_name
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_wireless_tab()
        self.browser.find_element_by_id("essid").clear()
        self.browser.find_element_by_id("essid").send_keys(self.link_name)
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_wireless_country_code(self, country_code): # Applies the setting when selected.
        self.country_code = str(country_code)
        if self.quiet == False:
            print 'set_wireless_country_code(%s)' % self.country_code
        self.opmode = self.get_main_operating_mode() 
        if self.quiet == False:
            print 'Operating Mode: %s' % self.opmode
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_wireless_tab()
        self.country_code_dict = {'32': 'argentina', '36': 'australia', '48': 'bahrain', '52': 'barbados', '84': 'belize', '68': 'bolivia', '76': 'brazil', '96': 'brunei darussalam', '124': 'canada', '152': 'chile', '156': 'china', '170': 'colombia', '188': 'costa rica', '208': 'denmark', '214': 'dominican republic', '218': 'ecuador', '222': 'el salvador', '8191': 'engineering', '246': 'finland', '276': 'germany', '300': 'greece', '308': 'grenada', '316': 'guam', '320': 'guatemala', '340': 'honduras', '344': 'hong kong', '352': 'iceland', '356': 'india', '360': 'indonesia', '368': 'iraq', '372': 'ireland', '388': 'jamaica', '404': 'kenya', '410': 'korea republic', '422': 'lebanon', '438': 'liechtenstein', '446': 'macau', '458': 'malaysia', '484': 'mexico', '504': 'morocco', '524': 'nepal', '554': 'new zealand', '566': 'nigeria', '578': 'norway', '512': 'oman', '586': 'pakistan', '591': 'panama', '598': 'papua new guinea', '604': 'peru', '608': 'philippines', '620': 'portugal', '630': 'puerto rico', '634': 'qatar', '643': 'russia', '682': 'saudi arabia', '702': 'singapore', '710': 'south africa', '724': 'spain', '144': 'sri lanka', '158': 'taiwan', '764': 'thailand', '780': 'trinidad and tobago', '804': 'ukraine', '826': 'united kingdom', '840': 'united states', '858': 'uruguay', '860': 'uzbekistan', '862': 'venezuela'} 
        if self.country_code.isdigit():
            self.countryname = self.country_code_dict[self.country_code]
        else:
            for self.code, self.name in self.country_code_dict.items():
                if self.name == self.country_code:
                    self.countryname = self.name
        if self.quiet == False:
            print 'self.countryname = %s' % self.countryname

        self.countrycode = self.browser.find_element_by_id("change_ccode").click()
        self.countrycode = self.browser.find_element_by_id("country_select") # Pulldown
        for self.option in self.countrycode.find_elements_by_tag_name('option'):
            if self.quiet == False:
                print 'self.option.text = %s' % self.option.text
            if self.option.text.lower() == self.countryname:
                if self.quiet == False:
                    print '%s == %s' % (self.option.text.lower(), self.countryname)
                self.option.click()
                if self.quiet == False:
                    print 'self.option clicked'
                self.browser.find_element_by_id("agreed").click()
                if self.quiet == False:
                    print 'agreed clicked'
                self.browser.find_element_by_xpath("//button[@type='button'][1]").click()
                if self.quiet == False:
                    print 'Accept clicked'
                self.valid_freqs = self.browser.find_element_by_id("tx_freq_rng").text
                self.valid_freq_lower = self.valid_freqs.split()[-4][1:]
                self.valid_freq_upper = self.valid_freqs.split()[-2]
                self.tx_freq = self.browser.find_element_by_id("tx_chan_freq").get_attribute("value")
                self.rx_freq = self.browser.find_element_by_id("rx_chan_freq").get_attribute("value") 
                if self.quiet == False:
                    print 'Valid Frequencies: %s' % self.valid_freqs
                    print 'Valid Lower Frequency: %s' % self.valid_freq_lower
                    print 'Valid Upper Frequency: %s' % self.valid_freq_upper
                    print 'TX Frequency: %s' % self.tx_freq
                    print 'RX Frequency: %s' % self.rx_freq
                #if self.browser.find_element_by_id("error"):
                if (self.tx_freq < self.valid_freq_lower or self.tx_freq > self.valid_freq_upper) or (self.rx_freq < self.valid_freq_lower or self.rx_freq > self.valid_freq_upper):
                    print 'WARNING FREQUENCY CHANGED TO ALLOW COUNTRY CODE SETTING!'
                    self.browser.find_element_by_id("tx_chan_freq").clear()
                    self.browser.find_element_by_id("rx_chan_freq").clear()
                    if self.opmode.lower() == 'master':
                        self.browser.find_element_by_id("tx_chan_freq").send_keys(self.valid_freq_lower)
                        self.browser.find_element_by_id("rx_chan_freq").send_keys(self.valid_freq_upper)
                    else:
                        self.browser.find_element_by_id("tx_chan_freq").send_keys(self.valid_freq_upper)
                        self.browser.find_element_by_id("rx_chan_freq").send_keys(self.valid_freq_lower)
                    #print 'WARNING COUNTRY CODE SETTING NOT CHANGED BECAUSE OF INVALID FREQUENCY SETTINGS!'
                time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
                self.browser.find_element_by_css_selector("input[type=\"submit\"]").click()
                if self.quiet == False:
                    print 'Change clicked'
                self.apply_settings()
                if self.quiet == False:
                    self.tx_freq = self.browser.find_element_by_id("tx_chan_freq").get_attribute("value")
                    self.rx_freq = self.browser.find_element_by_id("rx_chan_freq").get_attribute("value") 
                    print 'TX Frequency: %s' % self.tx_freq
                    print 'RX Frequency: %s' % self.rx_freq
                time.sleep(5)
                break
        else:
            print 'WARNING: set_wireless_country_code(%s) not found in list.' % self.country_code
        self.click_change_button() # MIGNT NOT BE NEEDED SINCE THE COMMENT ABOVE SAYS SETTING IS APPLIED WHEN SELECTED.

    def set_wireless_wireless_mode(self, mode):
        # No apply
        self.mode = mode
        if self.quiet == False:
            print 'set_wireless_wireless_mode(%s)' % self.mode
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            #self.goto_main_tab()
            self.click_wireless_tab()
        self.wirelessmode = self.browser.find_element_by_id('wmode') # Pulldown
        for self.option in self.wirelessmode.find_elements_by_tag_name('option'): # Master="ap", Slave="sta"
            if self.quiet == False:
                print 'self.option.text = %s' % self.option.text
            if self.option.text.lower() == self.mode.lower():
                self.option.click()
                break
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_wireless_duplex(self, duplex):
        # No apply
        self.duplex = duplex # "half" | "full"
        if (self.duplex.lower() == 'full') or (self.duplex.lower() == 'fdd') or (self.duplex.lower() == 'full duplex'):
            self.dplx = 'Full Duplex'
        else:
            self.dplx = 'Half Duplex'
        if self.quiet == False:
            print 'set_wireless_duplex(%s)' % self.duplex
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            #self.goto_main_tab()
            self.click_wireless_tab()
        self.duplex_element = self.browser.find_element_by_id('af_duplex_select') # Pulldown
        for self.option in self.duplex_element.find_elements_by_tag_name('option'): # "Half Duplex" | "Full Duplex"
            if self.quiet == False:
                print 'self.option.text = %s' % self.option.text
            if self.option.text == self.dplx:
                self.option.click()
                break
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_wireless_channel_bandwidth(self, channel_bandwidth, direction=None):
        # direction == 'rx' | 'tx' or None
        # AF cmd not available before 19206
        # GUI not available before 19233
        if self.radiotype == 'AF02':
            self.direction = direction
            self.channelbandwidth = str(channel_bandwidth) # "50" | "40" | "20" | "10"
            if '50' in self.channelbandwidth.lower():
                self.chbw = '50MHz'
            elif '40' in self.channelbandwidth.lower():
                self.chbw = '40MHz'
            elif '30' in self.channelbandwidth.lower():
                self.chbw = '30MHz'
            elif '20' in self.channelbandwidth.lower():
                self.chbw = '20MHz'
            else:
                self.chbw = '10MHz'
            if self.quiet == False:
                print 'set_wireless_channel_bandwidth(%s)' % self.channelbandwidth
            self.tabname = 'wireless'
            if self.browser.title.lower().find(self.tabname.lower()) < 0:
                #self.goto_main_tab()
                self.click_wireless_tab()
            if self.direction == None:
                self.chbw_element = self.browser.find_element_by_id('tx_chan_bw_select') # Pulldown
            elif self.direction.lower() == 'tx':
                self.chbw_element = self.browser.find_element_by_id('tx_chan_bw_select') # Pulldown
            else:
                self.chbw_element = self.browser.find_element_by_id('rx_chan_bw_select') # Pulldown
            for self.option in self.chbw_element.find_elements_by_tag_name('option'): # "50 MHz" | "40 MHz" | "20 MHz" | "10 MHz"
                if self.quiet == False:
                    print 'self.option.text = %s' % self.option.text
                if self.option.text == self.chbw:
                    self.option.click()
                    break
            time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
            self.click_change_button()

    def set_wireless_output_power(self, output_power):
        # No apply
        self.output_power = output_power
        if self.quiet == False:
            print 'set_wireless_output_power(%s)' % self.output_power
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_wireless_tab()
        self.browser.find_element_by_id("txpower").clear()
        self.browser.find_element_by_id("txpower").send_keys(self.output_power)
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_wireless_master_tx_duty_cycle(self, dutycycle):
        # No apply
        self.dutycycle = dutycycle
        if self.quiet == False:
            print 'set_wireless_wireless_master_tx_duty_cycle(%s)' % self.dutycycle
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_wireless_tab()
        self.wirelessdutycycle = self.browser.find_element_by_id('m_duty_cycle') # Pulldown
        for self.option in self.wirelessdutycycle.find_elements_by_tag_name('option'): # "25","33","50","67","75"
            if self.quiet == False:
                print 'self.option.text = %s' % self.option.text
            if self.option.text.lower() == self.dutycycle.lower():
                self.option.click()
                break
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_wireless_maximum_modulation_rate(self, maximum_modulation_rate):
        # No apply
        self.maximum_modulation_rate = maximum_modulation_rate # "10" | "10x" | "8" | "8x ..| "0" | "0x"
        if self.maximum_modulation_rate.lower() in ['10', '10x']:
            self.modrate = '10x (1024QAM MIMO)'
        elif self.maximum_modulation_rate.lower() in ['8', '8x']:
            self.modrate = '8x (256QAM MIMO)'
        elif self.maximum_modulation_rate.lower() in ['6', '6x']:
            self.modrate = '6x (64QAM MIMO)'
        elif self.maximum_modulation_rate.lower() in ['4', '4x']:
            self.modrate = '4x (16QAM MIMO)'
        elif self.maximum_modulation_rate.lower() in ['2', '2x']:
            self.modrate = '2x (QPSK MIMO)'
        elif self.maximum_modulation_rate.lower() in ['1', '1x']:
            self.modrate = '1x (QPSK SISO)'
        else:
            self.modrate = '1/4x (QPSK SISO)'
        if self.quiet == False:
            print 'set_wireless_maximum_modulation_rate(%s)' % self.maximum_modulation_rate
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_wireless_tab()
        self.max_modrate_element = self.browser.find_element_by_id('rate') # Pulldown
        for self.option in self.max_modrate_element.find_elements_by_tag_name('option'): # "10x (1024QAM MIMO)" | "8x (256QAM MIMO)" ... | "1/4x (QPSK SISO)"
            if self.quiet == False:
                print 'self.option.text = %s' % self.option.text
            if self.option.text == self.modrate:
                self.option.click()
                if self.quiet == False:
                    print 'clicked (%s)' % self.modrate
                break
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def get_wireless_automatic_rate_adaption(self):
        if self.quiet == False:
            print 'get_wireless_automatic_rate_adaption()'
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_wireless_tab()
        self.auto_rate_adaption_state = self.browser.find_element_by_id("rate_auto").is_selected()
        if self.quiet == False:
            print 'self.auto_rate_adaption_state: %s' % self.auto_rate_adaption_state
        return self.auto_rate_adaption_state

    def set_wireless_automatic_rate_adaption(self, automatic_rate_adaption):
        # No apply
        if automatic_rate_adaption == True:
            self.automatic_rate_adaption = 'true'
        elif automatic_rate_adaption == False:
            self.automatic_rate_adaption = 'false'
        else:
            self.automatic_rate_adaption = automatic_rate_adaption.lower()
        if self.quiet == False:
            print 'set_wireless_automatic_rate_adaption(%s)' % self.automatic_rate_adaption
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_wireless_tab()
        self.auto_rate_adaption_state = self.get_wireless_automatic_rate_adaption() # 'True'|'False'
        if self.quiet == False:
            print 'self.auto_rate_adaption_state: %s' % self.auto_rate_adaption_state
        if self.automatic_rate_adaption in ['on','enable','enabled','true']:
            self.automatic_rate_adaption = True
            if self.automatic_rate_adaption != self.auto_rate_adaption_state:
                self.browser.find_element_by_id("rate_auto").click()
                if self.quiet == False:
                    print 'Automatic Rate Adaption clicked.'
        if self.automatic_rate_adaption in ['off','disable','disabled','false']:
            self.automatic_rate_adaption = False
            if self.automatic_rate_adaption != self.auto_rate_adaption_state:
                self.browser.find_element_by_id("rate_auto").click()
                if self.quiet == False:
                    print 'Automatic Rate Adaption clicked.'
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_wireless_rx_gain(self, rxgain):
        # No apply
        if self.quiet == False:
            print 'Radio Type = %s' % self.radiotype
        if self.radiotype == 'AF':
            self.rxgain = rxgain.lower() # "high" | "low"
            if self.quiet == False:
                print 'set_wireless_rx_gain(%s)' % self.rxgain
            self.tabname = 'wireless'
            if self.browser.title.lower().find(self.tabname.lower()) < 0:
                self.click_wireless_tab()
            self.rxgain_element = self.browser.find_element_by_id('rxgain') # Pulldown
            for self.option in self.rxgain_element.find_elements_by_tag_name('option'): # "High" | "Low"
                if self.quiet == False:
                    print 'self.option.text = %s' % self.option.text
                if self.option.text == self.rxgain:
                    self.option.click()
                    break
            time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
            self.click_change_button()

    def get_wireless_valid_frequencies(self, direction=None):
        #<input id="rate_auto" type="checkbox" checked="" onclick="toggleRateAuto();" value="enabled" name="rate_auto"></input>
        self.direction = direction
        if self.quiet == False:
            print 'get_wireless_valid_frequencies(%s)' % self.direction
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            #self.goto_main_tab()
            self.click_wireless_tab()
        if self.direction == None:
            try:
                self.valid_freqs = str(self.browser.find_element_by_id("freq_rng").text) # use str() to suppress unicode 'u'
            except:
                self.valid_freqs = str(self.browser.find_element_by_id("tx_freq_rng").text) # use str() to suppress unicode 'u'
        elif self.direction.lower() == 'tx':
            self.valid_freqs = str(self.browser.find_element_by_id("tx_freq_rng").text) # use str() to suppress unicode 'u'
            if not self.valid_freqs:
                self.valid_freqs = str(self.browser.find_element_by_id("freq_rng").text) # use str() to suppress unicode 'u'
        else:
            self.valid_freqs = str(self.browser.find_element_by_id("rx_freq_rng").text) # use str() to suppress unicode 'u'
            if not self.valid_freqs:
                 self.valid_freqs = str(self.browser.find_element_by_id("tx_freq_rng").text) # use str() to suppress unicode 'u'
        self.valid_freqs_list = re.sub("[^0-9]", " ", self.valid_freqs).split()
        self.valid_freq_pairs = zip(self.valid_freqs_list[0::2], self.valid_freqs_list[1::2]) 
        if self.quiet == False:
            print 'Got: %s' % self.valid_freqs
            print 'Valid Frequencies List: %s' % self.valid_freqs_list
            print 'Valid Frequency Pairs: %s' % self.valid_freq_pairs
        return self.valid_freq_pairs

    def set_wireless_frequency(self, pair, direction, frequency):
        # No apply
        self.pair = str(pair)
        self.direction = direction.lower()
        self.frequency = frequency
        if self.quiet == False:
            print 'set_wireless_frequency(%s, %s, %s)' % (self.pair, self.direction, self.frequency)
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_wireless_tab()
        if self.pair == '1':
            self.freq_id = "%s_chan_freq" % self.direction
        else:
            self.freq_id = "%s_chan_freq%s" % (self.direction, self.pair)
        self.freq_element = self.browser.find_element_by_id(self.freq_id)
        if self.radiotype == 'AF02':
            self.freq_element.clear()
            self.freq_element.send_keys(self.frequency)
        else:
            self.duplex_element = self.browser.find_element_by_id('af_duplex_select') # Pulldown
            for self.option in self.freq_element.find_elements_by_tag_name('option'): # "Half Duplex" | "Full Duplex"
                if self.quiet == False:
                    print 'self.option.text = %s' % self.option.text
                if self.option.text.lower().find(self.frequency.lower()) >= 0:
                    self.option.click()
                    break
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def get_wireless_frequency(self, pair, direction):
        self.pair = pair
        self.direction = direction.lower()
        if self.quiet == False:
            print 'get_wireless_frequency(%s, %s)' % (self.pair, self.direction)
        self.tabname = 'wireless'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_wireless_tab()
        if self.pair == '1':
            self.freq_id = "%s_chan_freq" % self.direction
        else:
            self.freq_id = "%s_chan_freq%s" % (self.direction, self.pair)
        self.freq = self.browser.find_element_by_id(self.freq_id).get_attribute("value")
        return self.freq

    def is_wireless_frequency_valid(self, frequency, direction):
        self.freq = frequency
        self.direction = direction
        if self.quiet == False:
            print 'is_wireless_frequency_valid(%s)' % self.freq
        self.result = False
        self.validfreqs = self.get_wireless_valid_frequencies(self.direction)
        if self.quiet == False:
            print 'Valid Frequencies: %s' % self.validfreqs
        for index in range(len(self.validfreqs)):
            #print '%s : %s' % (self.validfreqs[index][0], self.validfreqs[index][1])
            if(int(self.freq) >= int(self.validfreqs[index][0])) and (int(self.freq) <= int(self.validfreqs[index][1])):
                validpair = index
                self.result = True
                if self.quiet == False:
                    print 'Value %s Within Freq Pair: %s' % (self.freq, self.validfreqs[validpair])
        return self.result

    def do_wireless_freq_clear_dfs_timeouts(self):
        # Clear DFS timeouts by shifting and applying the tx and rx frequencies by 1 MHz
        # and then shifting them back to their original value and applying the change.
        if self.quiet == False:
            print 'do_wireless_freq_clear_dfs_timeouts()'
        self.origfreqs = {'tx1':'', 'rx1':'', 'tx2':'', 'rx2':'', 'tx3':'', 'rx3':''}
        for self.pair in ['1', '2', '3']:
            for self.direction in ['tx', 'rx']:
                self.current = '%s%s' % (self.direction, self.pair)
                if self.quiet == False:
                    print 'Current Frequency Pair: %s' % self.current
                self.origfreqs[self.current] = self.get_wireless_frequency(self.pair, self.direction)
                self.freqval = int(self.origfreqs[self.current])
                if self.quiet == False:
                    print 'Current Frequency Value: %s' % self.freqval
                if self.is_wireless_frequency_valid(self.freqval+1, self.direction):
                    self.set_wireless_frequency(self.pair, self.direction, self.freqval+1)
                elif self.is_wireless_frequency_valid(self.freqval-1, self.direction):
                    self.set_wireless_frequency(self.pair, self.direction, self.freqval-1)
                else:
                    print 'ERROR: do_wireless_freq_clear_dfs_timeouts() could not find a valid frequency to switch to.'
                    sys.exit(1)
        self.apply_settings()
        for self.pair in ['1', '2', '3']:
            for self.direction in ['tx', 'rx']:
                self.current = '%s%s' % (self.direction, self.pair)
                if self.quiet == False:
                    print 'Current Frequency Pair: %s' % self.current
                    print 'Current Frequency Value: %s' % self.origfreqs[self.current]
                self.set_wireless_frequency(self.pair, self.direction, self.origfreqs[self.current])
        self.apply_settings()

    def set_wireless_key_type(self, key_type):
        pass

    def set_wireless_key(self, key):
        pass

    def get_advanced_gps_clock_sync(self):
        if self.quiet == False:
            print 'get_advanced_gps_clock_sync()'
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.gps_clock_sync_state = self.browser.find_element_by_id("gps_sync").is_selected()
        if self.quiet == False:
            print 'self.gps_clock_sync_state: %s' % self.gps_clock_sync_state
        return self.gps_clock_sync_state

    def set_advanced_gps_clock_sync(self, gps_clock_sync):
        # No apply
        if gps_clock_sync == True:
            self.gps_clock_sync = 'true'
        elif gps_clock_sync == False:
            self.gps_clock_sync = 'false'
        else:
            self.gps_clock_sync = gps_clock_sync.lower()
        if self.quiet == False:
            print 'set_advanced_gps_clock_sync(%s)' % self.gps_clock_sync
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.gps_clock_sync_state = self.get_advanced_gps_clock_sync() # 'True'|'False'
        if self.quiet == False:
            print 'self.gps_clock_sync_state: %s' % self.gps_clock_sync_state
        if self.gps_clock_sync in ['on','enable','enabled','true']:
            self.gps_clock_sync = True
            if self.gps_clock_sync != self.gps_clock_sync_state:
                self.browser.find_element_by_id("gps_sync").click()
                if self.quiet == False:
                    print 'Flow Control clicked.'
        if self.gps_clock_sync in ['off','disable','disabled','false']:
            self.gps_clock_sync = False
            if self.gps_clock_sync != self.gps_clock_sync_state:
                self.browser.find_element_by_id("gps_sync").click()
                if self.quiet == False:
                    print 'Flow Control clicked.'
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_advanced_data_speed(self, data_speed):
        # No apply
        self.dataspeed = data_speed.lower() # "high" | "low"
        if self.quiet == False:
            print 'set_advanced_data_speed(%s)' % self.dataspeed
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.dataspeed_element = self.browser.find_element_by_id('af0_speed') # Pulldown
        for self.option in self.dataspeed_element.find_elements_by_tag_name('option'): # "Auto" | "100Mbps-Full" | "100Mbps-Half" | "10Mbps-Full" | "10Mbps-Half"
            if self.quiet == False:
                print 'self.option.text = %s' % self.option.text
            if self.option.text.lower() == self.dataspeed:
                self.option.click()
                break
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_advanced_mgmt_speed(self, mgmt_speed):
        # No apply
        self.mgmtspeed = mgmt_speed.lower() # "high" | "low"
        if self.quiet == False:
            print 'set_advanced_mgmt_speed(%s)' % self.mgmtspeed
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.mgmtspeed_element = self.browser.find_element_by_id('eth0_speed') # Pulldown
        for self.option in self.mgmtspeed_element.find_elements_by_tag_name('option'): # "Auto" | "100Mbps-Full" | "100Mbps-Half" | "10Mbps-Full" | "10Mbps-Half"
            if self.quiet == False:
                print 'self.option.text = %s' % self.option.text
            if self.option.text.lower() == self.mgmtspeed:
                self.option.click()
                break
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def get_advanced_flow_control(self):
        if self.quiet == False:
            print 'get_advanced_flow_control()'
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            #self.goto_main_tab()
            self.click_advanced_tab()
        self.flow_control_state = self.browser.find_element_by_id("flowcntl").is_selected()
        if self.quiet == False:
            print 'self.flow_control_state: %s' % self.flow_control_state
        return self.flow_control_state

    def set_advanced_flow_control(self, flow_control):
        # No apply
        if flow_control == True:
            self.flow_control = 'true'
        elif flow_control == False:
            self.flow_control = 'false'
        else:
            self.flow_control = flow_control.lower()
        if self.quiet == False:
            print 'set_advanced_flow_control(%s)' % self.flow_control
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.flow_control_state = self.get_advanced_flow_control() # 'True'|'False'
        if self.quiet == False:
            print 'self.flow_control_state: %s' % self.flow_control_state
        if self.flow_control in ['on','enable','enabled','true']:
            self.flow_control = True
            if self.flow_control != self.flow_control_state:
                self.browser.find_element_by_id("flowcntl").click()
                if self.quiet == False:
                    print 'Flow Control clicked.'
        if self.flow_control in ['off','disable','disabled','false']:
            self.flow_control = False
            if self.flow_control != self.flow_control_state:
                self.browser.find_element_by_id("flowcntl").click()
                if self.quiet == False:
                    print 'Flow Control clicked.'
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def get_advanced_multicast_filter(self):
        if self.quiet == False:
            print 'get_advanced_multicast_filter()'
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.multicast_filter_state = self.browser.find_element_by_id("mcastfilter").is_selected()
        if self.quiet == False:
            print 'self.multicast_filter_state: %s' % self.multicast_filter_state
        return self.multicast_filter_state

    def set_advanced_multicast_filter(self, multicast_filter):
        # No apply
        if multicast_filter == True:
            self.multicast_filter = 'true'
        elif multicast_filter == False:
            self.multicast_filter = 'false'
        else:
            self.multicast_filter = multicast_filter.lower()
        if self.quiet == False:
            print 'set_advanced_multicast_filter(%s)' % self.multicast_filter
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.multicast_filter_state = self.get_advanced_multicast_filter() # 'True'|'False'
        if self.quiet == False:
            print 'self.multicast_filter_state: %s' % self.multicast_filter_state
        if self.multicast_filter in ['on','enable','enabled','true']:
            self.multicast_filter = True
            if self.multicast_filter != self.multicast_filter_state:
                self.browser.find_element_by_id("mcastfilter").click()
                if self.quiet == False:
                    print 'Flow Control clicked.'
        if self.multicast_filter in ['off','disable','disabled','false']:
            self.multicast_filter = False
            if self.multicast_filter != self.multicast_filter_state:
                self.browser.find_element_by_id("mcastfilter").click()
                if self.quiet == False:
                    print 'Flow Control clicked.'
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_advanced_track_radio_link(self, track_radio_link):
        # No apply
        self.track_radio_link = track_radio_link.lower() # "high" | "low"
        if self.quiet == False:
            print 'set_advanced_track_radio_link(%s)' % self.track_radio_link
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.track_radio_link_element = self.browser.find_element_by_id('carrierdrop') # Pulldown
        for self.option in self.track_radio_link_element.find_elements_by_tag_name('option'): # "Disabled" | "Use Timeout Duration" | "Enabled"
            if self.quiet == False:
                print 'self.option.text = %s' % self.option.text
            if self.option.text.lower() == self.track_radio_link:
                self.option.click()
                break
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_advanced_link_off_duration(self, link_off_duration):
        # No apply
        self.link_off_duration = link_off_duration
        if self.quiet == False:
            print 'set_advanced_link_off_duration(%s)' % self.link_off_duration
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.browser.find_element_by_id("carrierdropto").clear()
        self.browser.find_element_by_id("carrierdropto").send_keys(self.link_off_duration)
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def set_advanced_link_off_spacing(self, link_off_spacing):
        # No apply
        self.link_off_spacing = link_off_spacing
        if self.quiet == False:
            print 'set_advanced_link_off_spacing(%s)' % self.link_off_spacing
        self.tabname = 'advanced'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_advanced_tab()
        self.browser.find_element_by_id("carrierdropdebounce").clear()
        self.browser.find_element_by_id("carrierdropdebounce").send_keys(self.link_off_spacing)
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.click_change_button()

    def get_system_fw_version(self):
        """ Returns the Firmware Version displayed on the SYSTEM page. """
        # Returns: AF02.v2.1-dev.21845.140411.1605
        if self.quiet == False:
            print 'get_system_fw_version()'
        self.tabname = 'system'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_system_tab()
        self.firmware_version = self.browser.find_element_by_xpath("//form[@id='sys_form']/table/tbody/tr[3]/td[2]").text
        return self.firmware_version

    def get_system_radio_type(self):
        # Returns: AF02
        if self.firmware_version == '':
            self.get_system_fw_version()
        self.radiotype = self.firmware_version.split('.')[0]
        return self.radiotype

    def get_system_build_number(self):
        """ Returns the Build Number displayed on the SYSTEM page. """
        # Returns: 21845
        if self.quiet == False:
            print 'get_system_build_number()'
        self.tabname = 'system'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_system_tab()
        self.buildnumber = self.browser.find_element_by_xpath("//form[@id='sys_form']/table/tbody/tr[4]/td[2]").text
        return self.buildnumber

    def set_fw_image(self, image_pathname):
        """ Set the firmware image pathname which may include the path."""
        if self.quiet == False:
            print 'set_fw_image()'
        self.fw_image = image_pathname

    def remove_path_from_fw_filename(self, image_pathname):
        """ Returns the firmware file name with out the path or .bin extension"""
        if self.quiet == False:
            print 'remove_path_from_fw_filename()'
        self.fw_image = image_pathname
        self.fw_filename = ".".join((((self.fw_image).split("/"))[-1:][0]).split(".")[:-1])
        return self.fw_filename

    def update_firmware(self, image):
        self.fwimage = image
        if self.quiet == False:
            print 'update_firmware()'

        self.login()
        self.tabname = 'system'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            #self.goto_main_tab()
            self.click_system_tab()
        if self.quiet == False:
            self.fwversion = self.get_system_fw_version()
            print 'Old Firmware Version:', self.fwversion
            self.build = self.get_system_build_number()
            print 'Old Build Number:', self.build
        self.load_fw(self.fwimage)
        self.login()
        self.tabname = 'system'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.click_system_tab()
        self.fwversion = self.get_system_fw_version()
        self.build = self.get_system_build_number()
        if self.quiet == False:
            print 'New Firmware Version:', self.fwversion, 'New Build Number:', self.build
        self.logout()
        time.sleep(2)
        return (self.fwversion, self.build)


    def goto_labefana(self):
        if self.quiet == False:
            print 'goto_labefana()'
        self.browser.get("http://%s/labefana.cgi" % self.address)

    def get_labefana_dfs_reset(self):
        if self.quiet == False:
            print 'get_labefana_dfs_reset().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.dfs_reset = self.browser.find_element_by_id("dfsst").text
        if self.quiet == False:
            print "DFS Reset: ", self.dfs_reset
        return self.dfs_reset

    def get_labefana_dfs_live(self):
        if self.quiet == False:
            print 'get_labefana_dfs_live().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.dfs_live = self.browser.find_element_by_id("dfslive").text
        if self.quiet == False:
            print "DFS Live: ", self.dfs_live
        return self.dfs_live

    def get_labefana_dfs_int_mask(self):
        if self.quiet == False:
            print 'get_labefana_dfs_int_mask().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.dfs_int_mask = self.browser.find_element_by_id("dfsint").text
        if self.quiet == False:
            print "DFS Int Mask: ", self.dfs_int_mask
        return self.dfs_int_mask

    def get_labefana_dfs_version(self):
        if self.quiet == False:
            print 'get_labefana_dfs_version().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.dfs_version = self.browser.find_element_by_id("dfsmode").text
        if self.quiet == False:
            print "DFS Version: ", self.dfs_version
        return self.dfs_version

    def get_labefana_link_state(self):
        if self.quiet == False:
            print 'get_labefana_link_state().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.link_state = self.browser.find_element_by_id("linkstate").text
        if self.quiet == False:
            print "Link State: ", self.link_state
        return self.link_state

    def wait_labefana_link_state_operational_retry(self, retries):
        self.retries = retries
        if self.quiet == False:
            print 'wait_labefana_link_state_operational_retry().'
        self.link_state = ''
        while (self.link_state.lower() != 'operational') and (self.retries > 0):
            time.sleep(1)
            self.link_state = self.get_labefana_link_state()
            self.retries -= 1
            if self.quiet == False:
                print 'labefana_link_state = %s, remaining retries: %s' % (self.link_state, self.retries)
        if (self.retries == 0) and (self.link_state.lower() != 'operational'):
            print 'Remaining Retries = %s Labefana Link State = %s' % (self.retries, self.link_state)
        return self.link_state

    def get_labefana_mgmt_mac(self):
        if self.quiet == False:
            print 'get_labefana_mgmt_mac().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.mgmt_mac = self.browser.find_element_by_id("mgmtmac").text
        if self.quiet == False:
            print "Mgmt MAC: ", self.mgmt_mac
        return self.mgmt_mac

    def get_labefana_mgmt(self):
        if self.quiet == False:
            print 'get_labefana_mgmt().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.mgmt = self.browser.find_element_by_id("mgmtstateinfo").text
        if self.quiet == False:
            print "Mgmt: ", self.mgmt
        return self.mgmt

    def get_labefana_data(self):
        if self.quiet == False:
            print 'get_labefana_data().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.data = self.browser.find_element_by_id("datastateinfo").text
        if self.quiet == False:
            print "Data: ", self.data
        return self.data

    def get_labefana_channel_width(self, display_units=False):
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_labefana_channel_width().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.data = str(self.browser.find_element_by_id("chanwidthinfo").text)
        if self.displayunits == False:
            self.chw = ' '.join(self.data.split()[2:-1])
        else:
            self.chw = ' '.join(self.data.split()[2:])
        if self.quiet == False:
            print "Channel Width: ", self.chw
        return self.chw

    def get_labefana_rx_power(self, chain, wait=False, wait_count=1, display_units=False):
        self.chain = chain  # 0 or 1
        self.wait = wait
        self.wait_count = wait_count # seconds if wait=True
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_labefana_rx_power(chain=%s).' % self.chain
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        chain_id = 'rxpower%s' % self.chain
        self.rxpower = self.browser.find_element_by_id(chain_id).text
        if self.rxpower == None or self.rxpower == '':
            self.rxpower = '-'
        if self.wait == True:
            while (self.rxpower.strip() == '-') and (self.wait_count > 0):
                time.sleep(1)
                self.rxpower = self.browser.find_element_by_id(chain_id).text
                self.wait_count -= 1
        if self.displayunits == False:
            self.rxpower = ''.join(self.rxpower.split()[:-1])
        if self.quiet == False:
            print "RX Power%s: %s" % (self.chain, self.rxpower)
        return self.rxpower

    def get_labefana_coarse(self):
        if self.quiet == False:
            print 'get_labefana_coarse().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.coarse = str(self.browser.find_element_by_id("coarse").text) #coarse
        if self.quiet == False:
            print "Coarse: ", self.coarse
        return self.coarse

    def get_labefana_fine(self):
        if self.quiet == False:
            print 'get_labefana_fine().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.fine = str(self.browser.find_element_by_id("fine").text) #fine
        if self.quiet == False:
            print "Fine: ", self.fine
        return self.fine

    def get_labefana_chain_isolation(self, display_units=False):
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_labefana_chain_isolation().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.data = str(self.browser.find_element_by_id("ChainIsolation").text) #ChainIsolation
        #print "Chain Isolation Data: ", self.data    # Chain Isolation Data:  7 dB
        if self.displayunits == False:
            self.isolation = ' '.join(self.data.split()[0:-1])
        else:
            self.isolation = ' '.join(self.data.split())
        if self.quiet == False:
            print "Chain Isolation: ", self.isolation
        return self.isolation

    def get_labefana_chain_evm(self, chain, wait=False, wait_count=1, display_units=False):
        self.chain = chain  # 0 or 1
        self.wait = wait
        self.wait_count = wait_count # seconds if wait=True
        self.displayunits = display_units
        if self.quiet == False:
            print 'get_labefana_chain_evm(chain=%s).' % self.chain
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        chain_id = 'Chain%sEVM' % self.chain #Chain1EVM
        self.evm = self.browser.find_element_by_id(chain_id).text
        if self.evm == None or self.evm == '':
            self.evm = '-'
        if self.wait == True:
            while (self.evm.strip() == '-') and (self.wait_count > 0):
                time.sleep(1)
                self.evm = self.browser.find_element_by_id(chain_id).text
                self.wait_count -= 1
        if self.displayunits == False:
            self.evm = ''.join(self.evm.split()[:-1])
        if self.quiet == False:
            print "EVM%s: %s" % (self.chain, self.evm)
        return self.evm

    def get_labefana_ber(self):
        if self.quiet == False:
            print 'get_labefana_ber().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.data = str(self.browser.find_element_by_id("BER").text) #BER
        #print "BER Data: ", self.data    # BER Data:  3.1576271e-3
        #self.ber = ' '.join(self.data.split()[2:])
        self.ber = self.data
        if self.quiet == False:
            print "BER: ", self.ber
        return self.ber

    def get_labefana_dfs_detections(self):
        if self.quiet == False:
            print 'get_labefana_dfs_detections().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.dfs_detections = self.browser.find_element_by_id("dfs_detects").text
        if self.quiet == False:
            print "DFS Detections: ", self.dfs_detections
        return self.dfs_detections

    def get_labefana_dfs_freq_status(self, frequency):
        # frequency = 1|2|3
        self.freq = frequency
        if self.quiet == False:
            print 'get_labefana_dfs_freq_status(%s).' % self.freq
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.dfs_status_id = "dfs_status%s" % self.freq
        self.dfs_freq_status = self.browser.find_element_by_id(self.dfs_status_id).text
        if self.quiet == False:
            print "DFS Freq %s Status: %s" % (self.freq, self.dfs_freq_status)
        if self.dfs_freq_status == 'Not Configured.':
            self.dfs_freq_status_dict = {'Freq':'', 'State':'', 'Timeout':''}
        else:
            try:
                self.dfs_freq_status_dict = {}
                self.dfs_freq_status_list = self.dfs_freq_status.split(',')
                for item in self.dfs_freq_status_list:
                    pair = item.split(': ')
                    key = pair[0].strip()
                    value = pair[1].strip()
                    self.dfs_freq_status_dict[key] = value
            except:
                time.sleep(4)
                if self.browser.title.lower().find(self.tabname.lower()) < 0:
                    self.goto_labefana()
                time.sleep(1)
                self.dfs_status_id = "dfs_status%s" % self.freq
                self.dfs_freq_status = self.browser.find_element_by_id(self.dfs_status_id).text
                if self.quiet == False:
                    print "DFS Freq %s Status: %s" % (self.freq, self.dfs_freq_status)
                if self.dfs_freq_status == 'Not Configured.':
                    self.dfs_freq_status_dict = {'Freq':'', 'State':'', 'Timeout':''}
                else:
                    self.dfs_freq_status_dict = {}
                    self.dfs_freq_status_list = self.dfs_freq_status.split(',')
                    for item in self.dfs_freq_status_list:
                        pair = item.split(': ')
                        key = pair[0].strip()
                        value = pair[1].strip()
                        self.dfs_freq_status_dict[key] = value
        return self.dfs_freq_status_dict

    def get_labefana_dfs_freq_1_status(self):
        if self.quiet == False:
            print 'get_labefana_dfs_freq_1_status().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.dfs_freq_1_status = self.browser.find_element_by_id("dfs_status1").text
        if self.quiet == False:
            print "DFS Freq 1 Status: ", self.dfs_freq_1_status
        if self.dfs_freq_1_status == 'Not Configured.':
            self.dfs_freq_1_status_dict = {'Freq':'', 'State':'', 'Timeout':''}
        else:
            self.dfs_freq_1_status_dict = {}
            self.dfs_freq_1_status_list = self.dfs_freq_1_status.split(',')
            for item in self.dfs_freq_1_status_list:
                pair = item.split(': ')
                key = pair[0].strip()
                value = pair[1].strip()
                self.dfs_freq_1_status_dict[key] = value
        return self.dfs_freq_1_status_dict

    def get_labefana_dfs_freq_2_status(self):
        if self.quiet == False:
            print 'get_labefana_dfs_freq_2_status().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.dfs_freq_2_status = self.browser.find_element_by_id("dfs_status2").text
        if self.quiet == False:
            print "DFS Freq 2 Status: ", self.dfs_freq_2_status
        self.dfs_freq_2_status_dict = {}
        if self.dfs_freq_2_status != 'Not Configured.':
            self.dfs_freq_2_status_list = self.dfs_freq_2_status.split(',')
            for item in self.dfs_freq_2_status_list:
                pair = item.split(': ')
                key = pair[0].strip()
                value = pair[1].strip()
                self.dfs_freq_2_status_dict[key] = value
        return self.dfs_freq_2_status_dict

    def get_labefana_dfs_freq_3_status(self):
        if self.quiet == False:
            print 'get_labefana_dfs_freq_3_status().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.dfs_freq_3_status = self.browser.find_element_by_id("dfs_status3").text
        if self.quiet == False:
            print "DFS Freq 3 Status: ", self.dfs_freq_3_status
        self.dfs_freq_3_status_dict = {}
        if self.dfs_freq_3_status != 'Not Configured.':
            self.dfs_freq_3_status_list = self.dfs_freq_3_status.split(',')
            for item in self.dfs_freq_3_status_list:
                pair = item.split(': ')
                key = pair[0].strip()
                value = pair[1].strip()
                self.dfs_freq_3_status_dict[key] = value
        return self.dfs_freq_3_status_dict

    def set_labefana_dfs_threshold(self, threshold):
        self.threshold = threshold
        if self.quiet == False:
            print 'set_labefana_dfs_threshold(%s)' % self.threshold
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.browser.find_element_by_id("dfsthreshold").clear()
        self.browser.find_element_by_id("dfsthreshold").send_keys(self.threshold)
        self.btn_changeElement = self.browser.find_element_by_id("change").click()
        if self.quiet == False:
            print 'get_labefana_dfs_threshold() =', self.get_labefana_dfs_threshold()
   
    def get_labefana_dfs_threshold(self):
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.threshold = self.browser.find_element_by_id("dfsthreshold").get_attribute("value")
        if self.quiet == False:
            print 'dfs_threshold = %s' % self.threshold
        return self.threshold

    def do_labefana_cmd(self, cmd):
        self.cmd = cmd
        if self.quiet == False:
            print 'do_labefana_cmd(%s)' % self.cmd
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.browser.find_element_by_name("exec").clear()
        self.browser.find_element_by_name("exec").send_keys(self.cmd)
        time.sleep(1) # added to prevent NoSuchElementException for "input[type=\\"submit\\"]"
        self.browser.find_element_by_css_selector("form > input[type=\"submit\"]").click()

    def get_labefana_cmd_results(self):
        if self.quiet == False:
            print 'get_labefana_cmd()'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.cmd_results = self.browser.find_element_by_css_selector("pre").text
        return self.cmd_results

    def do_labefana_cmd_reboot(self):
        if self.quiet == False:
            print 'do_labefana_cmd_reboot()'
        self.cmd = 'reboot'
        self.do_labefana_cmd(self.cmd)

    def do_labefana_cmd_dfs_debug_d3(self):
        if self.quiet == False:
            print 'do_labefana_cmd_dfs_debug_d3()'
        self.cmd = 'af set debug D3'
        self.do_labefana_cmd(self.cmd)

    def get_labefana_cmd_temperature(self, sensor):
        self.sensor = sensor # 0 | 1
        if self.quiet == False:
            print 'get_labefana_cmd_temperature(%s)' % self.sensor
        self.cmd = 'af get temp%s' % self.sensor
        self.do_labefana_cmd(self.cmd)
        self.results = self.get_labefana_cmd_results()
        return self.results

    def get_labefana_cmd_fpga_ver(self):
        if self.quiet == False:
            print 'get_labefana_cmd_fpga_ver()'
        self.cmd = 'ver'
        self.do_labefana_cmd(self.cmd)
        self.resultslist = self.get_labefana_cmd_results().split()
        self.results = self.resultslist[4]+' '+self.resultslist[1]+' '+self.resultslist[2]
        return self.results # "FPGA Version 7  date: 11/1/2013"

    def get_labefana_cmd_fpga_ver_formatted(self):
        if self.quiet == False:
            print 'get_labefana_cmd_fpga_ver()'
        self.cmd = 'ver'
        self.do_labefana_cmd(self.cmd)
        self.results = self.get_labefana_cmd_results()
        if self.quiet == False:
            print 'results = ', self.results            # Invictus Version 6  date: 11/11/2013
        self.resultslist = self.results.split()
        if self.quiet == False:
            print 'resultslist = ', self.resultslist    # [u'Invictus', u'Version', u'6', u'date:', u'11/11/2013']
        #self.results = self.resultslist[4]+' '+self.resultslist[1]+' '+self.resultslist[2] # 11/11/2013 Version 6
        self.datelist = self.resultslist[4].split('/')
        self.date = self.datelist[2][2:].zfill(2)+self.datelist[0].zfill(2)+self.datelist[1].zfill(2)
        self.results = self.date+'v'+self.resultslist[2] # 131111v6
        return self.results

    def get_labefana_cmd_maximum_modulation_rate(self):
        if self.quiet == False:
            print 'get_labefana_cmd_maximum_modulation_rate()'
        self.cmd = 'af get speed'
        self.do_labefana_cmd(self.cmd)
        self.results = self.get_labefana_cmd_results()
        return self.results

    def get_labefana_max_tx_rate_curr_mod(self, display_units=False):
        if self.quiet == False:
            print 'get_labefana_max_tx_rate_curr_mod().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.curr_max_tx_rate = self.browser.find_element_by_id("curmaxtxrate").text
        self.curr_max_tx_rate = ''.join(self.curr_max_tx_rate.split(','))
        if display_units == False:
            self.curr_max_tx_rate = ''.join(self.curr_max_tx_rate.split()[:-2])
        if self.quiet == False:
            print "Max TX Rate for Curr Mod: ", self.curr_max_tx_rate
        return self.curr_max_tx_rate

    def get_labefana_max_rx_rate_curr_mod(self, display_units=False):
        if self.quiet == False:
            print 'get_labefana_max_rx_rate_curr_mod().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.curr_max_rx_rate = self.browser.find_element_by_id("curmaxrxrate").text
        self.curr_max_rx_rate = ''.join(self.curr_max_rx_rate.split(','))
        if display_units == False:
            self.curr_max_rx_rate = ''.join(self.curr_max_rx_rate.split()[:-2])
        if self.quiet == False:
            print "Max RX Rate for Curr Mod: ", self.curr_max_rx_rate
        return self.curr_max_rx_rate

    def get_labefana_max_tx_rate(self, display_units=False):
        if self.quiet == False:
            print 'get_labefana_max_tx_rate().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.max_tx_rate = self.browser.find_element_by_id("maxtxrate").text
        self.max_tx_rate = ''.join(self.max_tx_rate.split(','))
        if display_units == False:
            self.max_tx_rate = ''.join(self.max_tx_rate.split()[:-1])
        if self.quiet == False:
            print "Max TX Rate: ", self.max_tx_rate
        return self.max_tx_rate

    def get_labefana_max_rx_rate(self, display_units=False):
        if self.quiet == False:
            print 'get_labefana_max_rx_rate().'
        self.tabname = 'Device engineering utility'
        if self.browser.title.lower().find(self.tabname.lower()) < 0:
            self.goto_labefana()
        time.sleep(1)
        self.max_rx_rate = self.browser.find_element_by_id("maxrxrate").text
        self.max_rx_rate = ''.join(self.max_rx_rate.split(','))
        if display_units == False:
            self.max_rx_rate = ''.join(self.max_rx_rate.split()[:-1])
        if self.quiet == False:
            print "Max RX Rate: ", self.max_rx_rate
        return self.max_rx_rate

    def get_labefana_cmd_afaf(self):
        # returns a directory with keys:
        # 'rssi0', 'rssi1', 'baseline', 'feet', 'temp1', 'temp0', 'dpstat', 'Config', 'linkname',
        # 'txfrequency',2GHz', 'duplex', 'speed', 'rrxpower0', 'rrxpower1', 'rtxmodrate', 'txcapacity',
        # 'rxpower0', 'fade', '*******', 'Data',', 'status',operational', 'rpowerout', 'key', 'rxgain',
        #'rxfrequency',1GHz', 'rxcapacity', 'powerout', 'rxpower1', 'miles',010', 'modcontrol', 'txmodrate'
        if self.quiet == False:
            print 'get_labefana_cmd_afaf()'
        self.cmd = 'af af'
        self.do_labefana_cmd(self.cmd)
        self.results = self.get_labefana_cmd_results()
        # split results into a list
        self.resultslist = self.results.split()
        # remove the command and the prompt from the list
        self.statslist = self.resultslist[2:-1]
        # remove the : from the end of the names in the list
        for glindex in range(len(self.statslist)):
            if self.statslist[glindex][-1] == ':':
                self.statslist[glindex] = self.statslist[glindex][:-1]
        # convert the list into a dictionary
        self.retdict = dict(itertools.izip_longest(*[iter(self.statslist)] * 2, fillvalue=""))
        return self.retdict

    def get_labefana_cmd_afemac(self):
        # returns a directory with keys:
        # mac_0, mac_1, TxFramesOK, RxFramesOK, RxFrameCrcErr, RxAlignErr, TxOctetsOK, RxOctetsOK,
        # TxPauseFrames, RxPauseFrames, RxErroredFrames, TxErroredFrames, RxValidUnicastFrames,RxValidMulticastFrames,
        # RxValidBroadcastFrames, TxValidUnicastFrames, TxValidMulticastFrames, TxValidBroadcastFrames,
        # RxDroppedMacErrFrames, RxTotalOctets, RxTotalFrames, RxLess64ByteFrames, RxOverLengthFrames, Rx64BytePackets,
        # Rx65_127BytePackets, Rx128_255BytePackets, Rx256_511BytePackets, Rx512_1023BytePackets, Rx1024_1518BytesPackets,
        # Rx1519PlusBytePackets, RxTooLongFrameCrcErr, RxTooShortFrameCrcErr
        if self.quiet == False:
            print 'get_labefana_cmd_afemac()'
            print
        self.cmd = 'af emac'
        self.do_labefana_cmd(self.cmd)
        self.getresults = self.get_labefana_cmd_results()
        if self.quiet == False:
            print 'get results =', self.getresults
            print
        # split results into a list
        self.getlist = self.getresults.split()
        if self.quiet == False:
            print 'get list =', self.getlist
            print
        # remove the command and the prompt from the list
        self.statslist = self.getlist[2:]
        if self.quiet == False:
            print 'stats list =', self.statslist
            print
        # remove the : from the end of the names in the list
        for glindex in range(len(self.statslist)):
            if self.statslist[glindex][-1] == ':':
                self.statslist[glindex] = self.statslist[glindex][:-1]
        if self.quiet == False:
            print 'stats list edited =', self.statslist
            print
        # convert the list into a dictionary
        self.retdict = dict(itertools.izip_longest(*[iter(self.statslist)] * 2, fillvalue=""))
        return self.retdict

    def get_labefana_cmd_afemac_delta(self, initial):
        # returns a directory with keys:
        # mac_0, mac_1, TxFramesOK, RxFramesOK, RxFrameCrcErr, RxAlignErr, TxOctetsOK, RxOctetsOK,
        # TxPauseFrames, RxPauseFrames, RxErroredFrames, TxErroredFrames, RxValidUnicastFrames,RxValidMulticastFrames,
        # RxValidBroadcastFrames, TxValidUnicastFrames, TxValidMulticastFrames, TxValidBroadcastFrames,
        # RxDroppedMacErrFrames, RxTotalOctets, RxTotalFrames, RxLess64ByteFrames, RxOverLengthFrames, Rx64BytePackets,
        # Rx65_127BytePackets, Rx128_255BytePackets, Rx256_511BytePackets, Rx512_1023BytePackets, Rx1024_1518BytesPackets,
        # Rx1519PlusBytePackets, RxTooLongFrameCrcErr, RxTooShortFrameCrcErr
        self.initial = initial
        if self.quiet == False:
            print 'get_labefana_cmd_afemac_delta(%s)' % self.initial
        self.delta = {}
        self.counterBitLen = 32
        self.currEmac = self.get_labefana_cmd_afemac()
        if self.initial == True:
            self.prevEmac = self.currEmac
            return self.currEmac
        else:
            for key in self.currEmac:
                try:
                    self.delta[key] = int(self.currEmac[key]) - int(self.prevEmac[key])
                except:
                    continue
                if self.delta[key] < 0:
                    self.delta[key] = int(self.delta[key]) + pow(2, self.counterBitLen)
            self.prevEmac = self.currEmac
            return self.delta

    def getRadioDFSCACIndexStatus(self, maxattempts=60):
        self.attemptslimit = maxattempts
        self.operatingfreqindex = 0
        self.attempts = 0
        if self.quiet == False:
            print 'getRadioDFSCACIndexStatus()'
        while (self.attempts < self.attemptslimit):
            self.freqindex = self.attempts % 3 + 1
            if self.quiet == False:
                print 'Frequency Index: ', self.freqindex
            self.dfs_freq_status = self.get_labefana_dfs_freq_status(self.freqindex)
            if self.quiet == False:
                print 'Frequency %s Status = %s' % (self.freqindex, self.dfs_freq_status['State'])
            if (self.dfs_freq_status['State'] == "Channel Availablity Check"): # We've found the current operating frequency
                self.operatingfreqindex = self.freqindex
                break
            self.attempts += 1
            time.sleep(1)
        if self.quiet == False:
            print 'CAC Frequency Index: ', self.operatingfreqindex
        if self.operatingfreqindex == 0:
            self.dfs_freq_status = 'none'
            print
            print "ERROR: No operational DFS frequency found."
            print
        if self.quiet == False:
            print 'CAC Index: %s    Frequency: %s' % (self.operatingfreqindex, str(self.dfs_freq_status['Freq']))
        return (self.operatingfreqindex, self.dfs_freq_status)

    def getRadioDFSOperatingIndexStatus(self, maxattempts=60):
        self.attemptslimit = maxattempts
        self.operatingfreqindex = 0
        self.attempts = 0
        while (self.attempts < self.attemptslimit):
            self.freqindex = self.attempts % 3 + 1
            if self.quiet == False:
                print 'Frequency Index: ', self.freqindex
            self.dfs_freq_status = self.get_labefana_dfs_freq_status(self.freqindex)
            if self.quiet == False:
                print 'Frequency %s Status = %s' % (self.freqindex, self.dfs_freq_status['State'])
            if (self.dfs_freq_status['State'] == "Operating"): # We've found the current operating frequency
                self.operatingfreqindex = self.freqindex
                break
            self.attempts += 1
            time.sleep(1)
        if self.quiet == False:
            print 'Operating Frequency Index: ', self.operatingfreqindex
        if self.operatingfreqindex == 0:
            self.dfs_freq_status = 'none'
            print
            print "ERROR: No operational DFS frequency found."
            print
        if self.quiet == False:
            print 'Operating Index: %s    Frequency: %s' % (self.operatingfreqindex, str(self.dfs_freq_status['Freq']))
        return (self.operatingfreqindex, self.dfs_freq_status)

    def scanForOperating(self, reboot=False):
        # looks for 'Operating' state and returns when it is found.
        # waits for 'Channel Availablity Check' state to complete and transition
        # to 'Operating'.
        # if 3 'Unavailable' states are found, it will issue a clear dfs timeouts
        # and start looking for operational again

        #  Unavailable/NonOccupancy, Timeout: 00:29:36
        #  Channel Availablity Check, Timeout: 00:00:37
        #  Current State: UnAvailable
        #  Current State: Operating

        self.reboot = reboot
        self.scan = True
        if self.quiet == False:
            print 'scanForOperating()'
        while self.scan == True:
            self.unavailable = 0
            for self.findex in [1, 2, 3]:
                if self.quiet == False:
                    print 'Operating Frequency Index: ', self.findex
                self.dfs_freq_status = self.get_labefana_dfs_freq_status(self.findex)
                self.dfs_freq_state = self.dfs_freq_status['State']
                if self.dfs_freq_state == 'Operating':
                    self.scan = False
                    if self.quiet == False:
                        print 'Operating Frequency: ', str(self.dfs_freq_status['Freq'])
                    return (self.findex, self.dfs_freq_status)
                elif self.dfs_freq_state == 'Channel Availablity Check':
                    if self.quiet == False:
                        print 'Wait for Channel Availability Check timeout'
                    time.sleep(1)
                    break
                elif (self.dfs_freq_state == 'Unavailable/NonOccupancy'):
                    self.unavailable += 1
                    if self.quiet == False:
                        print 'Unavailable count =', self.unavailable
                else:
                    time.sleep(1)
            if self.unavailable == 3:
                if self.reboot == False:
                    self.do_wireless_freq_clear_dfs_timeouts()
                else:
                    self.do_labefana_cmd_reboot()
                    time.sleep(60)
                    self.login()
        return (0, 'none')

def main():

    filename = (((sys.argv[0]).split("\\"))[-1:][0].split("."))[:1][0]

    parser = argparse.ArgumentParser(description='A Selenium WebDriver program to load an AirFiber software image into a radio.')
    parser.add_argument('-a','--address', help='Radio IP Address', required=True)
    parser.add_argument('-u','--user', help='Radio User Name', required=False, default='ubnt')
    parser.add_argument('-p','--password', help='Radio Password', required=False, default='ubnt')
    parser.add_argument('-a2','--address2', help='Radio 2 IP Address', required=False)
    parser.add_argument('-u2','--user2', help='Radio 2 User Name', required=False, default='ubnt')
    parser.add_argument('-p2','--password2', help='Radio 2 Password', required=False, default='ubnt')
    parser.add_argument('--width', help='Browser width', required=False, default=900)
    parser.add_argument('--height', help='Browser height', required=False, default=800)
    parser.add_argument('-i','--image', help='path/firmware_image', required=False, default='none')
    parser.add_argument('-fl','--firmwarelist', help='load firmware image', required=False)
    parser.add_argument('-q','--quiet', help='Debug Output Quiet', required=False, default='True')
    args = vars(parser.parse_args())

    ipaddr = args['address']
    username = args['user']
    password = args['password']
    ipaddr2 = args['address2']
    username2 = args['user2']
    password2 = args['password2']
    width = args['width'] # defaults to 900
    height = args['height'] # defaults to 800
    image_pathname = args['image']
    if args['firmwarelist'] != None:
        firmware_list = ast.literal_eval(args['firmwarelist'])
    quiet = ast.literal_eval(args['quiet'].title())

    print 'quiet:', quiet

    hRadio1 = Http(ipaddr, username, password, quiet)
    hRadio1.login()
 
    if ipaddr2 != None:
        hRadio2 = Http(ipaddr2, username, password, quiet)
        hRadio2.login()
    ########################

    print 'Firmware Version: %s' % hRadio1.firmware_version
    print 'Radio Type: %s' % hRadio1.radiotype
    print 'Build Number: %s' % hRadio1.buildnumber
    print 'Software Version: %s' % hRadio1.version
    print 'Software Version Number: %s' % hRadio1.versionnumber
    version = hRadio1.get_system_fw_version()
    radiotype = hRadio1.get_system_radio_type()
    build = hRadio1.get_system_build_number()
    print 'Initial Firmware Version:', version, '  Build:', build, '  Radio Type:', radiotype
    print 'Isolation = %s' % hRadio1.get_labefana_chain_isolation()                      # Isolation = 7
    print 'Chain 0 EVM = %s' % hRadio1.get_labefana_chain_evm(chain=0)                   # Chain 0 EVM = -12
    print 'Chain 1 EVM = %s' % hRadio1.get_labefana_chain_evm(chain=1)                   # Chain 1 EVM = -21
    print 'BER = %s' % hRadio1.get_labefana_ber()                                        # BER = 3.0248337e-3
    print 'Coarse = %s' % hRadio1.get_labefana_coarse()
    print 'Fine = %s' % hRadio1.get_labefana_fine()

    if image_pathname != 'none':
        print 'Release:', image_pathname
        hRadio1.load_fw(image_pathname)
        version = hRadio1.get_system_fw_version()
        radiotype = hRadio1.get_system_radio_type()
        build = hRadio1.get_system_build_number()
        print 'New Firmware Version:', version, '  Build:', build, '  Radio Type:', radiotype

    hRadio1.browser.quit()
    if ipaddr2 != None:
        hRadio2.browser.quit()


if __name__ == '__main__':
    main()

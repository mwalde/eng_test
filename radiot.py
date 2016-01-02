#!/usr/bin/python

import sys
import telnetlib
import socket
import time
import datetime
import re
import itertools

sys.path.append('/mnt/shared/test/py/obj/')
import utils02 as utils

class RadioT(object):
    """Telnet Command Interface

    Attributes:
        radioTCount                     A class variable that counts instaniated RadioT objects.
        debug                           A flag to enable debugging print statements <False|True>.
        radio_id                        Interger ID of radio object instantiation.
        ip                              Radio IP address.
        username                        Radio user name for Telnet and HTTP.
        password                        Radio user password for Telnet and HTTP.
        tPort                           Telnet port number.
        tTimeout                        Telnet timeout.
        tRadio                          Radio's Telnet handle.
        tPrompt                         Radio's Telnet prompt (example: r2s2top login:).
        loginPrompt                     Radio's log-in prompt (example: login:).
        radioPrompt                     Radio's command prompt (example: #).
        devicename                      get only, Radio's device name (example: r2s2top) taken from the Telnet log-in prompt.
        firmware_version                get only, Radio's fw version taken from /usr/lib/version.
        radio_type                      get only, Radio's type (AF, AF02, AF06,...) taken from /usr/lib/version.
        build_number                    get only taken from /usr/lib/version.
        version_number                  get only (2.2) taken from /usr/lib/version.
        local_mac                       get only, return example: 04:18:D6:51:00:66
        fpga_version                    get only, return example: 141212v4
        status                          get only, Radio's mode and operational status.
        status_device_name
        status_operating_mode
        status_rf_link_status
        status_link_name
      o status_security
        status_version
      o status_uptime
        status_link_uptime
        status_remote_mac
      o status_remote_ip
      o status_date
        status_duplex
        status_frequency
        status_channel_width
        status_duty_cycle
        status_regulatory_domain
        status_chain_0_signal_strength
        status_chain_1_signal_strength
        status_remote_chain_0_signal_strength
        status_remote_chain_1_signal_strength
        status_local_modulation_rate
        status_remote_modulation_rate
        status_tx_capacity
        status_rx_capacity
        status_tx_power
        status_remote_tx_power
        status_dac_temp_0
        status_dac_temp_1
        status_distance_feet
        status_distance_miles
        status_distance_meters
        status_distance_kilometers

        # <Wireless> Basic Wireless Settings
        wireless_wireless_mode            mode get, set <master|slave>
        wireless_link_name                linkname get, set <string>
        wireless_country_code             countrycode get, set (156 (China), 276 (Germany), 840 (United States), 8191, )
        wireless_country_dom              countrydom get, set (none, fcc, etsi, other,...)
        wireless_duplex                   duplex get, set <half|full>
        wireless_channel_bandwidth        channelbandwidth get, set <50|40|30|20|10>
        wireless_tx_channel_bandwidth     txchannelbandwidth get, set <50|40|30|20|10>
        wireless_rx_channel_bandwidth     rxchannelbandwidth get, set <50|40|30|20|10>
        wireless_master_tx_duty_cycle     dutycycle get, set <25|33|50|67|75>
        wireless_output_power             powerout get, set integer valude in dBm
        wireless_antenna_gain             antennagain get, set integer value in dBi
        wireless_cable_loss               get, set integer value in dB
        wireless_maximum_modulation_rate  speed get, set <0x|1x|2x|4x|6x|8x|10x>
        wireless_automatic_rate_adaption  modcontrol get, set <manual|automatic>
        wireless_rx_gain                  rxgain get, set <low,high>

        # <Wireless> Frequency Settings
        wireless_tx_frequency             txfrequency get, set float in GHz or integer in MHz
        wireless_tx_frequency_1           tx1frequency get, set float in GHz or integer in MHz
        wireless_rx_frequency             rxfrequency get, set float in GHz or integer in MHz
        wireless_rx_frequency_1           rx1frequency get, set float in GHz or integer in MHz
        wireless_tx_frequency_2           tx2frequency get, set float in GHz or integer in MHz
        wireless_rx_frequency_2           rx2frequency get, set float in GHz or integer in MHz
        wireless_tx_frequency_3           tx3frequency get, set float in GHz or integer in MHz
        wireless_rx_frequency_3           rx3frequency get, set float in GHz or integer in MHz

        # <Wireless> Wireless Security
      ! wireless_key_type                 get, set <hex|ascii>       NO AF COMMAND
        wireless_key                      key get, set string (0000:0000:0000:0000:0000:0000:0000:0000)

        # <Advanced> Wireless Settings
        advanced_gps_clock_sync           gps get, set <off|on>

        # <Advanced> DATA Port Ethernet Settings
        advanced_data_speed               dpcntl get, set <auto|10Mbps-Half|100Mbps-Half|10Mbps-Full|100Mbps-Full> 
        advanced_data_link                dpstat get only (set returns a warning).
        advanced_flow_control             flowcntl get, set <off|on>          
        advanced_multicast_filter         mcastfilter get, set <off|on>          
        advanced_track_radio_link         carrierdrop get, set <off|timer|link>  
        advanced_link_off_duration        carrierdropto get, set integer           
        advanced_link_off_spacing         carrierdropspc get, set integer

        # AF Commands
        af_minfreq                        minfreq get only
        af_maxfreq                        maxfreq get only


    """
    radioTCount = 0

    def __init__(self, ipaddr, user, passwd, debug=False):
        RadioT.radioTCount += 1
        self.debug = debug
        self.radio_id = RadioT.radioTCount
        self.radio_interface = 'telnet'
        self.ip = ipaddr
        self.username = user
        self.password = passwd
        self.tRadio = None
        self.tPort = 23
        self.tTimeout = 5
        self.loginPrompt = 'login: '
        self.tLoggedIn = False
        self.radioPrompt = '#'
        self.width = 900
        self.height = 800
        self.hLoggedin = None
        self.__status = None
        self.__rflinkstatus = None
        self.__linkuptime = None
        self.__fpgaver = None
        self.__lmac = None
        self.__rmac = None
        self.__dfsdom = None
        self.__rxpower0 = None
        self.__rxpower1 = None
        self.__rrxpower0 = None
        self.__rrxpower1 = None
        self.__txmodrate = None
        self.__rtxmodrate = None
        self.__txcapacity = None
        self.__rxcapacity = None
        self.__rpowerout = None
        self.__temp0 = None
        self.__temp1 = None
        self.__feet = None
        self.__miles = None
        self.__meters = None
        self.__kilometers = None
        self.__afaf = None
        self.__afemac = None
        self.__rainfade = None
        self.__rainstat = None
        self.__rain = None
        self.__wirelessmode = None
        self.wireless_modes = ('master','slave','reset','spectral','hwtest')
        self.__firmware_version = None
        self.__radio_type = None
        self.__buildnumber = None
        self.__linkname = None
        self.__countrycode = None
        self.__countrydom = None
        self.__duplex = None
        self.__channelbandwidth = None
        self.__txchannelbandwidth = None
        self.__rxchannelbandwidth = None
        self.__dutycycle = None
        self.__speed = None
        self.__version_number = None
        self.__powerout = None
        self.__antennagain = None
        self.__cableloss = None
        self.__speed = None
        self.__modcontrol = None
        self.__rxgain = None
        self.__txfrequency = None
        self.__tx1frequency = None
        self.__rxfrequency = None
        self.__rx1frequency = None
        self.__tx2frequency = None
        self.__rx2frequency = None
        self.__tx3frequency = None
        self.__rx3frequency = None
        self.__keytype = None
        self.__key = None
        self.__gps = None
        self.__dpcntl = None
        self.__dpstat = None
        self.__flowcntl = None
        self.__mcastfilter = None
        self.__carrierdrop = None
        self.__carrierdropto = None
        self.__carrierdropspc = None
        self.__minfreq = None
        self.__maxfreq = None
        self.country_code_dict = {'32': 'argentina', '36': 'australia', '48': 'bahrain', '52': 'barbados', '84': 'belize', '68': 'bolivia', '76': 'brazil', '96': 'brunei darussalam', '124': 'canada', '152': 'chile', '156': 'china', '170': 'colombia', '188': 'costa rica', '208': 'denmark', '214': 'dominican republic', '218': 'ecuador', '222': 'el salvador', '8191': 'engineering', '246': 'finland', '276': 'germany', '300': 'greece', '308': 'grenada', '316': 'guam', '320': 'guatemala', '340': 'honduras', '344': 'hong kong', '352': 'iceland', '356': 'india', '360': 'indonesia', '368': 'iraq', '372': 'ireland', '388': 'jamaica', '404': 'kenya', '410': 'korea republic', '422': 'lebanon', '438': 'liechtenstein', '446': 'macau', '458': 'malaysia', '484': 'mexico', '504': 'morocco', '524': 'nepal', '554': 'new zealand', '566': 'nigeria', '578': 'norway', '512': 'oman', '586': 'pakistan', '591': 'panama', '598': 'papua new guinea', '604': 'peru', '608': 'philippines', '620': 'portugal', '630': 'puerto rico', '634': 'qatar', '643': 'russia', '682': 'saudi arabia', '702': 'singapore', '710': 'south africa', '724': 'spain', '144': 'sri lanka', '158': 'taiwan', '764': 'thailand', '780': 'trinidad and tobago', '804': 'ukraine', '826': 'united kingdom', '840': 'united states', '858': 'uruguay', '860': 'uzbekistan', '862': 'venezuela'}
        #self.config_section = section
        #self.config = ConfigParser.ConfigParser()
        #dataset = self.config.read(configfile)
        #if len(dataset) == 0:
        #    raise ValueError, "Failed to open file: %s" % configfile
        #try:
        #    self.ip = self.config.get('%s' % self.config_section, 'IP')
        #    self.username = self.config.get('%s' % self.config_section, 'User_Name')
        #    self.password = self.config.get('%s' % self.config_section, 'Password')
        #except ConfigParser.NoSectionError, err:
        #    raise ConfigParser.NoSectionError, 'ConfigParser NoSectionError: %s' % err
        #except ConfigParser.NoOptionError, err:
        #    raise ConfigParser.NoOptionError, 'ConfigParser NoOptionError: %s' % err
        
        if debug == True:
            print 'Finished __init__'
        
    def __del__(self):
        RadioT.radioTCount -= 1

    def tLogin(self):
        """ Sets and returns tLoggedIn = True|False"""
        if self.debug == True:
            print 'tLogin()'
            print '    username = %s' % self.username
            print '    password = %s' % self.password
            print '    radioPrompt = %s' % self.radioPrompt
        self.tRadio.write(self.username + "\n")
        self.usernameresults = self.tRadio.read_until("Password:", 10)
        self.tRadio.write(self.password + "\n")
        self.loginresults = self.tRadio.read_until(self.radioPrompt, 10)
        self.loginelements = self.loginresults.split()
        if self.debug == True:
            print '    loginresults = %s' % self.loginresults
        #print 'login elements = ', self.loginelements
        if self.loginelements[1] == 'incorrect':
            self.tLoggedIn = False
            return self.tLoggedIn
        else:
            #self.radiotype = self.firmware_version.split('.')[0]
            #self.buildnumber = self.getBuildnumber()
            #self.versionnumber = self.getVersionNumber()
            #    print '    version # = %s' % self.versionnumber
            self.tLoggedIn = True
        return self.tLoggedIn

    def tLogout(self):
        self.tRadio.close()
        self.tLoggedIn = False
        if self.debug == True:
            print 'tLogout()'

    def tConnect(self):
        """ Returns True or False. If True, sets devicename."""
        if self.debug == True:
            print 'tConnect()'
            print '    IP Address = %s' % self.ip
            print '    Telnet Port = %s' % self.tPort
            print '    Telnet Timeout = %s' % self.tTimeout
            print '    Login Prompt = %s' % self.loginPrompt
        try:
            self.tRadio = telnetlib.Telnet(self.ip, self.tPort, self.tTimeout)
            self.tPrompt = self.tRadio.read_until(self.loginPrompt, self.tTimeout)
            #print 'Telnet prompt: %s' % self.tPrompt
            self.devicename = self.tPrompt.split()[0]
            #print 'devicename: %s' % self.devicename
            return True
        except:
            if self.debug == True:
                print 'Radio %s (%s) telnet connection failure' % (self.radio_id, self.ip)
            return False



    ########

    def wireless_mode_get(self):
        self.cmd = 'af get mode'
        #print self.cmd
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__wirelessmode = self.results
        except:
            print
            print "EXCEPTION: wireless_mode_get() failed."
            print
            self.__wirelessmode = None
        return self.__wirelessmode

    def wireless_mode_set(self, value):
        if str(value.lower()) not in self.wireless_modes:
            print
            print 'ERROR: radio mode assignment (%s) failure, setting must be master|slave|reset|spectral|hwtest.' % value
            print
            return False
        self.cmd = 'af set mode %s' % value.lower()
        #print self.cmd
        try:
            self.results = self.sendcmd(self.cmd)
        except:
            print "EXCEPTION: af set mode %s  failed." % value
        return True

    wireless_wireless_mode = property(wireless_mode_get, wireless_mode_set)

    def link_name_get(self):
        self.cmd = 'af get linkname'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__linkname = self.results
        except:
            print 'EXCEPTION: af get linkname failed.'
            self.__linkname = None
        return self.__linkname

    def link_name_set(self, value):
        self.cmd = 'af set linkname %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set linkname %s  failed.' % value

    wireless_link_name = property(link_name_get, link_name_set)

    def country_code_get(self):
        if self.debug == True:
            print "self.cmd = 'af get countrycode'"
        self.cmd = 'af get countrycode'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            if self.debug == True:
                print 'start sleep(5)'
                time.sleep(5)
                print 'done sleep(5)'
            self.__countrycode = self.results
        except:
            print
            print 'EXCEPTION: af get countrycode failed.'
            print
            sys.exit(1)
            self.__countrycode = None
        return self.__countrycode

    def country_code_set(self, value):
        self.countrycode_value = str(value).lower() # value can be an integer or country name
        self.countrycode = None
        self.countryname = None
        if self.countrycode_value.isdigit():
            if self.countrycode_value in self.country_code_dict.keys():
                self.countrycode = self.countrycode_value
                self.countryname = self.country_code_dict[self.countrycode_value]
        else:
            for self.cc, self.name in self.country_code_dict.items():
                if self.name == self.countrycode_value:
                    self.countrycode = self.cc
                    break
        if self.countrycode == None:
            print
            print 'ERROR: countrycode (%s) not found.' % self.countrycode_value
            print
        else:
            self.cmd = 'af set countrycode %s' % self.countrycode
            try:
                self.sendcmd(self.cmd)
            except:
                print 'EXCEPTION: af set countrycode %s  failed.' % self.countrycode_value

    wireless_country_code = property(country_code_get, country_code_set)

    def country_name_get(self):
        self.cmd = 'af get countrycode'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__countrycode = self.results
            if self.results in self.country_code_dict.keys():
                self.__countryname = self.country_code_dict[self.results]
        except:
            print 'EXCEPTION: country_name, af get countrycode failed.'
            self.__countryname = None
        return self.__countryname

    def country_name_set(self, value):
        try:
            self.wireless_country_code = value
        except:
            return False
        return True

    country_name = property(country_name_get, country_name_set)

    def country_dom_get(self):
        self.cmd = 'af get countrydom'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__countrydom = self.results
        except:
            print 'EXCEPTION: af get countrydom failed.'
            self.__countrydom = None
        return self.__countrydom

    def country_dom_set(self, value):
        if str(value.lower()) not in ('none','fcc','etsi','acma','apla'):
            print
            print 'ERROR: countrydom assignment (%s) failure, setting must be none|fcc|etsi|acma|apla.' % value
            print
            return
        self.cmd = 'af set countrydom %s' % value.lower()
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set countrydom %s  failed.' % value

    wireless_country_dom = property(country_dom_get, country_dom_set)

    def duplex_get(self):
        # Returns: half,full
        self.cmd = 'af get duplex'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__duplex = self.results
        except:
            print 'EXCEPTION: af get duplex failed.'
            self.__duplex = None
        return self.__duplex

    def duplex_set(self, value):
        if str(value.lower()) not in ('half', 'full'):
            print
            print 'ERROR: duplex assignment (%s) failure, setting must be half|full.' % value
            print
            return
        self.cmd = 'af set duplex %s' % value.lower()
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set duplex %s  failed.' % value

    wireless_duplex = property(duplex_get, duplex_set)

    def channel_bandwidth_get(self):
        # Returns channel bandwidth for both channels: 50MHz 50MHz
        if self.radio_type.lower() == 'af' and self.version_number < '2.1':
            self.__channelbandwidth = '100'
        else:
            self.cmd = 'af get channelbandwidth' # Returns: 100MHz 100MHz
            try:
                self.results = self.sendcmd(self.cmd).split()[3][:-3]
                self.__channelbandwidth = self.results
            except:
                print 'EXCEPTION: af get channelbandwidth failed.'
                self.__channelbandwidth = None
        return self.__channelbandwidth

    def channel_bandwidth_set(self, value):
        if self.radio_type.lower() == 'af' and str(value) != '100':
            print
            print 'ERROR: wireless_channel_bandwidth assignment failure, AF setting must be 100.'
            print
            return
        else:
            if self.radio_type.lower() != 'af' and str(value) not in ('50', '40', '30', '20', '10'):
                print
                print 'ERROR: wireless_channel_bandwidth assignment (%s) failure, setting must be 50|40|30|20|10.' % value
                print
                return
        self.cmd = 'af set channelbandwidth %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set channelbandwidth %s  failed.' % value
        #if self.wait == True:
        #    self.waitOperational()

    wireless_channel_bandwidth = property(channel_bandwidth_get, channel_bandwidth_set)

    def tx_channel_bandwidth_get(self):
        if self.radio_type.lower() == 'af' and self.version_number < '2.1':
            self.__txchannelbandwidth = '100'
        else:
            self.cmd = 'af get txchannelbandwidth' # Returns: 100MHz
            try:
                self.results = self.sendcmd(self.cmd).split()[3][:-3]
                self.__txchannelbandwidth = self.results
            except:
                print 'EXCEPTION: af get txchannelbandwidth failed.'
                self.__txchannelbandwidth = None
        return self.__txchannelbandwidth

    def tx_channel_bandwidth_set(self, value):
        if self.radio_type.lower() == 'af' and str(value) != '100':
            print
            print 'ERROR: wireless_tx_channel_bandwidth assignment failure, AF setting must be 100.'
            print
            return
        else:
            if str(value) not in ('50', '40', '30', '20', '10'):
                print
                print 'ERROR: wireless_tx_channel_bandwidth assignment (%s) failure, setting must be 50|40|30|20|10.' % value
                print
                return
        self.cmd = 'af set txchannelbandwidth %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set txchannelbandwidth %s  failed.' % value
        #if self.wait == True:
        #    self.waitOperational()

    wireless_tx_channel_bandwidth = property(tx_channel_bandwidth_get, tx_channel_bandwidth_set)

    def rx_channel_bandwidth_get(self):
        # AF cmd not available before 19206
        # GUI not available before 19233
        if self.radio_type.lower() == 'af' and self.version_number < '2.1':
            self.__rxchannelbandwidth = '100'
        else:
            self.cmd = 'af get rxchannelbandwidth' # Returns: 100MHz
            try:
                self.results = self.sendcmd(self.cmd).split()[3][:-3]
                self.__rxchannelbandwidth = self.results
            except:
                print 'EXCEPTION: af get rxchannelbandwidth failed.'
                self.__rxchannelbandwidth = None
        return self.__rxchannelbandwidth

    def rx_channel_bandwidth_set(self, value):
        if self.radio_type.lower() == 'af' and str(value) != '100':
            print
            print 'ERROR: wireless_rx_channel_bandwidth assignment failure, AF setting must be 100.'
            print
            return
        else:
            if str(value) not in ('50', '40', '30', '20', '10'):
                print
                print 'ERROR: wireless_rx_channel_bandwidth assignment (%s) failure, setting must be 50|40|30|20|10.' % value
                print
                return
        self.cmd = 'af set rxchannelbandwidth %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set rxchannelbandwidth %s  failed.' % value
        #if self.wait == True:
        #    self.waitOperational()

    wireless_rx_channel_bandwidth = property(rx_channel_bandwidth_get, rx_channel_bandwidth_set)

    def master_tx_duty_cycle_get(self):
        # Returns: 25, 33, 50, 67, 75
        # Only officially available for af06
        # Some engineering releases for af and af02 contain af commands for dutycycle
        self.cmd = 'af get dutycycle'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__dutycycle = self.results
        except:
            print 'EXCEPTION: af get dutycycle failed.'
            self.__dutycycle = None
        return self.__dutycycle

    def master_tx_duty_cycle_set(self, value):
        if self.radio_type.lower() != 'af06':
            print
            print 'ERROR: wireless_master_tx_duty_cycle assignment failure, radio must be type AF06.'
            print
            return
        else:
            if str(value) not in ('25', '33', '50', '67', '75'):
                print
                print 'ERROR: wireless_master_tx_duty_cycle assignment (%s) failure, setting must be 25|33|50|67|75.' % value
                print
                return
        self.cmd = 'af set dutycycle %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set dutycycle %s  failed.' % value
        #if self.wait == True:
        #    self.waitOperational()

    wireless_master_tx_duty_cycle = property(master_tx_duty_cycle_get, master_tx_duty_cycle_set)

    def output_power_get(self):
        self.cmd = 'af get powerout'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__powerout = self.results
        except:
            print 'EXCEPTION: af get powerout failed.'
            self.__powerout = None
        return self.__powerout

    def output_power_set(self, value):
        self.cmd = 'af set powerout %s' % str(value)
        try:
            result = self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set powerout %s  failed.' % value
        return None

    wireless_output_power = property(output_power_get, output_power_set)

    def antenna_gain_get(self):
        # Not available: af
        # Available: af02, af06
        self.cmd = 'af get antennagain'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__antennagain = self.results
        except:
            print 'EXCEPTION: af get antennagain failed.'
            self.__antennagain = None
        return self.__antennagain

    def antenna_gain_set(self, value):
        # Not available: af, af02
        # Available: af06
        self.cmd = 'af set antennagain %s' % str(value)
        try:
            self.result = self.sendcmd(self.cmd)
            if 'error' in str(self.result).lower():
                print
                print 'ERROR: af set antennagain %s  failed.' % value
                print
        except:
            print 'EXCEPTION: af set antennagain %s  failed.' % value
        return None

    wireless_antenna_gain = property(antenna_gain_get, antenna_gain_set)

    def cable_loss_get(self):
        # Not available: af
        # Available: af02, af06
        self.cmd = 'af get cableloss'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__antennagain = self.results
        except:
            print 'EXCEPTION: af get cableloss failed.'
            self.__antennagain = None
        return self.__antennagain

    def cable_loss_set(self, value):
        # Not available: af
        # Available: af02, af06
        self.cmd = 'af set cableloss %s' % str(value)
        try:
            self.result = self.sendcmd(self.cmd)
            if 'error' in str(self.result).lower():
                print
                print 'ERROR: af set cableloss %s  failed.' % value
                print
        except:
            print 'EXCEPTION: af set cableloss %s  failed.' % value
        return None

    wireless_cable_loss = property(cable_loss_get, cable_loss_set)

    def maximum_modulation_rate_get(self):
        # Returns: 0x, 1x, 2x, 4x, 6x, 8x, 10x
        self.cmd = 'af get speed'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__speed = self.results
        except:
            print 'EXCEPTION: af get speed failed.'
            self.__speed = None
        return self.__speed

    def maximum_modulation_rate_set(self, value):
        if str(value) not in ('0x', '1x', '2x', '4x', '6x', '8x', '10x'):
            print
            print 'ERROR: wireless_maximum_modulation_rate assignment (%s) failure, setting must be 0x|1x|2x|4x|6x|8x|10x.' % value
            print
            return
        self.cmd = 'af set speed %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set speed %s  failed.' % value

    wireless_maximum_modulation_rate = property(maximum_modulation_rate_get, maximum_modulation_rate_set)

    def automatic_rate_adaption_get(self):
        # Returns: manual, automatic
        self.cmd = 'af get modcontrol'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__modcontrol = self.results
        except:
            print 'EXCEPTION: af get modcontrol failed.'
            self.__modcontrol = None
        return self.__modcontrol

    def automatic_rate_adaption_set(self, value):
        if str(value) not in ('manual', 'automatic'):
            print
            print 'ERROR: wireless_automatic_rate_adaption assignment (%s) failure, setting must be manual|automatic.' % value
            print
            return
        self.cmd = 'af set modcontrol %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set modcontrol %s  failed.' % value

    wireless_automatic_rate_adaption = property(automatic_rate_adaption_get, automatic_rate_adaption_set)

    def rx_gain_get(self):
        # Returns: low, high
        self.cmd = 'af get rxgain'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__speed = self.results
        except:
            print 'EXCEPTION: af get rxgain failed.'
            self.__speed = None
        return self.__speed

    def rx_gain_set(self, value):
        if str(value) not in ('low', 'high'):
            print
            print 'ERROR: wireless_rx_gain assignment (%s) failure, setting must be low|high.' % value
            print
            return
        self.cmd = 'af set rxgain %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set rxgain %s  failed.' % value

    wireless_rx_gain = property(rx_gain_get, rx_gain_set)

    def tx_frequency_get(self):
        # Returns: 5.752GHz
        self.cmd = 'af get tx1frequency'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__txfrequency = self.results
        except:
            print 'EXCEPTION: af get txfrequency failed.'
            self.__txfrequency = None
        return self.__txfrequency

    def tx_frequency_set(self, value):
        self.cmd = 'af set tx1frequency %s' % value
        try:
            self.results = self.sendcmd(self.cmd)
            if 'error' in str(self.results).lower():
                print
                print 'ERROR: af set txfrequency %s  failed.' % value
                print
        except:
            print 'EXCEPTION: af set txfrequency %s  failed.' % value

    wireless_tx_frequency = property(tx_frequency_get, tx_frequency_set)

    def tx_frequency_1_get(self):
        # Returns: 5.752GHz
        self.cmd = 'af get tx1frequency'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__tx1frequency = self.results
        except:
            print 'EXCEPTION: af get tx1frequency failed.'
            self.__tx1frequency = None
        return self.__tx1frequency

    def tx_frequency_1_set(self, value):
        self.cmd = 'af set tx1frequency %s' % value
        try:
            self.results = self.sendcmd(self.cmd)
            if 'error' in str(self.results).lower():
                print
                print 'ERROR: af set tx1frequency %s  failed.' % value
                print
        except:
            print 'EXCEPTION: af set tx1frequency %s  failed.' % value

    wireless_tx_frequency_1 = property(tx_frequency_1_get, tx_frequency_1_set)

    def rx_frequency_get(self):
        # Returns: 5.752GHz
        self.cmd = 'af get rxfrequency'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rxfrequency = self.results
        except:
            print 'EXCEPTION: af get rxfrequency failed.'
            self.__rxfrequency = None
        return self.__rxfrequency

    def rx_frequency_set(self, value):
        self.cmd = 'af set rxfrequency %s' % value
        try:
            self.results = self.sendcmd(self.cmd)
            if 'error' in str(self.results).lower():
                print
                print 'ERROR: af set rxfrequency %s  failed.' % value
                print
        except:
            print 'EXCEPTION: af set rxfrequency %s  failed.' % value

    wireless_rx_frequency = property(rx_frequency_get, rx_frequency_set)

    #def rx_frequency_1_get(self):
    #    # Returns: 5.752GHz
    #    self.cmd = 'af get rx1frequency'
    #    try:
    #        self.results = self.sendcmd(self.cmd).split()[3]
    #        self.__rx1frequency = self.results
    #    except:
    #        print 'EXCEPTION: af get rx1frequency failed.'
    #        self.__rx1frequency = None
    #    return self.__rx1frequency

    #def rx_frequency_1_set(self, value):
    #    self.cmd = 'af set rx1frequency %s' % value
    #    try:
    #        self.results = self.sendcmd(self.cmd)
    #        if 'error' in str(self.results).lower():
    #            print
    #            print 'ERROR: af set rx1frequency %s  failed.' % value
    #            print
    #    except:
    #        print 'EXCEPTION: af set rx1frequency %s  failed.' % value

    wireless_rx_frequency_1 = property(rx_frequency_get, rx_frequency_set)

    def tx_frequency_2_get(self):
        # Returns: 5.752GHz
        self.cmd = 'af get tx2frequency'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__tx2frequency = self.results
        except:
            print 'EXCEPTION: af get tx2frequency failed.'
            self.__tx2frequency = None
        return self.__tx2frequency

    def tx_frequency_2_set(self, value):
        self.cmd = 'af set tx2frequency %s' % value
        try:
            self.results = self.sendcmd(self.cmd)
            if 'error' in str(self.results).lower():
                print
                print 'ERROR: af set tx2frequency %s  failed.' % value
                print
        except:
            print 'EXCEPTION: af set tx2frequency %s  failed.' % value

    wireless_tx_frequency_2 = property(tx_frequency_2_get, tx_frequency_2_set)

    def rx_frequency_2_get(self):
        # Returns: 5.752GHz
        self.cmd = 'af get rx2frequency'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rx2frequency = self.results
        except:
            print 'EXCEPTION: af get rx2frequency failed.'
            self.__rx2frequency = None
        return self.__rx2frequency

    def rx_frequency_2_set(self, value):
        self.cmd = 'af set rx2frequency %s' % value
        try:
            self.results = self.sendcmd(self.cmd)
            if 'error' in str(self.results).lower():
                print
                print 'ERROR: af set rx2frequency %s  failed.' % value
                print
        except:
            print 'EXCEPTION: af set rx2frequency %s  failed.' % value

    wireless_rx_frequency_2 = property(rx_frequency_2_get, rx_frequency_2_set)

    def tx_frequency_3_get(self):
        # Returns: 5.752GHz
        self.cmd = 'af get tx3frequency'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__tx3frequency = self.results
        except:
            print 'EXCEPTION: af get tx3frequency failed.'
            self.__tx3frequency = None
        return self.__tx3frequency

    def tx_frequency_3_set(self, value):
        self.cmd = 'af set tx3frequency %s' % value
        try:
            self.results = self.sendcmd(self.cmd)
            if 'error' in str(self.results).lower():
                print
                print 'ERROR: af set tx3frequency %s  failed.' % value
                print
        except:
            print 'EXCEPTION: af set tx3frequency %s  failed.' % value

    wireless_tx_frequency_3 = property(tx_frequency_3_get, tx_frequency_3_set)

    def rx_frequency_3_get(self):
        # Returns: 5.752GHz
        self.cmd = 'af get rx3frequency'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rx3frequency = self.results
        except:
            print 'EXCEPTION: af get rx3frequency failed.'
            self.__rx3frequency = None
        return self.__rx3frequency

    def rx_frequency_3_set(self, value):
        self.cmd = 'af set rx3frequency %s' % value
        try:
            self.results = self.sendcmd(self.cmd)
            if 'error' in str(self.results).lower():
                print
                print 'ERROR: af set rx3frequency %s  failed.' % value
                print
        except:
            print 'EXCEPTION: af set rx3frequency %s  failed.' % value

    wireless_rx_frequency_3 = property(rx_frequency_3_get, rx_frequency_3_set)

    def key_type_get(self):
        # Returns: hex, ascii
        self.cmd = 'af get keytype'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__keytype = self.results
        except:
            print 'EXCEPTION: af get keytype failed.'
            self.__keytype = None
        return self.__keytype

    def key_type_set(self, value):
        if str(value) not in ('hex', 'ascii'):
            print
            print 'ERROR: wireless_key_type assignment (%s) failure, setting must be hex|ascii.' % value
            print
            return
        self.cmd = 'af set keytype %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set keytype %s  failed.' % value

    wireless_key_type = property(key_type_get, key_type_set)

    def key_get(self):
        # Returns: 0000:0000:0000:0000:0000:0000:0000:0000 in hex mode
        # Returns: in ascii mode
        self.cmd = 'af get key'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__key = self.results
        except:
            print 'EXCEPTION: af get key failed.'
            self.__key = None
        return self.__key

    def key_set(self, value):
        self.cmd = 'af set key %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set key %s  failed.' % value

    wireless_key = property(key_get, key_set)

    def gps_clock_sync_get(self):
        # Returns: off, on
        self.cmd = 'af get gps'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__gps = self.results
        except:
            print 'EXCEPTION: af get gps failed.'
            self.__gps = None
        return self.__gps

    def gps_clock_sync_set(self, value):
        if str(value) not in ('off', 'on'):
            print
            print 'ERROR: gps_clock_sync_set assignment (%s) failure, setting must be off|on.' % value
            print
            return
        self.cmd = 'af set gps %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set gps %s  failed.' % value

    advanced_gps_clock_sync = property(gps_clock_sync_get, gps_clock_sync_set)

    def data_speed_get(self):
        # Returns: auto,10Mbps-Half,100Mbps-Half,10Mbps-Full,100Mbps-Full
        self.cmd = 'af get dpcntl'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__dpcntl = self.results
        except:
            print 'EXCEPTION: af get dpcntl failed.'
            self.__dpcntl = None
        return self.__dpcntl

    def data_speed_set(self, value):
        if str(value) not in ('auto','10Mbps-Half','100Mbps-Half','10Mbps-Full','100Mbps-Full'):
            print
            print 'ERROR: data_speed_set assignment (%s) failure, setting must be off|on.' % value
            print
            return
        self.cmd = 'af set dpcntl %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set dpcntl %s  failed.' % value

    advanced_data_speed = property(data_speed_get, data_speed_set)

    def data_link_get(self):
        # Ethernet data link status
        # Returns: nolink, 1000Mbps-Full, ...
        self.cmd = 'af get dpstat'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__dpstat = self.results
        except:
            print 'EXCEPTION: af get dpstat failed.'
            self.__dpstat = None
        return self.__dpstat

    def data_link_set(self, value):
        print
        print 'ERROR: advanced_data_link is a read-only variable.'
        print
        return

    advanced_data_link = property(data_link_get, data_link_set)

    def flow_control_get(self):
        # Returns: off, on
        self.cmd = 'af get flowcntl'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__flowcntl = self.results
        except:
            print 'EXCEPTION: af get flowcntl failed.'
            self.__flowcntl = None
        return self.__flowcntl

    def flow_control_set(self, value):
        if str(value) not in ('off', 'on'):
            print
            print 'ERROR: flow_control_set assignment (%s) failure, setting must be off|on.' % value
            print
            return
        self.cmd = 'af set flowcntl %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set flowcntl %s  failed.' % value

    advanced_flow_control = property(flow_control_get, flow_control_set)

    def multicast_filter_get(self):
        # Returns: off, on
        self.cmd = 'af get mcastfilter'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__mcastfilter = self.results
        except:
            print 'EXCEPTION: af get mcastfilter failed.'
            self.__mcastfilter = None
        return self.__mcastfilter

    def multicast_filter_set(self, value):
        if str(value) not in ('off', 'on'):
            print
            print 'ERROR: multicast_filter_set assignment (%s) failure, setting must be off|on.' % value
            print
            return
        self.cmd = 'af set mcastfilter %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set mcastfilter %s  failed.' % value

    advanced_multicast_filter = property(multicast_filter_get, multicast_filter_set)

    def track_radio_link_get(self):
        # Returns: off,timer,link
        self.cmd = 'af get carrierdrop'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__carrierdrop = self.results
        except:
            print 'EXCEPTION: af get carrierdrop failed.'
            self.__carrierdrop = None
        return self.__carrierdrop

    def track_radio_link_set(self, value):
        if str(value) not in ('off','timer','link'):
            print
            print 'ERROR: track_radio_link_set assignment (%s) failure, setting must be off|timer|link.' % value
            print
            return
        self.cmd = 'af set carrierdrop %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set carrierdrop %s  failed.' % value

    advanced_track_radio_link = property(track_radio_link_get, track_radio_link_set)

    def link_off_duration_get(self):
        # Returns: integer
        self.cmd = 'af get carrierdropto'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__carrierdropto = self.results
        except:
            print 'EXCEPTION: af get carrierdropto failed.'
            self.__carrierdropto = None
        return self.__carrierdropto

    def link_off_duration_set(self, value):
        self.cmd = 'af set carrierdropto %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set carrierdropto %s  failed.' % value

    advanced_link_off_duration = property(link_off_duration_get, link_off_duration_set)

    def link_off_spacing_get(self):
        # Returns: integer
        self.cmd = 'af get carrierdropspc'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__carrierdropspc = self.results
        except:
            print 'EXCEPTION: af get carrierdropspc failed.'
            self.__carrierdropspc = None
        return self.__carrierdropspc

    def link_off_spacing_set(self, value):
        self.cmd = 'af set carrierdropspc %s' % value
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set carrierdropspc %s  failed.' % value

    advanced_link_off_spacing = property(link_off_spacing_get, link_off_spacing_set)



    #####################################################



    def firmware_version_get(self):
        # cat cmd returns 3 lines. Split the lines and select the second.
        # Split the second line at the periods, select the 3rd element from the back.
        # cat /usr/lib/version
        try:
            #self.tRadio.write("\n")
            #results = self.tRadio.read_until(self.radioPrompt, 10)
            #self.__firmware_version = results.split()[-1][:-1]
            self.cmd = 'cat /usr/lib/version'
            results = self.sendcmd(self.cmd).split('\n')[-2].split('.')
            #self.__firmware_version = results[0]+'.'+'.'.join(results[2:])
            self.__firmware_version = results[0]+'.'+'.'.join(results[2:]).replace("\r","")
        except:
            print "EXCEPTION: get firmware_version failed."
            self.__firmware_version = None
        return self.__firmware_version

    def firmware_version_set(self, value):
        print
        print "WARNING: firmware_version is not settable."
        print
        return None

    firmware_version = property(firmware_version_get, firmware_version_set)

    def radio_type_get(self):
        # cat cmd returns 3 lines. Split the lines and select the second.
        # Split the second line at the periods, select the 3rd element from the back.
        # cat /usr/lib/version
        try:
            #self.tRadio.write("\n")
            #results = self.tRadio.read_until(self.radioPrompt, 10)
            #self.__radio_type = results.split('.')[0].strip()
            self.cmd = 'cat /usr/lib/version'
            self.__radio_type = self.sendcmd(self.cmd).split('\n')[-2].split('.')[0].strip()
        except:
            print "EXCEPTION: get radio_type failed."
            self.__radio_type = None
        return self.__radio_type

    def radio_type_set(self, value):
        print
        print "WARNING: radio_type is not settable."
        print
        return None

    radio_type = property(radio_type_get, radio_type_set)

    def build_number_get(self):
        # cat cmd returns 3 lines. Split the lines and select the second.
        # Split the second line at the periods, select the 3rd element from the back.
        # cat /usr/lib/version
        try:
            self.cmd = 'cat /usr/lib/version'
            self.__buildnumber = self.sendcmd(self.cmd).split('\n')[-2].split('.')[-3]
        except:
            print 'EXCEPTION: get build_number failed'
            self.__buildnumber = None
        return self.__buildnumber

    def build_number_set(self, value):
        print
        print "WARNING: build_number is not settable."
        print
        return None

    build_number = property(build_number_get, build_number_set)

    def version_number_get(self):
        # cat cmd returns 3 lines. Split the lines and select the second.
        # Split the second line at the periods, select the 3rd element from the back.
        # cat /usr/lib/version
        try:
            self.cmd = 'cat /usr/lib/version'
            ver_members = self.sendcmd(self.cmd).split('\n')[-2].split('.')[2:4]
            if '-' in ver_members[1]:
                ver_minor = ver_members[1].split('-')[0]
            else:
                ver_minor = ver_members[1]
            self.__version_number = ver_members[0][1:]+'.'+ver_minor
        except:
            print 'EXCEPTION: get version_number failed'
            self.__versionn_umber = None
        return self.__version_number

    def version_number_set(self, value):
        print
        print "WARNING: version_number is not settable."
        print
        return None

    version_number = property(version_number_get, version_number_set)
         
    #   Send Command and wait for Prompt
    def sendcmd(self, cmd, attempts=5):
        if self.debug == True:
            print 'sendcmd(%s)' % cmd
        self.cmd = cmd
        self.retries = attempts
        self.results = 'fail'
        if self.cmd != None:
            while (self.retries > 0) and (self.results == 'fail'):
                self.retries = self.retries - 1
                try:
                    self.tRadio.write(self.cmd + '\n')
                except:
                    print 'EXCEPTION: sendcmd write cmd', self.cmd
                if self.radioPrompt != None:
                    try:
                        self.results = self.tRadio.read_until(self.radioPrompt, 10)
                    except:
                        print 'EXCEPTION: sendcmd:', self.cmd, ' read_until', self.results
                        self.results = 'fail'
            if 'error ' in str(self.results).lower():
                if self.debug == True:
                    print
                    print 'ERROR: %s' % self.results
                    print
                self.results = 'ERROR sendcmd()'
        if self.debug == True:
            print 'sendcmd results:', self.results
        return self.results

    def status_get(self):
        # Radio mode and operational status
        # Returns: master-operational, ...
        self.cmd = 'af get status'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__status = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__status = None
        return self.__status

    def status_set(self, value):
        print
        print 'ERROR: status is a read-only variable.'
        print
        return

    status = property(status_get, status_set)

    def status_device_name_get(self):
        # obtained during Telnet login
        return self.devicename

    def status_device_name_set(self, value):
        print
        print 'ERROR: status_device_name is a read-only variable.'
        print
        return

    status_device_name = property(status_device_name_get, status_device_name_set)

    def status_operating_mode_set(self, value):
        print
        print 'ERROR: status_operating_mode is a read-only variable.'
        print
        return

    status_operating_mode = property(wireless_mode_get, status_operating_mode_set)

    def rf_link_status_get(self):
        # Radio operational status
        # Returns: operational, ...
        self.cmd = 'af get status'
        try:
            self.results = self.sendcmd(self.cmd).split()[3].split('-')[1]
            self.__rflinkstatus = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__rflinkstatus = None
        return self.__rflinkstatus

    def rf_link_status_set(self, value):
        print
        print 'ERROR: status_rf_link_status is a read-only variable.'
        print
        return

    status_rf_link_status = property(rf_link_status_get, rf_link_status_set)

    def status_link_name_set(self, value):
        print
        print 'ERROR: status_link_name is a read-only variable.'
        print
        return

    status_link_name = property(link_name_get, status_link_name_set)

    def status_version_set(self, value):
        print
        print 'ERROR: status_version is a read-only variable.'
        print
        return

    status_version = property(firmware_version_get, status_version_set)

    def link_uptime_get(self):
        # Radio link up time
        # Returns: 
        self.cmd = 'af get linkuptime'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__linkuptime = str(datetime.timedelta(seconds=int(self.results)))
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__linkuptime = None
        return self.__linkuptime

    def link_uptime_set(self, value):
        print
        print 'ERROR: status_link_uptime is a read-only variable.'
        print
        return

    status_link_uptime = property(link_uptime_get, link_uptime_set)

    def remote_mac_get(self):
        # Radio link up time
        # Returns: 
        self.cmd = 'af get rmac'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rmac = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__rmac = None
        return self.__rmac

    def remote_mac_set(self, value):
        print
        print 'ERROR: status_remote_mac is a read-only variable.'
        print
        return

    status_remote_mac = property(remote_mac_get, remote_mac_set)

    def fpga_ver_get(self):
        self.cmd = "ver"
        #self.getresults = self.sendcmd(self.cmd).split()
        #print 'ver results = %s' % self.getresults
        try:
            self.getresults = self.sendcmd(self.cmd).split()
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__fpgaver = None
            return self.__fpgaver
        self.datelist = self.getresults[5].split('/')
        #print 'datelist results = %s' % self.datelist
        self.date = self.datelist[2][2:].zfill(2)+self.datelist[0].zfill(2)+self.datelist[1].zfill(2)
        #print 'date results = %s' % self.date
        self.__fpgaver = self.date+'v'+self.getresults[3]
        return self.__fpgaver

    def fpga_ver_set(self, value):
        print
        print 'ERROR: fpga_version is a read-only variable.'
        print
        return

    fpga_version = property(fpga_ver_get, fpga_ver_set)

    def mac_get(self):
        self.cmd = "ifconfig | grep HWaddr\n"
        try:
            self.tRadio.write(self.cmd)
            self.getresults = self.tRadio.read_until(self.radioPrompt, 5)
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__lmac = None
            return self.__lmac
        self.maclist = self.getresults[self.getresults.find('Ethernet'):].split()[2].split(':')
        self.__lmac = '%s:%s:%s:%s:%s:%s' % (self.maclist[0], self.maclist[1], self.maclist[2], self.maclist[3], self.maclist[4], self.maclist[5])
        return self.__lmac

    def mac_set(self, value):
        print
        print 'ERROR: local_mac is a read-only variable.'
        print
        return

    local_mac = property(mac_get, mac_set)

    def status_duplex_set(self, value):
        print
        print 'ERROR: status_duplex is a read-only variable.'
        print
        return

    status_duplex = property(duplex_get, status_duplex_set)

    def status_frequency_set(self, value):
        print
        print 'ERROR: status_frequency is a read-only variable.'
        print
        return

    status_frequency = property(tx_frequency_get, status_frequency_set)

    def status_channel_width_set(self, value):
        print
        print 'ERROR: status_channel_width is a read-only variable.'
        print
        return

    status_channel_width = property(tx_channel_bandwidth_get, status_channel_width_set)

    def status_duty_cycle_set(self, value):
        print
        print 'ERROR: status_duty_cycle is a read-only variable.'
        print
        return

    status_duty_cycle = property(master_tx_duty_cycle_get, status_duty_cycle_set)

    def regulatory_domain_get(self):
        # Radio regulatory domain status
        # Returns: 
        self.cmd = 'af get dfsdom'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__dfsdom = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__dfsdom = None
        return self.__dfsdom

    def regulatory_domain_set(self, value):
        print
        print 'ERROR: status_regulatory_domain is a read-only variable.'
        print
        return

    status_regulatory_domain = property(regulatory_domain_get, regulatory_domain_set)

    def chain_0_signal_strength_get(self):
        # Radio chain_0_signal_strength
        # Returns: integer string (ex.:-53)
        self.cmd = 'af get rxpower0'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rxpower0 = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__rxpower0 = None
        return self.__rxpower0

    def chain_0_signal_strength_set(self, value):
        print
        print 'ERROR: status_chain_0_signal_strength is a read-only variable.'
        print
        return

    status_chain_0_signal_strength = property(chain_0_signal_strength_get, chain_0_signal_strength_set)

    def chain_1_signal_strength_get(self):
        # Radio chain_1_signal_strength
        # Returns: integer string (ex.:-53)
        self.cmd = 'af get rxpower1'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rxpower1 = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__rxpower1 = None
        return self.__rxpower1

    def chain_1_signal_strength_set(self, value):
        print
        print 'ERROR: status_chain_1_signal_strength is a read-only variable.'
        print
        return

    status_chain_1_signal_strength = property(chain_1_signal_strength_get, chain_1_signal_strength_set)

    def remote_chain_0_signal_strength_get(self):
        # Radio remote_chain_0_signal_strength
        # Returns: integer string (ex.:-53)
        self.cmd = 'af get rrxpower0'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rrxpower0 = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__rrxpower0 = None
        return self.__rrxpower0

    def remote_chain_0_signal_strength_set(self, value):
        print
        print 'ERROR: status_remote_chain_0_signal_strength is a read-only variable.'
        print
        return

    status_remote_chain_0_signal_strength = property(remote_chain_0_signal_strength_get, remote_chain_0_signal_strength_set)

    def remote_chain_1_signal_strength_get(self):
        # Radio remote_chain_1_signal_strength
        # Returns: integer string (ex.:-53)
        self.cmd = 'af get rrxpower1'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rrxpower1 = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__rrxpower1 = None
        return self.__rrxpower1

    def remote_chain_1_signal_strength_set(self, value):
        print
        print 'ERROR: status_remote_chain_1_signal_strength is a read-only variable.'
        print
        return

    status_remote_chain_1_signal_strength = property(remote_chain_1_signal_strength_get, remote_chain_1_signal_strength_set)

    def local_modulation_rate_get(self):
        # Radio local_modulation_rate
        # Returns: 1x, 2x, 4x, ...
        self.cmd = 'af get txmodrate'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__txmodrate = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__txmodrate = None
        return self.__txmodrate

    def local_modulation_rate_set(self, value):
        print
        print 'ERROR: status_local_modulation_rate is a read-only variable.'
        print
        return

    status_local_modulation_rate = property(local_modulation_rate_get, local_modulation_rate_set)

    def remote_modulation_rate_get(self):
        # Radio remote_modulation_rate
        # Returns: 1x, 2x, 4x, ...
        self.cmd = 'af get rtxmodrate'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rtxmodrate = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__rtxmodrate = None
        return self.__rtxmodrate

    def remote_modulation_rate_set(self, value):
        print
        print 'ERROR: status_remote_modulation_rate is a read-only variable.'
        print
        return

    status_remote_modulation_rate = property(remote_modulation_rate_get, remote_modulation_rate_set)

    def tx_capacity_get(self):
        # Radio tx_capacity
        # Returns: integer string
        self.cmd = 'af get txcapacity'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__txcapacity = int(self.results)
        except:
            print 'EXCEPTION: %s failed, setting tx_capacity to 999999999. Results = %s' % (self.cmd, self.results)
            self.__txcapacity = 999999999
        return self.__txcapacity

    def tx_capacity_set(self, value):
        print
        print 'ERROR: status_tx_capacity is a read-only variable.'
        print
        return

    status_tx_capacity = property(tx_capacity_get, tx_capacity_set)

    def rx_capacity_get(self):
        # Radio rx_capacity
        # Returns: integer string
        self.cmd = 'af get rxcapacity'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rxcapacity = int(self.results)
        except:
            print 'EXCEPTION: %s failed, setting rx_capacity to 999999999. Results = %s' % (self.cmd, self.results)
            self.__rxcapacity = 999999999
        return self.__rxcapacity

    def rx_capacity_set(self, value):
        print
        print 'ERROR: status_rx_capacity is a read-only variable.'
        print
        return

    status_rx_capacity = property(rx_capacity_get, rx_capacity_set)

    def tx_power_get(self):
        # use output_power_get instead since it already exists
        pass

    def tx_power_set(self, value):
        print
        print 'ERROR: status_tx_power is a read-only variable.'
        print
        return

    status_tx_power = property(output_power_get, tx_power_set)

    def remote_tx_power_get(self):
        # Radio remote_tx_power
        # Returns: integer string (ex.:-62)
        self.cmd = 'af get rpowerout'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rpowerout = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__rpowerout = None
        return self.__rpowerout

    def remote_tx_power_set(self, value):
        print
        print 'ERROR: status_remote_tx_power is a read-only variable.'
        print
        return

    status_remote_tx_power = property(remote_tx_power_get, remote_tx_power_set)

    def dac_temp_0_get(self):
        # Radio dac_temp_0
        # Returns: integer string
        self.cmd = 'af get temp0'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__temp0 = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__temp0 = None
        return self.__temp0

    def dac_temp_0_set(self, value):
        print
        print 'ERROR: status_dac_temp_0 is a read-only variable.'
        print
        return

    status_dac_temp_0 = property(dac_temp_0_get, dac_temp_0_set)

    def dac_temp_1_get(self):
        # Radio dac_temp_1
        # Returns: integer string
        self.cmd = 'af get temp1'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__temp1 = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__temp1 = None
        return self.__temp1

    def dac_temp_1_set(self, value):
        print
        print 'ERROR: status_dac_temp_1 is a read-only variable.'
        print
        return

    status_dac_temp_1 = property(dac_temp_1_get, dac_temp_1_set)

    def distance_feet_get(self):
        # Radio distance in feet
        # Returns: float string
        self.cmd = 'af get feet'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__feet = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__feet = None
        return self.__feet

    def distance_feet_set(self, value):
        print
        print 'ERROR: status_distance_feet is a read-only variable.'
        print
        return

    status_distance_feet = property(distance_feet_get, distance_feet_set)

    def distance_miles_get(self):
        # Radio distance in miles
        # Returns: float string
        self.cmd = 'af get miles'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__miles = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__miles = None
        return self.__miles

    def distance_miles_set(self, value):
        print
        print 'ERROR: status_distance_miles is a read-only variable.'
        print
        return

    status_distance_miles = property(distance_miles_get, distance_miles_set)

    def distance_meters_get(self):
        # Radio distance in meters
        # Returns: float string
        self.cmd = 'af get meters'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__meters = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__meters = None
        return self.__meters

    def distance_meters_set(self, value):
        print
        print 'ERROR: status_distance_meters is a read-only variable.'
        print
        return

    status_distance_meters = property(distance_meters_get, distance_meters_set)

    def distance_kilometers_get(self):
        # Radio distance in kilometers
        # Returns: float string
        self.cmd = 'af get kilometers'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__kilometers = self.results
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__kilometers = None
        return self.__kilometers

    def distance_kilometers_set(self, value):
        print
        print 'ERROR: status_distance_kilometers is a read-only variable.'
        print
        return

    status_distance_kilometers = property(distance_kilometers_get, distance_kilometers_set)


    def waitOperational(self, seconds=90, displaystatus=True):
        # Success returns "operational"
        # Failure returns last sampled operational status string after x seconds of trying.
        self.statuscount = 0
        self.seconds = seconds
        self.displaystatus = displaystatus
        if self.debug == True:
            print 'waitOperational()'
        if (self.wireless_wireless_mode == 'master'):
            if self.status_rf_link_status.lower() == "operational":
                return "operational"
            else:
                self.operational_string = "master-beaconing" # Not 'master-operational' because slave may not be ready
        else:
            self.operational_string = "slave-operational"
        while (self.status != self.operational_string):
            time.sleep(1)
            if self.displaystatus:
                sys.stdout.write('Status: %s %s       \r' % (self.statuscount, self.status))
                sys.stdout.flush()
            self.statuscount += 1
            if (self.statuscount == self.seconds):
                return self.status
        if self.displaystatus:
            print
        if self.debug == True:
            print 'Status: %s          ' % self.status
        return "operational"

    def waitCapacity(self, targetcapacity=None, percentage=0.9, attempts=60, displaystatus=True):
        # Success returns last sampled capacity
        # Failure to reach capacity target within x attempts returns False
        self.percent = percentage
        self.attempts = attempts
        self.displaystatus = displaystatus
        self.currentcapacity = 0
        self.attempt = 0
        if self.debug == True:
            print 'waitCapacity()'
        self.linkrange = 0
        if self.debug == True:
            print 'BW: %s, Modrate: %s, Linkrange: %s, Duplex: %s' % (self.wireless_tx_channel_bandwidth, self.wireless_maximum_modulation_rate, self.linkrange, self.wireless_duplex)
        if targetcapacity == None:
            self.targetcapacity = utils.calc_capacity(self.wireless_tx_channel_bandwidth, self.wireless_maximum_modulation_rate, self.linkrange, self.wireless_duplex)
        else:
            self.targetcapacity = int(targetcapacity)
        while self.attempt < self.attempts:
            self.attempt += 1
            time.sleep(1)
            self.sampledcapacity = self.status_tx_capacity
            if self.displaystatus == True:
                sys.stdout.write('Target Capacity: %s, Percentage: %s, Current Capacity: %s    \r' % (self.targetcapacity, self.percent, self.sampledcapacity))
                sys.stdout.flush()
            if (float(self.sampledcapacity) >= float(self.targetcapacity*self.percent)):
                if self.displaystatus == True:
                    print
                return self.sampledcapacity
            else:
                self.sample = 0 # Reset sample count if cap falls below target
        else:
            if self.displaystatus == True:
                print
                print
                print 'ERROR: Capacity (%s) failed to reach target (%s) after %s tries.' % (self.sampledcapacity, self.targetcapacity, self.attempt)
                print
            return False

    def afaf_get(self):
        # returns a directory with keys:
        # 'rssi0', 'rssi1', 'baseline', 'feet', 'temp1', 'temp0', 'dpstat', 'Config', 'linkname',
        # 'txfrequency',2GHz', 'duplex', 'speed', 'rrxpower0', 'rrxpower1', 'rtxmodrate', 'txcapacity',
        # 'rxpower0', 'fade', '*******', 'Data',', 'status',operational', 'rpowerout', 'key', 'rxgain',
        #'rxfrequency',1GHz', 'rxcapacity', 'powerout', 'rxpower1', 'miles',010', 'modcontrol', 'txmodrate'
        self.cmd = 'af af'
        try:
            self.results = self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__afaf = None
            return self.__afaf
        # split results into a list
        self.getlist = self.results.split()
        # remove the command and the prompt from the list
        self.statslist = self.getlist[2:-1]
        # remove the : from the end of the names in the list
        for glindex in range(len(self.statslist)):
            if self.statslist[glindex][-1] == ':':
                self.statslist[glindex] = self.statslist[glindex][:-1]
        # convert the list into a dictionary
        self.__afaf = dict(itertools.izip_longest(*[iter(self.statslist)] * 2, fillvalue=""))
        return self.__afaf

    def afaf_set(self, value):
        print
        print 'ERROR: af_af is a read-only variable.'
        print
        return

    af_af = property(afaf_get, afaf_set)

    def afemac_get(self):
        # returns a directory with keys:
        # mac_0, mac_1, TxFramesOK, RxFramesOK, RxFrameCrcErr, RxAlignErr, TxOctetsOK, RxOctetsOK,
        # TxPauseFrames, RxPauseFrames, RxErroredFrames, TxErroredFrames, RxValidUnicastFrames,RxValidMulticastFrames,
        # RxValidBroadcastFrames, TxValidUnicastFrames, TxValidMulticastFrames, TxValidBroadcastFrames,
        # RxDroppedMacErrFrames, RxTotalOctets, RxTotalFrames, RxLess64ByteFrames, RxOverLengthFrames, Rx64BytePackets,
        # Rx65_127BytePackets, Rx128_255BytePackets, Rx256_511BytePackets, Rx512_1023BytePackets, Rx1024_1518BytesPackets,
        # Rx1519PlusBytePackets, RxTooLongFrameCrcErr, RxTooShortFrameCrcErr
        self.cmd = 'af emac'
        if self.debug == True:
            print 'afemac_get()'
            print '    cmd = %s' % self.cmd
        try:
            self.results = self.sendcmd(self.cmd)
            if self.debug == True:
                print '    sendcmd(%s) = %s' % (self.cmd, self.results)
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__afemac = None
            return self.__afemac
        # split results into a list
        self.getlist = self.results.split()
        if self.debug == True:
            print '    getlist = %s' % self.getlist
        # remove the command and the prompt from the list
        self.statslist = self.getlist[2:-1]
        if self.debug == True:
            print '    statslist = %s' % self.statslist
        # remove the : from the end of the names in the list
        for glindex in range(len(self.statslist)):
            if self.statslist[glindex][-1] == ':':
                self.statslist[glindex] = self.statslist[glindex][:-1]
        # convert the list into a dictionary
        self.__afemac = dict(itertools.izip_longest(*[iter(self.statslist)] * 2, fillvalue=""))
        return self.__afemac

    def afemac_set(self, value):
        print
        print 'ERROR: af_emac is a read-only variable.'
        print
        return

    af_emac = property(afemac_get, afemac_set)

    def rainfade_get(self):
        # rainfade depricated by rain
        self.cmd = 'af get rainfade'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rainfade = self.results
        except:
            print 'EXCEPTION: af get rainfade failed.'
            self.__rainfade = None
        return self.__rainfade  

    def rainfade_set(self, target):
        # rainfade depricated by rain
        self.cmd = 'af set rainfade %s' % target
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set rainfade %s  failed.' % target
            return False
        return True

    rainfade = property(rainfade_get, rainfade_set)

    def rainstat_get(self):
        self.cmd = 'af get rainstat'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__rainstat = self.results
        except:
            print 'EXCEPTION: af get rainstat failed.'
            self.__rainstat = None
        return self.__rainstat

    def rainstat_set(self, value):
        print
        print 'ERROR: rainstat is a read-only variable.'
        print
        return

    rainstat = property(rainstat_get, rainstat_set)

    def rain_get(self):
        # returns a directory with keys:
        # averagewindow, baselinewindow, limit, maxremotepower,
        # baselinepath, idealpath, fade, baselineoverride, idealoverride
        self.cmd = 'af get rain'
        try:
            self.results = self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: %s failed.' % self.cmd
            self.__rain = None
            return self.__rain
        # remove the command and the prompt from the list
        self.getlist = self.results.split()[3:-1]
        # remove the : from the end of the names in the list
        for glindex in range(len(self.getlist)):
            if self.getlist[glindex][-1] == ':':
                self.getlist[glindex] = self.getlist[glindex][:-1]
        # convert the list into a dictionary
        self.__rain = dict(itertools.izip_longest(*[iter(self.getlist)] * 2, fillvalue=""))
        return self.__rain

    def rain_set(self, cmdval):
        self.cmd = 'af set rain %s' % cmdval
        try:
            self.sendcmd(self.cmd)
        except:
            print 'EXCEPTION: af set rain %s  failed.' % cmdval
            return False
        return True

    rain = property(rain_get, rain_set)

    def minfreq_get(self):
        self.cmd = 'af get minfreq'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__minfreq = self.results
        except:
            print 'EXCEPTION: af get minfreq failed.'
            self.__rminfreq = None
        return self.__minfreq

    def minfreq_set(self, value):
        print
        print 'ERROR: minfreq is a read-only variable.'
        print
        return

    af_minfreq = property(minfreq_get, minfreq_set)

    def maxfreq_get(self):
        self.cmd = 'af get maxfreq'
        try:
            self.results = self.sendcmd(self.cmd).split()[3]
            self.__maxfreq = self.results
        except:
            print 'EXCEPTION: af get maxfreq failed.'
            self.__rmaxfreq = None
        return self.__maxfreq

    def maxfreq_set(self, value):
        print
        print 'ERROR: maxfreq is a read-only variable.'
        print
        return

    af_maxfreq = property(maxfreq_get, maxfreq_set)

    def afcal_get(self):
        # Returns dictionary with keys: 'magic', 'radio_caldata', 'mac1', 'subsystem_id', 'crc'', 'mac0', 'pcba_id', 'hardware_rev_id', 'archive_length', 'country_code'', 'crc_length', 'subvendor_id'
        self.cmd = 'afcal -p'
        try:
            self.results = self.sendcmd(self.cmd)
            self.results = re.sub(' ', '_', self.results) # replace space with underscore
            self.results = re.sub('\.\.+', ' ', self.results).split()[1:-1] # replace two or more periods with comma
            self.results = [x.lower() for x in self.results]
            self.__afcal = dict(itertools.izip_longest(*[iter(self.results)] * 2, fillvalue=""))
        except:
            print 'EXCEPTION: afcal -p failed.'
            self.__afcal = None
        return self.__afcal






def main():
 
     print
     debug = False
     #radio1 = RadioT('r2s2.cfg', 'Radio1', debug)
     #radio1 = RadioT('10.8.8.125', 'ubnt', 'ubnt', debug)
     radio1 = RadioT('10.8.8.80', 'ubnt', 'ubnt', debug)
     radio1.tConnect()
     radio1.tLogin()
     time.sleep(1)
     print
     print 'Radio %s' % radio1.radio_id
     print 'Radio IP = %s' % radio1.ip
     print 'devicename: %s' % radio1.status_device_name
     initialradiomode = radio1.wireless_wireless_mode
     print 'Initial Radio Mode = %s' % initialradiomode
     print 'Radio MAC = %s' % radio1.local_mac
     print 'Firmware Version = %s' % radio1.firmware_version
     print 'FPGA Version = %s' % radio1.fpga_version
     afcaldict = radio1.afcal_get()
     print 'subsystem_id = %s' % afcaldict['subsystem_id']
     print 'subvendor_id = %s' % afcaldict['subvendor_id']
     print 'pcba_id = %s' % afcaldict['pcba_id']
     print 'hardware_rev_id = %s' % afcaldict['hardware_rev_id']
     print

     """
     #radio1.wireless_wireless_mode = self.config.get('%s' % self.config_section, 'Wireless_Mode')
     if initialradiomode == 'master':
         radio1.wireless_wireless_mode = 'slave'
     else:
         radio1.wireless_wireless_mode = 'master'
     print 'New Radio Mode = %s' % radio1.wireless_wireless_mode 
     radio1.wireless_wireless_mode = initialradiomode
     print 'Restored Radio Mode = %s' % radio1.wireless_wireless_mode 
     print 'firmware_version = %s' % radio1.firmware_version
     print 'version_number = %s' % radio1.version_number
     print 'radio_type = %s' % radio1.radio_type
     radio1.radio_type = 'AF99'
     print 'radio_type = %s' % radio1.radio_type
     print 'build # = %s' % radio1.build_number
     radio1.build_number = '1234'
     print 'build # = %s' % radio1.build_number
     orig_link_name = radio1.wireless_link_name
     print 'wireless_link_name = %s' % orig_link_name
     radio1.wireless_link_name = 'cheese'
     print 'new wireless_link_name = %s' % radio1.wireless_link_name
     radio1.wireless_link_name = orig_link_name
     print 'restored wireless_link_name = %s' % radio1.wireless_link_name
     orig_country_code = radio1.wireless_country_code
     print 'original wireless_country_code = %s' % orig_country_code
     print 'country_name = %s' % radio1.country_name
     radio1.wireless_country_code = '156' #China
     print 'wireless_country_code = %s' % radio1.wireless_country_code
     print 'country_name = %s' % radio1.country_name
     radio1.wireless_country_code = 'austria' #040 fails, austria not in dictionary
     print 'wireless_country_code = %s' % radio1.wireless_country_code
     print 'country_name = %s' % radio1.country_name
     radio1.wireless_country_code = 'australia' #036
     print 'wireless_country_code = %s' % radio1.wireless_country_code
     print 'country_name = %s' % radio1.country_name
     radio1.country_name = 'france'
     radio1.country_name = 'germany'
     print 'wireless_country_code = %s' % radio1.wireless_country_code
     print 'country_name = %s' % radio1.country_name
     radio1.wireless_country_code = orig_country_code
     print 'wireless_country_code = %s' % radio1.wireless_country_code
     print 'country_name = %s' % radio1.country_name
     print 'wireless_country_dom = %s' % radio1.wireless_country_dom
     #radio1.wireless_country_dom = 'none'
     orig_duplex = radio1.wireless_duplex
     print 'wireless_duplex = %s' % orig_duplex
     radio1.wireless_duplex = 'halffull'
     print 'wireless_duplex = %s' % radio1.wireless_duplex
     if orig_duplex.lower() == 'full':
         radio1.wireless_duplex = 'half'
     else:
         radio1.wireless_duplex = 'full'
     print 'new wireless_duplex = %s' % radio1.wireless_duplex
     radio1.wireless_duplex = orig_duplex
     print 'restored wireless_duplex = %s' % radio1.wireless_duplex
     orig_channel_bandwidth_tx = radio1.wireless_tx_channel_bandwidth
     print 'orig wireless_tx_channel_bandwidth = %s' % orig_channel_bandwidth_tx
     radio1.wireless_tx_channel_bandwidth = 75
     print 'wireless_tx_channel_bandwidth = %s' % radio1.wireless_tx_channel_bandwidth
     radio1.wireless_tx_channel_bandwidth = 10
     print 'wireless_tx_channel_bandwidth = %s' % radio1.wireless_tx_channel_bandwidth
     radio1.wireless_tx_channel_bandwidth = orig_channel_bandwidth_tx
     print 'restored wireless_tx_channel_bandwidth = %s' % radio1.wireless_tx_channel_bandwidth
     orig_channel_bandwidth_rx = radio1.wireless_rx_channel_bandwidth
     print 'orig wireless_rx_channel_bandwidth = %s' % orig_channel_bandwidth_rx
     radio1.wireless_rx_channel_bandwidth = 31
     print 'wireless_rx_channel_bandwidth = %s' % radio1.wireless_rx_channel_bandwidth
     radio1.wireless_rx_channel_bandwidth = 30
     print 'wireless_rx_channel_bandwidth = %s' % radio1.wireless_rx_channel_bandwidth
     radio1.wireless_rx_channel_bandwidth = orig_channel_bandwidth_rx
     print 'restored wireless_rx_channel_bandwidth = %s' % radio1.wireless_rx_channel_bandwidth
     original_output_power = radio1.wireless_output_power 
     print 'orig wireless_output_power = %s' % original_output_power
     radio1.wireless_output_power = 100
     print 'wireless_output_power = %s' % radio1.wireless_output_power 
     radio1.wireless_output_power = 0
     print 'wireless_output_power = %s' % radio1.wireless_output_power 
     radio1.wireless_output_power = original_output_power
     print 'restored wireless_output_power = %s' % radio1.wireless_output_power 
     original_antenna_gain = radio1.wireless_antenna_gain 
     print 'orig wireless_antenna_gain = %s' % original_antenna_gain
     #radio1.wireless_antenna_gain = 1000
     #print 'wireless_antenna_gain = %s' % radio1.wireless_antenna_gain 
     #radio1.wireless_antenna_gain = radio1.wireless_output_power
     #print 'wireless_antenna_gain = %s' % radio1.wireless_antenna_gain 
     #radio1.wireless_antenna_gain = original_antenna_gain
     #print 'restored wireless_antenna_gain = %s' % radio1.wireless_antenna_gain 
     """

if __name__ == '__main__':
    main()


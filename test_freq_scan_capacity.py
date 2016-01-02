#!/usr/bin/python

"""
Frequency Scan Capacity Test

  - Two radios sync'd with good signal at max moduation.
  - Engineering Mode
  - No data traffic!
  - Fixed attenuation
  - Output power set to +10
  - Each channel bandwidth
  - Step through entire range of frequencies for the current bandwidth.
  - Configurable freq steps (1, 5, 10 MHz)
  - For each radio, read RX capacity 10 times with a 2 second delay.
  - Average the 10 readings.
  - Display a table of bw, freq, r1 theoretical, r1 avg, r2 theoretical, r1 avg

"""

import sys
import os, errno
import shutil
import ConfigParser
import argparse
import ast
import time


# Variables for imported custom libraries
hradiopkg = "afhttp13"
tradiopkg = "radiot"
gpibpkg = "gpib"
attenpkg = "attenuation"

# Using variable import names to enable archiving of the imported custom libraries
sys.path.append('../airos/libs/')
sys.path.append('../obj/')
hradio = __import__(hradiopkg)
tradio = __import__(tradiopkg)
gpib = __import__(gpibpkg)
attnctrl = __import__(attenpkg)

def printlog(log, plstr):
    print plstr
    print >> log, plstr
    log.flush()

def main():

    filename = (((sys.argv[0]).split("\\"))[-1:][0].split("."))[:1][0]

    parser = argparse.ArgumentParser(description='Frequency Scan vs. Capacity.')
    parser.add_argument('-c','--config', help='Configuration File', required=True)
    #parser.add_argument('-s','--step', help='Frequency step in MHz', required=True)
    parser.add_argument('-q','--quiet', action='store_false', help='Default=True', required=False, default='True')
    parser.add_argument('-d','--debug', action='store_true', help='Default=False', required=False, default='False')
    args = vars(parser.parse_args())

    sys_configfile = args['config']
    #stepfreq = int(args['step'])
    debug = args['debug']
    quiet = args['quiet']

    # Try to open and read the system configuration file
    config = ConfigParser.ConfigParser()
    dataset = config.read(sys_configfile)
    if len(dataset) == 0:
        raise ValueError, "Failed to open file: %s" % sys_configfile
    try:
        r1ipaddr = config.get('Radio1', 'ip_addr')
        r1username = config.get('Radio1', 'user')
        r1password = config.get('Radio1', 'password')
        #r1afconfig = ast.literal_eval(config.get('Radio1', 'afconfig'))
        r2ipaddr = config.get('Radio2', 'ip_addr')
        r2username = config.get('Radio2', 'user')
        r2password = config.get('Radio2', 'password')
        #r2afconfig = ast.literal_eval(config.get('Radio2', 'afconfig'))
    except ConfigParser.NoSectionError, err:
        raise ConfigParser.NoSectionError, 'ConfigParser NoSectionError: %s' % err
    except ConfigParser.NoOptionError, err:
        raise ConfigParser.NoOptionError, 'ConfigParser NoOptionError: %s' % err

    gpibip = ast.literal_eval(config.get('GPIB', 'ip_addr'))
    if gpibip != None:
        try:
            gpib1address = config.get('Atten1', 'gpib_addr')
            Yatten1 = config.get('Atten1', 'y_max')
            initval1 = config.get('Atten1', 'initval')
            gpib2address = config.get('Atten2', 'gpib_addr')
            Yatten2 = config.get('Atten2', 'y_max')
            initval2 = config.get('Atten2', 'initval')
        except ConfigParser.NoSectionError, err:
            raise ConfigParser.NoSectionError, 'ConfigParser NoSectionError: %s' % err
        except ConfigParser.NoOptionError, err:
            raise ConfigParser.NoOptionError, 'ConfigParser NoOptionError: %s' % err

    releases = ast.literal_eval(config.get('Test', 'releases'))
    channelbandwidths = ast.literal_eval(config.get('Test', 'channelbwlist'))
    minfreq = int(config.get('Test', 'minfreq'))
    maxfreq = int(config.get('Test', 'maxfreq'))
    stepfreq = int(config.get('Test', 'stepfreq'))

    # Configure system attenuation controllers to their initial values.
    if gpibip != None:
        prologix = gpib.gpibController(gpibip)
        gpib_tcp_sock = prologix.connect()
        if gpib_tcp_sock == None:
            print
            print 'gpibController(%s):  Connection Failure' % (gpibip)
            print
            sys.exit(1)

        atten1 = attnctrl.AttenuationController(prologix, gpib1address, Yatten1, debug)
        atten1.attenuation=initval1

        atten2 = attnctrl.AttenuationController(prologix, gpib2address, Yatten2, debug)
        atten2.attenuation=initval2

    # for each release in the config file, load the software release and initial config
    for release in releases:
        print 'release:', release
   
        # Open browser windows and log into radio web pages
        hRadio1 = hradio.Http(r1ipaddr, r1username, r1password, quiet)
        hRadio1.login()
        hRadio2 = hradio.Http(r2ipaddr, r2username, r2password, quiet)
        hRadio2.login()

        # Load software onto the radios
        if release.lower() != 'none':
            hRadio1.load_fw(release)
            hRadio2.load_fw(release)

        ## Load a baseline configuration into the radios
        #hRadio1.load_config(r1afconfig)
        #hRadio2.load_config(r2afconfig)

        print
        radio1 = tradio.RadioT(r1ipaddr, r1username, r1password, debug)
        radio2 = tradio.RadioT(r2ipaddr, r2username, r2password, debug)
        radio1.tConnect()
        radio1.tLogin()
        radio2.tConnect()
        radio2.tLogin()

        # Try to create the build directory.  If it exists, don't do anything.
        # Build directory is the root directory and is based on the software version
    
        #basedir = '/mnt/shared/test/data/'
        basedir = config.get('Test', 'basedir')
    
        builddir = basedir+radio1.firmware_version+'_'+radio1.fpga_version+'/'
        try:
            os.makedirs(builddir)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise
    
        # Try to create the test directory.  If it exists, don't do anything.
        # Test directory is beneath the build directory and is based on the test filename and time stamp
        timestamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        test_system = config.get('Test', 'system')
        testdir = builddir+filename+'_'+test_system+'_'+timestamp+'/'
        try:
            os.makedirs(testdir)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise
    
        # Copy test files and custom libraries to the test dir.
        shutil.copy2('./'+filename+'.py', testdir+filename+'.py')
        shutil.copy2('./'+sys_configfile, testdir+sys_configfile)
        shutil.copy2('./'+gpibpkg+'.py', testdir+gpibpkg+'.py')
        shutil.copy2('./'+attenpkg+'.py', testdir+attenpkg+'.py')
        shutil.copy2('./'+tradiopkg+'.py', testdir+tradiopkg+'.py')
        shutil.copy2('../obj/'+hradiopkg+'.py', testdir+hradiopkg+'.py')
        if debug == True:
            print 'testdir = %s' % testdir

        outprefix = testdir+filename+"-"+test_system+"-"+timestamp
                            
        # Try opening the log. If it doesn't exist, create one and insert the heading.
        logname = outprefix+'.csv'
        try:
            testlog = open(logname, 'a')
        except IOError, e:
            if e.errno != errno.EEXIST:
                raise
        
        # Verify that nothing is connected to the data port
        if radio1.advanced_data_link.lower() != 'nolink':
            print
            print 'Please disconnect Ethernet data cable from %s' % radio1.ip
            print 'And rerun this program.'
            print
            sys.exit(1)
        if radio2.advanced_data_link.lower() != 'nolink':
            print
            print 'Please disconnect Ethernet data cable from %s' % radio2.ip
            print 'And rerun this program.'
            print
            sys.exit(1)

        # Verify that Wireless> Country Code is 8191 (ENGINEERING)
        if radio1.wireless_country_code != '8191':
            radio1.wireless_country_code = 8191
        if radio2.wireless_country_code != '8191':
            radio2.wireless_country_code = 8191

        radio1.wireless_output_power = config.get('Radio1', 'powerout')
        radio2.wireless_output_power = config.get('Radio2', 'powerout')

        #minfreq = int(radio1.af_minfreq)
        #maxfreq = int(radio1.af_maxfreq)
        #print '(%s - %s)' % (minfreq, maxfreq)

        terminal_format_2 = '%11s: %36s'
        csv_file_format_2 = '%s,%s'
        terminal_format_3 = '%11s: %17s, %17s'
        csv_file_format_3 = '%s,%s,%s'
        date_params = ("Date", timestamp)
        system_params = ("System", test_system)
        device_params = ("Device", "Radio"+str(radio1.radio_id), "Radio"+str(radio2.radio_id))
        radio_ip_params = ("IP", radio1.ip, radio2.ip)
        device_name_params = ("Device Name", radio1.devicename, radio2.devicename)
        radio_mode_params = ("Mode", radio1.wireless_wireless_mode, radio2.wireless_wireless_mode)
        radio_mac_params = ("MAC", radio1.local_mac, radio2.local_mac)
        radio_fpga_params = ("FPGA", radio1.fpga_version, radio2.fpga_version)
        radio_sw_params = ("SW", radio1.firmware_version, radio2.firmware_version)
        radio_dutycycle_params = ("DutyCycle", radio1.wireless_master_tx_duty_cycle, radio2.wireless_master_tx_duty_cycle)
        radio_duplex_params = ("Duplex", radio1.wireless_duplex, radio2.wireless_duplex)
        radio_pwrout_params = ("PwrOut", radio1.wireless_output_power, radio2.wireless_output_power)
        radio_modctl_params = ("ModCtl", radio1.wireless_maximum_modulation_rate, radio2.wireless_maximum_modulation_rate)
        radio_t0_params = ("t0", radio1.status_dac_temp_0, radio2.status_dac_temp_0)
        radio_t1_params = ("t1", radio1.status_dac_temp_1, radio2.status_dac_temp_1)
        radio_txchbw_params = ("TXChBW", radio1.wireless_tx_channel_bandwidth, radio2.wireless_tx_channel_bandwidth)
        radio_rxchbw_params = ("RXChBW", radio1.wireless_rx_channel_bandwidth, radio2.wireless_rx_channel_bandwidth)
        radio_ccode_params = ("CCode", radio1.wireless_country_code, radio2.wireless_country_code)
        radio_cname_params = ("CName", radio1.country_name, radio2.country_name)
        cmdline_params = ('Cmdline', sys.argv)
        #radio__params = ("", radio1., radio2.)

        print ''
        print terminal_format_2 % date_params
        print terminal_format_2 % system_params
        print terminal_format_2 % cmdline_params
        print ''
        print terminal_format_3 % device_params
        print terminal_format_3 % radio_ip_params
        print terminal_format_3 % device_name_params
        print terminal_format_3 % radio_mode_params
        print terminal_format_3 % radio_mac_params
        print terminal_format_3 % radio_fpga_params
        print terminal_format_3 % radio_sw_params
        print terminal_format_3 % radio_dutycycle_params
        print terminal_format_3 % radio_duplex_params
        print terminal_format_3 % radio_pwrout_params
        print terminal_format_3 % radio_modctl_params
        print terminal_format_3 % radio_txchbw_params
        print terminal_format_3 % radio_rxchbw_params
        print terminal_format_3 % radio_ccode_params
        print terminal_format_3 % radio_cname_params
        print terminal_format_3 % radio_t0_params
        print terminal_format_3 % radio_t1_params
        print ''

        print >> testlog, ''
        print >> testlog, csv_file_format_2 % date_params
        print >> testlog, csv_file_format_2 % system_params
        print >> testlog, csv_file_format_2 % cmdline_params
        print >> testlog, ''
        print >> testlog, csv_file_format_3 % device_params
        print >> testlog, csv_file_format_3 % radio_ip_params
        print >> testlog, csv_file_format_3 % device_name_params
        print >> testlog, csv_file_format_3 % radio_mode_params
        print >> testlog, csv_file_format_3 % radio_mac_params
        print >> testlog, csv_file_format_3 % radio_fpga_params
        print >> testlog, csv_file_format_3 % radio_sw_params
        print >> testlog, csv_file_format_3 % radio_dutycycle_params
        print >> testlog, csv_file_format_3 % radio_duplex_params
        print >> testlog, csv_file_format_3 % radio_pwrout_params
        print >> testlog, csv_file_format_3 % radio_modctl_params
        print >> testlog, csv_file_format_3 % radio_txchbw_params
        print >> testlog, csv_file_format_3 % radio_rxchbw_params
        print >> testlog, csv_file_format_3 % radio_ccode_params
        print >> testlog, csv_file_format_3 % radio_cname_params
        print >> testlog, csv_file_format_3 % radio_t0_params
        print >> testlog, csv_file_format_3 % radio_t1_params
        print >> testlog, ''


        data_header_params = ("time", "ChBW", "Freq", "r1maxCap", "r1avgCap", "r1delta", "r2maxCap", "r2avgCap", "r2delta", "r1iso", "r2iso", "r1evm0", "r1evm1", "r2evm0", "r2evm1", "r1ber", "r2ber")
        terminal_data_format = '%15s, %4s, %4s, %10s, %10s, %10s, %10s, %10s, %10s, %5s, %5s, %6s, %6s, %6s, %6s, %10s, %10s'
        csv_file_data_format = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s'

        print terminal_data_format % data_header_params
        print >> testlog, csv_file_data_format % data_header_params
        testlog.flush()

        for channelbandwidth in channelbandwidths:
            radio1.wireless_tx_channel_bandwidth = channelbandwidth
            radio2.wireless_tx_channel_bandwidth = channelbandwidth
            for freq in xrange(minfreq, maxfreq+stepfreq, stepfreq):
                #print 'frequency %s' % freq
                radio1.wireless_tx_frequency = freq
                radio2.wireless_tx_frequency = freq
                #time.sleep(10)
                
                r1_max_rx_capacity = int(hRadio1.get_labefana_max_rx_rate())
                while r1_max_rx_capacity == 0:
                    time.sleep(1)
                    r1_max_rx_capacity = int(hRadio1.get_labefana_max_rx_rate())
                r2_max_rx_capacity = int(hRadio2.get_labefana_max_rx_rate())
                while r2_max_rx_capacity == 0:
                    time.sleep(1)
                    r2_max_rx_capacity = int(hRadio2.get_labefana_max_rx_rate())
                radio1.waitCapacity(targetcapacity=r1_max_rx_capacity, attempts=2, displaystatus=False)
                radio2.waitCapacity(targetcapacity=r2_max_rx_capacity, attempts=2, displaystatus=False)
               
                r1_rx_capacity_sum = 0
                r2_rx_capacity_sum = 0
                for sample in range(10):
                    time.sleep(2)
                    try:
                        r1_rx_capacity_sum += int(radio1.status_rx_capacity)
                    except:
                        r1_rx_capacity_sum += 0
                    try:
                        r2_rx_capacity_sum += int(radio2.status_rx_capacity)
                    except:
                        r2_rx_capacity_sum += 0
                r1_rx_capacity_avg = r1_rx_capacity_sum / 10
                r1delta = r1_max_rx_capacity - r1_rx_capacity_avg
                r2_rx_capacity_avg = r2_rx_capacity_sum / 10
                r2delta = r2_max_rx_capacity - r2_rx_capacity_avg
                data_value_params = (time.strftime("%Y%m%d-%H%M%S", time.localtime()), channelbandwidth, freq, r1_max_rx_capacity, r1_rx_capacity_avg, r1delta, r2_max_rx_capacity, r2_rx_capacity_avg, r2delta, hRadio1.get_labefana_chain_isolation(), hRadio2.get_labefana_chain_isolation(), hRadio1.get_labefana_chain_evm(chain=0), hRadio1.get_labefana_chain_evm(chain=1), hRadio2.get_labefana_chain_evm(chain=0), hRadio2.get_labefana_chain_evm(chain=1), hRadio1.get_labefana_ber(), hRadio2.get_labefana_ber())
                print terminal_data_format % data_value_params
                print >> testlog, csv_file_data_format % data_value_params
                testlog.flush()
                
                #print 'radio1.wireless_tx_frequency %s' % radio1.wireless_tx_frequency
                #print 'radio2.wireless_tx_frequency %s' % radio2.wireless_tx_frequency

        # Close the browser windows
        hRadio1.browser.quit()
        hRadio2.browser.quit()

if __name__ == '__main__':
    main()

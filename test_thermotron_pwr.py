#!/usr/bin/python

""" Thermotron Testing

- Two radios running in the thermotron.
- Vary output power over temperature.
- Record EVM and signal strength.

  $ python test_thermotron_pwr.py -c test_thermotron_pwr.cfg

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
thermopkg = "thermotron09"

# Using variable import names to enable archiving of the imported custom libraries
sys.path.append('../obj/')
hradio = __import__(hradiopkg)
tradio = __import__(tradiopkg)
gpib = __import__(gpibpkg)
attnctrl = __import__(attenpkg)
thermo = __import__(thermopkg)

def printlog(log, plstr):
    print plstr
    print >> log, plstr
    log.flush()

def main():

    filename = (((sys.argv[0]).split("\\"))[-1:][0].split("."))[:1][0]

    parser = argparse.ArgumentParser(description='Frequency Scan vs. Capacity.')
    parser.add_argument('-c','--config', help='Configuration File', required=True)
    parser.add_argument('-q','--quiet', action='store_false', help='Default=True', required=False, default=True)
    parser.add_argument('-dbg','--debug', action='store_true', help='Default=False', required=False, default=False)
    parser.add_argument('-s','--skip', action='store_true', help='Default=False', required=False, default=False)
    args = vars(parser.parse_args())

    sys_configfile = args['config']
    debug = args['debug']
    quiet = args['quiet']
    skipsoak = args['skip']

    # Try to open and read the system configuration file
    if debug == True:
        print 'Try to open and read the system configuration file'
    config = ConfigParser.ConfigParser()
    dataset = config.read(sys_configfile)
    if len(dataset) == 0:
        raise ValueError, "Failed to open file: %s" % sys_configfile
    try:
        r1ipaddr = config.get('Radio1', 'ip_addr')
        r1username = config.get('Radio1', 'user')
        r1password = config.get('Radio1', 'password')
        #r1afconfig = ast.literal_eval(config.get('Radio1', 'afconfig'))
        r1autorateadaption = config.get('Radio1', 'autorateadaption')
        r1countrycode = config.get('Radio1', 'countrycode')
        r2ipaddr = config.get('Radio2', 'ip_addr')
        r2username = config.get('Radio2', 'user')
        r2password = config.get('Radio2', 'password')
        #r2afconfig = ast.literal_eval(config.get('Radio2', 'afconfig'))
        r2autorateadaption = config.get('Radio2', 'autorateadaption')
        r2countrycode = config.get('Radio2', 'countrycode')
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
    test_note = config.get('Test', 'notes')
    #temperatures = ast.literal_eval(config.get('Test', 'temperaturelist'))
    #frequencies = ast.literal_eval(config.get('Test', 'freqlist'))
    frequency_start = int(config.get('Test', 'freq_start'))
    frequency_stop = int(config.get('Test', 'freq_stop'))
    frequency_step = int(config.get('Test', 'freq_step'))
    dutycycles = ast.literal_eval(config.get('Test', 'dutycyclelist'))
    channelbandwidths = ast.literal_eval(config.get('Test', 'channelbwlist'))
    maxmodrates = ast.literal_eval(config.get('Test', 'modratelist'))
    output_powers = ast.literal_eval(config.get('Test', 'outputpowerlist'))
    #snooze = config.get('Test', 'sample_delay')

    thermo_ip = config.get('Thermo', 'ip')
    thermo_port = config.get('Thermo', 'port')
    thermo_temperatures = ast.literal_eval(config.get('Thermo', 'templist'))
    #thermo_start = int(config.get('Thermo', 'temp_start'))
    #thermo_stop = int(config.get('Thermo', 'temp_stop'))
    #thermo_step = int(config.get('Thermo', 'temp_step'))
    thermo_deviation = float(config.get('Thermo', 'temp_dev'))
    thermo_soak = int(config.get('Thermo', 'soak_time'))*60  # convert config file minutes to secs.
    thermo_dwell = int(config.get('Thermo', 'dwell_time'))*60  # convert config file minutes to secs.

    # Configure system attenuation controllers to their initial values.
    if debug == True:
        print 'Configure system attenuation controllers to their initial values'
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
    if debug == True:
        print 'for each release in the config file, load the software release and initial config'
    for release in releases:
        print 'release:', release
        print
   
        # Open browser windows and log into radio web pages
        hRadio1 = hradio.Http(r1ipaddr, r1username, r1password, quiet)
        hRadio1.login()
        hRadio2 = hradio.Http(r2ipaddr, r2username, r2password, quiet)
        hRadio2.login()

        # Load software onto the radios
        if debug == True:
            print 'Load software onto the radios'
        if release.lower() != 'none':
            hRadio1.load_fw(release)
            hRadio2.load_fw(release)

        # Load a baseline configuration into the radios
        if debug == True:
            print 'Load a baseline configuration into the radios'
        #hRadio1.load_config(r1afconfig)
        #hRadio2.load_config(r2afconfig)

        # Telnet connect to the radios
        if debug == True:
            print 'Telnet connect to the radios'
        radio1 = tradio.RadioT(r1ipaddr, r1username, r1password, debug)
        radio2 = tradio.RadioT(r2ipaddr, r2username, r2password, debug)
        if radio1.tConnect():
            radio1.tLogin()
        else:
            time.sleep(10)
            if radio1.tConnect():
                radio1.tLogin()
            else:
                print
                print "Second Radio1 Connection Failure."
                print
            sys.exit(1)
        if radio2.tConnect():
            radio2.tLogin()
        else:
            time.sleep(10)
            if radio2.tConnect():
                radio2.tLogin()
                print
                print "Second Radio2 Connection Failure."
                print
            sys.exit(1)
        radio1.wireless_automatic_rate_adaption = r1autorateadaption
        radio2.wireless_automatic_rate_adaption = r2autorateadaption
        radio1.wireless_country_code = r1countrycode
        radio2.wireless_country_code = r2countrycode

        # Connect to the Thermotron
        if debug == True:
            print 'Telnet connect to the Thermotron'
        tt = thermo.Thermotron()
        tt.connect(thermo_ip, thermo_port)

        # Try to create the build directory.  If it exists, don't do anything.
        # Build directory is the root directory and is based on the software version
        if debug == True:
            print 'Try to create the build directory'
    
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
        if debug == True:
            print 'Try to create the test directory'
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
        
        ## Verify that computer is connected to the data port
        #if radio1.advanced_data_link.lower() == 'nolink':
        #    print
        #    print 'Please connect Ethernet data cable to %s and rerun this program.' % radio1.ip
        #    print
        #    sys.exit(1)
        #if radio2.advanced_data_link.lower() == 'nolink':
        #    print
        #    print 'Please connect Ethernet data cable to %s and rerun this program.' % radio2.ip
        #    print
        #    sys.exit(1)

        ## Verify that Wireless> Country Code is 8191 (ENGINEERING)
        #if radio1.wireless_country_code != '8191':
        #    radio1.wireless_country_code = 8191
        #if radio2.wireless_country_code != '8191':
        #    radio2.wireless_country_code = 8191

        #minfreq = int(radio1.af_minfreq)
        #maxfreq = int(radio1.af_maxfreq)
        #print '(%s - %s)' % (minfreq, maxfreq)

        r1afcaldict = radio1.afcal_get()
        r2afcaldict = radio2.afcal_get()


        terminal_format_2 = '%11s: %17s'
        csv_file_format_2 = '%s,%s'
        terminal_format_3 = '%11s: %17s, %17s'
        csv_file_format_3 = '%s,%s,%s'

        date_params = ("Date", timestamp)
        system_params = ("System", test_system)
        log_params = ("Log", logname)
        note_params = ("Note", test_note)
        cmdline_params = ("cmd line", sys.argv)
        device_params = ("Device", "Radio"+str(radio1.radio_id), "Radio"+str(radio2.radio_id))
        radio_ip_params = ("IP", radio1.ip, radio2.ip)
        device_name_params = ("DeviceName", radio1.devicename, radio2.devicename)
        radio_mode_params = ("Mode", radio1.wireless_wireless_mode, radio2.wireless_wireless_mode)
        radio_mac_params = ("MAC", radio1.local_mac, radio2.local_mac)
        radio_fpga_params = ("FPGA", radio1.fpga_version, radio2.fpga_version)
        radio_sw_params = ("SW", radio1.firmware_version, radio2.firmware_version)
        radio_subsys_params = ("Subsystem", r1afcaldict['subsystem_id'], r2afcaldict['subsystem_id'])
        radio_subvend_params = ("Subvendor", r1afcaldict['subvendor_id'], r2afcaldict['subvendor_id'])
        radio_pcba_params = ("PCBa", r1afcaldict['pcba_id'], r2afcaldict['pcba_id'])
        radio_hwrev_params = ("HWrev", r1afcaldict['hardware_rev_id'], r2afcaldict['hardware_rev_id'])
        radio_duplex_params = ("Duplex", radio1.wireless_duplex, radio2.wireless_duplex)
        radio_autorateadapt_params = ("ModCtl", radio1.wireless_automatic_rate_adaption, radio2.wireless_automatic_rate_adaption)
        radio_ccode_params = ("CCode", radio1.wireless_country_code, radio2.wireless_country_code)
        radio_cname_params = ("CName", radio1.country_name, radio2.country_name)
        thermo_soak_params = ("SoakTime", thermo_soak)
        thermo_params = ("DwellTime", thermo_dwell)


        print ''
        print terminal_format_2 % date_params
        print terminal_format_2 % system_params
        print terminal_format_2 % log_params
        print terminal_format_2 % note_params
        print terminal_format_2 % cmdline_params
        print ''
        print terminal_format_3 % device_params
        print terminal_format_3 % radio_ip_params
        print terminal_format_3 % device_name_params
        print terminal_format_3 % radio_mode_params
        print terminal_format_3 % radio_mac_params
        print terminal_format_3 % radio_fpga_params
        print terminal_format_3 % radio_sw_params
        print terminal_format_3 % radio_subsys_params
        print terminal_format_3 % radio_subvend_params
        print terminal_format_3 % radio_pcba_params
        print terminal_format_3 % radio_hwrev_params
        print terminal_format_3 % radio_duplex_params
        print terminal_format_3 % radio_autorateadapt_params
        print terminal_format_3 % radio_ccode_params
        print terminal_format_3 % radio_cname_params
        print terminal_format_2 % thermo_soak_params
        print terminal_format_2 % thermo_params
        print ''

        print >> testlog, ''
        print >> testlog, csv_file_format_2 % date_params
        print >> testlog, csv_file_format_2 % system_params
        print >> testlog, csv_file_format_2 % log_params
        print >> testlog, csv_file_format_2 % note_params
        print >> testlog, csv_file_format_2 % cmdline_params
        print >> testlog, ''
        print >> testlog, csv_file_format_3 % device_params
        print >> testlog, csv_file_format_3 % radio_ip_params
        print >> testlog, csv_file_format_3 % device_name_params
        print >> testlog, csv_file_format_3 % radio_mode_params
        print >> testlog, csv_file_format_3 % radio_mac_params
        print >> testlog, csv_file_format_3 % radio_fpga_params
        print >> testlog, csv_file_format_3 % radio_sw_params
        print >> testlog, csv_file_format_3 % radio_subsys_params
        print >> testlog, csv_file_format_3 % radio_subvend_params
        print >> testlog, csv_file_format_3 % radio_pcba_params
        print >> testlog, csv_file_format_3 % radio_hwrev_params
        print >> testlog, csv_file_format_3 % radio_duplex_params
        print >> testlog, csv_file_format_3 % radio_autorateadapt_params
        print >> testlog, csv_file_format_3 % radio_ccode_params
        print >> testlog, csv_file_format_3 % radio_cname_params
        print >> testlog, csv_file_format_2 % thermo_soak_params
        print >> testlog, csv_file_format_2 % thermo_params
        print >> testlog, ''

        data_header_params = ("time", "Freq", "DC", "CBW", "MaxLocRem", "Temp", "R1TxPwr", "R2TxPwr", "R1Iso", "R2Iso", "R1EVM0", "R1EVM1", "R2EVM0", "R2EVM1", "R1BER", "R2BER", "R1Cap", "R2Cap", "R1SS0", "R1SS1", "R2SS0", "R2SS1", "R1T0", "R1T1", "R2T0", "R2T1", "TTSetPt", "R1Coarse", "R1Fine")
        terminal_data_format = '%15s, %9s, %2s, %4s, %9s, %6s, %7s, %7s, %5s, %5s, %6s, %6s, %6s, %6s, %12s, %12s, %9s, %9s, %5s, %5s, %5s, %5s, %4s, %4s, %4s, %4s, %7s, %8s, %6s'
        csv_file_data_format = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s'

        print terminal_data_format % data_header_params
        print >> testlog, csv_file_data_format % data_header_params


        for temperature in thermo_temperatures:
        #for temperature in xrange(thermo_start, thermo_stop+thermo_step, thermo_step):
            tt.setTemp(temperature)
            tt.run()
            tt.waitForSetpoint(temperature, thermo_deviation)
            sys.stdout.write('                                                            \r')
            sys.stdout.flush()
            if debug == True:
                print '                temperature setting = ', temperature
                print '                Mode:', tt.getMode(debug)
                print '                Status:', tt.getStatus(debug)
                print '                Set Point:', tt.getSetPoint(1, debug)
                print '                Air Temp:', tt.getTemp(debug)
                print '                Air Temp Scale:', tt.getTempScale(debug)
                print '                Air Temp Ramp Rate:', tt.getTempRampRate(debug)
                print '                Humidity:', tt.getHumidity(debug)
            if skipsoak == True:
                if debug == True:
                    print
                    print '                Skip Soak Time'
                    print
            else:
                if debug == True:
                    print
                    print 'THERMOTRON SOAK PERIOD...'
                    print
                for elapsed in range(thermo_soak+1):
                    time.sleep(1)
                    remaining = thermo_soak - elapsed
                    sys.stdout.write('soak time remaining: %5s\r' % remaining)
                    sys.stdout.flush()
                    skipsoak = True # Soak only first time temperature setting.
            if debug == True:
                print
                print 'THERMOTRON DWELL PERIOD...'
                print
            for elapsed in range(thermo_dwell+1):
                time.sleep(1)
                remaining = thermo_dwell - elapsed
                sys.stdout.write('dwell time remaining: %5s\r' % remaining)
                sys.stdout.flush()
            sys.stdout.write('                                                            \r')
            sys.stdout.flush()

            for dutycycle in dutycycles:
                radio1.wireless_master_tx_duty_cycle = dutycycle
                #if True:
                if debug == True:
                    print '    dutycycle = ', dutycycle
                    print '    radio1.wireless_master_tx_duty_cycle = ', radio1.wireless_master_tx_duty_cycle
                    print '    frequency = ', frequency
                    print '    radio1.wireless_tx_frequency_1 = ', radio1.wireless_tx_frequency_1
                    print '    radio2.wireless_tx_frequency_1 = ', radio2.wireless_tx_frequency_1
                for channelbandwidth in channelbandwidths:
                    radio1.wireless_tx_channel_bandwidth = channelbandwidth
                    radio2.wireless_tx_channel_bandwidth = channelbandwidth
                    #if True:
                    if debug == True:
                        print '        channelbandwidth = ', channelbandwidth
                        print '        radio1.wireless_tx_channel_bandwidth = ', radio1.wireless_tx_channel_bandwidth
                        print '        radio2.wireless_tx_channel_bandwidth = ', radio2.wireless_tx_channel_bandwidth
                        print '        frequency = ', frequency
                        print '        radio1.wireless_tx_frequency_1 = ', radio1.wireless_tx_frequency_1
                        print '        radio2.wireless_tx_frequency_1 = ', radio2.wireless_tx_frequency_1
                    for maxmodrate in maxmodrates:
                        radio1.wireless_maximum_modulation_rate = maxmodrate
                        radio2.wireless_maximum_modulation_rate = maxmodrate
                        sys.stdout.write('                                                            \r')
                        sys.stdout.flush()
                        #if True:
                        if debug == True:
                            print '            maxmodrate = ', maxmodrate
                            print '            radio1.wireless_maximum_modulation_rate = ', radio1.wireless_maximum_modulation_rate
                            print '            radio2.wireless_maximum_modulation_rate = ', radio2.wireless_maximum_modulation_rate
                            print '            frequency = ', frequency
                            print '            radio1.wireless_tx_frequency_1 = ', radio1.wireless_tx_frequency_1
                            print '            radio2.wireless_tx_frequency_1 = ', radio2.wireless_tx_frequency_1

                        for pwr in output_powers:
                            radio1.wireless_output_power = pwr
                            radio2.wireless_output_power = pwr
                            if debug == True:
                                print '                    output pwr setting = ', pwr
                                print '                    radio1.wireless_output_power = ', radio1.wireless_output_power
                                print '                    radio2.wireless_output_power = ', radio2.wireless_output_power

                            #for frequency in frequencies:
                            for frequency in xrange(frequency_start, frequency_stop+frequency_step, frequency_step):
                                radio1.wireless_tx_frequency_1 = frequency
                                radio2.wireless_tx_frequency_1 = frequency
                                #if True:
                                if debug == True:
                                    print 'frequency = ', frequency
                                    print 'radio1.wireless_tx_frequency_1 = ', radio1.wireless_tx_frequency_1
                                    print 'radio2.wireless_tx_frequency_1 = ', radio2.wireless_tx_frequency_1

                                snooze = int(config.get('Test', 'sample_delay'))
                                sys.stdout.write('                                                            \r')
                                sys.stdout.flush()
                                while (snooze > 0):
                                    snooze -= 1
                                    time.sleep(1)
                                    sys.stdout.write('sample delay time remaining: %3s\r' % snooze)
                                    sys.stdout.flush()
                                timestr = time.strftime("%Y%m%d-%H%M%S", time.localtime())
                                modrates = '%3s%3s%3s' % (maxmodrate, radio1.status_local_modulation_rate, radio2.status_local_modulation_rate)
                                chbw = '%s%s' % (radio1.wireless_tx_channel_bandwidth, radio2.wireless_tx_channel_bandwidth)

                                data_value_params = (timestr, radio1.wireless_tx_frequency_1, radio1.wireless_master_tx_duty_cycle, chbw, modrates, tt.getTemp(False), radio1.status_tx_power, radio2.status_tx_power, hRadio1.get_labefana_chain_isolation(), hRadio2.get_labefana_chain_isolation(), hRadio1.get_labefana_chain_evm(chain=0), hRadio1.get_labefana_chain_evm(chain=1), hRadio2.get_labefana_chain_evm(chain=0), hRadio2.get_labefana_chain_evm(chain=1), hRadio1.get_labefana_ber(), hRadio2.get_labefana_ber(), int(radio1.status_rx_capacity), int(radio2.status_rx_capacity), radio1.status_chain_0_signal_strength, radio1.status_chain_1_signal_strength, radio2.status_chain_0_signal_strength, radio2.status_chain_1_signal_strength, radio1.status_dac_temp_0, radio1.status_dac_temp_1, radio2.status_dac_temp_0, radio2.status_dac_temp_1, tt.getSetPoint(1, False), hRadio1.get_labefana_coarse(), hRadio1.get_labefana_fine())
                                print terminal_data_format % data_value_params
                                print >> testlog, csv_file_data_format % data_value_params



        # Close the browser windows
        hRadio1.browser.quit()
        hRadio2.browser.quit()



if __name__ == '__main__':
    main()

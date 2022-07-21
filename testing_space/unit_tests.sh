#!/bin/bash
# Raymond Turrisi 
# Unit tests for MWDataMgr.py from the MWDataMgr repo. 
# Meant to be ran at the same level with the entire directory in place


#SINGLE FILE TESTS

## MOOS .alog

###Simplest use
python3 ../MWDataMgr.py -s data/2022_07_11_1/LOG_SHORESIDE_11_7_2022_____11_00_11/LOG_SHORESIDE_11_7_2022_____11_00_11.alog -o test_1

if [[ $? -ne 0 ]]; then 
    echo "Error observed - please resolve test case 1"
fi

printf "Intent: This directory should contain another directory, \n \
the name of the alog file (lowercase) with the _alog_csvs, \n \
which contains all the available topics as their own CSV files. " > test_1/test_1_intent.txt

### Intended as another simple use case for quickly and richly getting data from another ALOG file
python3 ../MWDataMgr.py -s data/2022_07_11_1/LOG_SHORESIDE_11_7_2022_____11_00_11/LOG_SHORESIDE_11_7_2022_____11_00_11.alog \
    -o test_2 \
    -i WIND_CONDITIONS WIND_CONDITIONS_GT WIND_DIR_MOD PMARINEVIEWER_PID UFLDANEMO_ITER_GAP UFLDANEMO_STATUS \
    -t json csv \
    --moos \
    --topic_mapping moos_topic_mapping.cfg

if [[ $? -ne 0 ]]; then 
    echo "Error observed - please resolve test case 2"
fi

printf "Intent: This directory should contain another directory, \n \
the name of the alog file (lowercase) with the _alog_csvs, \n \
which contains only the five included topics above. \n \
Next to this directory should be a json file of the same name \n \
which can be reopened and navigated in Python as a dictionary \n \
with the JSON library, or as a MAP in MATLAB. Also in this, \n \
by providing a configuration file tagged with MOOS_TOPIC_MAPPING \n \
(inside the cfg), a topic should already be parsed with the appropriate \n \
strategy. If a strategy is not provided, they are left as a string." > test_2/test_2_intent.txt


###Similar to above but with exclusion
python3 ../MWDataMgr.py -s data/2022_07_11_1/LOG_SHORESIDE_11_7_2022_____11_00_11/LOG_SHORESIDE_11_7_2022_____11_00_11.alog \
    -o test_3 \
    -x 'UMAC_551_STATUS' 'PREALM_STATUS' 'REALMCAST_CHANNELS' \
           'LOGGER_DIRECTORY' 'APPCAST_REQ_SHORESIDE' \
           'DB_EVENT' 'PLOGGER_STATUS' 'REGION_INFO' 'APPCAST_REQ' \
           'APPCAST_REQ_ALL' 'PREALM_ITER_GAP' 'PREALM_ITER_LEN' \
           'APPCAST' 'DB_TIME' 'DB_UPTIME' 'DB_CLIENTS' 'DB_QOS' \
           'PSHARE_INPUT_SUMMARY' 'PMARINEVIEWER_STATUS' 'HELM_MAP_CLEAR' \
           'PMV_CONNECT' 'PSHARE_STATUS' \
           'PMARINEVIEWER_ITER_GAP' 'PMARINEVIEWER_ITER_LEN' \
           'PSHARE_OUTPUT_SUMMARY' \
           'UFLDANEMO_ITER_LEN' 'PHI_HOST_IP' 'PHI_HOST_INFO' 'VIEW_ARROW' \
           'PHOSTINFO_STATUS' 'PHI_HOST_IP_ALL' 'PHI_HOST_IP_VERBOSE' \
           'PHI_HOST_PORT_DB' 'UFLDSHOREBROKER_STATUS' 'UFLDSHOREBROKER_ITER_LEN' \
           'UFLDANEMO_ITER_GAP' 'PHOSTINFO_ITER_LEN' 'PHOSTINFO_ITER_GAP' \
           'UFLDSHOREBROKER_ITER_GAP' 'NODE_BROKER_PING' 'PSHARE_CMD' \
           'NODE_BROKER_ACK_SALLY' 'NODE_BROKER_VACK' 'NODE_REPORT' \
           'APPCAST_REQ_SALLY' 'DEPLOY_ALL' 'STATION_ALL' \
           'MVIEWER_LCLICK' 'MOOS_MANUAL_OVERRIDE_ALL' 'RETURN_ALL' \
           'VIEW_SEGLIST' 'VIEW_POINT' \
    -t json csv \
    --moos \
    --topic_mapping moos_topic_mapping.cfg

if [[ $? -ne 0 ]]; then 
    echo "Error observed - please resolve test case 3"
fi

printf "Intent: Same as test two, except no matching topic names should appear \n \
in the CSV directory, and SAILPT_UPDATE should appear over what was produced in test 2" > test_3/test_3_intent.txt

## MOOS ._moos

#Still TBD

## ROS .bag
###Simplest use for ROS bags
python3 ../MWDataMgr.py -s data/2022_07_11_1/demo_system_bag.bag -o test_4

if [[ $? -ne 0 ]]; then 
    echo "Error observed - please resolve test case 4"
fi

printf "Intent: Same as test 1, however working with ROS bags require some more \n \
dependencies at apt/brew and python level. Particularly, some errors observed are \n \
related to YAML being unable to load CLoader, which is tried to have been fixed in \n \
setup.sh script (if you're using mac change apt to brew). If CLoader is totally unavailable \n \
yaml.load can be replaced with yaml.safe_load. Also installing rospy and rosbag \n \
with pip3 may be problematic. In this test one warning should have been observed with \n \
the N2KINfo message"# > test_4/test_4_intent.txt

### Same as test 2 but with rosbags
python3 ../MWDataMgr.py -s data/2022_07_11_1/XLOG_sally_11_7_2022_____15_00_33/mr_rosbag_2022-07-11-14-57-43_0.bag \
    -o test_5 \
    -i "/vessel_hdng_raw" "/humidity" "/battery_voltage" "/air_temperature" \
    -t json csv \

printf "Intent: This directory should contain another directory, \n \
the name of the rosbag file (lowercase) with the _ros_csvs, \n \
which contains only the five included topics above. \n \
Next to this directory should be a json file of the same name \n \
which can be reopened and navigated in Python as a dictionary \n \
with the JSON library, or as a MAP in MATLAB. We need not provide \n \
a parsing strategy configuration file since an attempted universal parsing algorithm was \n \
implemented which requires some more thorough testing across more ROS msg types" > test_5/test_5_intent.txt

#MISSIONS / DIRECTORIES

###Demonstrating configuration files for directory walking
###This would be used as if we point to a single mission
python3 ../MWDataMgr.py -d data/2022_07_11_1 \
    -o test_6 \
    -i directory_search_ix.cfg \
    --moos \
    --topic_mapping moos_topic_mapping.cfg
printf "Intent: Combines everything above in a single directory search. \n \
This functionality assumes that it is pointed to a folder which should maintain \n \
the structure of the subdirectories. This is so multiple vehicles/stations can have their \n \
own folder, while files representitive of the collection of them will still maintain their \n \
relative place in the tree. All expected files and conversions should be present. Reference \n \
the directory_search_ix.cfg file to see what topics should have been recorded." > test_6/test_6_intent.txt

###Demonstrating further directory walking, and how files are organized
###This would be used if we were to point it to a collection of missions
###which require data to be similarly organized
python3 ../MWDataMgr.py -d data/ \
    -o test_7 \
    -i directory_search_ix.cfg \
    --moos \
    --topic_mapping moos_topic_mapping.cfg
printf "Intent: Same as test 6 but from one directory above to further illustrate \n \
how files are located and how the subdirectories maintain their structure." > test_7/test_7_intent.txt

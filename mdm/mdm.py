'''
author: Raymond Turrisi <rturrisi(at)mit(dot)edu>
organization: MIT Marine Autonomy Lab
circa: Su'2022
fname: mdm.py
status: Development - Open for public use

about: MiddleWare Data Manager - Utilities for processing MOOS and/or ROS data and logs. 
        Intent to support .alog, ._moos, .bag files, with an extensible design to be able 
        to support wide ranging message protocols without modification of support code. 

license: MIT Licence

    Copyright 2022 <Raymond Turrisi & MIT Marine Autonomy Lab, MIT Dept. Mechanical Engineering>

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
    and associated documentation files (the "Software"), to deal in the Software without restriction, 
    including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, 
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial 
    portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT 
    LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''

from datetime import datetime
import os
import sys
import json
from operator import add, getitem
from functools import reduce
from typing import Dict, AnyStr, Callable, List


#Color pallette 
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

# util functions
def _isfloat(var:str):
    try:
        float(var)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

def _isint(var:str):
    try:
        int(var)
        return True
    except ValueError:
        return False

def _isbool(var:str): 
    if var.lower() == "true" or var.lower() == "false":
        return True 
    else:
        return False

#MiddleWare Data Mgr
class mdm:
    """mdm is a tool intended to function in both iPython environments, and support command line use. 
    It's objective is to do as much general heavy lifting which can be done for post-processing MOOS and ROS data file.
    Files it returns should be either fully processed, or have moved data into a more manipulatable state in data analysis
    environments such as Python and Matlab. 
    """
    def __init__(self):
        self._alogs = dict()
        self._moosconfs = dict()
        self._MWDataCollection = dict()
        self.warnings = True
        self.output_types = ["csv","json"]

        #When passed a configuration file, these are the MOOS parsing algorithm aliases which should be provided
        #in order to assign a parsing algorithm to a topic during runtime. 
        self.strategy_aliases = {"NUMBER":self.number_msg,
        "CSP_SIMPLE":self.csp_simple_msg,
        "CSP_NESTED":self.csp_nested_sequence_msg,
        "BOOL":self.boolean_msg}

        #Some standard MOOS topics and parsing algorithms
        self.moos_alog_strats = {"VIEW_ARROW":self.csp_simple_msg,
                            "REGION_INFO":self.csp_simple_msg,
                            "APPCAST_REQ":self.csp_simple_msg,
                            "UMAC_551_STATUS":self.csp_nested_sequence_msg,
                            "PREALM_STATUS":self.csp_nested_sequence_msg,
                            "REALMCAST_CHANNELS":self.csp_nested_sequence_msg,
                            "DB_EVENT":self.csp_simple_msg,
                            "PLOGGER_STATUS":self.csp_nested_sequence_msg,
                            "APPCAST_REQ_ALL":self.csp_simple_msg,
                            "DB_QOS":self.comma_separated_lists_msg,
                            "PMARINEVIEWER_STATUS":self.csp_nested_sequence_msg,
                            "PSHARE_STATUS":self.csp_nested_sequence_msg,
                            "PHOSTINFO_STATUS":self.csp_nested_sequence_msg,
                            "PHI_HOST_IP_VERBOSE":self.csp_simple_msg,
                            "UFLDSHOREBROKER_STATUS":self.csp_nested_sequence_msg,
                            "NODE_BROKER_PING":self.csp_simple_msg,
                            "PSHARE_CMD":self.csp_simple_msg,
                            "NODE_BROKER_ACK_SALLY":self.csp_simple_msg,
                            "MVIEWER_LCLICK":self.csp_simple_msg,
                            "VIEW_POINT":self.csp_simple_msg,
                            "DB_CLIENTS":self.comma_separated_lists_msg,
                            "PMARINEVIEWER_PID":self.number_msg,
                            "APPCAST_REQ_SHORESIDE":self.number_msg,
                            "PREALM_ITER_GAP":self.number_msg,
                            "PREALM_ITER_LEN":self.number_msg,
                            "DB_TIME":self.number_msg,
                            "DB_UPTIME":self.number_msg,
                            "HELM_MAP_CLEAR":self.number_msg,
                            "PMV_CONNECT":self.number_msg,
                            "PMARINEVIEWER_ITER_GAP":self.number_msg,
                            "PMARINEVIEWER_ITER_LEN":self.number_msg,
                            "PHI_HOST_PORT_DB":self.number_msg,
                            "UFLDSHOREBROKER_ITER_LEN":self.number_msg,
                            "PHOSTINFO_ITER_LEN":self.number_msg,
                            "PHOSTINFO_ITER_GAP":self.number_msg,
                            "UFLDSHOREBROKER_ITER_GAP":self.number_msg,
                            "DEPLOY_ALL":self.boolean_msg,
                            "STATION_ALL":self.boolean_msg,
                            "MOOS_MANUAL_OVERRIDE_ALL":self.boolean_msg,
                            "RETURN_ALL":self.boolean_msg,
                            "IVPHELM_BHV_ACTIVE":self.comma_separated_lists_msg,
                            "IVPHELM_BHV_RUNNING":self.comma_separated_lists_msg,
                            "IVPHELM_BHV_IDLE":self.comma_separated_lists_msg,
                            "IVPHELM_CREATE_CPU":self.number_msg,
                            "IVPHELM_LOOP_CPU":self.number_msg,
                            "IVPHELM_BHV_CNT":self.number_msg,
                            "IVPHELM_BHV_CNT_EVER":self.number_msg
                            }


        self.std_moos_topics = list(self.moos_alog_strats.keys())
        self.managed_moos_topics = self.std_moos_topics[:]

        #Parsing these topics will resort in crashes/runtime errors. Best if ignored. 
        self._ros_always_exclude = [
            "/rosout",
            "/rosout_agg",
            "/diagnostics",
            "/diagnostics_agg",
            "/diagnostics_toplevel_state"
            ]
        #supported input files
        self.managed_files = ['.alog', '._moos', '.bag']

        #supported output files
        self.supported_outputs = ['csv', 'json']
        
        return 
    
    def add_strategies(self, strategies:Dict[AnyStr, Callable]):
        """Associate a MOOS topic with a parsing alogorithm

        Args:
            strategies (Dict[AnyStr, Callable]): A dictionary which maps a topic name to a function. This function must take a string, and return a literal, a list, or a dictionary. 
        """
        self.managed_moos_topics.extend(strategies.keys())
        self.moos_alog_strats.update(**strategies)
        return 
        
    #standard strategies for parsing alog messages

    def boolean_msg(self, msg):
        """Converts a boolean message to a JSON compatible boolean value

        Args:
            msg (str): A boolean message as a string (true, True, TRUE, TrUe, etc..)

        Returns:
            str: JSON compatible boolean message (true, false)
        """
        return msg.lower()

    def number_msg(self, msg):
        """Converts a numeric message to a float or integer

        Args:
            msg (str): Numeric message as a string

        Returns:
            int or float: Returns a single integer or float at the original precision
        """
        if _isfloat(msg):
            if _isint(msg):
                msg = int(msg)
            else:
                msg = float(msg)
        return msg 

    def comma_separated_lists_msg(self, msg):
        """Converts a simple comma separated list to a list of tokens

        Args:
            msg (str): Comma separated list of tokens

        Returns:
            List: List of tokens sans commas
        """
        var = msg.split('|')
        if var[-1] == '':
            var.pop()
        var = '|'.join(var)
        return var 
    
    def csp_simple_msg(self, msg):
        """Converts a Comma Separated string of Pairs separated by an equals sign
        i.e. APPCAST_REQ = node=all,app=all,duration=3.0,key=pMarineViewer:shoreside,thresh=any

        Args:
            msg (str): Comma Separated string of Pairs, where a pair has a left and right hand side of an equals sign

        Returns:
            Dict: Returns a dictionary for each variable and value pair found in the comma separated message
        """
        new_msg = dict()
        for pair in msg.split('|'):
            section = pair.split("=")
            varname = section[0]
            var = section[1]
            if _isfloat(var):
                if _isint(var):
                    var = int(var)
                else:
                    var = float(var)
            elif _isbool(var):
                var = var.lower() #JSON standard
            new_msg.update({varname:var})
        return new_msg


    def csp_nested_sequence_msg(self, msg):
        """Converts a Comma Separated string of complex Pairs separated by an equals sign, 
        which can contain sublists separated by commas, and denoted with closed quotes
        i.e. UMAC_551_STATUS = AppErrorFlag=false,Uptime=0.851698,cpuload=3.276,memory_kb=4596,
        memory_max_kb=4724,MOOSName=uMAC_551,Publishing="APPCAST_REQ,APPCAST_REQ_ALL,",Subscribing="APPCAST,"
                                                        ^                            ^
        Args:
            msg (str): Comma Separated string of Pairs, where a pair has a left and right hand side of an equals sign, but 
            a value in the pair may be another comma separated list which requires a more complex parsing scheme (in Python)

        Returns:
            Dict: Returns a dictionary for each variable and value pair found in the comma separated message
        """     
        new_msg = dict()
        idx = 0
        cs_tokens = msg.split('|')
        while idx < len(cs_tokens):
            #get the 'supposed' pair and then split into lhs and rhs
            pair = cs_tokens[idx]
            section = pair.split("=")
            if len(section) != 2:
                #bad message
                idx+=1
                continue
            #if double quotes starts the sequence, then we have encountered a nested list
            if len(section[1]) != 0 and "\"" == section[1][0]:
                varname = section[0]
                #get the start of the sequence in the list, which be the everything right after this pair
                sos = cs_tokens.index(pair, idx)+1
                #now find the end of the sequence
                for eos in range(sos, len(cs_tokens)):
                    if '\"' in cs_tokens[eos]:
                        #in the succeeding tokens if they contain another apostrophe, then it is the last element in the nested list
                        break
                #Reassemble the sequence and make sure these are skipped on the next pass
                seq = '|'.join(cs_tokens[sos:eos]).replace('\"', '')
                new_msg.update({varname:seq}) 
                idx+=(eos-sos)
            else: 
                varname = section[0]
                var = section[1]
                if len(var) == 0:
                    var = "NA"
                if _isfloat(var):
                    if _isint(var):
                        var = int(var)
                    else:
                        var = float(var)
                elif _isbool(var):
                    var = var.lower() #JSON standard
                new_msg.update({varname:var})
            idx+=1
        return new_msg

    def get_alog(self, alogf=None, include_only=[], exclude=[], use_strategies = True):
        """ Provided a path to a MOOS alogf we return nested dictionaries of the recorded data. Format: 
          data["info", "data"]
          data["info"]["alias", "logfile", "opendate", "logstart"] - access information stored in the top of the log file
          data["data"]["topic"] - access the timeseries array for the associated topic in a log file
          data["data]["topic"][idx][time, "msg", "src"] - At an index, can access the time which the message was published, the raw string message, and where the message came from

        Arguments:
          alogf (AnyStr) -- Path to a MOOS .alog file
          include_only {List[AnyStr, ...]} - List of topics to include - in U and I and not E 
          exclude {List[AnyStr, ...]} - List of topics to exclude - in U and I and not E 
        Returns:
          Dict -- Returns nested dictionaries and arrays
        """

        # Parameter error checking
        if alogf == None:
            print(
                f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_alog>: Must provide path to MOOS .alog file)")
            return
        if not os.path.isfile(alogf) or ".alog" not in alogf:
            print(
                f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_alog>: File does not exist or is not a MOOS alog file\n\t < {alogf} >")
            return
        # Initializing the data storage object
        data = dict()
        data.update({"info": dict()})
        data.update({"data": dict()})
        with open(alogf, "r") as file:
            print(
                f"{bcolors.OKGREEN}Working{bcolors.ENDC}: Reading < {alogf.split(os.path.sep)[-1]} >")
            lines = file.readlines()
            linenums = len(lines)
            for linenum, line in enumerate(lines):
                # Handle the header in the alog file
                if linenum%1000 == 0:
                    print(f"On {linenum}/{linenums}", end='\r')
                if line[0] == "%":
                    if "LOG FILE" in line:
                        # we have the filename
                        chunks = line.split("  ", 1)
                        if "LOG FILE" in chunks[0]:
                            logfile = chunks[1].strip()
                            #TODO - updated this partially for cohesiveness
                            data["info"].update({"logfile": alogf})
                            data["info"].update({"alias": data['info']['logfile'].split(os.path.sep)[-1].split('.')[0]})
                    elif "FILE OPENED ON" in line:
                        # we have the date which the file was opened, which may be incorrect/a MOOS error
                        chunks = line.split("  ", 1)
                        if "FILE OPENED ON" in chunks[0]:
                            opendate = chunks[1].strip()
                            data["info"].update({"opendate": opendate})
                    elif "LOGSTART" in line:
                        # we have the time which the file was actually opened, timesince epoch, and on the machine
                        chunks = line.split("  ", 1)
                        if "LOGSTART" in chunks[0]:
                            logstart = float(chunks[1].strip())
                            data["info"].update({"logstart": logstart})
                    elif "%%%%%%%%%%" in line:
                        # skip the spacer blocks
                        continue
                    else:
                        print(
                            f"{bcolors.WARNING}Warning{bcolors.ENDC}: Undefined non-message related header:\n\t < {line} >")
                        pass
                else:
                    chunks = line.split(" ")
                    idx = 0
                    time = -1.0
                    topic = "NA"
                    src = "NA"
                    msg = "NA"
                    for component in range(0, len(chunks)):
                        # assuming that the first three parts are the time, the topic, the source, and then the remainder of the line is the message irregardless of the whitespace
                        if chunks[idx] == '':
                            chunks.pop(idx)
                            continue
                        if(idx == 0):
                            time = float(chunks[idx])+float(data["info"]["logstart"])
                        elif idx == 1:
                            topic = chunks[idx].strip()
                        elif idx == 2:
                            src = chunks[idx].strip()
                        elif idx == 3:
                            msg = ''.join(chunks[idx:]).strip('\n')
                            msg = msg.replace(',','|')
                            if len(msg) == 0:
                                msg = "NA"
                            if use_strategies:
                                #TODO: Make this work for generic types and work with suffixed standard topics
                                #i.e. if *STATUS was provided to a mapping, will work for all matches i.e. SALLY_STATUS, LARRY_STATUS, etc..
                                if topic in self.managed_moos_topics:
                                    msg = self.moos_alog_strats[topic](msg)
                            break
                        idx += 1
                    if include_only != [] and topic not in include_only or topic in exclude:
                        continue
                    if topic not in data["data"].keys():
                        data["data"].update({topic: [[time, msg, src]]})
                        continue
                    else:
                        data["data"][topic].append([time, msg, src])
        return data

    def get_moosconf(self, moosf=None):
        # TODO: WRITE FUNCTION
        """ Provided a path to a logged MOOS configuration file we return nested dictionaries of the recorded data. Format: 
        Arguments:
          moosf (AnyStr) -- Path to a MOOS .alog file
        Returns:
          Dict -- Returns nested dictionaries and arrays
        """
        if moosf == None:
            print(
                f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_moosconf>: Must provide path to collection of MOOS log files (.alog and/or .moos)")
            return
        if not os.path.isfile(moosf) or "._moos" not in moosf:
            print(
                f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_moosconf>: File does not exist or is not a MOOS alog file\n\t < {moosf} >")
            return
        with open(moosf, "r") as file:
            data = file.read()
        return data

    def get_rosbag(self, rosbagf=None, include_only=[], exclude=[]):

        """ Provided a path to a MOOS alogf we return nested dictionaries of the recorded data. Format: 
          data["info", "data"]
          data["info"]["alias", "opendate", "logstart", "topic_metadata"] - access information stored in the top of the log file
          data["data"]["topic"] - access the timeseries array for the associated topic in a log file
          data["data]["topic"][idx][time, "msg"] - At an index, can access the time which the message was published, the raw string message, and where the message came from

        Arguments:
          rosbagf (AnyStr) -- Path to a rosbag file
          include_only {List[AnyStr, ...]} - List of topics to include - in U and I and not E, I by default is U
          exclude {List[AnyStr, ...]} - List of topics to exclude - in U and I and not E, I by default is U
        Returns:
          Dict -- Returns nested dictionaries and arrays
        """
        #TODO: Can add source node for each message
        #bag = rosbag.Bag(file)
        #generator = bag.read_messages(topics=topic)
        #msg_lst=list(gen)
        #msg = msg_lst[0]
        #msg.message.origin_node
        try:
            if "rosbag" not in sys.modules:
                print(f"{bcolors.OKBLUE}Importing rosbag - this may take some time...{bcolors.ENDC}")
            import rosbag
            import yaml 
            from yaml import CLoader
        except ImportError:
            print(f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_rosbag>: Missing \'rosbag\'.     \
            \n\t> Try: \n\t$ pip install rosbag) \
            \n\t> Mac users may need: \n\t $ pip3 install --extra-index-url https://rospypi.github.io/simple/ rospy rosbag")

        data = dict()
        data.update({"info": dict()})
        data.update({"data": dict()})

        # Parameter error checking
        if rosbagf == None:
            print(
                f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_rosbag>: Must provide path to MOOS .alog file)")
            return
        if not os.path.isfile(rosbagf) or ".bag" not in rosbagf:
            print(
                f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_rosbag>: File does not exist or is not a MOOS alog file\n\t- < {rosbagf} >")
            return

        try:
            bag = rosbag.Bag(rosbagf)
        except rosbag.bag.ROSBagUnindexedException:
            print(
                f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_rosbag>: Unindexed/Corrupted ROS bag\n\t- < {rosbagf} >\n\t- Try running \"$ rosbag reindex {rosbagf}\"")
            return
        src_fname = bag.filename
        try:
            print(
                f"{bcolors.OKGREEN}Working{bcolors.ENDC}: Reading < {rosbagf.split(os.path.sep)[-1]} >")

            data["info"].update({"logfile":src_fname,
                "alias":src_fname.split(os.path.sep)[-1].split('.')[0],
                "opendate":bag.get_start_time(),
                "logstart":bag.get_start_time(),
                "topic_metadata":dict()})

            baginfo = bag.get_type_and_topic_info()

            job_size = 0
            for topic_id, topic in enumerate(baginfo.topics.keys()):
                if topic not in self._ros_always_exclude and not (include_only != [] and topic not in include_only or topic in exclude):
                    job_size+=baginfo.topics[topic][1]

            msgs_read = 0  
            for topic_id, topic in enumerate(baginfo.topics.keys()):
                #begin to instantiate a topic subtree to be inserted into the data after
        
                if include_only != [] and topic not in include_only or topic in exclude or topic in self._ros_always_exclude:
                    continue

                topic_data = {
                    "msg_type":baginfo.topics[topic][0],
                    "connections":baginfo.topics[topic][2],
                }
                
                data["info"]["topic_metadata"].update({topic:topic_data})
                data["data"].update({topic:[]})
                for i, (_topic, msg, t) in enumerate(bag.read_messages(topics=topic)):
                    if msgs_read%1000 == 0:
                        print(f"On {msgs_read}/{job_size}", end='\r')
                    try:
                        #msg = {"time":t.to_sec(), **yaml.safe_load(str(msg))}
                        msg = {"time":t.to_sec(), **yaml.load(str(msg), Loader=CLoader)}
                    except TypeError as e:
                        print(f"{bcolors.WARNING}Warning{bcolors.ENDC} <mdm.get_rosbag>: Error reading message type: \
                        \n\t > Message type < {baginfo.topics[topic][0]} > \
                        \n\t > Lost data < {str(msg)} > \
                        \n\t > Specific error: \"{e}\" \
                        \n\t > Resolution: {bcolors.OKBLUE}Skipping topic{bcolors.ENDC}")
                        data["data"].pop(topic)
                        break
                    #time = msg.pop('time')
                    data["data"][topic].append([msg])
                    msgs_read+=1
            return data
        except rosbag.bag.ROSBagException:
            print(
                f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_rosbag>: Something went wrong while reading file\n\t- < {rosbagf} >\n\t- Caught under rosbag.bag.ROSBagException\"")
            return None
            
    def dump_json(self, data_dict:dict, fname:str):
        #TODO: Add error checking to see if file exists similar to writing the CSV
        with open(fname+".json", "w") as jfile:
            json.dump(data_dict, jfile, indent=2)

    def alog_2_csv(self, alog_dict:dict, dirname:str = None, force_write = False, ignore_src = False, delim = ',', eol = ''):
        """Turns an alog file which has been retrieved with our algorithm into a CSV file

        Args:
            alog_dict (dict): alog data as a dictionary
            dirname (str, optional): output directory name. Defaults to None.
            force_write (bool, optional): Whether or not we will automatically write over existing files. Defaults to False.
            ignore_src (bool, optional): Whether or not we should drop the where the message came from. Defaults to False.
            delim (str, optional): alternative delimeter. Defaults to ','.
            eol (str, optional): alternative line terminator, either ''\\n or eol\\n. Defaults to ''.
        """
        #take a single data storage dictionary and store it as collection of csv files
        '''
        Assuming that a dictionary that was passed is representative of a single mission
        logfile_dir/
            ...
            topic1.csv
            topic2.csv
            ...
        '''
        #make the new directory
        if dirname is None:
            dirname = alog_dict["info"]["alias"].lower()+"_alog_2_csv"
        try:
            os.makedirs(dirname)
        except FileExistsError:
            print(f"{bcolors.WARNING}Warning{bcolors.ENDC} <mdm.alog_2_csv>: Directory exists: \
                \n\t > < {dirname} >")
            if force_write:
                print(f"\t > Resolution: {bcolors.OKBLUE}Overwriting data{bcolors.ENDC}")
            else:
                print(f"\t > Resolution: {bcolors.OKBLUE}Skipping file{bcolors.ENDC}")
                return
        #iterate over the topics and open csv files, stepping through the publications writing the data
        topic_names = alog_dict["data"].keys()
        for topic in topic_names:
            with open(os.path.join(dirname, f"{topic}.csv"), "w") as csv_file:
                test_msg = alog_dict["data"][topic][0][1]
                if ignore_src:
                    if isinstance(test_msg, list):
                        #LIST is untested as of 7/14 - rt
                        headers = f"time{delim}"+delim.join([f"idx_{idx}" for idx in range(0, len(test_msg))])+eol+'\n'
                        csv_file.write(headers)
                        for msg in alog_dict["data"][topic]:
                            line = f"{msg[0]}{delim}"+delim.join(msg[1])+eol+'\n'
                            csv_file.write(line)
                    elif isinstance(test_msg, dict):
                        headers = f"time{delim}"+delim.join([str(iter) for iter in test_msg.keys()])+eol+'\n'
                        csv_file.write(headers)
                        for msg in alog_dict["data"][topic]:
                            line = f"{msg[0]}{delim}"+delim.join([str(iter) for iter in msg[1].values()])+eol+'\n'
                            csv_file.write(line)
                    else:
                        headers = f"time{delim}data{eol}\n"
                        csv_file.write(headers)
                        for msg in alog_dict["data"][topic]:
                            line = f"{msg[0]}"+delim+str(msg[1])+eol+'\n'
                            csv_file.write(line)
                else:
                    if isinstance(test_msg, list):
                        #LIST is untested as of 7/14, and we shouldn't ever get here- rt
                        headers = f"time{delim}"+delim.join([f"idx_{idx}" for idx in range(0, len(test_msg))])+delim+"src"+eol+'\n'
                        csv_file.write(headers)
                        for msg in alog_dict["data"][topic]:
                            line = f"{msg[0]}{delim}"+delim.join(msg[1])+delim+msg[2]+eol+'\n'
                            csv_file.write(line)
                    elif isinstance(test_msg, dict):
                        headers = f"time{delim}"+delim.join([str(iter) for iter in test_msg.keys()])+delim+"src"+eol+'\n'
                        csv_file.write(headers)
                        for msg in alog_dict["data"][topic]:
                            line = f"{msg[0]}{delim}"+delim.join([str(iter) for iter in msg[1].values()])+delim+msg[2]+eol+'\n'
                            csv_file.write(line)
                    else:
                        headers = f"time{delim}data{delim}src{eol}\n"
                        csv_file.write(headers)
                        for msg in alog_dict["data"][topic]:
                            line = f"{msg[0]}"+delim+str(msg[1])+delim+msg[2]+eol+'\n'
                            csv_file.write(line)
        return 


    def _rb_get_headers(self, tree, path, children):
        #with dictionary keys, find all the roots/primative data types
        for child in tree.keys():
            if isinstance(tree[child], dict):
                self._rb_get_headers(tree[child], f"{path}:{child}", children)
            else:
                children.append(f"{path}:{child}") 

    def rosbag_2_csv(self, rosbag_dict:dict, dirname:str = None, force_write = False, delim = ',', eol = ''):
        """Turns an rosbag file which has been retrieved with our algorithm into a CSV file

        Args:
            alog_dict (dict): alog data as a dictionary
            dirname (str, optional): output directory name. Defaults to None.
            force_write (bool, optional): Whether or not we will automatically write over existing files. Defaults to False.
            delim (str, optional): alternative delimeter. Defaults to ','.
            eol (str, optional): alternative line terminator, either ''\\n or eol\\n. Defaults to ''.
        """
        #messages sometimes contains nested dictionaries, so the header of a message is going to be top:to:bottom

        #messages are going to be extracted recursively down to the primitive type
        #take a single data storage dictionary and store it as collection of csv files
        '''
        Assuming that a dictionary that was passed is representative of a single mission
        logfile_dir/
            ...
            topic1.csv
            topic2.csv
            ...
        '''
        #make the new directory
        if dirname is None:
            dirname = rosbag_dict["alias"]+"_rosbag_2_csv"
        try:
            os.makedirs(dirname)
        except FileExistsError:
            print(f"{bcolors.WARNING}Warning{bcolors.ENDC} <mdm.rosbag_2_csv>: Directory exists: \
                \n\t > < {dirname} >")
            if force_write:
                print("\t > Overwriting data")
            else:
                print("\t > Skipping file")
                return
        #iterate over the topics and open csv files, stepping through the publications writing the data
        topic_names = rosbag_dict["data"].keys()
        for topic in topic_names:
            #anyone who publishes to topics with \ has greater problems
            fname = topic[:]
            fname = topic.replace('/','')
            fname = fname.replace('\\','')
            with open(os.path.join(dirname, f"{fname}.csv"), "w") as csv_file:
                test_msg = rosbag_dict["data"][topic][0][0]
                headers = []
                memoized_paths = []
                for key in test_msg.keys():
                    if isinstance(test_msg[key], dict):
                        #get root name
                        root = key 
                        children = []
                        self._rb_get_headers(test_msg[key], root, children)
                        memoized_paths.extend([seq.split(':') for seq in children])
                        headers.extend(children)
                    else:
                        memoized_paths.append([key])
                        headers.append(key)

                line = delim.join(headers)+eol+'\n'
                csv_file.write(line)

                for msg in rosbag_dict["data"][topic]:
                    msg = msg[0]
                    line = delim.join([str(reduce(getitem, accessor, msg)).replace(",","|") for accessor in memoized_paths])+eol+'\n'
                    csv_file.write(line)
        return 

    def _preview_path(self, metadata:dict, directory:str, target:bool=True):
        """Helper function for mdm.convert_directory. Searches for all managed files, records their path, and counts the number of each match

        Args:
            metadata (Dict): Recursively built metadata about the requested directory and all its children
            directory (str): Parent directory
        """
        if os.path.isdir(directory):
            if target:
                #Here we consider only target files/suffixes
                members = os.listdir(directory)
                for file in members:
                    temp_path = directory+os.path.sep+file
                    if os.path.isdir(temp_path):
                        self._preview_path(metadata, temp_path)
                    elif os.path.isfile(temp_path):
                        if '.alog' == file[-5:]:
                            metadata['counts']['alogs']+=1
                            metadata['paths'].append(temp_path)
                        elif '._moos' == file[-6:]:
                            metadata['counts']['moosconfs']+=1
                            metadata['paths'].append(temp_path)
                        elif '.bag' == file[-4:]:
                            metadata['counts']['bags']+=1
                            metadata['paths'].append(temp_path)
                        else:
                            pass
            else:
                #we are collecting all the files and path in the directory
                members = os.listdir(directory)
                for file in members:
                    temp_path = directory+os.path.sep+file
                    if os.path.isdir(temp_path):
                        self._preview_path(metadata, temp_path, target=False)
                    elif os.path.isfile(temp_path):
                        metadata['paths'].append(temp_path)
        else:
            #This is a generic function - error handling is held elsewhere
            pass

    def convert_directory(self, path:str=None, newdirectory=None, include_only = [], exclude = []):
        """Searches an entire directory for all matching files, and converts them maintaining their relationship from the root directory

        Args:
            path (str, optional): Path to parent directory to be searched. Defaults to None.
            newdirectory (str, optional): Directory to dump all the results to. This new directory becomes the root for all converted files. Defaults to None.
            include_only (list, optional): Topic include only list. Defaults to [].
            exclude (list, optional): Topic exclude list. Defaults to [].

        Returns:
            dict: Returns a dictionary of all matching directory data
        """
        '''
        Returns a dictionary of all convertable files in a directory, as collection[filealias][data]
        Where 'data' would be a dictionary consisting of .alog, ._moos, and .bag data
        TODO: Break this function into two - one for the CLI, and one for the Python API such that it only returns the object (would be bad for someone to not save it though)
        '''
        path.replace('/', os.path.sep)
        path.replace('\\', os.path.sep)
        split_path = path.split(os.path.sep)
        if len(split_path) > 1:
            path_upto = os.path.sep.join(split_path[:-1])+os.path.sep
        else:
            path_upto = ''

        
        path_metadata = {'paths':[], 'counts':{'alogs':0, 'moosconfs':0, 'bags':0}}
        self._preview_path(path_metadata, path)
        num_files = reduce(add, path_metadata['counts'].values())
        target_metadata = {'paths':[], 'counts':{'alogs':0, 'moosconfs':0, 'bags':0}}
        self._preview_path(target_metadata, newdirectory, target=False)
        #Why have such a terrible one liner one may ask? One can also ask why Python provides such a performance incentive to do so. 
        #This is also maybe a roundabout solution.
        target_files = list(filter(lambda f: f is not None, map(lambda f: f.split(os.path.sep)[-2] if 'csv' not in f else None, target_metadata['paths'])))

        for destination_f in target_files: #0 to some number of found files in the destination path
            for src_f in path_metadata['paths']: #compare the names of the files found in the destination path with those which are asked to be converted
                #if there is a match, we skip this file. we only want to convert "new" data which has been added, to serve as a speedup.
                if destination_f in src_f:
                    path_metadata['paths'] = list(filter(lambda x: src_f not in x, path_metadata['paths']))
                    num_files-=1
                    if '.alog' == src_f[-5:]:
                        path_metadata['counts']['alogs']-=1
                    elif '._moos' == src_f[-6:]:
                        path_metadata['counts']['moosconfs']-=1
                    elif '.bag' == src_f[-4:]:
                        path_metadata['counts']['bags']-=1

        if num_files > 15 and self.warnings:
            print(f"{bcolors.WARNING}Warning{bcolors.ENDC}: You are requesting to convert over fifteen files in the path provided ({num_files}). \n \
                \t - .alog : {path_metadata['counts']['alogs']}\n \
                \t - ._moos: {path_metadata['counts']['moosconfs']}\n \
                \t - .bags : {path_metadata['counts']['bags']}")
            ans = input("Do you wish to continue? y/n: ")
            if ans.lower()[0] == 'y':
                pass 
            else: 
                exit(0)

        if num_files == 0:
            print(f"{bcolors.WARNING}Warning{bcolors.ENDC}: No new files to convert (target matches vs. destination matches). \n \
                \r\t > Delete data you wish to replace in the target directory. \n \
                \r\t > Report a bug.")

        directory_collection = dict()

        for fnum, file in enumerate(path_metadata['paths']):
            print(f"{bcolors.OKGREEN}Working{bcolors.ENDC}: On file {fnum+1}/{num_files}")
            #TODO: Check to see if an alias is already in the directory collection and raise a warning for bad file names
            file_path = file.split(os.path.sep)
            file_path.pop()
            file_path = os.path.sep.join(file_path)
            file_path = file_path.replace(path_upto, "")
            newdirectory = newdirectory+os.path.sep if newdirectory[-1] != os.path.sep else newdirectory
            new_file_path = newdirectory+file_path+os.path.sep
            
            try:
                os.makedirs(new_file_path)
            except FileExistsError:
                pass  

            if '.alog' == file[-5:]:
                alogfile_data = self.get_alog(alogf=file, include_only=include_only, exclude=exclude, use_strategies=True)
                if alogfile_data is None:
                    print(
                        f"{bcolors.WARNING}Warning{bcolors.ENDC}: mdm.get_alog returned None and is assumed to have been handled elsewhere, continuing:\n\t- < {file} >")
                directory_collection.update({alogfile_data['info']['alias']:alogfile_data})
                csv_filepath = new_file_path+alogfile_data['info']['alias'].lower()+"_alog_csvs"
                if 'csv' in self.output_types:
                    self.alog_2_csv(alog_dict=alogfile_data, dirname=csv_filepath, force_write=False, ignore_src=False)
                nickname = new_file_path+alogfile_data['info']['alias'].lower()
                if 'json' in self.output_types:
                    self.dump_json(alogfile_data, fname=nickname)
            elif '._moos' == file[-6:]:
                #moosconf_data = self.get_moosconf(moosconf=file)
                #directory_collection.update({moosconf_data['info']['alias']:moosconf_data})
                #self.dump_json(moosconf_data)
                pass
            elif '.bag' == file[-4:]:
                rosbag_data = self.get_rosbag(rosbagf=file, include_only=include_only, exclude=exclude)
                if rosbag_data is None:
                    print(
                        f"{bcolors.WARNING}Warning{bcolors.ENDC}: mdm.get_rosbag returned None and is assumed to have been handled elsewhere, continuing:\n\t- < {file} >")
                    continue
                directory_collection.update({rosbag_data['info']['alias']:rosbag_data})
                csv_filepath = new_file_path+rosbag_data['info']['alias'].lower()+"_ros_csvs"
                if 'csv' in self.output_types:
                    self.rosbag_2_csv(rosbag_dict=rosbag_data, dirname=csv_filepath, force_write=False)
                nickname = new_file_path+rosbag_data['info']['alias'].lower()
                if 'json' in self.output_types:
                    self.dump_json(rosbag_data, fname=nickname)
            
        timenow = datetime.now()
        stamp = timenow.strftime("%Y_%m_%d_mission_data_whole")
        collection_filepath = newdirectory+stamp
        if 'json' in self.output_types:
            self.dump_json(data_dict=directory_collection, fname = collection_filepath)

        return directory_collection

    def get_topic_ix(self, path):
        """Parses a TOPIC_IX configuration file for this mdm.

        Args:
            path (str): Path to configuration file

        Returns:
            list: Returns list of IX topics to match
        """
        ix_list = []
        with open(path, "r") as cfg_file:
            file_data = cfg_file.readlines()
            #search for the configuration file type
            for linenum, line in enumerate(file_data):
                if line[0] == '%':
                    continue 
                elif line[0:4] == "CFGT":
                    line = line.replace(" ", "")
                    ftype = line.split("=")[-1].strip()
                    if ftype != "TOPIC_IX":
                        print(f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_topic_ix>: Wrong configuration file type for this argument\n\t Should be \"TOPIC_IX\" and got \"{ftype}\" >")
                        exit(1)
                    break 
            #we either ran through the whole file finding nothing or we were passed a configuration file with a bad configuration
            if ftype == "TOPIC_IX": 
                #the configuration type was correct for how it was passed
                for line in file_data[linenum+1:-1]:
                    if line[0] == '%':
                        continue
                    #TODO: check integrity of configuration file format
                    #remove whitespace as minor convenience to user
                    line = line.replace(" ", '').strip()
                    if len(line) != 0:
                        ix_list.append(line)
            else:
                #we reached the bottom of the file without finding a configuration file type
                print("{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_topic_ix>: Incorrect use of configuration file - file has been read without any configuration type declaration. i.e. CFGT=TOPIC_IX")
                exit(1)
            return ix_list

    def get_moos_topic_mapping(self, path):
        """Parses MOOS_TOPIC_MAPPING configuration file for the mdm and adds topic-strategy matchings to its collection

        Args:
            path (str): Path to MOOS_TOPIC_MAPPING file. 
        """
        strategies=dict()
        with open(path, "r") as cfg_file:
            file_data = cfg_file.readlines()
            #search for the configuration file type
            for linenum, line in enumerate(file_data):
                if line[0] == '%':
                    continue 
                elif line[0:4] == "CFGT":
                    line = line.replace(" ", "").strip()
                    ftype = line.split("=")[-1]
                    if ftype != "MOOS_TOPIC_MAPPING":
                        print(f"{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_moos_topic_mapping>: Wrong configuration file type for this argument\n\t Should be \"MOOS_TOPIC_MAPPING\" and got \"{ftype}\" >")
                        exit(1)
                    break 
            #we either ran through the whole file finding nothing or we were passed a configuration file with a bad configuration
            if ftype == "MOOS_TOPIC_MAPPING": 
                #the configuration type was correct for how it was passed
                for line in file_data[linenum+1:-1]:
                    #TODO: check integrity of configuration file format
                    line = line.strip()
                    if line.count('=') == 1:
                        topic_strategy = line.replace(" ", "").split('=')
                        topic = topic_strategy[0]
                        strategy = topic_strategy[1]
                        if strategy in self.strategy_aliases.keys():
                            strategies.update({topic:self.strategy_aliases[strategy]})
                        else:
                            aliases = "\n".join([f'\t\t - {alias}' for alias in self.strategy_aliases])
                            print(f"{bcolors.WARNING}Warning{bcolors.ENDC}: Unregistered standard strategy. Got < {line} >.")
                            print(f"\t Needs to be in the form of: MOOS_VAR = STRATEGY_ALIAS")
                            print(f"Available aliases: \n{aliases}")
                    elif line.count('=') > 1:
                        print(f"{bcolors.WARNING}Warning{bcolors.ENDC}: Malformed configuration statement\n\t < {line} >")
                    else:
                        pass 
                self.add_strategies(strategies=strategies)
            else:
                #we reached the bottom of the file without finding a configuration file type
                print("{bcolors.FAIL}Error{bcolors.ENDC} <mdm.py: mdm.get_moos_topic_mapping>: Incorrect use of configuration file - file has been read without any configuration type declaration. i.e. CFGT=TOPIC_IX")
                exit(1)
# mdm/__main__.py

if __name__ == '__main__':
    from .mdm import mdm
    from .mdm import bcolors
    import sys
    import argparse
    import os
    #CONFIGURE ARGUMENT PARSER
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--examples", help="Display example uses", action="store_true")
    parser.add_argument("--templates", help="Generate a template for moos topic mappings, inclusion/exclusions, and a shell script for converting a directory", action="store_true")
    parser.add_argument("-s", "--source", help="Single file source", default=None)
    parser.add_argument("-d", "--directory", help="Mission directory", default=None)
    parser.add_argument("-o", "--output", help="Output directory", default=None)
    parser.add_argument("-x", "--exclude", help="List of topics to exclude - can be a list or a configuration file", default=[], nargs='*')
    parser.add_argument("-i", "--include_only", help="List of topics to include - can be a list or a configuration file", default=[], nargs='*')
    parser.add_argument("-t", "--type", help="Output file types <json>, <csv>.", default="csv", nargs='*')
    parser.add_argument("-nw", "--nowarnings", help="Execute with no warnings", action="store_true")
    parser.add_argument("--moos", help="Will accept MOOS specific arguments. Without this they will be ignored.", action="store_true")
    parser.add_argument("--topic_mapping", help="MOOS - Configuration file mapping MOOS topic names to a standard message parser")
    parser.add_argument("--ros", help="Will accept ROS specific arguments")
    args = parser.parse_args()

    #CHECK AND PARSE ARGUMENTS
    if len(sys.argv) == 1:
        print(f"{bcolors.FAIL}Error{bcolors.ENDC}: Must provide additional arguments")
    
    #Default parameters
    output_directory = None
    exclude = []
    include_only = []
    output_types = ["csv"]
    mgr = mdm()

    if args.output:
        output_directory = args.output

    if args.exclude != [] and args.include_only != []:
        print(f"{bcolors.FAIL}Error{bcolors.ENDC}: Providing topics to both include_only and exclude returns an empty set, thus yielding no data.")
        exit(1)

    if args.exclude != []:
        #same structure and idea only varies by the context for how ix list is passed to the program
        #indiscriminate of ROS or MOOS
        for x in args.exclude:
            if os.path.isfile(x):
                exclude.extend(mgr.get_topic_ix(x))
            else:
                exclude.append(x)

    if args.include_only != []:
        for x in args.include_only:
            if os.path.isfile(x):
                include_only.extend(mgr.get_topic_ix(x))
            else:
                include_only.append(x)

    if args.type:
        output_types = args.type
        if not isinstance(output_types, list):
            output_types = [output_types]
        if any([str(elem) not in mgr.supported_outputs for elem in output_types]):
            print(f"{bcolors.FAIL}Error{bcolors.ENDC}: A requested output is not supported\n\t < {output_types} >\n\t Supported types:")
            print("\n".join([f"\t\t- \"{t}\"" for t in mgr.supported_outputs]))
        else:
            mgr.output_types = output_types

    if args.nowarnings:
        mgr.warnings = False

    if args.moos:
        #parse moos specific arguments, specifically the topic mapping parameters
        if args.topic_mapping:
            path = args.topic_mapping
            if os.path.isfile(path):
                mgr.get_moos_topic_mapping(path)

    #There are four exclusive interactions and outcomes for engaging with this program

    #Interaction 1 - help is automatically captured and then program terminates

    #For this terminal applications use, we are either operating on a single file, or a directory
    #We cannot provide a source and a directory, so only work on one
    if args.examples:
        #Interaction 2 - User wants to see examples (ignores everything else)
        print("mdm examples and intended result -")
        print("This script is intended for use with .alog, ._moos, and .bag files. With this you can do two things: \n\
            \t- Run the script and pass a single file with -s or --source \n\
            \t- Run the script and pass a mission directory and convert all the files at once by passing -d or --directory \n \
            You MUST pass at least one of these arguments to produce a conversion. For example cannot run the script and pass ONLY a file to be converted without -s.")
        print()
        print("Converting a single file: \n \
            \t- python3 mdm.py -s path/to/mission.alog \n\
            \t\t- Will make directory path/to/mission_mwmgr and by default write csv files to another directory path/to/mission_mwmgr/mission_alog_csvs/ for all the topics in the alog file \n\
            \t- python3 mdm.py -s path/to/mission.alog -i 'topic1' 'topic2' 'topic3' \n \
            \t\t- Similar to above, except will only include topics 'topic1', 'topic2', and 'topic3' \n \
            \t- python3 mdm.py -s path/to/mission.alog -x 'topic1' 'topic2' 'topic3' \n \
            \t\t- Similar to above, except will exclude topics 'topic1', 'topic2', and 'topic3' and include all others \n \
            Internally all the data is organized into Python dictionaries. You can also dump all the extracted data as a JSON as it is stored in the dictionary, i.e.\n \
            \t python3 mdm.py -s path/to/mission.alog -i 'topic1' 'topic2' 'topic3' -t json csv \n\
            \t\t- Here you will find the JSON file next to the directory containing the csv files")
        print()
        print("Converting a mission directory:\n \
            \t python3 mdm.py -d path/to/mission/directory output_directory\n \
            \t\t Assume that the directory it was pointed to references a mission that should be similarly grouped. Therefore, \n \
            \t\t each file will maintain a reference to its parent directory, but no more, in order to preserve some file structure. \n \
            \t\t For example, you may want to analyze logs from a collection of vehicles and shoreside from a particular mission. \n \
            \t\t Each vehicle would have its own folder in a mission directory, with its associated ROS bags. In the case you have \n \
            \t\t a ROS bag reflective of all the vehicles, this order is also maintained. \n\n \
            \t Support for more arguments is coming soon, however since this function is meant to scale, \n \
            \t it will support mission configuration parsing and management files. i.e. --exclude_topics exclusion_list.txt, \n \
            \t --include_topics include_only_list.txt, --moos_mappings moos_topic_mappings.txt, etc..")
        exit(0)
    elif args.source != None and args.directory == None:
        #Interaction 3 - User wants to convert a single file
        source = args.source
        #check if file exists and is file
        if not any(ftype in source for ftype in mgr.managed_files):
            print("{bcolors.FAIL}Error{bcolors.ENDC}: Unrecognized file type")
            exit(1)
        #get the data and conduct error checking on the file type
        if '.alog' == source[-5:]:
            data = mgr.get_alog(source, include_only=include_only, exclude=exclude, use_strategies=True)
        elif '._moos' == source[-6:]:
            data = mgr.get_moosconf(source)
            if args.output:
                data["info"]["alias"] = args.output
            if 'json' in output_types:
                mgr.dump_json(data, data["info"]["alias"]+"_moos")
        elif '.bag' == source[-4:]:
            data = mgr.get_rosbag(source, include_only=include_only, exclude=exclude)
            if data is None:
                print("Error in file")
                exit(1)
        else: 
            #redundant check
            print(f"{bcolors.FAIL}Error{bcolors.ENDC} Unrecognized filetype < {source} >")
        #we now have the data, start to write the data
        if args.output:
            #if we are given a desired output directory, we take it with no modifications, only checking so see if a slash is included in the path provided
            output_directory = args.output if output_directory[-1] == os.path.sep else args.output+os.path.sep
        else:
            #if we are not, the suggested preferred method is to make a new directory next to the target file, in this directory we dump all the produced files
            #given path/to/file.alog, we would make path/to/file_mwmgr/[data_csvs/[topic1.csv, ...], data.json, ...]
            src_path = data["info"]["logfile"][:].split(os.path.sep)
            if len(src_path) > 1:
                src_path.pop()
            src_path = os.path.sep.join(src_path)
            #given path/to/file.alog, we would make path/to/file_mwmgr/[data_csvs/[topic1.csv, ...], data.json, ...]
            output_directory = src_path+f"{os.path.sep}{src_path.split(os.path.sep)[-1]}_mwmgr/"
        try:
            #try to make the full path
            os.makedirs(output_directory)
        except FileExistsError:
            print("Directory already exists, overwriting existing files")
            ans = "y"
            if mgr.warnings:
                ans = input("Do you wish to continue with overwriting any existing files in this directory? (y/n)")
            if ans[0].lower() == 'n':
                print(f"\t> Resolution: {bcolors.OKBLUE}Shutting down and not processing conversion request{bcolors.OKBLUE}.")
                exit(0)
            else:
                print(f"\t> Resolution: {bcolors.OKBLUE}Overwriting data in < {output_directory} >{bcolors.OKBLUE}")
        if '.alog' == source[-5:]:
            if 'csv' in output_types:
                csv_path = output_directory+data["info"]["alias"]+"_alog_csvs"
                mgr.alog_2_csv(data, csv_path, ignore_src=False, force_write=True)
            if 'json' in output_types:
                mgr.dump_json(data, output_directory+os.path.sep+data["info"]["alias"]+"_alog")
        elif '._moos' == source[-6:]:
            raise(NotImplementedError)
        elif '.bag' == source[-4:]:
            if 'csv' in output_types:
                mgr.rosbag_2_csv(data, output_directory+os.path.sep+data["info"]["alias"]+"_ros_csvs", force_write=True)
            if 'json' in output_types:
                mgr.dump_json(data, output_directory+os.path.sep+data["info"]["alias"]+"_ros")

    elif args.directory != None and args.source == None:
        #Interaction 4 - User wants to convert a whole directory
        src_directory = args.directory 
        dest_directory = output_directory
        if os.path.exists(src_directory):
            if os.path.isdir(src_directory):
                mgr.convert_directory(src_directory, dest_directory, include_only=include_only, exclude=exclude)
            else:
                print(f"Source directory does not exist:\n\t- < {src_directory} >")
        else:
            print(f"Path does not exist:\n\t- < {src_directory} >")
    elif args.templates:
        #generate examples for topic mappings, inclusion/exclusions, and a shell script for converting a directory
        with open("mdm_ix.cfg", 'w') as f:
            f.write("Example %mdm topic inclusion/exclusion configuration file\
                \r%The example topics come with an implication that this is for exclusion\
                \r%Can be used for both MOOS and ROS topic names. Generally use different conventions so double matchings are not a problem.\
                \r%Configuration type for mdm. Either TOPIC_IX or MOOS_TOPIC_MAPPING\
                \rCFGT=TOPIC_IX\
                \r\n\
                \r%expected configuration is agnostic to MOOS or ROS or how either is used, only matters how it is passed to the program\
                \r\n\
                \r%MOOS TOPICS \
                \r%%Some suggested topics to ignore which are included in alog files \
                \rUMAC_551_STATUS \
                \rPREALM_STATUS \
                \rREALMCAST_CHANNELS \
                \rLOGGER_DIRECTORY \
                \rAPPCAST_REQ_SHORESIDE \
                \rDB_EVENT \
                \rUMAC_9186_STATUS \
                \rPLOGGER_STATUS \
                \rREGION_INFO \
                \rAPPCAST_REQ \
                \rAPPCAST_REQ_ALL \
                \rPREALM_ITER_GAP \
                \rPREALM_ITER_LEN \
                \rAPPCAST DB_TIME \
                \rDB_UPTIME \
                \rDB_CLIENTS \
                \rDB_QOS \
                \rPSHARE_INPUT_SUMMARY \
                \rPMARINEVIEWER_STATUS \
                \rHELM_MAP_CLEAR \
                \rPMV_CONNECT \
                \rPSHARE_STATUS \
                \rPMARINEVIEWER_ITER_GAP \
                \rPMARINEVIEWER_ITER_LEN \
                \rPSHARE_OUTPUT_SUMMARY \
                \rUFLDANEMO_ITER_LEN \
                \rPHI_HOST_IP \
                \rPHI_HOST_INFO \
                \rVIEW_ARROW \
                \rPHOSTINFO_STATUS \
                \rPHI_HOST_IP_ALL \
                \rPHI_HOST_IP_VERBOSE \
                \rPHI_HOST_PORT_DB \
                \rUFLDSHOREBROKER_STATUS \
                \rUFLDSHOREBROKER_ITER_LEN \
                \rPHOSTINFO_ITER_LEN \
                \rPHOSTINFO_ITER_GAP \
                \rNODE_BROKER_PING \
                \rPSHARE_CMD \
                \rNODE_BROKER_VACK \
                \rNODE_REPORT \
                \rSTATION_ALL \
                \rMVIEWER_LCLICK \
                \rMOOS_MANUAL_OVERRIDE_ALL \
                \rRETURN_ALL \
                \rVIEW_SEGLIST \
                \rVIEW_POINT \
                \rPROC_WATCH_FULL_SUMMARY \
                \r\n\
                \r%ROS TOPICS \
                \r%%These topics by default are always excluded from a search since they are buggy (regardless if they are included here or asked for)\
                \r/rosout\
                \r/rosout_agg \
                \r/diagnostics \
                \r/diagnostics_agg \
                \r/diagnostics_toplevel_state \
                ".replace('  ', ''))

            with open("mdm_moos_topic_mapping.cfg", 'w') as f:
                f.write("Example %mdm topic topic / parsing algorithm pairing configuration file\
                \r%The example topics below are related to the provided dataset for testing installation\
                \r%Algorithm list\
                \r% - CSP_SIMPLE = Comma Separated Pairs i.e. \"variable1=value1,variable2=value2,variable3=value3\"\
                \r% - CSP_NESTED = Comma Separated Pairs with nested lists i.e. \"variable1=value1,variable2=value2,variable3=\"VAL1,VAL2,VAL3,VAL4\"\"\
                \r% - NUMBER = Integer or float type\
                \r% - BOOLEAN = Boolean value, i.e. True, False, true, false, TRUE, FALSE. All will reduce to true and false which is JSON standard\
                \r%If a message is just a string and should be maintained as-is, put nothing. Existing commas in the message get overwritten with pipes so the message can remain in a single cell of a csv file.\
                \r\
                \rCFGT=MOOS_TOPIC_MAPPING\
                \r\
                \rWIND_CONDITIONS = CSP_SIMPLE\
                \rWIND_CONDITIONS_GT = CSP_SIMPLE\
                \rWIND_DIR_MOD = NUMBER \
                \rUFLDANEMO_ITER_GAP = NUMBER\
                \rUFLDANEMO_ITER_LEN = NUMBER\
                \rUFLDANEMO_STATUS = CSP_NESTED\
                \r\
                \r%Standard moos topics are pre-assigned within the program\
                ".replace('  ', ''))
            bs = lambda n: ''.join(['\b' for elem in range(0,n)]) 
            with open("mdm_directory_conversion.sh", 'wb') as f:
                f.write(bytearray(f"#!/bin/bash\r\n#Example directory conversion script\
                \rpython3 -m mdm -d data_directory/ \\\
                \n    -o destination_directory \\\
                \n    -x mw_ix.cfg \\\
                \n    --moos \\\
                \n    --topic_mapping mw_moos_topic_mapping.cfg \
                ".replace("                ", ''), 'UTF-8'))

        pass 
    else:
        print("The CLI has been misused. Try passing -e for examples.")
        exit(0)
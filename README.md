# MWDataMgr

This is an in-development Python utility for converting MOOS log files and ROS bag files into CSV files for post processing analysis. See testing space for use cases. 

This program parses MOOS alog files and ROS bags and converts them to CSV and JSON files for post-processing analysis. 

The intent of this program is to as-realistically as possible minimize and abstract away all the parsing and programming necessary for parsing MOOS and ROS data. For MOOS, topic data consists of strings of a user defined pattern which should generally follow convention. Since the type cannot 100% be inferred, I have it such that you assign an algorithm to an unknown topic if you would like it pre-parsed, alternatively, you can provide nothing, and all commas in the message will be replaced with pipes so it can be opened as a CSV in any other data analysis software and parse in post-processing. 

For help, you can clone the repo, go into the testing space, and download the provided data and make sure your installation runs correctly. If you check out the unit tests, there are descriptions for the different features incorporated. Once you have it downloaded locally, you can also get started with: 
```
$ python3 MWDataMgr -h # to get help
$ python3 MWDataMgr -e # to get examples
$ python3 MWDataMgr --templates # to generate template files
```

A talked through example. 

```
$ python3 ../MWDataMgr.py -d data/ \
    -o test_7 \
    -i directory_search_ix.cfg \
    --moos \
    --topic_mapping moos_topic_mapping.cfg
```

Convert directory called _data_ and name the output directory _test\_7_. All other subfolders maintain the original structure. I pass -i and a *ix.cfg text file which has a list of topics I want to include. You can also do -x for exclude. I pass --moos flag for moos specific arguments, where there is a topic mapping file where I have a topic and assigned algorithm for a unique parsing strategy. 

Simply list the topics in a cfg file specified as a TOPIC_IX config type. %'s are comments in the file and will be ignored

```
​directory_search_ix.cfg
--
%MOOS topic inclusion/exclusion configuration file
CFGT=TOPIC_IX
 
%expected configuration is agnostic to MOOS or ROS or how either is used, only matters how it is passed to the program
 
%MOOS TOPICS
 
WIND_CONDITIONS
WIND_CONDITIONS_GT 
WIND_DIR_MOD
PMARINEVIEWER_PID
UFLDANEMO_ITER_GAP
UFLDANEMO_STATUS
 
%ROS TOPICS
/vessel_hdng_raw
/humidity
/battery_voltage
/air_temperature
/cog 
/wind_info 
/water_speed
/water_temperature
/pressure
--
```

To assign an algorithm to a topic, you can reference the supported types and the examples and assign it to a topic

```
moos_topic_mapping.cfg
--
%MOOS TOPIC MAPPING FILE
%CSP_SIMPLE = Comma Separated Pairs i.e. "variable1=value1,variable2=value2,variable3=value3"
%CSP_NESTED = Comma Separated Pairs with nested lists i.e. "variable1=value1,variable2=value2,variable3="VAL1,VAL2,VAL3,VAL4""
%NUMBER = Integer or float type
%BOOLEAN = Boolean value, i.e. True, False, true, false, TRUE, FALSE. All will reduce to true and false which is JSON standard
%If a message is just a string and should be maintained as-is, put nothing
 
CFGT=MOOS_TOPIC_MAPPING
 
WIND_CONDITIONS = CSP_SIMPLE
WIND_CONDITIONS_GT = CSP_SIMPLE
WIND_DIR_MOD = NUMBER 
UFLDANEMO_ITER_GAP = NUMBER
UFLDANEMO_ITER_LEN = NUMBER
UFLDANEMO_STATUS = CSP_NESTED
--
```

I was also working on a universal ROS-message message parser which closely works decently well. It is at least consistent and you can clean it up later if it doesn't work on its first shot. 

If you are working locally and there is an parsing strategy not available here, you can add the function to the class, and register it in one line of code and it should work automatically without any additional modification. 

Within the constructor you will find: 

```
self.strategy_aliases = {"NUMBER":self.number_msg,
        "CSP_SIMPLE":self.csp_simple_msg,
        "CSP_NESTED":self.csp_nested_sequence_msg,
        "BOOL":self.boolean_msg,
        "YOURTYPE":self.your_type_msg}
```

Where you can add a parsing function with the same parameter/return template as the other functions, and when you setup a topic mapping file it should automatically link your topic / algorithm type, and the algorithm within the class, during processing. 

I hope you find this useful - if you notice any bugs, or have an idea for what else can be added, you can send me an email at **raymond(dot)turrisi(at)gmail(dot)com**. If you end up using it and find it useful, I'd also appreciate the email knowing where the program finds itself and whose benefitting from it. 

If someone is screaming with ambition and has ideas for where else this can go, I'm also open to collaboration as long as the scope is appropriate. 


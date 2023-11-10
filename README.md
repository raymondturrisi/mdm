# Middleware Data Manager

---

## Overview
This is an in-development Python utility for converting MOOS log files and ROS bag files into CSV files for post processing analysis. See testing space for use cases. It is only developed on an as-needed basis, and collaboration may be welcome if it makes sense. 

This program parses MOOS alog files and ROS bags and converts them to CSV and JSON files for post-processing analysis. It is intended to make your life at the minimum easier, and not ask much of the user, with the simple goal of homogenizing the representation and organization of data to make it more portable for a variety of other applications - whether it is Python, MATLAB, Excel, or beyond. It works best on MOOS alog files, and the script may hang, depending on your OS, when it imports the rosbag library - if you don't have it installed, it will tell you precisely what to run. 

Middleware Data Manager (mdm) tries to minimize and abstract away all the parsing and programming necessary for parsing MOOS and ROS data. For MOOS, topic data consists of strings of a user defined pattern which should generally follow convention. Since the type cannot 100% be inferred, I have it such that you assign an algorithm to an unknown topic if you would like it pre-parsed. __Alternatively__, you can provide nothing, and all commas in the message will be replaced with pipes so it can be opened as a CSV in any other data analysis software and parse in post-processing. 

## Getting Started
You can download it and make sure it is installed correctly by running the following: 
```
$ pip3 install mdm
$ python3 -m mdm -h # to get help
$ python3 -m mdm -e # to get examples
```

It'll will be most clear if you run the `m2_berta` mission provided in a moos-ivp installation, move the log files into a directory, and run the following: 

```
$ cd path/to/moos-ivp/ivp/missions/m2_berta
```

Now by personal preference - not a general requirement for use but what is demonstrated herein - I would also change the pLogger configuration block in `plug_pLogger.moos` and `meta_shoreside.moos` to write log files into a specific log directory. 
Note: All I changed/added was `PATH = ./logs/`. 

```
    .
    .
    .
ProcessConfig = pLogger
{
  AppTick 	= 10
  CommsTick 	= 10
  
  File		= LOG_%(VNAME)
  PATH		= ./logs
  SyncLog 	= true @ 0.2
  AsyncLog 	= true
  FileTimeStamp = true
    .
    .
    .
}
```

Make the directory for pLogger

```
$mkdir logs
```

run m2_berta

```
$ python3 -m mdm --templates # to generate template files, which you change for each project
$ chmod +x mdm_directory_conversion.sh # make the wrapper script executable
```

Update the shell script to point to your logging directory

``` bash
python3 -m mdm -d logs/ \
    -o mdm_logs \
    -x mdm_ix.cfg \
    --moos \
    --topic_mapping mdm_moos_topic_mapping.cfg 
```

Now you can run the shell script as-is, however if you would like to use more powerfully, you can do some of the following: 
- Pass a 'type' argument, to output 'json' or 'csv' or both

- You can bundle your data per mission under the log directory, such that all the data in a multi-agent mission appears in the same JSON file. The structure of your logs directory is preserved when moved over to an output directory, and JSON structured data exists at each folder level. 

- You can update the configuration files to include relevant variables and a correct pre-processing algorithm to extract most of the data for you, and you can also exclude variables you know you don't need, or include only the variables you do care about. The context for how it is used depends on whether you pass a `-x` or `-i` argument which is immediately followed by the configuration file. 

For more context, you can also poke around the 'testing_space' folder in the repository, and read over the unit tests file I provided. The file itself is out of date, but it is still useful. 

## ROS

I was also working on a universal ROS-message message parser which works decently well. It is at least consistent and you can clean it up later if it doesn't work on its first shot. It worked for all the data which I observed/tested it with. If you are using it on ROS Bag files you may have some dependency issues which there is documentation to help you work through, but bear in mind, this wasn't primarily made for ROS. 

## Other

The scope for how this is intended to be used is evolving. Currently the most generic case is supposed, but later, when the time is right, it will also be importable to other Python programs, so data can be analyzed on the fly with Pandas or nested dictionaries, without writing any new files. 

(Not entirely relevant for the current published version)

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

## Contact
I hope you find this useful - if you notice any bugs, or have an idea for what else can be added, you can send me an email at **rturrisi(at)mit(dot)edu**. If you end up using it and find it useful, I'd also appreciate the email knowing where the program finds itself and whose benefitting from it. 

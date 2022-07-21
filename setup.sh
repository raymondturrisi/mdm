#!/bin/bash

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt install libyaml-dev 
elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install libyaml 
else
    echo "Not supported or tested"
    exit 0
fi

pip3 install pyyaml
pip3 install --extra-index-url https://rospypi.github.io/simple/ rosbag

printf "\e[32mPython printing an error saying it failed to load an extension for LZ4 support is fine\e[0m\n"
python3 -c "import yaml; yaml.CLoader" 

python3 -c "import rosbag"


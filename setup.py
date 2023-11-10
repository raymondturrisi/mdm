from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '0.0.143'
DESCRIPTION = 'A middleware data manager for at least MOOS-IvP and ROS'
LONG_DESCRIPTION = 'A package which provides configurable data extraction and data management tools from command line, within a Python application, or within a notebook-like environment.'

# Setting up
setup(
    name="mdm",
    version=VERSION,
    author="Raymond Turrisi",
    author_email="<rturrisi@mit.edu>",
    description=DESCRIPTION,
    license='MIT',
    url='https://github.com/raymondturrisi/mdm',
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    #install_requires=['rosbag @ https://rospypi.github.io/simple/rosbag'],
    entry_points={
        'console_scripts':[
            'mdm = mdm.mdm:main'
        ]
    },
    package_data={
        'mdm': ['templates/*'],
        'mdm': ['examples/*'],
    },
    keywords=['python', 'moos', 'moos-ivp', 'ros', 'ros2',  'data management', 'data extraction', 'csv', 'json'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)

import sys
import argparse
import configparser

parser = argparse.ArgumentParser(prog=
                                 'Setup configuration file',
                                 description=
                                 "Please enter all arguments in one command. "
                                 "Reset arguments by running this program again."
                                 )
parser.add_argument('-e', '--exec_path', help='Set chromedriver executable full file path')
parser.add_argument('-r', '--root_path', help="Set semester's download full file path")
parser.add_argument('-u', '--username', help='Set username')
parser.add_argument('-p', '--password', help='Set password')
args = parser.parse_args()

all_arguments_specified = len(sys.argv) == 9
assert all_arguments_specified, 'All arguments are required for the setup'

config = configparser.ConfigParser()
config['SETTINGS'] = {'EXEC_PATH': args.exec_path,
                      'ROOT_PATH': args.root_path,
                      'USERNAME': args.username,
                      'PASSWORD': args.password}
with open('config.ini', 'w') as f:
    config.write(f)

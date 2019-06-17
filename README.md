# WES_client
Python client for WES

This work is based on https://github.com/elixir-europe/WES-cli 

Installation
============

Requires e.g. python3 and bravado.

The token file name is hardcoded currently. It could be fetched somewhere else than by this code, which won't work if you do not have fixed the client id and secret in auth.py.  
auth.py can be compiled as a binary to hide (?) secret string. 
pyinstaller --onefile auth.py 
create a auth binary.

In the demonstrator was registered a test service to ELIXIR AAI. 

Configure email address to the generic configuration file. 


Usage 
=====

See:
run.sh -h

Here are couple of CWL pipeline examples included.
abc1.yml does not have URLs configured so it won't work.

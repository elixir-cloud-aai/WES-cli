# WES_client
Python client for WES

This work is based on https://github.com/elixir-europe/WES-cli 
Requires e.g. python3 and bravado.

The token file name is hardcoded currently. It could be fetched somewhere else than by this code, which won't work if you do not have fixed the client id and secret in auth.py.  
auth.py can be compiled as a binary to hide (?) secret string. 
This was based on ELIXIR AAI OATH2 client test permissions. 

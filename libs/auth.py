# #!/usr/bin/python3.6
import os
import platform
import time
from collections import namedtuple
import getopt
import requests
import qrcode
import sys

def get_auth_credentials():
    """Make request to authentication server and retrieve remote authentication credentials."""
    client_id='put client id here'
    client_s='put client secret here' 
    url_auth='https://login.elixir-czech.org/oidc/devicecode'

    # Make a request to authentication server
    response = requests.post(url_auth,
                             auth=(client_id, client_s),
                             data={'client_id': client_id, 'scope':'openid groupNames'}) 
    #config.claims})
    if 'error' in response.json():
        print({response.json()["error"]} +':'+ {response.json()["error_description"]})
    return response.json()


def remote_auth_instructions(credentials):
    """Print remote authentication instructions for user."""

    # Extract remote authentication address, or construct it if complete uri is not available
    if 'verification_uri_complete' in credentials:
        url = credentials['verification_uri_complete']
    elif 'verification_uri' and 'user_code' in credentials:
        url = f'{credentials["verification_uri"]}?user_code={credentials["user_code"]}'
    else:
        print('Authentication server response did not contain required items.')
        print(credentials)

    # Print remote authentication instructions
    print(" Please authenticate with another device, for example your phone or computer, to gain access to permitted datasets.")  
    print(" If you cannot read the QR code with a smartphone, you may use the link below: ")
    print("URL: "+url)
    print(qr_code(url))


def poll_for_token(credentials):
    device_code = str(credentials['device_code'])
    timeout = 120
    interval = 1

    url_token='https://login.elixir-czech.org/oidc/token'
    client_id='put client id here'
    client_s='put client secret here'

    while True:
        time.sleep(interval)
        timeout -= interval

        # Request token from authentication server
        token_response = requests.post(url_token,
                                       auth=(client_id, client_s),
                                       data={'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                                             'device_code': device_code,
                                             'client_id': client_id,
                                             'scope': 'openid groupNames'
                                            })

        if 'error' in token_response.json():
            if token_response.json()['error'] == 'authorization_pending':
                # User hasn't authenticated yet, wait for some time
                pass
            elif token_response.json()['error'] in ['slow_down', 'buffering']:
                # We are pinging auth server too much, ping more seldom
                interval += 1
                pass
            else:
                print(f'Error({token_response.json()["error"]}): {token_response.json()["error_description"]}')
                print('Authentication was terminated.')
                break
        else:
            break

        if timeout < 0:
            print('Authentication timed out, please try again.')
            print(f'Error({token_response.json()["error"]}): {token_response.json()["error_description"]}.')
            print('Authentication was terminated.')
            break

    return token_response.json()


def qr_code(url):
    """Draw QR code."""

    # Determine user operating system
    if platform.system() == "Windows":
        white_block = '▇'
        black_block = '  '
        new_line = '\n'
    else:
        white_block = '\033[0;37;47m  '
        black_block = '\033[0;37;40m  '
        new_line = '\033[0m\n'

    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make()

    # Draw top white border
    output = white_block*(qr.modules_count+2) + new_line

    # Fill QR code area
    for mn in qr.modules:
        output += white_block
        for m in mn:
            if m:
                output += black_block
            else:
                output += white_block
        output += white_block + new_line
    
    # Draw bottom white border
    output += white_block*(qr.modules_count+2) + new_line

    return output


def make_userinfo_request(token_response):
    userinfo_endpoint='https://login.elixir-czech.org/oidc/userinfo'

    userinfo_response = requests.post(userinfo_endpoint,
                                       data={},
                                       headers={
                                         'Authorization': 'Bearer %s' % str(token_response['access_token'])
                                       })

    if 'error' in userinfo_response.json():
        print("error")
        print (userinfo_response.json()['error'])
        print (userinfo_response.json()['error_description'])

    return userinfo_response.json()

def save_token(token):
    """Save access token to file."""
    with open('access_token.txt', 'w') as f:
        f.write(token)
    os.chmod('access_token.txt',0o600)    
    print("The Access Token is saved into access_token.txt file.")
    print("You can delete it when not needed anymore with rm or -d option of this script.\n\n")
    return 

def deleteToken():
    if (os.path.exists('access_token.txt')):
       os.unlink('access_token.txt')
    else:  
       print("Cannot remove access_token.txt. Perhaps not in this directory?")
    return

def load_token():
    """Save access token to file."""
    Debug = False

    if Debug: print('Look for saved access tokens.')

    try:
        file_age = os.stat('access_token.txt').st_mtime
        # for this service 6 h
        if time.time() - file_age < 21500:
           # Stored access token file is less than one hour old, load the token
           with open('access_token.txt', 'r') as f:
                if Debug: print('Found a saved access token. Skipping authentication.')
                return f.read()
        else:
           # EGA Data API doesn't allow tokens that are older than one hour
            if Debug: print('Found a saved access token, but it was over an hour old. Proceed with authentication.')
            return ''
    except FileNotFoundError as e:
        if Debug: print('No fresh saved access tokens found, proceed with authentication.')



def getToken():
    """Start remote authentication workflow."""
    Debug = False
    # check if we have a valid token
    token = load_token()
    if token: 
       # return token
       return
    credentials = get_auth_credentials()
    remote_auth_instructions(credentials)
    token_response = poll_for_token(credentials)
     
    if 'access_token' in token_response:

       if Debug is True:
          print(f'Access Token: {token_response.get("access_token")}')  
          userinfo = make_userinfo_request(token_response)
          print("user info: ")
          for key,val in userinfo.items():
            print (key, "=>", val)
       save_token(token_response.get("access_token"))
       #return token_response.get("access_token")
       return 
    else:
        print('Error: Authentication response did not contain an access token.')
        return 

def usage():
   print("Usage: ")
   print("Get token : -g or --getToken")
   print("Delete token: -d or --deleteToken")
   return
 
def main():
   try:
      (opts, args) = getopt.getopt(sys.argv[1:], 'hgd',['help','getToken','deleteToken'])
   #raised whenever an option (which requires a value) is passed without a value.
   except getopt.GetoptError as err:
      print(err)
      sys.exit(2)
   if len(opts) != 0:
      for (o, a) in opts:
         if o in ('-h', '--help'):
            usage()
            sys.exit()
         elif o in ('-g', '--getToken'):     
            getToken()
            sys.exit(0)
         elif o in ('-d', '--deleteToken'):
            deleteToken()
            sys.exit()
         else: 
            usage()
            sys.exit(2)
   else: 
      usage()
      sys.exit(2)

if __name__ == '__main__':
   main()


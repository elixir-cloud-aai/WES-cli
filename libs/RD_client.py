#import urllib3
#urllib3.disable_warnings()
# Required to create a new Requests 'http_client' instance
#from bravado.requests_client import RequestsClient
# Required to create a Bravado SwaggerClient instance
#from bravado_core.spec import Spec
#from bravado.client import SwaggerClient,SwaggerFormat
import os.path
from wes_client import init_client
from wes_client import get_service_info
from wes_client import get_runs
from wes_client import get_run_log
from wes_client import get_run_status
from wes_client import post_run
from wes_client import post_cancel_run
import getopt
import sys, traceback
import yaml
import json
import time
from subprocess import PIPE, run
from configparser import ConfigParser
from collections import namedtuple
from send_notice import send_email

def parse_config_file(path):

    """Parse workflow configuration file."""
    try: 
      config = ConfigParser()
      config.read(path)
      config_vars = {
        'workflow_type': config.get('workflow', 'workflow_type'),
        'workflow_type_version': config.get('workflow', 'workflow_type_version'),
        'workflow_url': config.get('workflow', 'workflow_url'),
        'workflow_engine_parameters': config.get('workflow', 'workflow_engine_parameters'),
        'workflow_attachment': config.get('workflow', 'workflow_attachment'),
        'inputs_yml_file' : config.get('workflow','inputs_yml_file'),
      }
    except Exception:
      traceback.print_exc(file.sys.stdout)
      print("Cannot read the workflow configuration file given as a parameer for -s.")
      sys.exit(2)

    return namedtuple("Config", config_vars.keys())(*config_vars.values())


def parse_generic_config_file(path):
    try: 
        config = ConfigParser()
        config.read(path)
        config_vars = {
           'receiver_email' : config.get('workflow','receiver_email')
        }
    except Exception:
        traceback.print_exc(file.sys.stdout)
        print("Cannot read the generic configuration file")
        sys.exit(2)
    return  namedtuple("Config", config_vars.keys())(*config_vars.values()) 
 
def submitJob(client, token, workflow_parameters_file):

    config = parse_config_file(workflow_parameters_file)

    workflow_inputs = None
    with open(config.inputs_yml_file) as yaml_in:
       yaml_object = yaml.safe_load(yaml_in) # yaml_object will be a list or a dict
       workflow_inputs = json.dumps(yaml_object)
    run_id = post_run(
      client=client,
      token=token,
      workflow_params=workflow_inputs,
      workflow_type=config.workflow_type,
      workflow_type_version=config.workflow_type_version,
      workflow_url=config.workflow_url
    )

    print ("The Job is submitted with ID: ")
    print(run_id)
    print("You can query the status with  -i <id> with this script.")
    print("run.sh -i " + run_id.get('run_id') )
    print("or you can start the script polling the job and sending email when finished.")
    print("run.sh -w  " + run_id.get('run_id') )
    print("to view execution logs:")
    print("run.sh -l " + run_id.get('run_id') )
    return 

def getServiceInfo(client,token):
    service_info = get_service_info(client=client,token=token)
    print("Service info:")
    print(service_info)
    return 

def getJobLog(client,token,jobid):
    job_log = get_run_log(client=client,token=token, run_id=jobid)
    print("Job log:")
    yaml.dump(job_log.get('run_log'),sys.stdout)  
    return 

def getRunStatus(client,token,jobid):
    run_status = get_run_status(client=client,token=token, run_id=jobid)
    print("Run status: "+ run_status.get('state'))
    return 

def pollJob(client,token,jobid,workflow_parameters_file):
    timeout = 11500 # ca. 6 h
    interval = 60
    list_running_states=['PENDING','INITIALIZNIG','RUNNING']
    run_status=None
    
    while True:
        run_status = get_run_status(client=client,token=token, run_id=jobid)
        if not run_status.get('state') in list_running_states:
           config = parse_generic_config_file(workflow_parameters_file)
           send_email(config.receiver_email,jobid,run_status.get('state'))
           break
        if (timeout<0):
           print("Timeout in polling.")
           print("Your token has probably expired as well")
           print("It might be that the workflow lasts longer than token?")
           break
        time.sleep(interval)
        timeout -= interval

    print("Run status: "+str(run_status))
    return 

def getToken():
    # this command does not return token string 
    os.system('auth -g')
    try:
      with open('access_token.txt', 'r') as f:
        return f.read()
    except FileNotFoundError as e:
      print("access_token.txt was not found.")


#print script usage
def usage():
    print("Submission: -s <workflow_configuration_file> or --submit <workflow_configuration_file> ")
    print("Job status: -i <id> or --jobid=<id>  (to check if job is finished") 
    print("Log of a job: -l <id> or --logid=<id> (to look possible failure reasons)") 
    print("Poll job id: -w <id> or --pollid=<id> (to poll job status every minute and send email when finished.")
    print("Service info: -t or --serviceinfo (usually not needed)")
    return 
 
def main():
    Debug = False

    if Debug: print("Getting options")
    try:
       
        (opts, args) = getopt.getopt(sys.argv[1:], 'hi:s:l:tw:d',['help','jobid=','logid=','submit','serviceinfo','pollid=','delete_token'])  
    #raised whenever an option (which requires a value) is passed without a value.
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)

    jobid = None
    pollid = None
    yml_file = None
    serviceInfo=False
    submit = False
    logid = None
    #check if any options were passed
    if len(opts) != 0:
        # loop over opts: Ex, [(a,10), (b,20)] => <list>
        for (o, a) in opts:
            if o in ('-h', '--help'):
                usage()
                sys.exit(0)
            elif o in ('-i', '--jobid'):
                jobid = a
                break
            elif o in ('-l', '--log_id'):
                logid = a
                break 
            elif o in ('-w', '--pollid'):
                pollid = a
                break
            elif o in ('-s', '--submit'):
                submit=True
                workflow_parameters_file = a
                if not os.path.isfile(a):
                   print ("The given parameter for -s is not a file.")
                   sys.exit(2)
            elif o in ('-t', '--serviceinfo'):
                serviceInfo = True
                break
            elif o in ('-d', '--delete_token'):
                deleteToken()
                sys.exit(0)
            else:
                #none of the acceptable options were passed
                usage()
                sys.exit(2)
    else:
        #no options were passed
        usage()
        sys.exit(2)

    token = ''
    token = getToken()
    if len(str(token)) < 10:
       sys.exit(2)
    else: 
       token = "Bearer "+token

    WES_URL='http://193.167.189.73:7777/ga4gh/wes/v1/swagger.json'

    if Debug: print("Init client")

    client = init_client(url=WES_URL,ssl_verify=True, use_models=False)

    if serviceInfo:
       getServiceInfo(client,token)
       sys.exit(0)
    if jobid:
       getRunStatus(client,token,jobid)
       sys.exit(0)
    if logid:
       getJobLog(client,token,logid)
       sys.exit(0)
    if pollid:
       workflow_parameters_file='generic_workflow.cfg'
       pollJob(client,token,pollid,workflow_parameters_file)
       sys.exit(0)
    if submit:
       submitJob(client,token,workflow_parameters_file)
    else:
       usage()
       sys.exit(2)
 
if __name__ == '__main__':
    main()

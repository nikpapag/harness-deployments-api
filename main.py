import math
import os
import zipfile
from logging.config import dictConfig
from logging.handlers import SysLogHandler
from zipfile import ZipFile
from workflow import Workflow
from pipeline import Pipeline
from terraform import Terraform, TerraformPipeline
import requests
import json
import logging
import datetime
import time
import sys
import argparse
import shutil


running_directory='./'
log_path='./'


#Get all command line arguments
full_cmd_arguments=sys.argv

argument_list= full_cmd_arguments[1:]

parser = argparse.ArgumentParser()
parser.add_argument('--account', help='Harness account id')
parser.add_argument('--apiKey', help='Harness api key')
parser.add_argument('--userGroup', help='Harness user group ')
parser.add_argument('--runtime', help='Runtime directory defaults to ./', default='./')
args = vars(parser.parse_args())

accountId=args['account']
api_key=args['apiKey']
userGroupId=args['userGroup']
running_directory=args['runtime']


current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
execution_directory= os.path.join(running_directory,"harness-execution/","deployments-"+current_time)
download_path= os.path.join(execution_directory,"execution.zip")
logs_directory=os.path.join(log_path,"harness-execution/","deployments-"+current_time,"logs")
archive_directory=os.path.join(running_directory,"harness-execution","archive")
print(archive_directory)


time_now= time.time()
time_end_hour = math.floor(time_now/3600)*3600*1000
time_start_hour = time_end_hour-3600000

try:
    def fast_scandir(dirname):
        subfolders = [f.path for f in os.scandir(dirname) if f.is_dir()]
        return subfolders


    subfolders = fast_scandir(os.path.join(running_directory, 'harness-execution'))
    def zipdir(path, ziph):
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:
                ziph.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file),
                                           os.path.join(path, '..')))
    for dir in subfolders:
        if 'deployment' in dir:
            zipf = zipfile.ZipFile(dir+'.zip', 'w', zipfile.ZIP_DEFLATED)
            zipdir(archive_directory+'/', zipf)
            zipf.close()
            shutil.rmtree(dir)
except:
    pass


try:
    os.makedirs(logs_directory)
except:
    # directory already exists
    pass

try:
    os.makedirs(execution_directory)
except:
    # directory already exists
    pass



logger = logging.getLogger(__name__)
DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
}
def configure_logging(logfile_path):
    dictConfig(DEFAULT_LOGGING)
    default_formatter = logging.Formatter(
        " %(message)s",
        "%d/%m/%Y %H:%M:%S")
    file_handler = logging.handlers.RotatingFileHandler(logfile_path, maxBytes=(1048576*5), backupCount=7)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(default_formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    console_handler.setFormatter(default_formatter)
    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(console_handler)

configure_logging(os.path.join(logs_directory,"execution.log"))



logger.debug("Start time:"+ str(time_start_hour)+"End time:"+str(time_end_hour))




query = """mutation ($usergroup: [String!], $apistarttime: DateTime!, $apiendtime: DateTime!){
  exportExecutions(input: {
    clientMutationId: "exporter-test"
    filters: [
      {endTime: {operator: BEFORE, value: $apiendtime }},
      {startTime: {operator: AFTER, value: $apistarttime }},
    ]
    userGroupIds: $usergroup
  }) {
    clientMutationId
    requestId
    status
    totalExecutions
    triggeredAt
    downloadLink
    expiresAt
    errorMessage
  }
}"""


variables = {'usergroup': userGroupId, 'apistarttime': time_start_hour, 'apiendtime':time_end_hour }


s = requests.session()
url = 'https://app.harness.io/gateway/api/graphql'
headers = {
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'x-api-key': api_key
}
params = { 'accountId':accountId}
r = s.post(url, headers=headers,params=params, json={'query': query,'variables': variables})
print(r.status_code)
print(r.text)
json_data = json.loads(r.text)
#Uncommend for new execution
downloadLink= str(json_data['data']['exportExecutions']['downloadLink'])



s = requests.session()
time.sleep(30)

#Delete when switching to API
downloadLink=downloadLink

#Uncommend for new execution
response = s.get(downloadLink, allow_redirects=True)
if response.status_code == 200:
    with open(download_path, 'wb') as f:
        f.write(response.content)


# Create a ZipFile Object and load sample.zip in it
with ZipFile(download_path, 'r') as zipObj:
   # Extract all the contents of zip file in different directory
   zipObj.extractall(execution_directory)



def workflowDecoder(obj):
    if 'workflow' in obj and obj['executionType'] == 'Workflow':
        return Workflow(obj['executionType'], obj['application'], obj['workflow'],obj['environment']['name'],obj['timing']['startTime'],obj['timing']['endTime'],obj['triggeredBy']['name'],obj['status'],obj['serviceInfrastructures'],obj['executionGraph'])
    return obj


def terraformDecoder(obj):
    if 'workflow' in obj and obj['executionType'] == 'Workflow':
        return Terraform(obj['executionType'], obj['application'], obj['workflow'],obj['timing']['startTime'],obj['timing']['endTime'],obj['triggeredBy']['name'],obj['status'],obj['executionGraph'])
    return obj

def terraformPipelineDecoder(obj):
    if 'pipeline' in obj and obj['executionType'] == 'Pipeline':
        return TerraformPipeline(obj['executionType'],obj['pipeline'],obj['timing']['startTime'],obj['timing']['endTime'],obj['triggeredBy']['name'],obj['status'], obj['stages'])
    return obj

def pipelineDecoder(obj):
    if 'pipeline' in obj and obj['executionType'] == 'Pipeline':
        return Pipeline(obj['executionType'],obj['pipeline'],obj['timing']['startTime'],obj['timing']['endTime'],obj['triggeredBy']['name'],obj['status'], obj['stages'])
    return obj



for subdir, dirs, files in os.walk(execution_directory):
    for file in files:
        if file.__contains__('execution.json'):
            print(os.path.join(subdir, file))
            with open(os.path.join(subdir, file)) as json_file:
                data_str =json_file.read().replace('\n', '')
                if 'TERRAFORM' in data_str and 'Pipeline' in data_str:
                    data = json.loads(data_str, object_hook=terraformPipelineDecoder)
                elif 'TERRAFORM' in data_str:
                    data = json.loads(data_str, object_hook=terraformDecoder)
                elif 'Pipeline' in data_str :
                    data = json.loads(data_str, object_hook=pipelineDecoder)
                else:
                    data = json.loads(data_str, object_hook=workflowDecoder)
                #Multiline logs for pipeline or workflow execution
                #multiline pattern: '^\['
                #match: everything after pattern
                logger.debug("[harness-log-multiline]"+str(type(data)))
                logger.debug("********************************************************")
                data.log()









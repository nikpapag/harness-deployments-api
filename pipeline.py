import logging
import sys
import json
from workflow import Workflow

a_logger = logging.getLogger(__name__)

class JiraApproval(object):
    def __init__(self,approval_name,approval_start, approval_stop,approval_url,approval_curr_status):
        self.approval_name = approval_name
        self.approval_start = approval_start
        self.approval_stop = approval_stop
        self.approval_url = approval_url
        self.approval_curr_status = approval_curr_status

    def approval_log(self):
        a_logger.debug("\t\t" + self.approval_name + "| INFO | " + " Current Status " + self.approval_curr_status )
        a_logger.debug("\t\t" + self.approval_name + "| INFO | " + " Jira URL " + self.approval_url)

class snowApproval(object):
    def __init__(self,approval_name,approval_start, approval_stop,approval_url,approval_curr_status):
        self.approval_name = approval_name
        self.approval_start = approval_start
        self.approval_stop = approval_stop
        self.approval_url = approval_url
        self.approval_curr_status = approval_curr_status

    def approval_log(self):
        a_logger.debug("\t\t" + self.approval_name + "| INFO | " + " Current Status " + self.approval_curr_status )
        a_logger.debug("\t\t" + self.approval_name + "| INFO | " + " ServiceNow ticket URL " + self.approval_url)



class ManualApproval(object):
    def __init__(self,approval_name,approval_start, approval_stop, approval_status, approved_by_name,approved_by_email):
        self.approval_name = approval_name
        self.approval_start = approval_start
        self.approval_stop = approval_stop
        self.approval_status = approval_status
        self.approved_by_name = approved_by_name
        self.approved_by_email = approved_by_email

    def approval_log(self):
        a_logger.debug("\t\t" + " Approval |" + self.approval_name + " | INFO | Current Status " + self.approval_status )
        a_logger.debug("\t\t" + " Approval |" + self.approval_name +":"+self.approval_status +" by " +self.approved_by_name + ":"+self.approved_by_email )



def workflowDecoder(obj):
    if 'workflow' in obj and obj['executionType'] == 'Workflow':
        return Workflow(obj['executionType'], obj['application'], obj['workflow'],obj['environment']['name'],obj['timing']['startTime'],obj['timing']['endTime'],"pipeline trigger",obj['status'],obj['serviceInfrastructures'],obj['executionGraph'])
    return obj

def jiraDecoder(obj):
    if "stageName" in obj and obj['approvalData']['approvalType'] == 'JIRA':
        return JiraApproval(obj['name'],obj['timing']['startTime'],obj['timing']['endTime'],obj['approvalData']['issueUrl'],obj['approvalData']['currentStatus'])
    return obj


def manualApprovalDecoder(obj):
    if "stageName" in obj and obj['approvalData']['approvalType'] == 'USER_GROUP':
        return ManualApproval(obj['name'],obj['timing']['startTime'],obj['timing']['endTime'],obj['approvalData']['status'],obj['approvalData']['approvedBy']['name'],obj['approvalData']['approvedBy']['email'])
    return obj


def snowDecoder(obj):
    if "stageName" in obj and obj['approvalData']['approvalType'] == 'SERVICENOW':
        return snowApproval(obj['name'],obj['timing']['startTime'],obj['timing']['endTime'],obj['approvalData']['ticketUrl'],obj['approvalData']['currentStatus'])
    return obj


class Pipeline(object):
    def __init__(self, executionType,pipeline_name, pipeline_start,pipeline_end,triggered_by_name ,pipeline_status, stages):
        self.executionType = executionType
        self.pipeline_start = pipeline_start
        self.pipeline_end =  pipeline_end
        self.pipeline_name= pipeline_name
        self.triggered_by_name = triggered_by_name
        self.pipeline_status = pipeline_status
        self.stages=stages

    def stages_log(self):
        for stage in self.stages:
            stageName= stage['stageName']
            stage_name= stage['name']
            stage_start = ""
            stage_end = ""
            stage_status = stage['status']
            stage_type= stage['type']

            if stage_status != "QUEUED" and stage_status != "EXPIRED":
                try:
                    stage_start = stage['timing']['startTime']
                    stage_end = stage['timing']['endTime']

                except:
                    pass

                a_logger.debug("\t"+stage_start+" Pipeline | Stage | "+stageName+" | "+stage_name+": started ")

                if stage_type== 'WORKFLOW_EXECUTION':

                    workflow_str= json.dumps(stage['workflowExecution'])
                    stage_workflow = json.loads(workflow_str, object_hook=workflowDecoder)
                    stage_workflow.log()
                elif stage_type == 'APPROVAL':
                    try:
                        stage_start = stage['timing']['startTime']
                        stage_end = stage['timing']['endTime']

                    except:
                        pass
                    approval_str= json.dumps(stage)
                    try:
                        if stage['approvalData']['approvalType'] == 'SERVICENOW':
                            data = json.loads(approval_str, object_hook=snowDecoder)
                            data.approval_log()
                        elif stage['approvalData']['approvalType'] == 'JIRA':
                            data = json.loads(approval_str, object_hook=jiraDecoder)
                            data.approval_log()
                        elif stage['approvalData']['approvalType'] == 'USER_GROUP' and stage['status'] in ('REJECTED','SUCCESS'):
                            data = json.loads(approval_str, object_hook=manualApprovalDecoder)
                            data.approval_log()
                    except:
                        pass

            a_logger.debug("\t"+stage_end +" Pipeline | Stage | "+ stage_name + " completed with status "+stage_status)

    def log(self):
        a_logger.debug(self.pipeline_start + "| INFO |"+ " Pipeline Execution | "+ self.pipeline_name+ "| Triggered By |"+ self.triggered_by_name)
        self.stages_log()
        a_logger.debug(self.pipeline_end + "| INFO |"+ " Pipeline Execution | "+self.pipeline_name+ " | Completed with Status "+ self.pipeline_status)


    def approval_log(self):
        a_logger.debug("\t\t" + self.approval_name + "| INFO | " + " Current Status " + self.approval_curr_status )
        a_logger.debug("\t\t" + self.approval_name + "| INFO | " + " Jira URL " + self.approval_url)





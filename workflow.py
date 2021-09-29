import logging
import sys

a_logger=logging.getLogger(__name__)



class Workflow(object):
    def __init__(self, executionType, application, workflow, environment_name,timing_start,timing_end,triggered_by_name,status,services,execution_graph):
        self.executionType = executionType
        self.application = application
        self.workflow = workflow
        self.environment_name = environment_name
        self.timing_start=timing_start
        self.timing_start = timing_start
        self.timing_end = timing_end
        self.triggered_by_name = triggered_by_name
        self.status = status
        self.services =services
        self.execution_graph=execution_graph


    def services_str(self):
        all_services=[li['service'] for li in self.services]
        joined_services = ",".join(all_services)
        return joined_services

    def execution_graph_str(self):
        for step in self.execution_graph:
            step_start = step['timing']['startTime']
            step_stop= step['timing']['endTime']
            step_name=step['name']
            step_type=step['type']
            step_status=step['status']
            a_logger.debug("\t\t\t" + "Workflow Step | " + step_name + " | of type: " + step_type +" started ")
            a_logger.debug("\t\t\t" + "Workflow Step | " + step_name + " | exited with status: " + step_status)


    def log(self):
        a_logger.debug("\t\t"+self.timing_start+" | Workflow Execution | "+self.workflow+" triggered by: "+ self.triggered_by_name)
        a_logger.debug("\t\t"+self.timing_start+" | "+self.workflow+" is using services: "+ self.services_str())
        self.execution_graph_str()
        a_logger.debug("\t\t"+self.timing_end + " | Workflow Execution | "+self.workflow+" Completed with Status "+ self.status)
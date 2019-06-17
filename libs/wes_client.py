import urllib3
urllib3.disable_warnings()
# Required to create a new Requests 'http_client' instance
from bravado.requests_client import RequestsClient
# Required to create a Bravado SwaggerClient instance
from bravado.client import SwaggerClient,SwaggerFormat
from bravado_core.response import OutgoingResponse, validate_response
from bravado.swagger_model import Loader

def init_client(
        url,
        disable_fallback_results=False,
        validate_responses=False,
        validate_requests=False,
        validate_swagger_spec=False,
        use_models=False,
        ssl_verify=False
):

    """Init client"""

    # Create a new Requests client instance
    http_client = RequestsClient()

    http_client.session.verify = ssl_verify
    swagger_client = SwaggerClient.from_url(
        url,
        http_client=http_client,
        config={'disable_fallback_results': disable_fallback_results,
                'validate_responses': validate_responses,
                'validate_requests': validate_requests,
                'validate_swagger_spec': validate_swagger_spec,
                'use_models': use_models,
               # 'also_return_response': True,
               # 'force_fallback_result': True 
                }
    )
    return swagger_client    



def get_service_info(client,token):

    """Get service info"""

    return client.WorkflowExecutionService.GetServiceInfo(
        _request_options={"headers": {"Authorization": token}}
    ).response(timeout=0.5, fallback_result=[]).result

def get_runs(client,token):

    """Get runs"""

    return client.WorkflowExecutionService.ListRuns(
       _request_options={"headers": {"Authorization": token}}
    ).response(timeout=0.5, fallback_result=[]).result

def get_run_log(client, token, run_id):

    """Get run id"""

    return client.WorkflowExecutionService.GetRunLog(
        _request_options={"headers": {"Authorization": token}},
        run_id=run_id
    ).response(timeout=0.5, fallback_result=[]).result


def get_run_status(client,token, run_id):

    """Get run status"""

    return client.WorkflowExecutionService.GetRunStatus(
        _request_options={"headers": {"Authorization": token}},
        run_id=run_id
    ).response(timeout=0.5, fallback_result=[]).result


def post_run(
    client,
    token,
    workflow_params,
    workflow_type,
    workflow_type_version,
    workflow_url
):
    post_run_id = client.WorkflowExecutionService.RunWorkflow(
          _request_options={"headers": {"Authorization": token}},
          workflow_params=workflow_params,
          workflow_type=workflow_type,
          workflow_type_version=workflow_type_version,
          workflow_url=workflow_url
    ).response(timeout=60, fallback_result=[]).result

    return post_run_id

def post_cancel_run(client,token, run_id):

    """Cancel run"""

    return client.WorkflowExecutionService.CancelRun(
        _request_options={"headers": {"Authorization": token}},
        run_id=run_id
    ).response(timeout=0.5, fallback_result=[]).result

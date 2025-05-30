import azure.functions as func
import azure.durable_functions as df

import json
import logging
import os
import gc
import nightcrawler.cli.main
import nightcrawler.cli.full_pipeline
from nightcrawler.context import Context
from typing import Generator

app = df.DFApp(http_auth_level=func.AuthLevel.FUNCTION)
os.environ["NIGHTCRAWLER_USE_FILE_STORAGE"] = "false"
os.environ["NIGHTCRAWLER_POSTGRES_AUTO_MIGRATE"] = "false"

# Triggers


## Scheduled: every day at 10 p.m.
@app.function_name(name="dailyUpdates")
@app.timer_trigger(schedule="0 0 22 * * *", arg_name="timer", run_on_startup=False)
@app.durable_client_input(client_name="client")
async def daily_update(timer: func.TimerRequest, client: df.DurableOrchestrationClient):
    """Triggers orchestrator from scheduled call

    Parameters
    ----------
    timer: func.TimerRequest
        Request parameters
    client: df.DurableOrchestrationClient
        Client for starting, querying, terminating and raising events to orchestration instances.
    """

    logging.warning("Daily updates triggered")
    instance_id = await client.start_new("pipeline_orchestrator", None, dict())
    logging.warning("Created instance %s", instance_id)


## HTTP
@app.route(route="orchestrators/pipeline_orchestrator")
@app.durable_client_input(client_name="client")
async def pipeline_start(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    """Triggers orchestrator from http call

    Parameters
    ----------
    req: func.HttpRequest
        Http request
    client: df.DurableOrchestrationClient
        Client for starting, querying, terminating and raising events to orchestration instances.

    Returns
    -------
    func.HttpResponse
        HttpResponse that contains useful information for checking the status of the specified instance
    """

    try:
        req_data = {x: req.params.get(x) for x in req.params.keys()}
        req_data.pop("code", None)
        logging.info(f"HTTP Trigger pipeline with params {req_data}")
        instance_id = await client.start_new("pipeline_orchestrator", None, req_data)
        logging.info(f"Trigger pipeline with instance id {instance_id}")
        response = client.create_check_status_response(req, instance_id)
    except Exception as e:
        logging.error(e, exc_info=True)
    return response


## Message Queue
@app.function_name(name="ServiceBusQueueKeyword")
@app.service_bus_queue_trigger(
    arg_name="msg", queue_name="run-keyword", connection="ServiceBus"
)
def sb_pipeline_start(msg: func.ServiceBusMessage) -> None:
    """Triggers pipeline from message in Service Bus

    Parameters
    ----------
    msg: func.ServiceBusMessage
        Message from Service Bus
    """
    logging.info("Python ServiceBus queue trigger processed message")
    try:
        req_data = json.loads(msg.get_body().decode("utf-8"))
        pipeline_wrapper(req_data)
    except Exception as e:
        logging.error(e, exc_info=True)


# Orchestrator
@app.orchestration_trigger(context_name="context")
def pipeline_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[str, str, list[str]]:
    """Orchestrate a pipeline

    Parameters
    ----------
    context: df.DurableOrchestrationContext
        Azure context for durable function

    Returns
    -------
    list[str]
        List of results for each activity
    """
    params = context.get_input()
    req_data = {x: params.get(x) for x in params.keys()}
    logging.warning("Pipeline orchestration triggered with data: %s", req_data)
    if req_data:
        status = yield context.call_activity("pipeline_work", req_data)
        return [status]

    # no params == scheduled triggers
    nc_context = Context()
    # Disable expired cases
    nc_context.disable_expired_cases()
    # Call one activity for each active keyword
    keywords = nc_context.get_today_keywords()
    tasks = [
        context.call_activity("pipeline_work", {"keyword_id": x}) for x in keywords
    ]
    results = yield context.task_all(tasks)
    return results


# Activity
@app.activity_trigger(input_name="query")
def pipeline_work(query: dict) -> str:
    """Run single activity

    Parameters
    ----------
    query: dict
        Query parameters

    Returns
    -------
    str
        Success or Failure error
    """
    try:
        pipeline_wrapper(query)
    except Exception as e:
        logging.error(e, exc_info=True)
        return f"Failed: {e}"

    return "Success"


def pipeline_wrapper(query: dict) -> None:
    """Run full pipeline on a single case or all cases

    Parameters
    ----------
    query: dict
        Query parameters

    """
    nc_context = Context()
    requests = nc_context.get_crawl_requests(**query)

    if not requests:
        logging.warning("No requests found in database for query %s", query)
        return
    for request in requests:
        logging.info(
            f"Running pipeline for keyword `{request.keyword_value}' for organization {request.organization.name}"
        )
        try:
            nightcrawler.cli.full_pipeline.handle_request(nc_context, request)
        except Exception as e:
            logging.critical(e, exc_info=True)
            nc_context.set_crawl_error(request.case_id, request.keyword_id, str(e))
        gc.collect()
    logging.info("Pipeline terminated successfully")

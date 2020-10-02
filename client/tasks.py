from __future__ import absolute_import, unicode_literals
from .celery import app
import time, logging
from celery import task
from celery.utils.log import get_task_logger
from celery.signals import after_setup_logger

logger = get_task_logger(__name__)


class RetryException(Exception):
    pass


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh = logging.FileHandler("logs.log")
    fh.setFormatter(formatter)
    logger.addHandler(fh)


logger.info("\n\n WORKER HAS BEEN STARTED")


@app.task(
    track_started=True,
    bind=True,
    task_send_sent_event=True,
    autoretry_for=(RetryException,),
    retry_kwargs={'max_retries': 5},
)
def maintask(self, timeout, name, server):
    if name == "taskfail":
        logger.warning("Retrying: " + name)
        raise RetryException
    print(
        " Executing Task: "
        + name
        + " Received from: "
        + server
        + " Timeout: "
        + str(timeout)
    )
    time.sleep(timeout)
    return (server + ":" + name)
from __future__ import absolute_import, unicode_literals

from celery import Celery

app = Celery()

# Config for celery
class Config:
    broker_url = "amqp://172.20.128.2:5672"  # rabbitmq
    result_backend = "rpc://"
    imports = "client.tasks"
    task_track_started = True


app.config_from_object(Config)

if __name__ == "__main__":
    app.start()


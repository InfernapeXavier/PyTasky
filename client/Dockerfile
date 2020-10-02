FROM python:3.8.2-buster
WORKDIR /worker
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY celery.py ./client/
COPY __init__.py ./client/
COPY tasks.py ./client/
CMD ["touch", "logs.log"]
CMD ["celery", "-A", "client", "worker", "-l", "info", "-E"]
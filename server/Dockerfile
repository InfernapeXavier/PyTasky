FROM python:3.8.2-buster
WORKDIR /server
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server.py .
COPY __init__.py .
CMD ["python", "./server.py"]
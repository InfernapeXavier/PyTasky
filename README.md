# PyTasky

### Setup

- `docker-compose up -d`

- The docker-compose file creates

  1. MongoDB instance to use as a backend for passing task
  2. RabbitMQ instance to use as a message queuing system for passing tasks from the server to the client
  3. An instance of the server program
  4. An instance of the worker

- The server doesn't activate unless the offline script file has been run
- Once the database is populated with the `tasks`, the server will start sending them one by one to the `celery` backend via `RabbitMQ` where it gets executed and the result is sent back (but not used as there's no real purpose for the result for this demo).
- The server uses the actor system via `thespian` on python to gracefully spawn 2 actors:
  1. taskSender - Sends the tasks to the client and does initial updating of the database document
  2. statusChecker - Checks the status of each task and updates the data with new information
- The actor system is quite robust and shuts itself down gracefully when all tasks are executed completely
- The server is the only one with access to the database
- The client only has access to the message queue for receiving tasks and contains the code for the actual tasks
- The offline script has been created in a way that replaces the old data when it is run so that there can be a fresh start every time

### Procedure
1. `docker-compose up -d`
2. run `creator.py`
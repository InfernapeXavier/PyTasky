from __future__ import absolute_import, unicode_literals
from celery import Celery
from celery.result import AsyncResult
from pprint import pprint
from thespian.actors import *
from pymongo import MongoClient

import time, socket


time.sleep(10)

# Configuration Object used by Celery
class Config:
    broker_url = "amqp://172.20.128.2:5672"
    result_backend = "rpc://"
    task_track_started = True

def check_for_clients():
    i = app.control.inspect()
    availability = i.ping()
    active_tasks = i.active()
    result = {
        "availability": availability,
        "active_tasks": active_tasks,
    }
    return result

# This actor keeps track of the task statuses and updates the state in the database
class statusChecker(Actor):
    def __init__(self):
        super().__init__()
        # store a set of finished taskIDs to skip over duplicates fast
        self.done = set()

    def receiveMessage(self, taskID, sender):

        if not isinstance(taskID, ActorExitRequest):
            # checks if task is already finished
            if taskID not in self.done:

                # gets the result object for the task
                result = AsyncResult(taskID, app=app)
                taskState = result.state

                client = MongoClient(
                    "mongodb://admin:secret@172.20.128.1:27017/?authSource=admin"
                )
                db = client.datastore
                collection = db.tasks

                findFilter = {"taskID": taskID}
                currVal = collection.find_one(findFilter)["state"]

                # if the state has changed, then update
                if currVal != taskState:
                    updateVals = {"$set": {"state": taskState}}
                    collection.update_one(findFilter, updateVals)

                # check if it's finished
                if taskState == "SUCCESS":
                    # track finished
                    self.done.add(taskID)
                    query = {"state": "SUCCESS"}
                    if collection.count_documents({}) == collection.count_documents(
                        query
                    ):
                        print("COMPLETED ALL TASKS")
                        # send a exit request to kill off the actor i.e. itself
                        self.send(self.myAddress, ActorExitRequest())
                else:
                    # add the task to the queue to check status later
                    self.send(self.myAddress, taskID)
                client.close()


# This actor creates the task and sends it to the message queue for the clients to pick up from
class taskSender(Actor):

    # Method to find out the host for taskID
    def find_host(self, taskID):
        active = app.control.inspect().active()
        if active:
            for host in active:
                for task in active[host]:
                    if task["id"] == taskID:
                        return host

    def receiveMessage(self, messsage, sender):
        # check if message is of the correct type
        if isinstance(messsage, dict):
            document = messsage

            # build the task
            docID = document["_id"]
            timeout = document["sleeptime"]
            name = document["taskname"]
            server = socket.gethostname()

            # send task to rabbitmq queue
            result = app.send_task("client.tasks.maintask", args=[timeout, name, server])
            taskID = result.id

            hostName = self.find_host(taskID)

            # update the database
            client = MongoClient(
                "mongodb://admin:secret@172.20.128.1:27017/?authSource=admin"
            )
            db = client.datastore
            collection = db.tasks

            updateFilter = {"_id": docID}
            updateVals = {
                "$set": {"host": hostName, "taskID": taskID, "state": result.state}
            }
            collection.update_one(updateFilter, updateVals)
            client.close()

            # spawn a child actor only if one doesn't already exist
            if not hasattr(self, "statusActor"):
                self.statusActor = self.createActor(statusChecker)
            self.send(self.statusActor, taskID)


if __name__ == "__main__":

    app = Celery()
    app.config_from_object(Config)

    flag = True
    while True:
        # Wait till there are available workers
        status = check_for_clients()
        if status:
            break
        else:
            if flag:
                print("No workers available")
                print("Waiting for workers to come online")
                flag = False

    system = ActorSystem("multiprocTCPBase")
    sendActor = system.createActor(taskSender)

    processedTasks = set()

    while True:

        try:
            client = MongoClient("mongodb://admin:secret@172.20.128.1:27017/?authSource=admin")
            db = client.datastore
            collection = db.tasks
        except:
            print("MongoDB Connection Failed")

        query = {"state": "CREATED"}

        if collection.count_documents(query) > 0:
            newtasks = collection.find(query)
            for document in newtasks:
                try:
                    if document["taskname"] not in processedTasks:
                        # sends the message to sendActor
                        system.tell(sendActor, document)
                        processedTasks.add(document["taskname"])
                except Exception as exc:
                    print("Error with Actor System")
                    print(exc)
                    ActorSystem("multiprocTCPBase").shutdown()

            system.tell(sendActor, "DONE")

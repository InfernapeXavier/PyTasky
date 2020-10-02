import time
import random
import string
from pymongo import MongoClient
from pprint import pprint

# Connecting to the MongoDB instance
client = MongoClient("mongodb://admin:secret@localhost:27888/?authSource=admin")

# Creating a new database
db = client.datastore

# Create the collection
collection = db.tasks

# Deleting old instance if it existed
collection.drop()


def getName():
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(5))
    return result_str


try:
    for x in range(100):
        # Generate a random timeout period as a task
        timeout = random.randint(1, 3)
        document = {
            "taskname": "task" + getName(),
            "sleeptime": timeout,
            "state": "CREATED",
        }
        collection.insert_one(document)
except:
    print("Error while inserting records")
else:
    print("Records inserted successfully")


from pymongo import MongoClient

# Connect to the local MongoDB server
client = MongoClient(
    "mongodb://127.0.0.1:27017",
    serverSelectionTimeoutMS=3000
)

# Select the AgriGrant database
db = client["agrigrant"]

# Select the collection for farmer applications
applications_collection = db["applications"]

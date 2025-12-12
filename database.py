# database.py
from pymongo import MongoClient, ASCENDING
from config import MONGO_URI, DB_NAME, ORG_COLLECTION, ADMIN_COLLECTION

# setup mongo client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# get collections
orgs = db[ORG_COLLECTION]
admins = db[ADMIN_COLLECTION]

def init_db():
    """setup indexes when app starts"""
    try:
        orgs.create_index([("organization_name", ASCENDING)], unique=True)
        admins.create_index([("email", ASCENDING)], unique=True)
        print("DB indexes created")
    except Exception as e:
        print(f"Index creation issue: {e}")

def get_org_collection(collection_name):
    """get a specific org's collection"""
    return db[collection_name]
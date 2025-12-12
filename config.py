# config.py
import os

# JWT stuff
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-this")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MIN = 30

# mongo connection
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = "master_organization_db"

# collections
ORG_COLLECTION = "organizations"
ADMIN_COLLECTION = "admins"
ADMIN_COLLECTION = "admins"
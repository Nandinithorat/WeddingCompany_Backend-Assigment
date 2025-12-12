# services.py
import re
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException, status

from database import orgs, admins, db
from auth import hash_pwd


def clean_org_name(name):
    """make org name safe for collection naming"""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    return f"org_{cleaned}"


def setup_org_collection(coll_name):
    """create new collection for org"""
    try:
        db.create_collection(coll_name)
        coll = db[coll_name]
        # add initial doc so collection actually exists
        coll.insert_one({
            "initialized": True,
            "created_at": datetime.now(timezone.utc),
            "note": "Org data goes here"
        })
        return True
    except:
        return False


def create_org(org_name, email, password):
    """create new org with admin"""
    # check duplicates
    if orgs.find_one({"organization_name": org_name}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization name taken"
        )

    if admins.find_one({"email": email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # make collection
    coll_name = clean_org_name(org_name)
    setup_org_collection(coll_name)

    # create admin
    admin_data = {
        "email": email,
        "password": hash_pwd(password),
        "created_at": datetime.now(timezone.utc)
    }
    admin_result = admins.insert_one(admin_data)

    # create org
    org_data = {
        "organization_name": org_name,
        "collection_name": coll_name,
        "admin_id": str(admin_result.inserted_id),
        "admin_email": email,
        "created_at": datetime.now(timezone.utc),
        "connection_details": {
            "database": db.name,
            "collection": coll_name
        }
    }
    org_result = orgs.insert_one(org_data)

    return {
        "organization_id": str(org_result.inserted_id),
        "organization_name": org_name,
        "collection_name": coll_name,
        "admin_email": email,
        "created_at": org_data["created_at"].isoformat()
    }


def get_org(org_name):
    """fetch org details"""
    org = orgs.find_one({"organization_name": org_name})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    return {
        "organization_id": str(org["_id"]),
        "organization_name": org["organization_name"],
        "collection_name": org["collection_name"],
        "admin_email": org["admin_email"],
        "created_at": org["created_at"].isoformat(),
        "connection_details": org["connection_details"]
    }


def update_org(old_name, new_name, email, password):
    """update org and admin info"""
    org = orgs.find_one({"organization_name": old_name})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # check new name availability
    if old_name != new_name:
        if orgs.find_one({"organization_name": new_name}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New name already exists"
            )

    old_coll = org["collection_name"]
    new_coll = clean_org_name(new_name)

    # migrate collection if name changed
    if old_name != new_name:
        old_collection = db[old_coll]
        new_collection = db[new_coll]

        docs = list(old_collection.find())
        if docs:
            new_collection.insert_many(docs)

        old_collection.drop()
    else:
        new_coll = old_coll

    # update admin if needed
    admin_id = org["admin_id"]
    admin_updates = {}

    if email:
        # check email not used by others
        existing = admins.find_one({
            "email": email,
            "_id": {"$ne": ObjectId(admin_id)}
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email in use"
            )
        admin_updates["email"] = email

    if password:
        admin_updates["password"] = hash_pwd(password)

    if admin_updates:
        admins.update_one(
            {"_id": ObjectId(admin_id)},
            {"$set": admin_updates}
        )

    # update org doc
    org_updates = {
        "organization_name": new_name,
        "collection_name": new_coll,
        "updated_at": datetime.now(timezone.utc)
    }
    if email:
        org_updates["admin_email"] = email

    orgs.update_one(
        {"_id": org["_id"]},
        {"$set": org_updates}
    )

    return {
        "message": "Organization updated",
        "organization_name": new_name,
        "collection_name": new_coll
    }


def delete_org(org_name, current_user):
    """delete org and everything related"""
    org = orgs.find_one({"organization_name": org_name})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # verify ownership
    if org["admin_id"] != current_user["admin_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # cleanup
    db[org["collection_name"]].drop()

    try:
        admins.delete_one({"_id": ObjectId(org["admin_id"])})
    except Exception as e:
        print(f"Admin delete error: {e}")

    orgs.delete_one({"_id": org["_id"]})

    return {
        "message": "Organization deleted",
        "organization_name": org_name
    }
# routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta

from models import OrgCreate, OrgUpdate, OrgDelete, LoginRequest, Token
from services import create_org, get_org, update_org, delete_org
from auth import get_current_user, check_pwd, create_token
from database import admins, orgs
from config import TOKEN_EXPIRE_MIN

router = APIRouter()


@router.post("/org/create", status_code=status.HTTP_201_CREATED)
def create_organization_endpoint(req: OrgCreate):
    """create new org"""
    result = create_org(req.organization_name, req.email, req.password)
    return {
        "success": True,
        "message": "Org created",
        "data": result
    }


@router.get("/org/get")
def get_organization_endpoint(organization_name: str):
    """get org info"""
    result = get_org(organization_name)
    return {
        "success": True,
        "data": result
    }


@router.put("/org/update")
def update_organization_endpoint(req: OrgUpdate):
    """update org"""
    result = update_org(
        req.organization_name,
        req.new_organization_name,
        req.email,
        req.password
    )
    return {
        "success": True,
        "data": result
    }


@router.delete("/org/delete")
def delete_organization_endpoint(
        req: OrgDelete,
        user: dict = Depends(get_current_user)
):
    """delete org - needs auth"""
    result = delete_org(req.organization_name, user)
    return {
        "success": True,
        "data": result
    }


@router.post("/admin/login", response_model=Token)
def login_endpoint(req: LoginRequest):
    """admin login"""
    admin = admins.find_one({"email": req.email})
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not check_pwd(req.password, admin["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    org = orgs.find_one({"admin_id": str(admin["_id"])})
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No org found"
        )

    token_data = {
        "admin_id": str(admin["_id"]),
        "organization_id": str(org["_id"]),
        "email": admin["email"]
    }

    token = create_token(token_data)

    return Token(
        access_token=token,
        admin_id=str(admin["_id"]),
        organization_id=str(org["_id"]),
        organization_name=org["organization_name"]
    )
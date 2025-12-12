# main.py
from fastapi import FastAPI
from database import init_db
from routes import router

app = FastAPI(
    title="Organization Management API",
    version="1.0.0"
)

# setup db on startup
@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {
        "message": "Org Management API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "create": "POST /org/create",
            "get": "GET /org/get",
            "update": "PUT /org/update",
            "delete": "DELETE /org/delete",
            "login": "POST /admin/login"
        }
    }

# include all routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
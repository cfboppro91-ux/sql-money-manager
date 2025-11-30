# app/main.py
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi

from app.database import Base, engine
from app.routers import auth, category, wallet, transaction, budget, family

import firebase_admin
from firebase_admin import credentials
import os, json

# ✅ Init Firebase Admin TẠI ĐÂY và CHỈ ở đây

if not firebase_admin._apps:
    # ưu tiên dùng env JSON nếu có
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if raw:
        cred_info = json.loads(raw)
        cred = credentials.Certificate(cred_info)
    else:
        # fallback dùng secret file (Render)
        cred = credentials.Certificate("/etc/secrets/firebase-admin-key.json")

    firebase_admin.initialize_app(cred)

Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Money Manager API",
        version="1.0",
        description="Backend for Money Manager",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(auth.router)
app.include_router(category.router)
app.include_router(wallet.router)
app.include_router(transaction.router)
app.include_router(budget.router)
app.include_router(family.router)

@app.get("/")
def root():
    return {"message": "Money Manager API running!"}

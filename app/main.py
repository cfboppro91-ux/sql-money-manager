from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi

from app.database import Base, engine
from app.routers import auth, category, wallet, transaction, budget, family
from app.database import engine
engine.execute(
    "ALTER TABLE family_members ADD COLUMN status VARCHAR NOT NULL DEFAULT 'pending';"
)
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

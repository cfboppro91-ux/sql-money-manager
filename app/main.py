from fastapi import FastAPI
from app.database import Base, engine
from app.routers import auth, category, wallet, transaction, budget

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(category.router)
app.include_router(wallet.router)
app.include_router(transaction.router)
app.include_router(budget.router)

@app.get("/")
def root():
    return {"message": "Money Manager API running!"}

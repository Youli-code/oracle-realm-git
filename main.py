from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import docs_loader
from backend import import_github
from backend import ask_oracle

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs_loader.router)
app.include_router(import_github.router)
app.include_router(ask_oracle.router)

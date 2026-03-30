from fastapi import FastAPI

from app.api.routes.github_webhooks import router as webhooks_router
from app.api.routes.health import router as health_router
from app.api.routes.policies import router as policies_router
from app.api.routes.sessions import router as sessions_router
from app.persistence.db import Base, engine


app = FastAPI(title="PR/MR Comprehension Gate")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(health_router)
app.include_router(webhooks_router)
app.include_router(policies_router)
app.include_router(sessions_router)

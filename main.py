from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.database import init_db
from src.api.v1 import api_router

@asynccontextmanager
async def lifespan(_:FastAPI):
    await init_db()
    yield 

def make_app():
    app = FastAPI(lifespan=lifespan)
    app.include_router(api_router,)

    return app

app = make_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=9001,reload=True,timeout_graceful_shutdown=360) 
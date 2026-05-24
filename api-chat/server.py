import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from db import init_db
from auth import router as auth_router
from chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="API Chat", version="1.0.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


def main():
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()

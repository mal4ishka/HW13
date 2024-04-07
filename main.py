from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware
from address_book.routes import contacts, auth, users
import redis.asyncio as redis
from address_book.conf.config import settings

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contacts.router, prefix='/api')
app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.on_event("startup")
async def startup():
    r = await redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)
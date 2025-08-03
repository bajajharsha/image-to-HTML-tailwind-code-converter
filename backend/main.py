from contextlib import asynccontextmanager
import traceback
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys

from backend.app.config.database import mongodb_database
from backend.app.routes import convert_route
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
import uuid

@asynccontextmanager
async def db_lifespan(app: FastAPI):
    mongodb_database.connect()
    yield
    mongodb_database.disconnect()

app = FastAPI(
    title="Image to Component API",
    description="API for converting images to web components",
    version="1.0.0",
    lifespan=db_lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["POST", "GET"], 
    allow_headers=["*"],
)

app.include_router(convert_route.router)

@app.exception_handler(JsonResponseError)
async def json_response_error_handler(request: Request, exc: JsonResponseError):
    print(f"ERROR: {exc.detail}", file=sys.stderr)
    print(f"TRACEBACK: {exc.traceback}", file=sys.stderr)
    return exc.response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace = traceback.format_exc()

    print(f"UNHANDLED ERROR: {str(exc)}", file=sys.stderr)
    print(f"TRACEBACK: {trace}", file=sys.stderr)

    return exc.response

@app.middleware("http")
async def set_request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    if not request_context.get():
        token = request_context.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_context.reset(token)
    return response

"""Application factory with lifespan-managed initialization and a bounded sync worker."""
from contextlib import asynccontextmanager, suppress
from pathlib import Path
import asyncio
import logging
import os
import sqlite3

from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from core import AiClient, Database, Knowledge, Problem, User, current_user, KNOWLEDGE_SCHEMA


def make_application(title, schema, register, seed, service_type, db_path=None,
                     ai_mode=None, enable_worker=True, ai_client=None):
    database = Database(db_path or os.getenv("DATABASE_PATH", "data/app.sqlite3"))
    ai = ai_client or AiClient(mode=ai_mode)
    knowledge = Knowledge(database, ai)
    service = service_type(database)
    stop = asyncio.Event()

    async def worker():
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=5)
            except asyncio.TimeoutError:
                try:
                    await asyncio.to_thread(service.run_due)
                except Exception:
                    logging.exception("Sync worker failed; next cycle will retry")

    @asynccontextmanager
    async def lifespan(app):
        database.initialize(KNOWLEDGE_SCHEMA + schema)
        await asyncio.to_thread(seed, database, knowledge)
        task = None
        worker_on = enable_worker and os.getenv("WORKER_ENABLED", "true").lower() == "true"
        if hasattr(service, "run_due") and worker_on:
            stop.clear()
            task = asyncio.create_task(worker())
        try:
            yield
        finally:
            stop.set()
            if task:
                await task

    app = FastAPI(title=title, version="1.0.0", lifespan=lifespan)
    app.state.db, app.state.kb, app.state.service = database, knowledge, service

    @app.exception_handler(Problem)
    async def domain_error(request, error):
        headers = {"WWW-Authenticate": "Basic"} if error.status == 401 else None
        return JSONResponse({"error": error.message}, status_code=error.status, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        messages = [f"{'.'.join(map(str,e['loc']))}: {e['msg']}" for e in error.errors()]
        return JSONResponse({"error": messages}, status_code=400)

    @app.exception_handler(HTTPException)
    async def http_error(request, error):
        return JSONResponse({"error": error.detail}, status_code=error.status_code, headers=error.headers)

    @app.exception_handler(sqlite3.IntegrityError)
    async def conflict(request, error):
        return JSONResponse({"error": "Database constraint conflict"}, status_code=409)

    @app.exception_handler(Exception)
    async def unexpected(request, error):
        logging.getLogger(__name__).exception("Request failed", exc_info=error)
        return JSONResponse({"error": "Unexpected server error; inspect application logs"}, status_code=500)

    @app.middleware("http")
    async def bounds(request, call_next):
        length = request.headers.get("content-length", "")
        if length.isdecimal() and int(length) > 256_000:
            return JSONResponse({"error": "Request body exceeds 256000 bytes"}, status_code=413)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/actuator/health", include_in_schema=False)
    def health():
        return {"status": "UP"}

    @app.get("/api/me")
    def me(user: User = Depends(current_user)):
        return {"username": user.username, "roles": ["ROLE_"+user.role]}

    register(app, database, knowledge, service)
    app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="ui")
    return app

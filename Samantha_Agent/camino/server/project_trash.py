"""Authenticated phone control protocol and independent expiry worker."""
import asyncio
import threading
import sqlite3
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from camino.domain.project_lifecycle import lifecycle_lock
from camino.domain.project_trash import TrashError, canonical


def failure(code, message, status):
    return JSONResponse({'contract_version': 1, 'error': {'code': code, 'message': message}},
                        status_code=status, headers={'Cache-Control': 'no-store'})


class ProjectLeaseMiddleware:
    def __init__(self, app, *, database):
        self.app, self.database = app, database

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['path'].startswith('/api/v1/project-trash'):
            return await self.app(scope, receive, send)
        # Never block the event loop while an expiry worker holds its lease.
        while True:
            lease = lifecycle_lock(self.database, blocking=False)
            try:
                lease.__enter__()
                break
            except BlockingIOError:
                await asyncio.sleep(.05)
        try:
            await self.app(scope, receive, send)
        finally:
            lease.__exit__(None, None, None)


class TrashWorker:
    def __init__(self, trash, interval=60):
        self.trash, self.interval = trash, interval
        self.stop_event = threading.Event()
        self.thread = None
        self.last_error = None

    def start(self):
        self.thread = threading.Thread(target=self.run, name='camino-trash', daemon=True)
        self.thread.start()

    def run(self):
        while not self.stop_event.is_set():
            try:
                self.trash.sweep()
                self.last_error = None
            except Exception as error:
                # Paths, names and content never enter the worker status.
                self.last_error = getattr(error, 'code', 'purge_requires_review')
            self.stop_event.wait(self.interval)

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()


def phone_router(trash, authorized, exact_json):
    router = APIRouter()

    @router.get('/api/v1/project-trash')
    @router.post('/api/v1/project-trash')
    async def control(request: Request):
        if not authorized(request):
            return failure('unauthorized', 'private authorization required', 401)
        try:
            if request.method == 'GET':
                if set(request.query_params) != {'device_id'} or len(request.query_params.multi_items()) != 1:
                    raise TrashError('invalid_request', 'Chybí identita telefonu.')
                device = canonical(request.query_params['device_id'])
                rows = await asyncio.to_thread(trash.listing, device_id=device)
                result = {**trash.identity(), 'requests': rows}
            else:
                body = await exact_json(request, {'request_id', 'trip_id', 'device_id', 'server_id', 'epoch', 'name'})
                result = await asyncio.to_thread(trash.request_trip, body)
            return JSONResponse(result, headers={'Cache-Control': 'no-store'})
        except (TrashError, ValueError) as error:
            return failure(getattr(error, 'code', 'invalid_request'), str(error), 409)
        except (sqlite3.DatabaseError, OSError):
            return failure('storage_unavailable', 'Koš teď nelze bezpečně ověřit.', 503)

    @router.post('/api/v1/project-trash/ack')
    async def acknowledge(request: Request):
        if not authorized(request):
            return failure('unauthorized', 'private authorization required', 401)
        try:
            body = await exact_json(request, {'request_id', 'device_id'})
            result = await asyncio.to_thread(trash.acknowledge, body['request_id'], body['device_id'])
            return JSONResponse(result, headers={'Cache-Control': 'no-store'})
        except (TrashError, ValueError) as error:
            return failure(getattr(error, 'code', 'invalid_request'), str(error), 409)
        except (sqlite3.DatabaseError, OSError):
            return failure('storage_unavailable', 'Koš teď nelze bezpečně ověřit.', 503)
    return router

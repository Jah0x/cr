import sqlite3
import asyncio

DatabaseError = sqlite3.DatabaseError
IntegrityError = sqlite3.IntegrityError
ProgrammingError = sqlite3.ProgrammingError
OperationalError = sqlite3.OperationalError
Error = sqlite3.Error
Warning = sqlite3.Warning
InterfaceError = sqlite3.InterfaceError
DataError = sqlite3.DataError
InternalError = sqlite3.InternalError
NotSupportedError = sqlite3.NotSupportedError
sqlite_version = sqlite3.sqlite_version
sqlite_version_info = sqlite3.sqlite_version_info
paramstyle = sqlite3.paramstyle
version = sqlite3.version
version_info = sqlite3.version_info


class Cursor:
    def __init__(self, cursor):
        self._cursor = cursor

    async def execute(self, sql, parameters=None):
        params = parameters or ()
        return await asyncio.get_running_loop().run_in_executor(None, self._cursor.execute, sql, params)

    async def fetchone(self):
        return await asyncio.get_running_loop().run_in_executor(None, self._cursor.fetchone)

    async def fetchall(self):
        return await asyncio.get_running_loop().run_in_executor(None, self._cursor.fetchall)

    async def close(self):
        return await asyncio.get_running_loop().run_in_executor(None, self._cursor.close)

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def description(self):
        return self._cursor.description


class Connection:
    def __init__(self, conn):
        self._conn = conn
        self.row_factory = conn.row_factory

    async def execute(self, sql, parameters=None):
        cursor = await self.cursor()
        await cursor.execute(sql, parameters or ())
        return cursor

    async def cursor(self):
        return Cursor(self._conn.cursor())

    async def commit(self):
        return await asyncio.get_running_loop().run_in_executor(None, self._conn.commit)

    async def rollback(self):
        return await asyncio.get_running_loop().run_in_executor(None, self._conn.rollback)

    async def close(self):
        return await asyncio.get_running_loop().run_in_executor(None, self._conn.close)

    async def create_function(self, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self._conn.create_function(*args, **kwargs))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.rollback()
        else:
            await self.commit()
        await self.close()


class ConnectCoroutine:
    def __init__(self, coro):
        self._coro = coro
        self.daemon = True

    def __await__(self):
        return self._coro.__await__()


async def _connect(database, **kwargs):
    conn = sqlite3.connect(database, check_same_thread=False)
    for key, value in kwargs.items():
        if hasattr(conn, key):
            setattr(conn, key, value)
    return Connection(conn)


def connect(database, **kwargs):
    return ConnectCoroutine(_connect(database, **kwargs))

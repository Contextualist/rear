import builtins
import trio
from contextlib import contextmanager, asynccontextmanager
from zipfile import ZipFile
import io
import os
from pathlib import Path
from time import strftime, gmtime as ts

@asynccontextmanager
async def rear_fs(arch_base, success_only=True, rotation_span=5*60):
    """Context to set up rotating tmp archives for file collection

    e.g.::

        async with rear_fs("/path/to/archive_base"):
            with rear_open("ar.zip/relpath/to/file", 'w+b') as f:
                f.write(b"Hello world") # Write buffers all content
            # Closing file flushes all of the buffer to a tmp archive

            with rear_pickup("/path/to/temp-file", "ar.zip/relpath/to/file"):
                await trio.run("echo 'external output' > /path/to/temp-file", shell=True)
            # Closing context moves the file to a tmp archive
    """
    _ar = None
    temp = Path(arch_base)/"inbox"
    temp.mkdir(parents=True, exist_ok=True)
    hostname = trio.socket.gethostname()

    async def _rotated():
        nonlocal _ar
        while True:
            await trio.sleep(rotation_span)
            if _ar:
                _ar.close()
                _ar = None

    def _get_ar():
        nonlocal _ar
        if _ar is None:
            # NOTE: time tuples are all in UTC
            _ar = ZipFile(temp/f"{hostname}-{strftime('%y%m%d_%H%M%S',ts())}.zip", 'w')
        return _ar

    @contextmanager
    def rear_open(relpath, mode):
        assert mode in {'w+b', 'w+'}, "ReAr only support read-write mode"
        assert not os.path.isabs(relpath), "ReAr reqiures a relative path"
        f = io.BytesIO() if mode.endswith('b') else io.StringIO()
        ok = False
        try:
            yield f
            ok = True
        finally:
            if ok or not success_only:
                ar = _get_ar()
                if ar.NameToInfo.get(relpath) is None: # duplicated files are discarded
                    ar.writestr(relpath, f.getbuffer() if mode.endswith('b') else f.getvalue().encode())

    @contextmanager
    def rear_pickup(tmpf, relpath):
        assert not os.path.isabs(relpath), "ReAr reqiures a relative path"
        ok = False
        try:
            yield
            ok = True
        finally:
            if ok or not success_only:
                ar = _get_ar()
                if ar.NameToInfo.get(relpath) is None: # duplicated files are discarded
                    ar.write(tmpf, arcname=relpath)
            Path(tmpf).unlink()

    async with trio.open_nursery() as _n:
        _n.start_soon(_rotated)
        setattr(builtins, "rear_open", rear_open)
        setattr(builtins, "rear_pickup", rear_pickup)
        try:
            yield
        finally:
            if _ar:
                _ar.close()
            delattr(builtins, "rear_open")
            delattr(builtins, "rear_pickup")
            _n.cancel_scope.cancel()

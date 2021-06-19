from .rear import rear_fs

from contextlib import asynccontextmanager

@asynccontextmanager
async def scavengerd(arch_base, rotation_span=5*60):
    """A daemon scanning the temporary (inbox) dir periodically and collect the
    files in the temporary archives to their dest archives. It is safe to run
    this function in multiple instances, unnecessary updates are avoided through
    file lock. The daemon is stopped at the exit of this context.

    Args:
        arch_base (pathlike): path to store the final archives. Must be on a
            proper network filesystem.
        rotation_span (int): time to switch to a new temp zip, in s; must be the
            same as `rear_fs`'s
    """
    import sys
    import trio

    async def _scan_once():
        with trio.move_on_after(1800) as cs:
            cs.shield = True # try to wait, even when the main process wants to exit
            await trio.run_process( # start a process since this is CPU intensive
                [sys.executable, "-m", "rear.scavenger", "-d", arch_base, "--rotation", str(rotation_span)]
            )

    async def _d():
        while True:
            await _scan_once()
            await trio.sleep(rotation_span)

    async with trio.open_nursery() as _n:
        _n.start_soon(_d)
        yield
        _n.cancel_scope.cancel()

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
    from .scavenger import scan_once
    import trio
    from multiprocessing import Process

    def _scan_once(arch_base):
        # start a process since this is CPU intensive
        p = Process(target=scan_once, args=(arch_base, False, rotation_span))
        p.start()
        p.join()

    async def _d():
        while True:
            await trio.to_thread.run_sync(_scan_once, arch_base)
            await trio.sleep(rotation_span)

    async with trio.open_nursery() as _n:
        _n.start_soon(_d)
        yield
        _n.cancel_scope.cancel()

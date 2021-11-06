from .rear import rear_fs
from .scavenger import try_scan_once

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

async def test_integration():
    arch_base = Path(".")
    async with rear_fs(arch_base):
        with rear_open("a.zip/b/c.txt", 'w+b') as f:
            f.write(b"Lorem ipsum")
        with rear_open("a.zip/b/d.txt", 'w+') as f:
            f.write("Lorem ipsum")
        with TemporaryDirectory() as tmp, \
             rear_pickup(Path(tmp)/"e.txt", "a.zip/b/e.txt"):
            (Path(tmp)/"e.txt").write_text("dolor sit amet")

    try_scan_once(arch_base, flush=True)
    with ZipFile(arch_base/"a.zip") as ar:
        assert ar.read("b/c.txt") == b"Lorem ipsum"
        assert ar.read("b/d.txt") == b"Lorem ipsum"
        assert ar.read("b/e.txt") == b"dolor sit amet"
    (arch_base/"a.zip").unlink()
    (arch_base/"inbox/rear.lock").unlink()
    (arch_base/"inbox").rmdir()

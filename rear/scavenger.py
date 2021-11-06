from zipfile import ZipFile, BadZipFile, is_zipfile
from time import strptime, time as utc, strftime
from calendar import timegm as ts2utc
from pathlib import Path
from contextlib import ExitStack
import subprocess

from filelock import Timeout, FileLock
import logging
logging.getLogger("filelock").setLevel(logging.WARNING)

SIZE_CAP = 50 * 1024**3 # 50GB; final archive size limit

def fix_zipfile(ar):
    subprocess.run(f"yes | zip -FF {ar} --out {ar}.fixed > {ar}.fixed.log && mv {ar}.fixed {ar}", shell=True, check=True)
    print(f"Fixed zip file {ar}")

def ar_size_cap(ar):
    if ar.stat().st_size < SIZE_CAP:
        return
    sufind = 0
    while (ar1 := ar.with_name(f"{ar.stem}-{sufind}{ar.suffix}")).exists():
        sufind += 1
    ar.rename(ar1)
    print(f"mv {ar} {ar1}")

def try_scan_once(arch_base, flush=False, rotation_span=5*60):
    arch_base = Path(arch_base)
    temp = arch_base/"inbox"
    temp.mkdir(exist_ok=True)

    now = utc()
    lockf = temp/"rear.lock"
    if not flush and lockf.exists() and now - lockf.stat().st_mtime < rotation_span:
        return
    try:
        with FileLock(lockf, timeout=0.01):
            _scan_once(arch_base, now, flush, rotation_span)
    except Timeout:
        pass

def _scan_once(arch_base, now, flush=False, rotation_span=5*60):
    stat_fi, stat_ta, stat_da = 0, 0, 0
    with ExitStack() as ar_cm:
        dazlist = {} # list of dest archive zip handlers
        for ta in (arch_base/"inbox").glob("*.zip"):
            # NOTE: time tuples are all in UTC
            rottime = ts2utc(strptime(ta.stem.split('-')[-1], '%y%m%d_%H%M%S'))
            if not flush and now - rottime < rotation_span * 1.5: # we wait longer than rotation_span to avoid any delayed release
                continue
            try:
                taz = ZipFile(ta, 'r')
            except BadZipFile:
                fix_zipfile(ta)
                taz = ZipFile(ta, 'r')
            stat_ta += 1
            with taz:
                for finfo in taz.infolist():
                    dest, fname = finfo.filename.split('/',1)
                    if dest not in dazlist:
                        abdest = arch_base/dest
                        if abdest.exists():
                            if not is_zipfile(abdest):
                                fix_zipfile(abdest)
                            ar_size_cap(abdest)
                        dazlist[dest] = ar_cm.enter_context(ZipFile(abdest, 'a'))
                        stat_da += 1
                    daz = dazlist[dest]
                    if daz.NameToInfo.get(fname) is None:
                        try:
                            fbytes = taz.read(finfo)
                        except BadZipFile:
                            print(f"Error reading file {finfo.filename} from {ta}")
                            continue
                        finfo.filename = fname
                        daz.writestr(finfo, fbytes)
                        stat_fi += 1
            ta.unlink()

    if stat_fi > 0:
        print(f"[{strftime('%y/%m/%d %H:%M:%S')}]\ttransferred {stat_fi} files from {stat_ta} temp ars to {stat_da} dest ars")

def main():
    import argparse
    argp = argparse.ArgumentParser(description="ReAr's scavenger: collecting temporary archives into final archives")
    argp.add_argument('-d', default=".", help="the Zip archive base")
    argp.add_argument('--flush', action='store_true', help="transfer all files within the inbox; caution: use it only when all temp archives are closed")
    argp.add_argument('--rotation', type=int, default=5*60, help="time to switch to a new temp zip, in s; must be the same as `rear_fs`'s (default: 300)")
    carg = argp.parse_args()
    try_scan_once(carg.d, carg.flush, carg.rotation)
if __name__ == "__main__":
    main()

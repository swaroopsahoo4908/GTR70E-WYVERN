#!/usr/bin/env python3
"""Write/read/verify a 16 MB pattern on both SPI microSD cards; report throughput."""
import os, time, hashlib
CARDS = {"video":"/mnt/sd_video","log":"/mnt/sd_log"}
BLK = b"WYVERN3"*1024*16  # ~112 KB
N = 150                    # ~16 MB
ok = True
for name, mnt in CARDS.items():
    try:
        os.makedirs(mnt, exist_ok=True); p=f"{mnt}/_rwtest.bin"
        h=hashlib.sha256(); t=time.time()
        with open(p,"wb") as f:
            for _ in range(N): f.write(BLK); h.update(BLK)
            f.flush(); os.fsync(f.fileno())
        wt=time.time()-t; sz=N*len(BLK)
        t=time.time(); hr=hashlib.sha256()
        with open(p,"rb") as f:
            while (c:=f.read(1<<20)): hr.update(c)
        rt=time.time()-t; good = h.hexdigest()==hr.hexdigest(); os.remove(p)
        print(f"  uSD {name:5} write {sz/wt/1e6:5.1f} MB/s  read {sz/rt/1e6:5.1f} MB/s  verify {'OK' if good else 'CORRUPT'}")
        ok &= good
    except Exception as e: print(f"  uSD {name}: FAIL {e}"); ok=False
raise SystemExit(0 if ok else 1)

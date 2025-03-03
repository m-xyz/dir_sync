import argparse
import os
import shutil
import threading
from filecmp import dircmp
from pathlib import Path

FILE_SIZE_CHUNK = 4096

def file_content_sync(src_file: Path, dst_file: Path):
    if(src_file.stat().st_size != dst_file.stat().st_size): return False

    with src_file.open("rb") as f1, dst_file.open("rb") as f2:
        while 1:
            r1 = f1.read(FILE_SIZE_CHUNK)
            r2 = f2.read(FILE_SIZE_CHUNK)

            if(r1 != r2): return False
            if not r1: break # No more bytes to read (EOF)

    return True

def sync(src, dst):
    c = dircmp(src, dst)

    # Check files in src and not in dst, copy them to dst
    for file in c.left_only:
        print(f"{src}/{file} not in {dst}, copying...")
        src_file = src / file
        dst_file = dst / file

        # Either it's a directory or file that differs
        if(src_file.is_dir()): shutil.copytree(src_file, dst_file)
        else: shutil.copy2(src_file, dst_file)

    # Check files in dst and not in src, delete them in dst
    for file in c.right_only:
        dst_file = dst / file

        if(dst_file.is_dir()):
            print(f"Dir {dst_file} in replica and not in source, deleting...")
            shutil.rmtree(dst_file)
        else:
            print(f"File {dst_file} in replica and not in source, deleting...")
            dst_file.unlink()

    # Check if there are differences in common files
    for file in c.common_files:
        src_file = src / file
        dst_file = dst / file
        if not file_content_sync(src_file, dst_file):
            shutil.copy2(src_file, dst_file)
            print(f"Updated {dst_file}.")

    # Recursively call sync() on common directories
    for cdir in c.common_dirs:
        sync(src / cdir, dst / cdir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronization between directories")
    parser.add_argument(
        "-s",
        "--source",
        type=str.lower,
        help="Source directory",
        required=True,
    )
    parser.add_argument(
        "-r",
        "--replica",
        type=str.lower,
        help="Replica directory",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--time",
        type=str.lower,
        help="Sync timer",
        required=True,
    )
    args = parser.parse_args()

    src_path = Path(args.source).resolve()
    dst_path = Path(args.replica).resolve()
    sync_timer = int(args.time)

    def synchronize_directories():
        print(":)")
        try:
            sync(src_path, dst_path)
            threading.Timer(sync_timer, synchronize_directories).start()
        except Exception as e: print(e)

    synchronize_directories()

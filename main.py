import argparse
import os
import shutil
import threading
from datetime import datetime
import logging
from filecmp import dircmp
from pathlib import Path

LOG_DATE = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
FILE_SIZE_CHUNK = 4096

def file_content_sync(src_file: Path, dst_file: Path):
    """
    Compares the contents of two files to determine if they are identical.
    Given two files, this function compares the contents of each file by
    reading them in chunks of FILE_SIZE_CHUNK bytes and comparing the
    contents of each chunk. If the files are not the same size, this function
    will return False. If the contents of the files are different, this
    function will also return False. If the contents of the files are the same,
    this function will return True.

    :param src_file: The source file
    :param dst_file: The destination file
    :return: True if the contents of the files are the same, False otherwise
    """
    if(src_file.stat().st_size != dst_file.stat().st_size): return False

    with src_file.open("rb") as f1, dst_file.open("rb") as f2:
        while 1:
            r1 = f1.read(FILE_SIZE_CHUNK)
            r2 = f2.read(FILE_SIZE_CHUNK)

            if(r1 != r2): return False
            if not r1: break # No more bytes to read (EOF)

    return True

def sync(src: Path, dst: Path):
    """
    Syncs two directories (src and dst) by copying new files from src to dst,
    deleting files in dst that are not in src, and updating files in dst that
    are different from src.

    :param src: source directory
    :param dst: replica directory
    """
    c = dircmp(src, dst)

    # Check files in src and not in dst, copy them to dst
    for file in c.left_only:
        logger.info(f"{src}/{file} not in {dst}, copying...")
        src_file = src / file
        dst_file = dst / file

        # Either it's a directory or file that differs
        if(src_file.is_dir()): shutil.copytree(src_file, dst_file)
        else: shutil.copy2(src_file, dst_file)

    # Check files in dst and not in src, delete them in dst
    for file in c.right_only:
        dst_file = dst / file

        if(dst_file.is_dir()):
            logger.info(f"Dir {dst_file} in replica and not in source, deleting...")
            shutil.rmtree(dst_file)
        else:
            logger.info(f"File {dst_file} in replica and not in source, deleting...")
            dst_file.unlink()

    # Check if there are differences in common files
    for file in c.common_files:
        src_file = src / file
        dst_file = dst / file
        if not file_content_sync(src_file, dst_file):
            shutil.copy2(src_file, dst_file)
            logger.info(f"Updated {dst_file}.")

    # Recursively call sync() on common directories
    for cdir in c.common_dirs: sync(src / cdir, dst / cdir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronization between directories")
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        help="Source directory",
        required=True,
    )
    parser.add_argument(
        "-r",
        "--replica",
        type=str,
        help="Replica directory",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--time",
        type=str,
        help="Sync timer",
        required=True,
    )
    parser.add_argument(
        "-l",
        "--log",
        type=str,
        help="Path to log file",
        required=True,
    )

    args = parser.parse_args()
    src_path = Path(args.source).resolve()
    dst_path = Path(args.replica).resolve()
    sync_timer = int(args.time)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(args.log)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('(%(asctime)s) [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    def synchronize_directories():
        """
        Continuously synchronizes two directories at regular intervals.

        This function triggers the synchronization process between the source
        and replica directories, and sets a timer to repeatedly perform this
        operation based on the specified sync_timer interval.

        Exception handling is included to log any errors encountered during
        the synchronization process.

        :raises Exception: If an error occurs during the synchronization process.
        """

        logger.info(f"Synchronizing {src_path} and {dst_path}")
        try:
            sync(src_path, dst_path)
            threading.Timer(sync_timer, synchronize_directories).start()
        except Exception as e: logger.error(f"Failed to sync: {e}")

    synchronize_directories()

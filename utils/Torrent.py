import hashlib
from pathlib import Path
import os
import json
from typing import Dict, List, Tuple

"""
    Use this to create a .torrent(json) file
"""


def generate_torrent_file(path: Path,
                          output_dir: Path,
                          ip_addr: str,
                          port: int,
                          piece_size=1024,
                          ) -> Path:
    """
    Generate a .torrent(json) file, save in torrents directory

    :param path:
    :param output_dir:
    :param ip_addr:
    :param port:
    :param piece_size:
    :return:
    """
    # Collect basic file information
    file_size = os.path.getsize(path)
    file_name = path.stem  # File name without extension
    file_extension = path.suffix  # File extension

    # Calculate piece hashes
    piece_hashes = []
    with open(path, "rb") as f:
        while True:
            piece = f.read(piece_size)  # Read in chunks
            if not piece:
                break
            # SHA-1 hash for each piece
            piece_hash = hashlib.sha1(piece).hexdigest()
            piece_hashes.append(piece_hash)
    # Construct minimal torrent dictionary
    torrent_data = {
        "tracker": {
            "ip": ip_addr,
            "port": port
        },
        "name": file_name,
        "extension": file_extension,
        "size": file_size,
        "piece_size": piece_size,
        "pieces": piece_hashes  # List of SHA-1 hashes for each piece
    }

    # Optional: Save as JSON for easy inspection
    output_path = output_dir / file_name
    output_path = output_path.with_suffix('.json')
    with open(output_path, "w") as json_file:
        json.dump(torrent_data, json_file, indent=4)

    return output_path

def hash_torrent(data: dict) -> int:
    """
    Hash dictionary data type

    :param data: Dictionary data type
    :return:
    """
    return hash(json.dumps(data))

# def test_assembling():
#     fileInRepo = Path("../Files/test.txt")
#     piece_list: List = []
#     with open(fileInRepo, "rb") as f:
#         while True:
#             piece = f.read()  # Read in chunks
#             if not piece:
#                 break
#             piece_list.append(piece)
#
#     # Test trying to assemble the pieces after splitting them
#     torrent_path: Path = Path("../Files/test.json")
#     with open(torrent_path) as tf:
#         data = json.load(tf)
#         assembled_data = bytearray()
#         piece_hashes = data["pieces"]
#         extension = data["extension"]
#         for piece in piece_list:
#             piece_hash = hashlib.sha1(piece).hexdigest()
#             if piece_hash not in piece_hashes:
#                 raise Exception("Data corruption detected")
#             assembled_data.extend(piece)
#
#     # Write the assembled data to a new file
#     output_file_path = Path("../Files/test_reassembled_2" + extension)
#     with open(output_file_path, "wb") as output_file:
#         output_file.write(assembled_data)


if __name__ == "__main__":
    # Example usage
    generate_torrent_file(path=Path("../Files/alice.txt"),
                          piece_size=4096)

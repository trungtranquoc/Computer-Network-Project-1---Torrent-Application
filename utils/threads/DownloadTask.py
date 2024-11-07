import socket
from threading import Thread
from typing import Tuple, List
import time

BUFFER_SIZE = 1024

class DownloadThread(Thread):
    def __init__(self,
                 file_id: int,
                 file_name: str,
                 total_size: int,
                 addr: Tuple[str, int],
                 pieces: List[str],
                 seeders: List[Tuple[str, int]]):
        super().__init__()
        self.file_id = file_id
        self.file_name = file_name
        self.total_size = total_size
        self.pieces = pieces
        self.seeders = seeders
        self.progress = 0
        self.completed = False
        self.skipped = False
        self.__addr = addr

    def run(self):
        #TODO
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(self.__addr)

            # Receive file size
            self.total_size = int(s.recv(1024).decode())

            with open("files/download_text_1.txt", "wb") as f:
                while not self.skipped:
                    data = s.recv(BUFFER_SIZE)
                    if not data:
                        break
                    f.write(data)
                    self.progress += len(data)
                    time.sleep(0.1)

            if self.progress >= self.total_size:
                self.completed = True

                # Add to seeders list
    def __assign_piece_distribution_to_seeders(self, total_piece: int, seeders_count: int):
        pass


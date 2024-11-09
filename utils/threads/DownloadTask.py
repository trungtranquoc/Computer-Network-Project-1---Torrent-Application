import hashlib
import json
import socket
import threading
from threading import Thread
from typing import Tuple, List, Dict
import time
from pathlib import Path

BUFFER_SIZE = 4096
BIT_STR_LOCK = threading.Lock()

class DownloadThread(Thread):
    def __init__(self,
                 file_id: int,
                 torrent_data: dict,
                 seeders: List[Tuple[str, int]],
                 download_dir: Path):
        super().__init__()
        self.file_id = file_id
        self.torrent_data = torrent_data
        self.seeders = seeders
        self.download_dir = download_dir

        self.progress = 0
        self.bit_field = ['0'] * len(self.torrent_data['pieces'])
        self.completed = False
        self.skipped = False



    def run(self):
        # TODO
        seeders_count = len(self.seeders)
        total_piece = len(self.torrent_data['pieces'])
        piece_distribution: List[Tuple[int, int]] = self._assign_piece_distribution_to_seeders(
            total_piece=total_piece,
            seeders_count=seeders_count
        )

        segment_list: List[bytearray] = [bytearray() for _ in range(len(self.seeders))]
        # flag: List[bool] = [True] * len(self.seeders)

        download_threads: List[threading.Thread] = []
        for i in range(seeders_count):
            helper_thread = threading.Thread(target=self.download_from_peers_helper,
                                             args=(i,
                                                   piece_distribution[i],
                                                   self.seeders[i],
                                                   segment_list,
                                                   ))
            helper_thread.start()
            download_threads.append(helper_thread)

        # Wait for all download task complete
        for i in range(seeders_count):
            download_threads[i].join()

        if not all([bit == '1' for bit in self.bit_field]):
            print('[Error] Download unsuccessfully')
        else:
            completeBytesArray: bytearray = bytearray()
            for idx, segment in enumerate(segment_list):
                completeBytesArray.extend(segment)

            try:
                file_name = self.torrent_data['name'] + self.torrent_data['extension']
                with open(self.download_dir / file_name, "wb") as f:
                    f.write(completeBytesArray)

                self.completed = True
            except Exception as e:
                print(f'[Error] Process has failed writing the file to disk due to error: {e}')


    @staticmethod
    def _assign_piece_distribution_to_seeders(total_piece: int, seeders_count: int) -> List[Tuple[int, int]]:
        pieces_distribution = []
        if seeders_count > 0:
            base_pieces_per_seeder = total_piece // seeders_count  # Integer division
            extra_pieces = total_piece % seeders_count  # Remainder pieces to be distributed

            temp_start = 0
            for i in range(seeders_count):
                piece_for_this_seeder = base_pieces_per_seeder + (1 if i < extra_pieces else 0)
                pieces_distribution.append((temp_start, temp_start + piece_for_this_seeder))
                temp_start += piece_for_this_seeder

        return  pieces_distribution

    def download_from_peers_helper(self,
                                   seeder_idx: int,
                                   piece_distribution: Tuple[int, int],
                                   seeder: Tuple[str, int],
                                   segment_list: List[bytearray]):
        # This is where the downloading of the file is handled
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as downloadSocket:
            # Connect to seeder
            downloadSocket.connect(seeder)
            print(f'Prepare to to send torrent to Seeder: {seeder}')
            downloadSocket.sendall(json.dumps(self.torrent_data).encode())
            # time.sleep(5)

            data = downloadSocket.recv(BUFFER_SIZE)

            if not data or data.decode() != "OK":
                print(f'Download from seeder {seeder} failed')
                return

            start, end = piece_distribution
            corrupted_count = 0
            while start < end and corrupted_count <= 3 and not self.skipped:
                downloadSocket.sendall(str(start).encode()) # Send the piece index

                data: bytes = downloadSocket.recv(BUFFER_SIZE)
                retrieved_hash = hashlib.sha1(data).hexdigest()
                if not data or retrieved_hash not in self.torrent_data['pieces']:
                    # blue: str =  "\033[1;36m"
                    # reset: str = "\033[0m"
                    # print(f"Received data: {blue} {data} {reset}")
                    # print(f"Piece no.{start} has been corrupted!")
                    corrupted_count += 1
                    if corrupted_count > 3: # error
                        downloadSocket.sendall("STOP".encode())
                        print(f'[Error] Download unsuccessfully in {seeder_idx} due to maximum corrupted time')
                        # flag[seeder_idx] = False
                        return
                    time.sleep(2)
                    continue # Re:download this piece, due to corruption
                # TODO: how long to sleep between pieces
                print(f"Piece no.{start} is received successfully!")
                segment_list[seeder_idx].extend(data)
                # Update bit field
                with BIT_STR_LOCK:
                    self.bit_field[start] = '1'
                    self.progress += 1

                    print(f'bit_field = {"".join(self.bit_field)}')

                start += 1
                time.sleep(0.5)

            # Tell the seeder to stop
            downloadSocket.sendall("STOP".encode())
            if not self.skipped:
                print("Download thread helper has finished its task!")
            else:
                print("Download thread has skipped downloading this segment!")
            return
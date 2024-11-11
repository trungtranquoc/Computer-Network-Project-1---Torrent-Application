import hashlib
import json
import socket
import threading
from threading import Thread
from typing import Tuple, List, Dict
import time
from pathlib import Path
from enum import Enum
from ..Connection import Connection
from ..Swarm import Swarm, SwarmStatus
from custom import HostAddress


BUFFER_SIZE = 4096
BIT_STR_LOCK = threading.Lock()
STATUS_UPDATE_LOCK = threading.Lock()

class DownloadStatus(Enum):
    INITIAL = 0
    DOWNLOADING = 1
    COMPLETE = 2
    SKIPPED = 3
    ERROR = 4

class DownloadThread(Thread, Swarm):
    def __init__(self,
                 file_id: int,
                 torrent_data: dict,
                 seeders: List[HostAddress],
                 server_conn: Connection,                       # Notify server to become seeder
                 listen_addr: HostAddress,                  # Notify server to become seeder
                 download_dir: Path,
                 daemon: bool = True,
                 ):
        Thread.__init__(self, daemon=daemon)
        Swarm.__init__(self, file_id=file_id, server_conn=server_conn)
        self.__torrent_data = torrent_data
        self.__seeders = seeders
        self.__download_dir = download_dir
        self.__listen_addr = listen_addr

        self.bit_field = ['0'] * len(self.__torrent_data['pieces'])
        self.status: DownloadStatus = DownloadStatus.INITIAL
        self.skipped = False
        self.error_message: str = ''

    def run(self):
        if self.status != DownloadStatus.INITIAL:
            print("File already downloaded !")
            return

        seeders_count = len(self.__seeders)
        total_piece = len(self.__torrent_data['pieces'])
        piece_distribution: List[Tuple[int, int]] = self._assign_piece_distribution_to_seeders(
            total_piece=total_piece,
            seeders_count=seeders_count
        )

        segment_list: List[bytearray] = [bytearray() for _ in range(len(self.__seeders))]

        download_threads: List[threading.Thread] = []
        self.status = DownloadStatus.DOWNLOADING
        for i in range(seeders_count):
            helper_thread = threading.Thread(target=self.download_from_peers_helper,
                                             args=(i, piece_distribution[i], self.__seeders[i], segment_list,))
            helper_thread.start()
            download_threads.append(helper_thread)

        # Wait for all download task complete
        for i in range(seeders_count):
            download_threads[i].join()

        if self.status != DownloadStatus.DOWNLOADING:
            return

        if not all([bit == '1' for bit in self.bit_field]):
            self.status = DownloadStatus.ERROR
            self.error_message = "Missing on some pieces"
        else:
            completeBytesArray: bytearray = bytearray()
            for idx, segment in enumerate(segment_list):
                completeBytesArray.extend(segment)
            try:
                file_name = self.__torrent_data['name'] + self.__torrent_data['extension']
                with open(self.__download_dir / file_name, "wb") as f:
                    f.write(completeBytesArray)

                # Client become leecher in the swarm
                self.status = DownloadStatus.COMPLETE
                self.server_conn.upload_command(json.dumps(self.__torrent_data), self.__listen_addr)
            except:
                self.status = DownloadStatus.ERROR
                self.error_message = "Process has failed writing the file to disk"

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

    def skip_download(self):
        """
        Skip the download task
        """
        with STATUS_UPDATE_LOCK:
            self.status = DownloadStatus.SKIPPED

    def is_error(self):
        """
        :return: True if status is Error
        """
        with STATUS_UPDATE_LOCK:
            return self.status == DownloadStatus.ERROR

    def is_skip(self):
        """
        :return: True if status is Skip
        """
        with STATUS_UPDATE_LOCK:
            return self.status == DownloadStatus.SKIPPED

    def is_downloading(self):
        """
        :return: True if status is Downloading
        """
        with STATUS_UPDATE_LOCK:
            return self.status == DownloadStatus.DOWNLOADING

    def download_from_peers_helper(self,
                                   seeder_idx: int,
                                   piece_distribution: Tuple[int, int],
                                   seeder: HostAddress,
                                   segment_list: List[bytearray]):
        # This is where the downloading of the file is handled
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as downloadSocket:
            # Connect to seeder
            downloadSocket.connect(seeder)
            downloadSocket.sendall(json.dumps(self.__torrent_data).encode())

            data = downloadSocket.recv(BUFFER_SIZE)

            if not data or data.decode() != "OK":
                with STATUS_UPDATE_LOCK:
                    self.status = DownloadStatus.ERROR
                    self.error_message = f'Connect to {seeder} failed'
                return

            start, end = piece_distribution
            corrupted_count = 0
            while start < end and corrupted_count <= 3 and self.status == DownloadStatus.DOWNLOADING:
                downloadSocket.sendall(str(start).encode()) # Send the piece index

                data: bytes = downloadSocket.recv(BUFFER_SIZE)
                retrieved_hash = hashlib.sha1(data).hexdigest()
                if not data or retrieved_hash not in self.__torrent_data['pieces']:
                    corrupted_count += 1
                    if corrupted_count > 3: # error
                        downloadSocket.sendall("STOP".encode())

                        with STATUS_UPDATE_LOCK:
                            self.status = DownloadStatus.ERROR
                            self.error_message = f"Download terminated in seeder {seeder} due to maximum corrupted time"

                        return
                    time.sleep(3)
                    continue # Re:download this piece, due to corruption

                # print(f"Piece no.{start} is received successfully!")
                segment_list[seeder_idx].extend(data)
                # Update bit field
                with BIT_STR_LOCK:
                    self.bit_field[start] = '1'

                start += 1
                time.sleep(0.5)

            # Tell the seeder to stop
            downloadSocket.sendall("STOP".encode())

    def get_status(self):
        if self.status != DownloadStatus.COMPLETE:
            return SwarmStatus.LEECHER
        else:
            return SwarmStatus.SEEDER
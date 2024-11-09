import ast
import socket
import os
import json
import sys
from pathlib import Path
from pprint import pprint
from turtledemo.penrose import f
from typing import Tuple, Dict, Union, List
import threading
from utils import Connection, generate_torrent_file, hash_torrent
from utils.threads import DownloadTask, DownloadThread, ClientListenThread


class Client:
    __client_addr: Tuple[str, int]
    __listen_addr: Tuple[str, int]
    __connections: Dict
    __folder_path: Union[str , Path]
    __listener_thread: ClientListenThread
    __command_line_thread: threading.Thread

    def __init__(self, port: int, listen_port: int):
        # lan_ip = socket.gethostbyname(socket.gethostname())
        ip = "localhost"
        self.__client_addr = (ip, port)
        self.__listen_addr = (ip, listen_port)
        self.__folder_path = Path(os.getcwd()) / f'client_{port}'
        self.__connections = {}

        # Multitasking
        self.__command_line_thread = threading.Thread(target=self._command_line_program)
        self.__listener_thread = ClientListenThread(self.__folder_path,
                                                    addr=self.__listen_addr, client_name=f"client_{port}")

        # Case client not exist yet, then we add directory
        if not os.path.exists(self.__folder_path):
            os.makedirs(self.__folder_path)
        torrent_folder = Path(self.__folder_path) / 'torrents'
        if not os.path.exists(torrent_folder):
            os.makedirs(torrent_folder)

    def run(self):
        self.__listener_thread.daemon = True
        self.__listener_thread.start()                          # Start listener thread
        self.__command_line_thread.start()

        # Wait for command_line program to be terminated
        self.__command_line_thread.join()


    def create_torrent_file(self, file_name: str, server_addr: Tuple[str, int] = ("localhost", 25565), piece_size: int = 1024):
        """
        create torrent file for a sharing file

        :param file_name: name of the file
        :param server_addr: address and port of the server
        """
        file_path = Path(self.__folder_path) / file_name
        output_dir = self.__folder_path / 'torrents'

        print("-"*33)
        try:
            ip_addr, port = server_addr
            torrent_path = generate_torrent_file(file_path, output_dir, ip_addr, port, piece_size)

            print(f"[SUCCESSFULLY] New torrent file has been created in {torrent_path} !")
        except Exception as e:
            print(f"[ERROR] Can not create new torrent file due to error: {e}")
            pass
        finally:
            print("-" * 33)

    def upload_torrent(self, torrent_file):
        try:
            with open(Path(self.__folder_path) / 'torrents' / torrent_file, 'r') as tf:
                data: dict = json.load(tf)

            # Get server connection
            ip, port = data['tracker'].values()                 # Convert dictionary {"tracker": { "ip": ip_addr, "port": port} to (ip_addr, port)
            server_addr = (ip, int(port))
            print(f"Upload file to server {server_addr}")
            server_conn: Connection = self._connect_server(server_addr)
            if server_conn is None:
                print('[ERROR] Can not connect to server')
                return

            # Send data
            torrent_data_dump = json.dumps(data)
            server_conn.upload_command(torrent_data_dump, self.__listen_addr)

        except FileNotFoundError:
            print('[ERROR] Can not open torrent file')
        except Exception as e:
            print(f"[ERROR] Can not start upload torrent file due to error: {e}")

    def show_progress(self):
        ## TODO
        pass

    def start_download(self, torrent_file: str):
        print("-"*33)
        try:
            with open(Path(self.__folder_path) / 'torrents' / torrent_file, 'r') as tf:
                data: Dict = json.load(tf)

                # Get server connection
                ip, port = data['tracker'].values()  # Convert dictionary {"tracker": { "ip": ip_addr, "port": port} to (ip_addr, port)
                server_addr = (ip, int(port))
                print(f"Upload file to server {server_addr}")
                server_conn: Connection = self._connect_server(server_addr)

                if server_conn is None:
                    print('[ERROR] Can not connect to server')
                    return

                # Send data
                torrent_data_dump = json.dumps(data)
                seeders = server_conn.download_command(torrent_data_dump)

        except FileNotFoundError:
            print('[ERROR] Can not open torrent file')
            return
        except Exception as e:
            print(f'[ERROR] Can not start download file due to error: {e}')
            return

        if seeders is None:
            print("[ERROR] No seeders found for this swarm !")
        else:
            print(f"List of swarms: {seeders}")

            file_id: int = hash_torrent(data)
            download_task: DownloadThread = DownloadThread(file_id=file_id,
                                                           torrent_data=data,
                                                           seeders=seeders,
                                                           download_dir=self.__folder_path,
                                                           )

            download_task.daemon = True
            download_task.start()

        print("-"*33)

    def show_directory(self):
        print("-"*33)
        for f in os.listdir(self.__folder_path):
            print(f'-> {f}')
            if os.path.isdir(self.__folder_path / f):
                for file in os.listdir(self.__folder_path / f):
                    print(f'---> {file}')

        print("-"*33)

    def show_swarms(self):
        if len(self.__connections) == 0:
            print("-"*33)
            print("No connection has been established yet !")
            print("-"*33)

        else:
            print("-"*33)
            for idx, connection in enumerate(self.__connections.values()):
                connection.show_swarms()

                if idx < len(self.__connections) - 1:
                    print("-"*22)
            print("-"*33)

        pass

    def _connect_server(self, server_addr: Tuple[str, int]):
        if server_addr not in self.__connections.keys():
            try:
                self.__connections[server_addr] = Connection(server_addr)
                self.__connections[server_addr].run()
            except Exception as e:
                print(f"Can not connect to server {server_addr} due to error: {e}")
                if server_addr in self.__connections.keys():
                    del self.__connections[server_addr]

                return None

        return self.__connections[server_addr]

    def _command_line_program(self):
        while True:
            command = input(f"client_{self.__client_addr[1]}> ")
            info = command.split()

            if len(info) == 5 and info[0] == "create" and info[1] == "torrent":
                server_addr = info[3], int(info[4])
                self.create_torrent_file(file_name=info[2], server_addr=server_addr)
            if len(info) == 6 and info[0] == "create" and info[1] == "torrent":
                server_addr = info[3], int(info[4])
                piece_size = int(info[5])
                self.create_torrent_file(file_name=info[2], server_addr=server_addr, piece_size=piece_size)
            elif len(info) == 2 and info[0] == "upload":
                self.upload_torrent(torrent_file=info[1])
            elif len(info) == 2 and info[0] == "download":
                self.start_download(torrent_file=info[1])
            elif len(info) == 2 and info[0] == "show" and info[1] == "progress":
                self.show_progress()
            elif len(info) == 2 and info[0] == "show" and info[1] == "directory":
                self.show_directory()
            elif len(info) == 2 and info[0] == "show" and info[1] == "swarms":
                self.show_swarms()
            elif len(info) == 1 and info[0] == "quit":
                break
            else:
                print("[ERROR] Command not found")

        print("Program has been terminate !")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Please provide a port number for command line program and listening port !')
        sys.exit(1)

    # Read port number
    port = int(sys.argv[1])
    listen_port = int(sys.argv[2])
    client = Client(port, listen_port)
    client.run()

    sys.exit()
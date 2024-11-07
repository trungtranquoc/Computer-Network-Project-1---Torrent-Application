import socket
import os
import json
import sys
from pathlib import Path
from pprint import pprint
from typing import Tuple, Dict, Union
import threading
from utils import Connection, generate_torrent_file


class Client:
    __client_addr: Tuple[str, int]
    __connections: Dict
    __folder_path: Union[str , Path]
    # __listener: threading.Thread
    __input_reader: threading.Thread

    def __init__(self, port: int):
        # lan_ip = socket.gethostbyname(socket.gethostname())
        ip = "localhost"
        self.__client_addr = (ip, port)
        self.__folder_path = Path(os.getcwd()) / f'client_{port}'
        self.__connections = {}

        # Multitasking
        self.__input_reader = threading.Thread(target=self._command_line_program())

        # Case client not exist yet, then we add directory
        if not os.path.exists(self.__folder_path):
            os.makedirs(self.__folder_path)
        torrent_folder = Path(self.__folder_path) / 'torrents'
        if not os.path.exists(torrent_folder):
            os.makedirs(torrent_folder)

    def run(self):
        self.__input_reader.start()

        # Wait for command_line program to be terminated
        self.__input_reader.join()


    def create_torrent_file(self, file_name: str, server_addr: Tuple[str, int] = ("localhost", 25565)):
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
            torrent_path = generate_torrent_file(file_path, output_dir, ip_addr, port)

            print(f"[SUCCESS] New torrent file has been created in {torrent_path} !")
        except Exception as e:
            print(f"[ERROR] Can not create new torrent file due to error: {e}")
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
            server_conn = self._connect_server(server_addr)

            # Send data
            torrent_data_dump = json.dumps(data)
            server_conn.send_command("upload", torrent_data_dump)

        except FileNotFoundError:
            print('Can not open torrent file')
        except Exception as e:
            print(f"Can not start upload torrent file due to error: {e}")

    def show_progress(self):
        ## TODO
        pass

    def start_download(self, torrent_file: str):
        try:
            with open(Path(self.__folder_path) / 'torrents' / torrent_file, 'r') as tf:
                data: Dict = json.load(tf)

                # Get server connection
                ip, port = data[
                    'tracker'].values()  # Convert dictionary {"tracker": { "ip": ip_addr, "port": port} to (ip_addr, port)
                server_addr = (ip, int(port))
                print(f"Upload file to server {server_addr}")
                server_conn = self._connect_server(server_addr)

                # Send data
                torrent_data_dump = json.dumps(data)
                server_conn.send_command("download", torrent_data_dump)
        except FileNotFoundError:
            print('Can not open torrent file')
        except Exception as e:
            print(f'{e}\nCan not start download file')

        # Create DownloadTask here
        ## TODO
        # Step 1: Create Thread

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
            self.__connections[server_addr] = Connection(server_addr)
            self.__connections[server_addr].run()

        return self.__connections[server_addr]

    def _command_line_program(self):
        while True:
            command = input(f"client_{self.__client_addr[1]}> ")
            info = command.split()

            if len(info) == 5 and info[0] == "create" and info[1] == "torrent":
                server_addr = info[3], int(info[4])
                self.create_torrent_file(file_name=info[2], server_addr=server_addr)
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
    if len(sys.argv) < 2:
        print('Please provide a port number')
        sys.exit(1)

    # Read port number
    port = int(sys.argv[1])
    client = Client(port)
    client.run()

    sys.exit()
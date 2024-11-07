import json
import socket
import threading
from typing import Tuple, Dict
import sys
from utils import hash_torrent
import pprint

HOST = "localhost"
PORT = 1232

class Server:
    __addr: Tuple[str, int]
    __connections: Dict[Tuple[str, int], socket.socket]
    __listener_thread: threading.Thread
    __command_line_thread: threading.Thread
    __swarms: dict

    def __init__(self):
        self.__addr = (HOST, PORT)
        self.__listener_thread = threading.Thread(target=self._listening_for_connections)
        self.__command_line_thread = threading.Thread(target=self._command_line_program)

        self.__connections = {}
        self.__swarms = {}

    def run(self):
        self.__listener_thread.daemon = True           # Terminate when main thread end
        self.__listener_thread.start()
        self.__command_line_thread.start()

        # Only command line thread due to control stop of the program
        self.__command_line_thread.join()

    def add_new_swarm(self, torrent_data: dict, client_addr: Tuple[str, int]):
        """

        :param torrent_data: json file of torrent data
        :param client_addr: (host, port) info of client
        :return: key of swarm in the list
        """
        key = hash_torrent(torrent_data)
        if key not in self.__swarms.keys():                                 # Swarm not exists yet
            self.__swarms[key] = torrent_data
            self.__swarms[key]["seeders"] = []

            self.__swarms[key]["seeders"].append(client_addr)
            print(f"[SUCCESSFULLY] New swarm has been created: {key}")
        else:                                                               # Swarm already exist
            if client_addr not in self.__swarms[key]["seeders"]:
                self.__swarms[key]["seeders"].append(client_addr)
                print(f"[SUCCESSFULLY] Add seeder to swarm {key}")
            else:
                print(f"[ERROR] Seeder already in swarm {key}")

        return key

    def show_swarm(self):
        print("-"*33)
        if len(self.__swarms) == 0:
            print("No swarms")
        for idx, swarm_data in enumerate(self.__swarms.items()):
            key, swarm = swarm_data
            print(f"[{idx+1}] Key: {key}")
            pprint.pprint(swarm)

            if idx < len(self.__swarms)-1:
                print("-"*22)

        print("-"*33)

    def _listening_for_connections(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(self.__addr)
        server_socket.listen()

        print(f"[LISTENING] Server is listening on {self.__addr}")
        while True:
            client_socket, addr = server_socket.accept()

            # Save in the connections list
            client_ip, client_port = addr
            addr = client_ip, int(client_port)
            self.__connections[addr] = client_socket

            print(f"[ACCEPTED] Accepted connection from {addr}")

            connect_thread = threading.Thread(target=self._connection, args=(client_socket, addr))
            connect_thread.daemon = True
            connect_thread.start()

    def _connection(self, conn: socket.socket, client_addr: Tuple[str, int]):
        client_name = f"{client_addr[0]}:{client_addr[1]}"

        while True:
            command = conn.recv(4096).decode()           # Receive command here
            info = command.split("::")

            print("-"*33)
            print(f"{client_name}> data: {info}")

            if len(info) == 2 and info[0] == "upload":
                torrent_data = json.loads(info[1])
                try:
                    key = self.add_new_swarm(torrent_data, client_addr)
                except Exception as e:
                    print(f"[Error] Error when create swarm: {e}")

            elif len(info) == 2 and "download":
                ## TODO
                pass
            elif info[0] == "quit":
                break
            else:
                print("[ERROR] Unknown command")

            print("-"*33)

        conn.close()

    def _command_line_program(self):
        while True:
            command = input(f"")
            info = command.split()

            if len(info) == 1 and info[0] == "quit":
                break
            if len(info) == 2 and info[0] == "show" and info[1] == "swarm":
                self.show_swarm()
            else:
                print("[ERROR] Command not found")

        print("Program has been terminate !")

if __name__ == "__main__":
    server = Server()
    server.run()

    sys.exit()

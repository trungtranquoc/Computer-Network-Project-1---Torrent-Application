import json
import socket
import threading
from typing import Dict, Union, List
import sys
from utils import hash_torrent
import pprint
from custom import HostAddress, MAXSIZE_TORRENT
from custom import server_help

class Server:
    __addr: HostAddress
    __connections: Dict[HostAddress, socket.socket]
    __listener_thread: threading.Thread
    __command_line_thread: threading.Thread
    __swarms: dict

    # Locking for safe using the sharing resources
    __swarms_lock: threading.Lock
    __command_line_lock: threading.Lock

    def __init__(self, port: int, ip: str = "localhost"):
        self.__addr = (ip, port)
        self.__listener_thread = threading.Thread(target=self.__listening_for_connections, daemon=True)
        self.__command_line_thread = threading.Thread(target=self.__command_line_program)
        self.__command_line_lock = threading.Lock()

        self.__connections = {}

        self.__swarms = {}
        self.__swarms_lock = threading.Lock()

    def run(self):
        self.__command_line_thread.start()
        self.__listener_thread.start()

        # Only command line thread due to control stop of the program
        self.__command_line_thread.join()

    def add_new_swarm(self, torrent_data: dict, client_addr: HostAddress) -> int:
        """

        :param torrent_data: json file of torrent data
        :param client_addr: (host, port) info of client
        :return: key of swarm in the list
        """
        key = hash_torrent(torrent_data)
        msg = None
        if key not in self.__swarms.keys():  # Swarm not exists yet
            with self.__swarms_lock:
                self.__swarms[key] = torrent_data
                self.__swarms[key]["seeders"] = []
                self.__swarms[key]["seeders"].append(client_addr)

            print(f"[SUCCESSFULLY] New swarm has been created: {key}")
        else:  # Swarm already exist
            if client_addr not in self.__swarms[key]["seeders"]:
                with self.__swarms_lock:
                    self.__swarms[key]["seeders"].append(client_addr)
                print(f"[SUCCESSFULLY] Add seeder to swarm {key}")
            else:
                print(f"[ERROR] Seeder already in swarm {key}")

        return key

    def get_swarm(self, key: int) -> Union[List[HostAddress], None]:
        """

        :param key: key of torrent_data
        :return: none of swarm do not exist, otherwise: none
        """
        with self.__swarms_lock:
            if key not in self.__swarms.keys():
                return None
            else:
                return self.__swarms[key]["seeders"]  # Return list of seeders

    def show_swarm(self):
        with self.__swarms_lock:
            if len(self.__swarms) == 0:
                print("No swarms")
            for idx, swarm_data in enumerate(self.__swarms.items()):
                key, swarm = swarm_data
                print(f"[{idx + 1}] Key: {key}")
                pprint.pprint(swarm)

                if idx < len(self.__swarms) - 1:
                    print("-" * 22)

    def __print_message(self, message: str):
        """
        Print and restore the input string "client_port" into new line
        :param message: string to print
        """
        with self.__command_line_lock:
            sys.stdout.write("\033[2K\r")  # Clear the current line
            print(message)  # Print the received message on a new line
            sys.stdout.write(f"server_{self.__addr[1]}> ")  # Restore the prompt
            sys.stdout.flush()

    def __listening_for_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind(self.__addr)
            server_socket.listen()

            self.__print_message(f"[LISTENING] Server is listening on {self.__addr}")
            while True:
                client_socket, addr = server_socket.accept()

                # Save in the connections list
                client_ip, client_port = addr
                addr = client_ip, int(client_port)
                self.__connections[addr] = client_socket

                self.__print_message(f"[ACCEPTED] Accepted connection from {addr}")

                connect_thread = threading.Thread(target=self.__connection, args=(client_socket, addr), daemon=True)
                connect_thread.start()

    def __connection(self, conn: socket.socket, client_addr: HostAddress):
        client_name = f"{client_addr[0]}:{client_addr[1]}"

        try:
            rcv_data = conn.recv(1024).decode()
            listen_ip, listen_port = rcv_data.split("::")
            listen_addr = (listen_ip, int(listen_port))                 # Use for remove user from swarm after disconnection
            print(f"Listen address: {listen_addr}")

            conn.sendall('OK'.encode())
        except Exception as e:
            print(f"[ERROR] Fail for request listener address due to error: {e}")
            conn.sendall(''.encode())
            conn.close()

            return

        while True:
            command = conn.recv(MAXSIZE_TORRENT).decode()  # Receive command here
            if not command:
                break

            with self.__command_line_lock:
                # Clear the "server> " command line
                sys.stdout.write("\033[2K\r")  # Clear the current line

                info = command.split("::")
                print("-" * 33)

                if len(info) == 2 and info[0] == "upload":
                    try:
                        torrent_data = json.loads(info[1])
                        key = self.add_new_swarm(torrent_data, listen_addr)
                        # Send key of client back to the client
                        conn.sendall(str(key).encode())
                    except Exception as e:
                        print(f"[Error] Error when create swarm: {e}")
                        conn.sendall("".encode())

                elif len(info) == 2 and info[0] == "download":
                    print(f"{client_name}: download file using torrent")

                    torrent_data = json.loads(info[1])
                    key = hash_torrent(torrent_data)
                    swarm_lists = self.get_swarm(key)

                    if swarm_lists is None:
                        conn.sendall("Error".encode())
                    else:
                        conn.sendall(f"{key}::{json.dumps(swarm_lists)}".encode())

                elif len(info) == 3 and info[0] == "download" and info[1] == "key":
                    print(f"{client_name}: download file using key")

                    key = int(json.loads(info[2]))

                    if key not in self.__swarms.keys():
                        conn.sendall("Error".encode())
                    else:
                        conn.sendall(json.dumps(self.__swarms[key]).encode())

                elif len(info) == 1 and info[0] == "get_swarms":
                    print(f"{client_name}: request swarm list")
                    data = []   # Return list data
                    swarm_info_data = {}

                    try:
                        for key in self.__swarms.keys():
                            swarm_info_data["size"] = self.__swarms[key]["size"]
                            swarm_info_data["key"] = key
                            swarm_info_data["seeders"] = len(self.__swarms[key]["seeders"])
                            swarm_info_data["name"] = self.__swarms[key]["name"] + self.__swarms[key]["extension"]

                            data.append(swarm_info_data)
                            swarm_info_data = {}

                        conn.sendall(json.dumps(data).encode())
                    except Exception as e:
                        conn.sendall("Error".encode())

                else:
                    print("[ERROR] Unknown command")

                print("-" * 33)

                sys.stdout.write(f"server_{self.__addr[1]}> ")  # Restore the prompt
                sys.stdout.flush()

        print(f"Client {client_name} disconnected !")
        # Remove this client from seeders list
        self.__remove_seeder(listen_addr)

        conn.close()

    def __remove_seeder(self, listen_addr: HostAddress) -> None:
        print('Update swarm seeders...')

        for swarm_key in self.__swarms.keys():
            if listen_addr in self.__swarms[swarm_key]["seeders"]:
                self.__swarms[swarm_key]["seeders"].remove(listen_addr)

    def __command_line_program(self):
        while True:
            command = input(f"\nserver_{self.__addr[1]}> ")

            if command == "quit":
                break

            with self.__command_line_lock:
                print("-"*33)
                info = command.split()
                if len(info) == 1 and info[0] == "help":
                    server_help()
                elif len(info) == 2 and info[0] == "show" and info[1] == "swarm":
                    self.show_swarm()
                else:
                    print(f"[ERROR] Command not found: {command}")

                print("-"*33)

        print("Program has been terminated!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        port = 1232
    else:
        port = int(sys.argv[1])

    ip_addr = socket.gethostbyname(socket.gethostname())

    server = Server(port=port, ip=ip_addr)
    server.run()

    sys.exit()

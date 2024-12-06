"""
    Display command function
"""


def client_help():
    """
    Display available client commands and their descriptions in argparse style with colors.
    """

    HEADER_____ = "\033[95m"      # Light Magenta
    COMMAND____ = "\033[94m"      # Light Blue
    DESCRIPTION = "\033[92m"      # Light Green
    EXAMPLE____ = "\033[93m"      # Yellow
    NOTE_______ = "\033[91m"      # Red
    END = "\033[0m"               # Reset to default

    print(f"{HEADER_____}\nCommands:{END}")

    print(f"{COMMAND____}  create torrent <file_name> <server_ip> <server_port> [piece_size]{END}")
    print(f"{DESCRIPTION}                      Create a torrent(json) file for <file_name> with optional [piece_size] (default: 1024).{END}")
    print(f"{EXAMPLE____}                      Example: create torrent alice.txt localhost 1232{END}")
    print(f"{EXAMPLE____}                               create torrent alice.txt localhost 1232 2048{END}\n")

    print(f"{COMMAND____}  upload <torrent_file_name>{END}")
    print(f"{DESCRIPTION}                      Upload a torrent(json) file to the server to create or join a swarm.{END}")
    print(f"{EXAMPLE____}                      Example: upload alice.json{END}\n")

    print(f"{COMMAND____}  download <torrent_file_name>{END}")
    print(f"{DESCRIPTION}                      Start downloading a file using a torrent(json) file.{END}")
    print(f"{EXAMPLE____}                      Example: download alice.txt{END}")
    print(f"{NOTE_______}                      Note: A client (Leecher) may only download the same file once!{END}")
    print(f"{NOTE_______}                            Once the client has downloaded that file, it will become a Seeder.{END}\n")

    print(f"{COMMAND____}  download key  <server_ip>::<server_port>::<swarm_key>{END}")
    print(f"{DESCRIPTION}                      Start downloading a file using server address and swarm key.{END}")
    print(f"{EXAMPLE____}                      Example: download key localhost::1232::-6838630007736510526{END}")
    print(f"{NOTE_______}                      Note: A client (Leecher) may only download the same file once!{END}")
    print(f"{NOTE_______}                            Once the client has downloaded that file, it will become a Seeder.{END}\n")

    print(f"{COMMAND____}  skip <file_id>{END}")
    print(f"{DESCRIPTION}                      Skip an ongoing download identified by the swarm key <file_id>.{END}")
    print(f"{DESCRIPTION}                      The skipped file can be downloaded again via the download command.{END}")
    print(f"{EXAMPLE____}                      Example: skip -6838630007736510526{END}\n")

    print(f"{COMMAND____}  show progress{END}")
    print(f"{DESCRIPTION}                      Show download progress for all active downloads.{END}")
    print(f"{EXAMPLE____}                      Example: show progress{END}\n")

    print(f"{COMMAND____}  show directory{END}")
    print(f"{DESCRIPTION}                      List all files and directories in the client's working folder.{END}")
    print(f"{EXAMPLE____}                      Example: show directory{END}\n")

    print(f"{COMMAND____}  show swarm{END}")
    print(f"{DESCRIPTION}                      Display information about the swarms the client is currently part of,{END}")
    print(f"{DESCRIPTION}                      and its role being Seeder or Leecher in that swarm.{END}")
    print(f"{EXAMPLE____}                      Example: show swarm{END}\n")

    print(f"{COMMAND____}  show server swarm{END}")
    print(f"{DESCRIPTION}                      Retrive list of swarms from all connected servers,{END}")
    print(f"{NOTE_______}                      Note: This command will request all connected servers, {END}")
    print(f"{NOTE_______}                      so, make sure to connect to server before requesting {END}")
    print(f"{EXAMPLE____}                      Example: show server swarm{END}\n")

    print(f"{COMMAND____}  quit{END}")
    print(f"{DESCRIPTION}                      Exit the client program.{END}")
    print(f"{EXAMPLE____}                      Example: quit{END}")


def server_help():
    """
    Display available server commands and their descriptions in argparse style with colors.
    """
    HEADER_____ = "\033[95m"    # Light Magenta
    COMMAND____ = "\033[94m"    # Light Blue
    DESCRIPTION = "\033[92m"    # Light Green
    EXAMPLE____ = "\033[93m"    # Yellow
    END = "\033[0m"             # Reset to default

    print(f"{HEADER_____}\nCommands:{END}")

    print(f"{COMMAND____}  show swarm{END}")
    print(f"{DESCRIPTION}                      Display all active swarms with their details.{END}")
    print(f"{EXAMPLE____}                      Example: show swarm{END}\n")

    print(f"{COMMAND____}  quit{END}")
    print(f"{DESCRIPTION}                      Stop the server and terminate the program.{END}")
    print(f"{EXAMPLE____}                      Example: quit{END}")


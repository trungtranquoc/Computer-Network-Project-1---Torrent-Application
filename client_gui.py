from client import Client
import socket
import sys

from GUI import App

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Please provide a port number for command line program and listening port !')
        sys.exit(1)

    client = Client(int(sys.argv[1]), int(sys.argv[2]), socket.gethostbyname(socket.gethostname()))
    client.daemon = True    # terminate when GUI Thread end
    client.start()  # No command line mode

    print("Come here")

    app = App(client)
    app.mainloop()

    sys.exit()
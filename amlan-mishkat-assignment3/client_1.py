
import sys
import getopt
import socket
import random
from threading import Thread
import util



class Client:

    def __init__(self, username, dest, port, window_size):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username
        self.open = True

    def start(self):

        # Send JOIN message to the server
        join_message = util.make_message(util.JOIN_MESSAGE, util.TYPE_ONE_MSG_FORMAT, self.name)
        join_packet = util.make_packet(util.DATA_PACKET_TYPE, 0, join_message)
        self.sock.sendto(join_packet.encode(), (self.server_addr, self.server_port))

        # Main loop for user interaction
        while self.open:
            user_input = input()

            # Process user input
            if user_input == "help":
                print('''1) msg <number_of_users> <username1> <username2> ... <message>
                                2) list
                                3) help
                                4) quit''')

            elif user_input == "list":
                message = util.make_message(util.REQUEST_USERS_LIST_MESSAGE, util.TYPE_TWO_MSG_FORMAT)
                packet = util.make_packet(util.DATA_PACKET_TYPE, 0, message)
                self.sock.sendto(packet.encode(), (self.server_addr, self.server_port))
            elif user_input.startswith('msg'):
                self.send_message(user_input)
            elif user_input == "quit":
                self.send_quit_message()
                print("quitting")
                return
            else:
                print("incorrect userinput format")

    def send_message(self, input):
        input_arr = input.split()

        if len(input_arr) < 4:
            print("incorrect userinput format")
            return
        try:
            total_users = int(input_arr[1])
        except ValueError:
            print("incorrect userinput format")
            return
        if len(input_arr) < 2 + total_users:
            print("incorrect userinput format")
            return
        all_users = ' '.join(input_arr[2: 2 + total_users])
        message = ' '.join(input_arr[2 + total_users:])

        # Check if message length exceeds maximum allowed size
        if len(message.encode()) > 1500:
            print("Message size exceeds the maximum allowed size of 1500 bytes.")
            return

        message_packet = util.make_packet(util.DATA_PACKET_TYPE, 0, util.make_message(
            util.SEND_MESSAGE_MESSAGE, util.TYPE_FOUR_MSG_FORMAT,
            "{} {} {}".format(total_users, all_users, message)
        ))
        self.sock.sendto(message_packet.encode(), (self.server_addr, self.server_port))

    def send_quit_message(self):
        quit_message = util.make_message(util.DISCONNECT_MESSAGE, util.TYPE_ONE_MSG_FORMAT, self.name)
        quit_packet = util.make_packet(util.DATA_PACKET_TYPE, 0, quit_message)
        self.sock.sendto(quit_packet.encode(), (self.server_addr, self.server_port))

    def receive_handler(self):
        while True:
            try:
                msg, _ = self.sock.recvfrom(util.CHUNK_SIZE)
                packet, sequence_number, data, checksum = util.parse_packet(msg.decode())

                if packet == util.DATA_PACKET_TYPE:
                    message = data.split()[0]
                    if message == util.ERR_SERVER_FULL_MESSAGE:
                        print("disconnected: server full")
                        raise SystemExit
                    elif message == util.ERR_USERNAME_UNAVAILABLE_MESSAGE:
                        print("disconnected: username not available")
                        self.should_close_connection = True
                        return
                    elif message == util.FORWARD_MESSAGE_MESSAGE:
                        sender = data.split()[3]
                        msg = ' '.join(data.split()[4:])
                        print("msg: {}: {}".format(sender,msg))
                    elif message == util.RESPONSE_USERS_LIST_MESSAGE:
                        usernames_list = ' '.join([e for e in data.split()[2:]])
                        print("list: {}".format(usernames_list))

                    else:
                        pass
                else:
                    pass
            except Exception:
                self.sock.close()
                self.open = False
                raise sys.exit()

# Do not change below part of code
if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our Client module completion
        '''
        print("Client")
        print("-u username | --user=username The username of Client")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW_SIZE | --window=WINDOW_SIZE The window_size, defaults to 3")
        print("-h | --help Print this help")
    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "u:p:a:w", ["user=", "port=", "address=","window="])
    except getopt.error:
        helper()
        exit(1)

    PORT = 15000
    DEST = "localhost"
    USER_NAME = None
    WINDOW_SIZE = 3
    for o, a in OPTS:
        if o in ("-u", "--user="):
            USER_NAME = a
        elif o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW_SIZE = a

    if USER_NAME is None:
        print("Missing Username.")
        helper()
        exit(1)

    S = Client(USER_NAME, DEST, PORT, WINDOW_SIZE)
    try:
        # Start receiving Messages
        T = Thread(target=S.receive_handler)
        T.daemon = True
        T.start()
        # Start Client
        S.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()

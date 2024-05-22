'''
This module defines the behaviour of server in your Chat Application
'''
import sys
import getopt
import socket
import util

class Server:
    '''
    This is the main Server Class. You will write Server code inside this class.
    '''
    def __init__(self, dest, port, window):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind((self.server_addr, self.server_port))
        self.active_clients = {}

    def start(self):
        while True:
            msg, client = self.sock.recvfrom(util.CHUNK_SIZE)
            packet, sequence_number, data, checksum = util.parse_packet(msg.decode())
            sender_username = self.get_sender_username(client)

            if packet == util.DATA_PACKET_TYPE: #process packet
                self.process_data_packet(data, client, sender_username)
            elif packet == util.START_PACKET_TYPE or packet == util.END_PACKET_TYPE or packet == util.ACK_PACKET_TYPE:
                pass
            else:   #report warning
                response = util.make_packet(util.DATA_PACKET_TYPE, 0,
                                            util.make_message(util.SEND_MESSAGE_MESSAGE, util.TYPE_ONE_MSG_FORMAT,
                                                              "incorrect userinput format"))
                self.sock.sendto(response.encode(), client)

    def get_sender_username(self, client):
        keys = list(self.active_clients.keys()) #all keys
        values = list(self.active_clients.values())
        try:
            return keys[values.index(client)]
        except ValueError:  #when it hasnt been processed
            return None

    def process_data_packet(self, data, client, sender_username):
        message = data.split()[0]

        if message == util.JOIN_MESSAGE:
            self.process_join_message(data, client)
        elif message == util.DISCONNECT_MESSAGE:
            self.process_disconnect_message(sender_username)
        elif message == util.REQUEST_USERS_LIST_MESSAGE:
            self.process_users_list_request(client, sender_username)
        elif message == util.SEND_MESSAGE_MESSAGE:
            self.process_send_message(data, sender_username)
        else:
            self.handle_invalid_message(client)

    def process_join_message(self, data, client):
        if len(self.active_clients) == util.MAX_NUM_CLIENTS:
            response = util.make_packet(util.DATA_PACKET_TYPE, 0,
                                        util.make_message(util.ERR_SERVER_FULL_MESSAGE,
                                                          util.TYPE_TWO_MSG_FORMAT))
            self.sock.sendto(response.encode(), client)
            print("disconnected: server full")
            return

        client_username = data.split()[-1]
        if client_username in self.active_clients:
            response = util.make_packet(util.DATA_PACKET_TYPE, 0,
                                        util.make_message(util.ERR_USERNAME_UNAVAILABLE_MESSAGE,
                                                          util.TYPE_TWO_MSG_FORMAT))
            self.sock.sendto(response.encode(), client)
            print("disconnected: username not available")
            return

        self.active_clients[client_username] = client
        print("join: {}".format(client_username))

    def process_disconnect_message(self, sender_username):
        self.active_clients.pop(sender_username, None)
        print("disconnected:", sender_username)

    def process_users_list_request(self, client, sender_username):
        response = util.make_packet(util.DATA_PACKET_TYPE, 0,
                                    util.make_message(util.RESPONSE_USERS_LIST_MESSAGE,
                                                      util.TYPE_THREE_MSG_FORMAT,
                                                      ' '.join(sorted(self.active_clients.keys()))))
        self.sock.sendto(response.encode(), client)
        print("request_users_list: {}".format(sender_username))

    def process_send_message(self, data, sender_username):
        num_recipients = int(data.split()[2])
        data = data.split()[3:]
        recipients = data[0:num_recipients]
        message = ' '.join(data[num_recipients:])

        invalid_clients = []
        for r in recipients:
            if r in self.active_clients:
                recipient_addr, recipient_port = self.active_clients.get(r)
                fwd_response_msg = "1 {} {}".format(sender_username, message)
                response = util.make_packet(util.DATA_PACKET_TYPE, 0, util.make_message(
                    util.FORWARD_MESSAGE_MESSAGE, util.TYPE_FOUR_MSG_FORMAT, fwd_response_msg
                ))
                self.sock.sendto(response.encode(), (recipient_addr, recipient_port))
                print("msg: {}".format(sender_username))
            else:
                invalid_clients.append(r)

        for non_existent_client in invalid_clients:
            print("msg: {} to non-existent user {}".format(
                sender_username, non_existent_client
            ))

    def handle_invalid_message(self, client):
        response = util.make_packet(util.DATA_PACKET_TYPE, 0,
                                    util.make_message(util.SEND_MESSAGE_MESSAGE, util.TYPE_ONE_MSG_FORMAT,
                                                      "incorrect userinput format"))
        self.sock.sendto(response.encode(), client)



# Do not change below part of code

if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our module completion
        '''
        print("Server")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW | --window=WINDOW The window size, default is 3")
        print("-h | --help Print this help")

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "p:a:w", ["port=", "address=","window="])
    except getopt.GetoptError:
        helper()
        exit()

    PORT = 15000
    DEST = "localhost"
    WINDOW = 3

    for o, a in OPTS:
        if o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW = a

    SERVER = Server(DEST, PORT,WINDOW)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        exit()

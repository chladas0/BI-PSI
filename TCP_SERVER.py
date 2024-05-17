from constants import *
import socket
import threading


class ServerSyntaxError(Exception):
    pass


class ServerLogicError(Exception):
    pass


class ServerLoginFailed(Exception):
    pass


class ServerKeyRangeError(Exception):
    pass


def validate_username(username):
    if not len(username) <= 18:
        raise ServerSyntaxError
    return username


def validate_move(message):
    parts = message.split()
    if parts[0] != 'OK' or not message.rstrip() == message:
        raise ServerSyntaxError

    try:
        parts[1], parts[2] = int(parts[1]), int(parts[2])
        return parts[1:]
    except ValueError:
        raise ServerSyntaxError


def validate_key(key):
    try:
        key = int(key)
        if key not in range(0, 10):
            raise ServerKeyRangeError
        return key
    except ValueError:
        raise ServerSyntaxError


def validate_code(code):
    if len(str(code)) > 5 or not code.isdigit():
        raise ServerSyntaxError
    try:
        code = int(code)
        return code
    except ValueError:
        raise ServerSyntaxError


def validate_message(message):
    if len(message) > 100:
        raise ServerSyntaxError


def thread_handler(client, client_address):
    client.settimeout(TIMEOUT)
    connection = TcpServerConnection(client)
    print("New Connection established: ", client_address, " connected")
    connection.run()


class TcpServerConnection:
    def __init__(self, client: socket):
        self.client: socket = client
        self.client_keys = (32037, 29295, 13603, 29533, 21952)
        self.server_keys = (23019, 32037, 18789, 16443, 18189)
        self.username: str = ''
        self.key_id: int = 0
        self.message: str = ''
        self.stage: int = 0
        self.x: int = -1
        self.y: int = -1
        self.prev_x: int = -1
        self.prev_y: int = -1
        self.direction: int = -1

    def run(self):
        with self.client:
            try:
                self.authenticate()
                self.navigate()
            except ServerSyntaxError:
                self.client.sendall(SERVER_SYNTAX_ERROR)
            except ServerLogicError:
                self.client.sendall(SERVER_LOGIC_ERROR)
            except ServerLoginFailed:
                self.client.sendall(SERVER_LOGIN_FAILED)
            except ServerKeyRangeError:
                self.client.sendall(SERVER_KEY_OUT_OF_RANGE_ERROR)
            except TimeoutError:
                pass

    def authenticate(self):

        while True:
            message = self.read_message()

            # logging the user in
            if self.stage == NOT_LOGGED_IN:
                self.username = validate_username(message)
                self.client.sendall(SERVER_KEY_REQUEST)
                self.stage += 1

            # waiting for key_id
            elif self.stage == KEY_REQUEST:
                self.key_id = validate_key(message)
                self.client.sendall((str(self.confirmation_code(self.server_keys)) + SERVER_CONFIRMATION).encode('utf-8'))
                self.stage += 1

            # waiting for client confirmation
            elif self.stage == CLIENT_CONFIRMATION:
                if validate_code(message) == self.confirmation_code(self.client_keys):
                    self.client.sendall(SERVER_OK)
                    self.stage += 1
                    break
                else:
                    raise ServerLoginFailed

    def navigate(self):
        # moving to [0,0]
        self.initial_move()
        while True:
            if self.desired_destination():
                # we reached the end
                self.client.sendall(SERVER_PICK_UP)
                validate_message(self.read_message())
                self.client.sendall(SERVER_LOGOUT)
                break

            # direction x -> 0 or y -> 0
            if self.perspective_direction(self.direction):
                self.go_straight()
            else:
                self.rotate_right()

    def read_message(self):
        not_complete = False
        while True:
            # reading next message into buffer
            if len(self.message) == 0 or not_complete:
                new_part = self.client.recv(2048).decode('utf-8')
                if len(new_part) == 0 or not self.perspective_data(new_part):
                    raise ServerSyntaxError
                self.message += new_part
            # check for message ending
            for i in range(len(self.message)-1):
                if self.message[i:i+2] == '\a\b':
                    new_message = self.message[:i]
                    self.message = self.message[i+2:]
                    if new_message == "RECHARGING":
                        new_message = self.handle_recharging()
                    return new_message
            not_complete = True

    def perspective_data(self, message):
        # optimization
        for i in range(len(message)-1):
            if message[i:i+2] == '\a\b':
                return True

        if self.stage == NOT_LOGGED_IN:
            if len(message) >= 20:
                return False

        if self.stage == COMMUNICATION:
            if not self.desired_destination():
                if len(message) >= 12:
                    return False

            elif len(message) >= 100:
                return False

        return True

    def handle_recharging(self):
        # recharging until full power
        self.client.settimeout(TIMEOUT_RECHARGING)
        message = self.read_message()

        if message != "FULL POWER":
            raise ServerLogicError

        self.client.settimeout(TIMEOUT)
        return self.read_message()

    def get_direction(self):
        # determine direction from coordinates
        if self.prev_x < self.x:
            self.direction = RIGHT

        elif self.prev_x > self.x:
            self.direction = LEFT

        elif self.prev_y > self.y:
            self.direction = DOWN

        else:
            self.direction = UP

    def initial_move(self):
        # checking direction
        self.client.sendall(SERVER_TURN_RIGHT)
        self.prev_x, self.prev_y = validate_move(self.read_message())

        # trying to move forward
        self.client.sendall(SERVER_MOVE)
        self.update_coordinates()
        if self.x == self.prev_x and self.y == self.prev_y:
            self.detour(SERVER_TURN_LEFT, 3)
        self.get_direction()

    def perspective_direction(self, direction):
        # checking desired direction
        if direction == LEFT and self.x > 0:
            return True
        if direction == RIGHT and self.x < 0:
            return True
        if direction == UP and self.y < 0:
            return True
        if direction == DOWN and self.y > 0:
            return True
        return False

    def detour(self, direction, offset):
        # detouring based on perspective direction
        self.direction = (self.direction + offset) % 4

        self.client.sendall(direction)
        self.read_move()

        self.client.sendall(SERVER_MOVE)
        self.read_move()

    def go_straight(self):
        # going straight or detouring
        self.client.sendall(SERVER_MOVE)
        self.read_move()

        if self.x == self.prev_x and self.y == self.prev_y:
            if self.perspective_direction((self.direction + 1) % 4):
                self.detour(SERVER_TURN_RIGHT, 1)
            else:
                self.detour(SERVER_TURN_LEFT, 3)

    def confirmation_code(self, keys):
        return (sum([ord(c) for c in self.username]) * 1000 + keys[self.key_id]) % 65536

    def desired_destination(self):
        return self.x == 0 and self.y == 0

    def update_coordinates(self):
        self.x, self.y = validate_move(self.read_message())

    def rotate_right(self):
        self.client.sendall(SERVER_TURN_RIGHT)
        self.direction = (self.direction + 1) % 4
        self.update_coordinates()

    def read_move(self):
        self.prev_x, self.prev_y = self.x, self.y
        self.update_coordinates()


def main():
    # TCP/IP protokol, stream oriented connection
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # associate ip_address and port with socket
    server_socket.bind(('', PORT))
    server_socket.listen()

    # wait for client to connect
    while True:
        client, client_address = server_socket.accept()
        thread = threading.Thread(target=thread_handler, args=(client, client_address))
        thread.start()


if __name__ == '__main__':
    main()










# Constants ------------------------------------------------------------------------------------------------------------


NOT_LOGGED_IN = 0
KEY_REQUEST = 1
CLIENT_CONFIRMATION = 2
COMMUNICATION = 3


UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3


PORT = 5000
IP_ADDRESS = '120.1.1.7'


TIMEOUT = 1
TIMEOUT_RECHARGING = 5


SERVER_CONFIRMATION = '\a\b'

SERVER_MOVE = '102 MOVE\a\b'.encode('utf-8')

SERVER_TURN_LEFT = '103 TURN LEFT\a\b'.encode('utf-8')

SERVER_TURN_RIGHT = '104 TURN RIGHT\a\b'.encode('utf-8')

SERVER_PICK_UP = '105 GET MESSAGE\a\b'.encode('utf-8')

SERVER_LOGOUT = '106 LOGOUT\a\b'.encode('utf-8')

SERVER_KEY_REQUEST = '107 KEY REQUEST\a\b'.encode('utf-8')

SERVER_OK = '200 OK\a\b'.encode('utf-8')

SERVER_LOGIN_FAILED = '300 LOGIN FAILED\a\b'.encode('utf-8')

SERVER_SYNTAX_ERROR = '301 SYNTAX ERROR\a\b'.encode('utf-8')

SERVER_LOGIC_ERROR = '302 LOGIC ERROR\a\b'.encode('utf-8')

SERVER_KEY_OUT_OF_RANGE_ERROR = '303 KEY OUT OF RANGE\a\b'.encode('utf-8')

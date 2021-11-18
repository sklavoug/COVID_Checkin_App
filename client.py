# client.py
# A client program for server.py and the BlueTrace simulator.
# Handles user input, server communications, and UDP beaconing.
# Usage: python3
# by George Sklavounos


from socket import *
import threading
import datetime as dt
import sys
import time


# clean_log
# A function to remove all expired records from contactlog.txt
# Note this requires the write time to be written to the file
def clean_log():
    try:
        read = open('contactlog.txt', 'r')
    except FileNotFoundError:
        read = open('contactlog.txt', 'w')
        read.close()
        read = open('contactlog.txt', 'r')
    lines = read.readlines()
    with open('contactlog.txt', 'w') as write:
        for raw_line in lines:
            line = raw_line.split()
            stored_time = dt.datetime.strptime((line[0] + ' ' + line[1]), "%d/%m/%Y %H:%M:%S")
            if dt.datetime.now() < (stored_time + dt.timedelta(minutes=3)):
                write.write(raw_line)        

# recv_handler
# Handles UDP beacon packets sent to the client
# Checks expiry time for tempID in beacon; if it's valid, writes it to 
# contactlog.txt
def recv_handler():
    global t_lock
    global clientSocket
    global serverSocket
    # print('Client online')
    while(1):
        
        raw_message, clientAddress = serverSocket.recvfrom(2048)
        raw_message = raw_message.decode()
        message = raw_message.split()

        print(f'Received beacon: {message[0]}, {message[1]}, {message[2]}')
        print(f'Current time is: {dt.datetime.now()}')
        
        end = dt.datetime.strptime((message[3] + ' ' + message[4]), "%d/%m/%Y %H:%M:%S")
        
        # Lock the file, just in case another thread tries to access it at the same time
        with t_lock:
            clean_log()
            if dt.datetime.now() < end:
                print('Beacon is valid.')
                to_write = str(dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S")) + ' ' + raw_message[:-2] + '\n'
                with open('contactlog.txt', 'a') as file:
                    file.write(to_write)
            else:
                print('Beacon is invalid.')
            t_lock.notify()

# send_handler
# Handles all packet sending (TCP or UDP) based on keywords input
# by user.
def send_handler():
    global t_lock
    global clients
    global clientSocket
    global serverSocket
    global tcp_socket
    global timeout
    
    # NOTE: Below commented for testing
    username = input('Username: ')
    password = input('Password: ')
    
    credentials = (username + ' ' + password).encode()
    
    # credentials = ('+61410666667 kara1234').encode()

    tcp_client.send(credentials)
    response = tcp_client.recv(1024)
    response = response.decode('utf-8')
    
    temp_id = 0
    
    print(response)
    
    # Various catches for responses from the server (e.g., incorrect password,
    # incorrect username)
    if 'Incorrect password' in response:
        while 'Incorrect password' in response and 'blocked' not in response:
            password = input('Password: ')
            tcp_client.send(password.encode('utf-8'))
            response = tcp_client.recv(1024).decode()
            print(response)
    elif 'Incorrect username' in response:
        while 'Incorrect username' in response:
            username = input('Username: ')
            password = input('Password: ')
            credentials = username + ' ' + password
            tcp_client.send(credentials.encode('utf-8'))
            response = tcp_client.recv(1024)
            response = response.decode('utf-8')
    # The main event: the below condition and while loop is where all the
    # commands are read by the client and sent to the server. Note that an
    # invalid command is stopped before it even reaches the socket; the client
    # only permits the four functions (logout, Upload_contact_log, Download_tempID, Beacon)
    # to be used -- anything else throws an error.
    if 'Welcome' in response:
        command = input()
        while command != 'logout':
            # Request a temp ID from the server. Server will return the temp ID
            # along with relevant timestamps (start/end) to be used for beaconing.
            if command == 'Download_tempID':
                tcp_client.send(command.encode('utf-8'))
                temp_response = tcp_client.recv(2048).decode()
                temp_response = temp_response.split(',')
                temp_id = temp_response[0]
                start = temp_response[1]
                end = temp_response[2]
                print(f'TempID: {temp_id}')
            
            # Send the server the length of the file (so it knows when to stop
            # waiting for new packets). Then send the file line by line.
            elif command == 'Upload_contact_log':
                clean_log()
                tcp_client.send(command.encode('utf-8'))
                with open('contactlog.txt', 'r') as file:
                    full = file.readlines()
                tcp_client.send(str(len(full)).encode())
                # Sleep for a second before sending the file, to make sure
                # length arrives first.
                time.sleep(1)
                for line in full:
                    line = line[:-1]
                    line = line.split()
                    to_send = f'{line[2]} {line[3]} {line[4]} {line[5]} {line[6]}'
                    print(f'{line[2]}, {line[3]} {line[4]}, {line[5]} {line[6]};')
                    tcp_client.send(to_send.encode())
                    
            # Send beacon (if the client has a tempID)
            elif 'Beacon' in command:
                if temp_id == 0:
                    print("Cannot send beacon without a tempID. Use 'Download_tempID' command to obtain tempID from the server.")
                else:
                    command = command.split()
                    print(f'{temp_id}, {start}, {end}')
                    version = '1'
                    packet = temp_id + ' ' + str(start) + ' ' + str(end) + ' ' + version
                    clientSocket.sendto(packet.encode(), (command[1], int(command[2])))
            else:
                print('Error. Invalid command')
            command = input()
        tcp_client.send(command.encode('utf-8'))
    tcp_client.close()

# Server IP and port
tcp_ip = sys.argv[1]
tcp_port = sys.argv[2]

# UDP port (IP auto-populated as 'localhost')
udp_port = sys.argv[3]
t_lock=threading.Condition()
# timeout=False

# clientSocket and serverSocket are both UDP, while tcp_client is TCP
clientSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket = socket(AF_INET, SOCK_DGRAM)

serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('localhost', int(udp_port)))

tcp_client = socket(AF_INET, SOCK_STREAM)
tcp_client.connect((tcp_ip, int(tcp_port)))

# The client has two threads: one for UDP receiving (other clients' beacons)
# and one for UDP/TCP sending (contact with the server and sending beacons 
# to other clients)
recv_thread=threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon=True
recv_thread.start()

send_thread=threading.Thread(name="SendHandler",target=send_handler)
send_thread.daemon=True
send_thread.start()

#this is the main thread
while True:
    time.sleep(0.1)


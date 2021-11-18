# server.py
# The server program for the BlueTrace simulator.
# Handles user authentication and creation of tempIDs for clients, as well
# as final contact log checking.
# Usage: python3
# by George Sklavounos


from socket import *
import sys
import datetime
import threading
import random

# Running list of active users; used to check whether a user is already
# logged in or not.
active_users = []

# logged_in
# Handles client interaction after the user has logged in.
def logged_in(username, password, connectionSocket):
    active_users.append(username)
    connectionSocket.send(('Welcome to the BlueTrace simulator!').encode())
    
    # logout_request changes to 1 when 'logout' is received
    logout_request = 0
    while logout_request == 0:
        command = connectionSocket.recv(1024).decode()
        if command == 'logout':
            logout_request = 1
        elif command == 'Download_tempID':
            # Catch cases where tempIDs.txt doesn't exist
            try:
                ids = open('tempIDs.txt', 'r')
            except FileNotFoundError:
                ids = open('tempIDs.txt', 'w')
                ids.close()
                ids = open('tempIDs.txt', 'r')
            current = datetime.datetime.now()
            found = 0
            # Check if username + current ID combo exists in file.
            # If so, return the existing ID and timestamps.
            for line in ids:
                line = line.split()
                start = line[2] + ' ' + line[3]
                end = line[4] + ' ' + line[5]
                start = datetime.datetime.strptime(start, "%d/%m/%Y %H:%M:%S")
                end = datetime.datetime.strptime(end, "%d/%m/%Y %H:%M:%S")
                if username == line[0] and datetime.datetime.now() > start and datetime.datetime.now() < end:
                    print(f'user: {line[0]}')
                    print(f'TempID: {line[1]}')
                    start = start.strftime("%d/%m/%Y %H:%M:%S")
                    end = end.strftime("%d/%m/%Y %H:%M:%S")
                    to_send = f'{line[1]},{str(start)},{str(end)}'
                    connectionSocket.send(to_send.encode('utf-8'))
                    found = 1
                    pass
            ids.close()
            # Otherwise, create an ID, send it to the client, and add it to tempIDs with the timestamps
            if found == 0:
                adding_id = ''
                for i in range(0, 20):
                    adding_id += str(random.randint(0,9))
                # Print to server
                print(f'user: {username}')
                print(f'TempID: {adding_id}')
                ids = open('tempIDs.txt', 'a')
                current = datetime.datetime.now()
                end_time = current + datetime.timedelta(minutes=15)
                current = current.strftime("%d/%m/%Y %H:%M:%S")
                end_time = end_time.strftime("%d/%m/%Y %H:%M:%S")
                to_append = username + ' ' + str(adding_id) + ' ' + current + ' ' + end_time
                connectionSocket.send((f'{str(adding_id)},{str(current)},{str(end_time)}').encode('utf-8'))
                ids.write(f'{to_append}\n')
                ids.close()
        elif command == 'Upload_contact_log':
            contact_log = []
            length = connectionSocket.recv(2048).decode()
            print(f'Received contact log from {username}')
            for i in range(int(length)):
                temp = connectionSocket.recv(2048).decode()
                contact_log.append(temp)
            for line in contact_log:
                line = line.split()
                print(f'{line[0]}, {line[1]} {line[2]}, {line[3]} {line[4]};')
            ids = open('tempIDs.txt', 'r')
            check_ids = ids.readlines()
            ids.close()
            for record in contact_log:
                for line in check_ids:
                    if record in line:
                        line = line.split()
                        print(f'{line[0]}, {line[2]} {line[3]}, {line[1]};')
    print(f'{username} logout')
    active_users.remove(username)
    connectionSocket.close()
    
# client_login
# Handles client interactions before they've logged in
def client_login(connectionSocket, addr):
    
    global blocked
    global block_duration
    
    credentials = connectionSocket.recv(1024).decode()
    credentials = credentials.split()
        
    # Grab incorrect usernames
    if len(credentials[0]) != 12 or credentials[0][:3] != '+61':
        incorrect_username = 'Incorrect username. Usernames must be a valid phone number, 12 digits long with the Australia area code (+61)'
        connectionSocket.send(incorrect_username.encode('utf-8'))

    # Valid username
    elif len(credentials[0]) == 12 and credentials[0][:3] == '+61':
        try:
            file = open('credentials.txt', 'r')
        except FileNotFoundError:
            file = open('credentials.txt', 'w')
            file.close()
            file = open('credentials.txt', 'r')
        found_username = 0
        still_blocked = 0
        # Check if username has been blocked
        if credentials[0] in blocked and datetime.datetime.now() < blocked[credentials[0]] + datetime.timedelta(seconds=block_duration):
            connectionSocket.send(str('Your account is blocked due to multiple login failures. Please try again later.').encode())
            connectionSocket.close()
            still_blocked = 1
        if still_blocked != 1:
            # socket_blocked tracks whether this thread has blocked the user;
            # because it's going through line by line, without socket_blocked
            # it'd keep checking.
            socket_blocked = 0
            for line in file:
                if socket_blocked == 0:
                    line = line.split()
                    # If username in file
                    if credentials[0] == line[0]:
                        found_username = 1
                        # Check password
                        if credentials[1] == line[1] and credentials[0] not in active_users:
                            logged_in(credentials[0], credentials[1], connectionSocket)
                        # Implement re-entry of password and eventual block
                        elif credentials[1] == line[1] and credentials[0] in active_users:
                            connectionSocket.send(str('You are already logged in from another device.').encode())
                        elif credentials[1] != line[1]:
                            block_username = 1
                            while credentials[1] != line[1] and block_username != 3:
                                block_username += 1
                                connectionSocket.send(str('Incorrect password. Please try again').encode('utf-8'))
                                credentials[1] = connectionSocket.recv(1024).decode()
                            if credentials[1] == line[1] and credentials[0] not in active_users:
                                logged_in(credentials[0], credentials[1], connectionSocket)
                            elif credentials[1] == line[1] and credentials[0] in active_users:
                                connectionSocket.send(str('You are already logged in from another device.').encode())
                            elif block_username == 3:
                                blocked[credentials[0]] = datetime.datetime.now()
                                connectionSocket.send(str('Incorrect password. Your account has been blocked. Please try again later.').encode('utf-8'))
                                socket_blocked = 1
                        else:
                            connectionSocket.close()
            # connectionSocket.close()
            file.close()
            if found_username == 0:
                append = open('credentials.txt', 'a')
                append.write(f'{credentials[0] + " " + credentials[1]}\n')
                append.close()
                logged_in(credentials[0], credentials[1], connectionSocket)
    connectionSocket.close()


# UNCOMMENT
block_duration = int(sys.argv[2])
# block_duration = 60

blocked = {}

# UNCOMMENT
serverPort = int(sys.argv[1])
# serverPort = 8000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('localhost', serverPort))
serverSocket.listen(5)
print("BlueTrace server online")
while 1:
    connectionSocket, addr = serverSocket.accept()
    try:
        threading.Thread(target=client_login, 
                         args=(connectionSocket, addr),
                         daemon=True).start()
    except:
        print('Thread failed')

serverSocket.close()

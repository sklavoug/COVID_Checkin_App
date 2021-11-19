# COVID Contact Tracing App

Based on a university assignment demonstrating familiarity with basic networking with Python by building a BlueTrace protocol simulator. client.py and server.py interact to simulate a COVID contact tracing app. Functionality is outlined below.

## Server
The  reporting  server  is  responsible  for  handling  initial  registration,  provisioning  unique  user identifiers, and collecting contact logs created by the P2P part of the protocol. When the user first launches the app they will be asked to create a UserID (internationally format mobile phone number,  e.g.,  +61-410-888-888)  and  password.  This  phone  number  is  later  used  if  the  user  has registered an encounter in an infected patient's contact log. Once registered, users are provisioned TempID uniquely identifying them to other devices. Each TempID has a lifetime of a defined period (e.g., 15 minutes) to prevent malicious parties from performing replay attacks or tracking users over time with static unique identifiers. Therefore, the server has the following responsibilities:

**User Authentication** - 
When a client requests for a connection to the server, e.g., for obtaining a TempID or uploading contact logs after being tested as a COVID-19 positive, the server should prompt the user to input the username and password and authenticate the user. The valid username and password combinations will be stored in a file called credentials.txt which will be in the same 
directory as the server program. Each username and password should be on a separate line and there should only be one white space between the two. If the credentials are correct,  the  client  is  considered  to  be  logged  in  and  a  welcome  message  is  displayed.  When  all tasks are done (e.g., TempID has been obtained or the contact log has been uploaded), a user should be able to logout from the server.

On entering invalid credentials, the user is prompted to retry. After 3 consecutive failed attempts, the user is blocked for a duration of *block_duration* seconds (block_duration is a command line argument supplied to the server) and cannot login during this duration (even from another IP address). 

**TempID Generation** - 
TempIDs are generated as a 20-byte random number, and the server uses a file  (tempIDs.txt,  which  will  be  in  the  same  directory  as  the  server  program)  to  associate  the 
relationship between TempIDs and the static UserIDs.

**Contact  log  checking** - 
Once a user has tested positive for COVID, he/she will upload his/her contact log to the reporting server. The contact log is in the following format: TempID (20 bytes), start time (19 bytes) and expiry time (19 bytes). Then, the server will map the TempID to reveal the UserID and retrieve start time and expiry time (with help of the tempIDs.txt file). The health authority can then contact the UserID (phone number) to inform a user of potential contact with an infected patient. Therefore, the program  will print out a list of phone numbers and  encounter timestamps.

### Arguments
The server accepts the following two arguments:
- **server_port**: this is the port number which the server will use to communicate with the clients.
- **block_duration**: this is the duration in seconds for which a user should be blocked after three unsuccessful authentication attempts.

## Client
The client has the following responsibilities:

**Authentication** - 
The client provides a login prompt to enable the user to authenticate with the server.

**Download TempID** - 
After authentication, the client can download a TempID from the server and display it. 

**Upload contact log** - 
The  client can upload the contact logs to the server after authentication. The content of the contactlog.txt file is generated dynamically.

### Peer to Peer Communication Protocol (Beaconing)
The P2P part of the protocol defines how two devices communicate and log their contact. The program simulates BLE encounters with UDP in this section. Each device is in one of two states, Central or Peripheral. The peripheral device sends a packet with the following information to the central device: 
TempID (20 bytes), start time (19 bytes), expiry time (19 bytes) and BlueTrace protocol version (1 byte). 
After receiving the packet/beacon, the central device will compare current timestamp with the start time and expiry time information in the beacon. If the timing information is valid (i.e., current timestamp is between start time and expiry time), the central device will store the beacon information in a local file (<contactlog.txt) for 3 minutes. Note that a client can behave in either Central or Peripheral states. 

To implement this functionality the client supports the following command and auotmatically removes the outdated contact log (i.e., older than 3 minutes).

### Commands supported by the client 
After a user is logged in, the client supports all the commands shown in the table below. Any command that is not listed below will result in an error message being displayed to the user. For the following, assume that commands were run by user A.

| **Command**        | **Description**                    |
| :----------        | :--------------                    |
| Download_tempID    | Download tempID from the server.   |
| Upload_contact_log | Upload contact logs to the server. |
| logout             | Log out user A.                    |
| Beacon <dest IP> <dest port> | This  command  sends  a  beacon  to  another  user  (identified  by destination  IP  address  <dest  IP>  and  UDP  port  number  <dest port>).  Note that in BlueTrace app, a beacon will be broadcasted via the BLE interface of a smartphone and all other BLE devices in the transmission range will receive the beacon. This app uses UDP unicast to mimic (and significantly simplify) the process. |

### Arguments
The client accepts the following three arguments:
- **server_IP**: this is the IP address of the machine on which the server is running. 
- **server_port**: this is the port number being used by the server. This argument should be the same as the first argument of the server. 
- **client_udp_port**: this is the port number which the client will listen to/wait for the UDP traffic/beacons from the other clients. 

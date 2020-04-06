# This Python file controls all of the logic for a SEAT server. SEAT is a streamlined protocol combining
# functionality from both IMAP and SMTP together running on port 27901 This server should be constantly
# listening and ready to accept requests from SEAT clients. Network states for an instance of a
# client-server interaction are organized and maintained by separating valid commands within separate
# functions, moving between functions only as necessary, and synchronizing the movement between these
# functions between both the client and server.


# Basic imports. The below packages are standard Python libraries.
# socket is the standard Python package for handling socket programming.
# os handles operating system level interactions such as file manipulation
# datetime allows the program to use the system clock of the server
# _thread is used to allow multiple connections simultaneously

import socket
import os
import datetime
from _thread import *

# Standard socket instantiation according to Python documentation. SOCK_STREAM is specifically for TCP connections.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
state = ""
# Bind the program to port 27901. This is the standard port for the SEAT protocol to use
s.bind(('localhost', 27901))
print('Binded to port 27901')

# Allows the server to accept connections. As it is set, the server will refuse
# a connection if 5 unaccepted connections are attempted to it.
s.listen(5)
print('Running and ready to serve some emails')


# Opening state to handle user connection initiation.
# Spins up a new thread for every connection, allowing multiple clients simultaneously
def main():
    while True:
        conn, addr = s.accept()
        print("Connected with " + addr[0] + ":" + str(addr[1]))
        start_new_thread(thread, (conn, addr))


# New thread begins here and progresses client to the Greeting state.
def thread(conn, addr):
    while True:
        # Move to Greeting state
        try:
            greeting(conn, addr)
        except:
            print("Connection with " + addr[0] + ":" + str(addr[1]) + " has been terminated.")
            break


# Greeting state. Server accepts a HI message and responds with OK, completing the handshake.
# If the SEAT server recognizes this connection address, it can respond with a PREAUTH, directing the
# client directly to the Authenticated state
def greeting(conn, addr):
    while True:
        # If the client is a valid SEAT Client, the server should receive a HI here
        data = conn.recv(4096)
        datadecode = data.decode()
        from_client = datadecode
        if "HI" in from_client:
            # Server checks to see if the client is trusted already based on the information in the
            # trustSEATaddress.txt file.
            # If so, they will be sent a PREAUTH message and sent directly to the Authenticated state
            # If not, they will be sent to the Not Authenticated state
            try:
                f = open("trustedSEATaddresses.txt", 'r')
            except FileNotFoundError:
                f = open("trustedSEATaddresses.txt", "w+")
                print("Instantiated new trustSEATaddresses.txt\n")
                f.close()
                f = open("trustedSEATaddresses.txt", 'r')
            f1 = f.readlines()
            trustedaddresses = ""
            for line in f1:
                trustedaddresses += line
            f.close()
            if addr[0] in trustedaddresses:
                thingtosendfromserver = "OK PREAUTH"
                conn.send(thingtosendfromserver.encode())
                authenticated(conn, addr, "admin")
            else:
                thingtosendfromserver = "OK HI"
                conn.send(thingtosendfromserver.encode())
                notauthenticated(conn,addr)
        else:
            thingtosendfromserver = "BAD Request is not understood"
            conn.send(thingtosendfromserver.encode())


# Not Authenticated state. Here the user must attempt to log in to the SEAT server with some valid credentials.
# For the purposes of this project, the valid credentials are admin / pass
# This data, and all other data sent between the server and the client should necessarily use a telnet
# encryption suite. It is up to the individual implementer of this python application to provide
# a secure network connection for data to move through
def notauthenticated(conn, addr):
    while True:
        data = conn.recv(4096)
        datadecode = data.decode()
        from_client = datadecode
        # Server should receive a LOGIN command to begin authentication.
        # Again, there is no user setup implemented for the purpose of this demonstration. admin / pass are
        # the only valid credentials if the user is not Pre-authenticated.
        # STATEFUL
        if "LOGIN" in from_client:
            split = from_client.split(' ')
            if len(split) != 3:
                print("Invalid arguments to login")
                thingtosendfromserver = "BAD Username/Password does not make sense"
                conn.send(thingtosendfromserver.encode())
            elif split[1] == "admin" and split[2] == "pass":
                thingtosendfromserver = "OK Login Successful"
                conn.send(thingtosendfromserver.encode())
                username = "admin"
                authenticated(conn, addr, username)
            else:
                thingtosendfromserver = "NO Invalid Credentials"
                conn.send(thingtosendfromserver.encode())
        else:
            thingtosendfromserver = "BAD Request is not understood"
            conn.send(thingtosendfromserver.encode())


# Authenticated state. Here the user is officially logged in and has a variety of options available to them.
# The user may list all existing mailboxes they have access to.
# The user may create new mailboxes or delete existing mailboxes.
# The user may enter a mailbox to view and interact with mail.
# The user may enter the Send state to send their own email.
# The user may try to see what version of SEAT is running on this server and what extra capabilities it might have.
def authenticated(conn, addr, username):
    # print and send user's mailboxes from a txt doc
    while True:
        # A file is read or created if it does not exist for the user.
        # This file contains a list of all mailboxes that currently exist on the SEAT server for the user.
        try:
            f = open(username + ".txt", 'r')
        except FileNotFoundError:
            f = open(username + ".txt", "w+")
            print("Registered new user")
            f.close()
            f = open(username + ".txt", 'r')
        # A directory is created if it does not exist where the mailboxes will be stored.
        try:
            os.makedirs("admin")
        except FileExistsError:
            pass
        f1 = f.readlines()
        mailboxes = ""
        for line in f1:
            mailboxes += line
        f.close()
        data = conn.recv(4096)
        datadecode = data.decode()
        from_client = datadecode
        # List simply displays all of the existing mailboxes or informs the user that there are none.
        #STATEFUL
        if "LIST" in from_client:
            if mailboxes == "":
                thingtosendfromserver = "OK Empty"
                conn.send(thingtosendfromserver.encode())
            else:
                thingtosendfromserver = mailboxes
                conn.send(thingtosendfromserver.encode())
        # Create will create a new mailbox on the SEAT server.
        elif "CREATE" in from_client:
            newmailbox = from_client[7:]
            duplicate = "False"
            with open(username + ".txt", "r+") as f:
                g = f.readlines()
                f.seek(0)
                for line in g:
                    if line == newmailbox + "\n":
                        duplicate = "True"
                        thingtosendfromserver = "BAD " + newmailbox + " already exists"
                        conn.send(thingtosendfromserver.encode())
            if duplicate == "False":
                f = open(username + ".txt", 'a+')
                f.write(newmailbox + "\n")
                f.close()
                try:
                    os.makedirs(username + "/" + newmailbox)
                except FileExistsError:
                    pass
                print("Created folder to store new emails under new mailbox")
                thingtosendfromserver = "OK Created " + newmailbox
                conn.send(thingtosendfromserver.encode())
        # Delete will delete an existing mailbox on the server.
        elif "DELETE" in from_client:
            deletemailbox = from_client[7:] + "\n"
            with open(username + ".txt", "r+") as f:
                g = f.readlines()
                f.seek(0)
                for line in g:
                    if line != deletemailbox:
                        f.write(line)
                f.truncate()
            f.close()
            thingtosendfromserver = "OK Deleted " + deletemailbox
            conn.send(thingtosendfromserver.encode())
        # Select will move us into the Select state and allow a user to interact with their mail.
        elif "SELECT" in from_client:
            selectmailbox = from_client[7:]
            selected(conn, addr, username, selectmailbox)
        # Send will send us to the Send state and allow us to send our own new mail.
        elif "SEND" in from_client:
            clientaddr = addr[0]
            thingtosendfromserver = "OK " + clientaddr
            conn.send(thingtosendfromserver.encode())
            send(conn, addr, username)
        # Capability lists the SEAT version the server is running on and any extra capabilities
        elif "CAPABILITY" in from_client:
            capability(conn)
        # Logout will move to the Logout state, confirming to the user that the server has acknowledged
        # that they will be disconnecting.
        elif "LOGOUT" in from_client:
            logout(conn)
        # Weekday is an example of a special capability that this SEAT server can provide to the user.
        # Weekday tells the user which day of the week it is. A simple example, but it displays the power
        # and extensibility of SEAT.
        elif "Weekday" in from_client:
            weekday(conn)
        else:
            thingtosendfromserver = "BAD Request is not understood"
            conn.send(thingtosendfromserver.encode())


# In the selected state, users can interact with the mail in their mailbox.
# Mail is stored as simple text files.
def selected(conn, addr, username, mailbox):
    while True:
        data = conn.recv(4096)
        datadecode = data.decode()
        from_client = datadecode
        # List displays all mail currently residing in the mailbox
        # STATEFUL
        if "LIST" in from_client:
            relativepath = os.path.relpath(".")
            emaillist = os.listdir(relativepath + "/" + username + "/" + mailbox)
            emails = '\n'.join(str(e) for e in emaillist).replace(".txt","")
            if emails == "":
                thingtosendfromserver = "OK Empty"
                conn.send(thingtosendfromserver.encode())
            else:
                thingtosendfromserver = "OK " + emails
                conn.send(thingtosendfromserver.encode())
        # Search will search all of the mail in the mailbox and return all mail that contains
        # the search query in either the email name or in the body of the email
        elif "SEARCH" in from_client:
            searchstring = from_client[7:]
            foundinfile = []
            relativepath = os.path.relpath(".")
            emaillist = os.listdir(relativepath + "/" + username + "/" + mailbox)
            for e in emaillist:
                if searchstring in e:
                    foundinfile.append(e)
                else:
                    if searchstring in open(username + "/" + mailbox + "/" + e).read():
                        foundinfile.append(e)
            emails = '\n'.join(str(e) for e in foundinfile).replace(".txt", "")
            if emails == "":
                thingtosendfromserver = "OK No Results"
                conn.send(thingtosendfromserver.encode())
            else:
                thingtosendfromserver = "OK" + emails
                conn.send(thingtosendfromserver.encode())
        # Fetch will display the email body of a specific email
        elif "FETCH" in from_client:
            emailtoread = from_client[6:]
            try:
                f = open(username + "/" + mailbox + "/" + emailtoread, 'r')
                contents = f.read()
                thingtosendfromserver = "OK" + contents
                conn.send(thingtosendfromserver.encode())
            except:
                thingtosendfromserver = "NO No such email exists"
                conn.send(thingtosendfromserver.encode())
        # Close closes the mailbox and returns the user to the Authenticated state.
        elif "CLOSE" in from_client:
            thingtosendfromserver = "OK Closing Mailbox"
            conn.send(thingtosendfromserver.encode())
            authenticated(conn,addr,username)
        # Capability and Weekday are once again acceptable commands the server can handle, as described above.
        elif "CAPABILITY" in from_client:
            capability(conn, addr)
        elif "Weekday" in from_client:
            weekday(conn, addr)
        # Logout will move to the Logout state, confirming to the user that the server has acknowledged
        # that they will be disconnecting.
        elif "LOGOUT" in from_client:
          logout(conn)
        else:
            thingtosendfromserver = "BAD Request is not understood"
            conn.send(thingtosendfromserver.encode())


# The send state is the SMTP portion of SEAT. It is a bit more complex in implementation than the IMAP portion.
# Here a user has the opportunity to create and send some new mail to another user on either this SEAT server or
# another SEAT server.
def send(conn, addr, username):
    while True:
        data = conn.recv(4096)
        datadecode = data.decode()
        from_client = datadecode
        # The MAIL command begins the process of creating an email.
        # STATEFUL
        if "MAIL" in from_client:
            reversepath = from_client[5:]
            thingtosendfromserver = "OK Starting Mail"
            conn.send(thingtosendfromserver.encode())
            sendrcpt(conn, addr, username, reversepath)
        # Close returns the user to the Authenticated state.
        elif "CLOSE" in from_client:
            thingtosendfromserver = "OK Closing Mailbox"
            conn.send(thingtosendfromserver.encode())
            authenticated(conn, addr, username)
        # Capability and Weekday are once again acceptable commands the server can handle, as described above.
        elif "CAPABILITY" in from_client:
            capability(conn, addr, username)
        elif "Weekday" in from_client:
            weekday(conn, addr, username)
        # Logout will move to the Logout state, confirming to the user that the server has acknowledged
        # that they will be disconnecting.
        elif "LOGOUT" in from_client:
            logout(conn)
        else:
            thingtosendfromserver = "BAD Request is not understood"
            conn.send(thingtosendfromserver.encode())


# The second stage of a mail request. This is still within the Send state, but the commands to send mail should
# be received to the SEAT server within a certain order (MAIL > RCPT > DATA)
def sendrcpt(conn, addr, username, reversepath):
    recipientlist = []
    while True:
        data = conn.recv(4096)
        datadecode = data.decode()
        from_client = datadecode
        # The RCPT command accepts some user input on one or more email addresses to send mail to
        # format for an email address is "someuser@somedomain".
        if "RCPT" in from_client:
            recipient = from_client[5:]
            recipientlist.append(recipient)
            thingtosendfromserver = "OK Sending to " + recipient
            conn.send(thingtosendfromserver.encode())
        # DATA lets the SEAT server know that the user is about to begin sending in email body contents
        # DATA takes a special delimiter, as we will soon see.
        elif "DATA" in from_client:
            thingtosendfromserver = "OK Ready for DATA"
            conn.send(thingtosendfromserver.encode())
            senddata(conn, addr, username, reversepath, recipientlist)
        # Close and return to the authenticated state, canceling the last MAIL request
        elif "CLOSE" in from_client:
            thingtosendfromserver = "OK Closing Mailbox"
            conn.send(thingtosendfromserver.encode())
            authenticated(conn, addr, username)
        # Capability and Weekday are once again acceptable commands the server can handle, as described above.
        elif "CAPABILITY" in from_client:
            capability(conn, addr, username)
        elif "Weekday" in from_client:
            weekday(conn, addr, username)
        # Logout will move to the Logout state, confirming to the user that the server has acknowledged
        # that they will be disconnecting.
        elif "LOGOUT" in from_client:
            logout(conn)
        else:
            thingtosendfromserver = "BAD Request is not understood"
            conn.send(thingtosendfromserver.encode())


# Send data is the crux of the SMTP functionality of SEAT. This is the 3rd step of the mail process (MAIL > RCPT > DATA)
# DATA will either store the mail in the mailbox of the recipient right away if the mailbox is on this localhost, or
# DATA will pass the mail along to another SEAT server to handle the request.
def senddata(conn, addr, username, reversepath, recipientlist):
    emailbody = ""
    while True:
        data = conn.recv(4096)
        datadecode = data.decode()
        # DATA will continually loop until it finds the special \n.\n delimiter in the message.
        if "\n.\n" in datadecode:
            emailsplit = datadecode.split('\n.\n')
            endofemail = emailsplit[0]
            emailbody += endofemail
            # The server will one-by-one attempt to mail the recipients for the mail
            for recipient in recipientlist:
                if "@localhost" in recipient:
                    recipientname = recipient.split('@localhost')
                    recipientnamestring = recipientname[0]
                    try:
                        f = open(username + ".txt", 'r')
                    except FileNotFoundError:
                        f = open(username + ".txt", "w+")
                        print("Registered new user")
                        f.close()
                        f = open(username + ".txt", 'r')
                    f1 = f.readlines()
                    mailboxes = ""
                    for line in f1:
                        mailboxes += line
                    f.close()
                    # The server will create a txt file with the mail in the appropriate mailbox right now, if
                    # the recipient is on this SEAT server.
                    # The txt filename will contain the user sending, the recipient, and the current
                    # datetime of receiving the email.
                    if recipientnamestring in mailboxes:
                        timenow = datetime.datetime.now()
                        timenow = timenow.strftime("%Y:%m:%d:%H:%M:%S")
                        timenow = timenow.replace(":", "-")
                        newemailfile = username + "/" + recipientnamestring + "/" + reversepath + timenow + ".txt"
                        f = open(newemailfile, "w+")
                        f.close()
                        f = open(newemailfile, "a")
                        f.write("From: " + reversepath + "\nTo:" + recipient + "\n" + emailbody)
                        f.close()
                    # This else will occur if localhost was specified in the email address but the mailbox
                    # does not exist on localhost
                    else:
                        print("The recipient is not a valid user on this SEAT server.")
                # If the destination recipient is not on the localhost, SEAT will spin up a new thread and
                # connect to the recipient SEAT server, but this server will be acting as the client now.
                else:
                    recipientsplit = recipient.split("@")
                    recipientname = recipientsplit[0]
                    recipientdomain = recipientsplit[1]
                    try:
                        start_new_thread(smtpthread, (recipientname, recipientdomain, reversepath, emailbody))
                    except:
                        print("Connection with " + recipientdomain + "@" + recipientdomain + " has been halted.\n")

            send(conn, addr, username)
        #Special case for the situation where the user wants to contain "\n.\n" in their email message.
        # This will be transformed from \n..\n into \n.\n for the purposes of the SEAT server not to
        # end the data stream.
        else:
            if "\n..\n" in datadecode:
                datadecode.replace("\n..\n", "\n.\n")
            emailbody += datadecode


# As detailed above, this thread will be created when the mail function of SEAT needs to pass an email
# along to a different SEAT server to handle the request.
# This function is essentially going through a simplified version of the process until this point to pass the email.
# SEAT servers should necessarily trust each other on a network by design. As such, this function expects to be
# receiving a PREAUTH response to its greeting.
def smtpthread(recipientname, recipientdomain, reversepath, emailbody):
    # "Greeting phase"
    s.connect((recipientdomain, 27901))
    request = "HI"
    s.send(request.encode())
    from_server = s.recv(4096);
    from_server = from_server.decode()
    if "BYE" in from_server:
        print("Server rejected this mail connection")
    if "PREAUTH" in from_server:
    # "Authenticated phase"
        print("Server pre-authenticated your connection. Welcome!")
        authenticated(s, "admin")
        s.send(request.encode())
        from_server = s.recv(4096);
        response = from_server.decode()
        if "OK" in response:
        #"Send Phase (Specifically MAIL)
            addr = response[3:]
            request = "MAIL " + reversepath
            s.send(request.encode())
            from_server = s.recv(4096)
            from_server = from_server.decode()
            if "OK" in from_server:
                # "Send Phase (Specifically RCPT)
                request = "RCPT " + recipientname
                s.send(request.encode())
                from_server = s.recv(4096)
                from_server = from_server.decode()
                if "OK" in from_server:
                    # "Send Phase (Specifically DATA)
                    request = "DATA"
                    s.send(request.encode())
                    emailbody = emailbody + "\n.\n"
                    request = emailbody
                    print("\nEmail has been sent!\n")
                    s.send(request.encode())
                else:
                    print("Server is busy. Please try again later.")
            else:
                print("Server is busy. Please try again later.")
        else:
            print("Server is busy. Please try again later.")
    else:
        print("Server is busy. Please try again later.")


# Capability lists the SEAT version the server is running on and any extra capabilities
def capability(conn):
    thingtosendfromserver = "CAPABILITY SEAT1.0 Weekday"
    conn.send(thingtosendfromserver.encode())


# Weekday is an example of a special capability that this SEAT server can provide to the user.
# Weekday tells the user which day of the week it is. A simple example, but it displays the power
# and extensibility of SEAT.
def weekday(conn):
    today = datetime.datetime.today().weekday()
    if today == 0:
        today = "Monday"
    elif today == 1:
        today = "Tuesday"
    elif today == 2:
        today = "Wednesday"
    elif today == 3:
        today = "Thursday"
    elif today == 4:
        today = "Friday"
    elif today == 5:
        today = "Saturday"
    elif today == 6:
        today = "Sunday"
    thingtosendfromserver = "OK Today is " + today
    conn.send(thingtosendfromserver.encode())


# Logout will send a BYE message to the user confirming the agreement to end the connection.
def logout(conn):
    thingtosendfromserver = "BYE"
    conn.send(thingtosendfromserver.encode())


# this kicks off the main function, kicking off all other functions in the process :)
main()

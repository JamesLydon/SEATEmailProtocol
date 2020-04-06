# This Python file controls all of the logic for a SEAT client. SEAT is a streamlined protocol combining
# functionality from both IMAP and SMTP together running on port 27901 This server should be constantly
# listening and ready to accept requests from SEAT clients. Network states for an instance of a
# client-server interaction are organized and maintained by separating valid commands within separate
# functions, moving between functions only as necessary, and synchronizing the movement between these
# functions between both the client and server.


# Basic imports. The below packages are standard Python libraries.
# socket is the standard Python package for handling socket programming.
# sys simply allows us to end the process as needed.
# time allows us to view the clock or sleep
import sys
import socket
import time

# placeholder for command options within each state.
options = "placeholder"

# Standard socket instantiation according to Python documentation. SOCK_STREAM is specifically for TCP connections.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# Opening a connection with a SEAT server. The user is prompted with choosing a server to connect to.
# Depending on the host of this client and the host of the SEAT server, the user will either be pre-authenticated
# or the user will have to login with a username and password.
def main():
    print("WELCOME TO SEAT 1.0")
    var = input("Type the name or IP Address of a server you'd like to connect to.\nNote: if you have a SEAT Server running locally, then 'localhost' would be a good option to try\n")
    s.connect((var, 27901))
    request = "HI"
    s.send(request.encode())
    from_server = s.recv(4096);
    from_server = from_server.decode()
    if "BYE" in from_server:
        print("Server rejected your connection")
        sys.exit()
    # 127.0.0.1 is probably set as a trusted IP Address in the SEAT server's trusted host file, and so you will
    # probably see this PREAUTH response.
    if "PREAUTH" in from_server:
        print("Server pre-authenticated your connection. Welcome!")
        authenticated(s, "admin")
    # If 127.0.0.1 is not Pre-authenticated, the user will be prompted for credentials. For the purposes of this
    # project, username andd password are admin / pass.
    if "OK" in from_server:
        while True:
            username = input("Username:")
            password = input("Password:")
            request = "LOGIN " + username + " " + password
            s.send(request.encode())
            from_server = s.recv(4096);
            from_server = from_server.decode()
            if "OK" in from_server:
                print("Login successful!\n")
                authenticated(s, username)
            elif "NO" in from_server:
                print("Invalid Username / Password")
            elif "BAD" in from_server:
                print(from_server[4:])
            else:
                print("Server is busy. Please try again later.")
    else:
        print("Server is busy. Please try again later.")


# In the authenticated state, the user has access to myriad functionality.
# The user may list all existing mailboxes they have access to.
# The user may create new mailboxes or delete existing mailboxes.
# The user may enter a mailbox to view and interact with mail.
# The user may enter the Send state to send their own email.
# The user may try to see what version of SEAT is running on this server and what extra capabilities it might have.
def authenticated(s, username):
    request = "LIST"
    s.send(request.encode())
    from_server = s.recv(4096);
    mailboxes = from_server.decode()
    while True:
        empty = "False"
        if "OK Empty" in mailboxes :
            empty = "True"
            print("You have no existing mailboxes right now. Maybe you should create one?\n")
        else:
            print("\nAvailable mailboxes are:\n" + mailboxes)
        options = "Check my emails\nCreate a new mailbox\nDelete a mailbox\nSend an email\nSee secret features\nLogout of SEAT\n"
        var = input("Here are your available options:\n" + options)
        # Will move us into the Select state and allow a user to interact with their mail.
        # STATEFUL
        if "Check" in var:
            if empty == "True":
                print("You need to create a mailbox first")
            else:
                print("Which mailbox do you want to check?")
                print(mailboxes)
                mailbox = input()
                if mailbox in mailboxes:
                    request = "SELECT " + mailbox
                    s.send(request.encode())
                    selected(s,mailbox, username)
                else:
                    print("That's not a mailbox")
        # Will create a new mailbox on the SEAT server.
        elif "Create" in var:
            newmailbox = input("What will you name your new mailbox?\n")
            request = "CREATE " + newmailbox
            s.send(request.encode())
            time.sleep(1)
            from_server2 = s.recv(4096);
            from_server2 = from_server2.decode()
            if "OK" in from_server2:
                print("Mailbox " + newmailbox + " created successfully!\n")
                request = "LIST"
                time.sleep(1)
                s.send(request.encode())
                from_server = s.recv(4096);
                mailboxes = from_server.decode()
            elif "BAD" in from_server2:
                print("That mailbox already exists!\n")
            else:
                print("Oops, that's a bad name for a mailbox. Keep it simple\n")
        # Will delete an existing mailbox on the server.
        elif "Delete" in var:
            print(mailboxes)
            deletemailbox = input("Which mailbox do you want to delete? Note: This is permanent\n")
            request = "DELETE " + deletemailbox
            s.send(request.encode())
            time.sleep(1)
            from_server3 = s.recv(4096);
            from_server3 = from_server3.decode()
            if "OK" in from_server3:
                print("Mailbox " + deletemailbox + " deleted successfully!\n")
                request = "LIST"
                s.send(request.encode())
                from_server = s.recv(4096);
                mailboxes = from_server.decode()
            else:
                print("Oops, that's a bad name for a mailbox. Keep it simple\n")
        # Send will send us to the Send state and allow us to send our own new mail.
        elif "Send" in var:
            request = "SEND "
            s.send(request.encode())
            from_server = s.recv(4096);
            response = from_server.decode()
            if "OK" in response:
                addr = response[3:]
                send(s, addr, username)
        # Logout will end the session with the server and stop the application process.
        elif "Logout" in var:
            request = "LOGOUT "
            s.send(request.encode())
            from_server = s.recv(4096);
            response = from_server.decode()
            if "BYE" in response:
                print("The server got your message and is sad to see you go!")
                print("Have a good day! Closing SEAT.")
                sys.exit()
            else:
                print("The server did not receive your goodbye.")
                sys.exit()
        # Capability lists the SEAT version the server is running on and any extra capabilities
        elif "See" in var or "secret" in var:
            request = "CAPABILITY "
            s.send(request.encode())
            from_server = s.recv(4096);
            response = from_server.decode()
            if "CAPABILITY" in response:
                spacedelimitedresponse = response.split()
                version = spacedelimitedresponse[1]
                commands = ""
                for i in spacedelimitedresponse[2:]:
                    commands += i + " "
                print("The server connection is using version " + version + " and the secret commands it can do include: " + commands)
                capabcommand = input("Try it out! Or type 'Back' to return to your mailboxes\n")
                if capabcommand in commands:
                    request = capabcommand
                    s.send(request.encode())
                    from_server = s.recv(4096);
                    response = from_server.decode()
                    if "BAD" in response:
                        print("Hmm. It seems that wasn't a valid command.")
                    elif "OK" in response:
                        print(response[2:])
                    else:
                        print(response)
        else:
            print("I don't understand what you're saying")


# The selected state is the state wherein the user can interact with their emails
def selected(s, mailbox, username):
        while True:
            options = "List emails\nSearch emails\nRead an email\nClose the mailbox\nLogout of SEAT\n"
            var = input("Here are your available options:\n" + options)
            # List displays all mail currently residing in the mailbox
            # STATEFUL
            if "List" in var:
                request = "LIST"
                s.send(request.encode())
                time.sleep(1)
                from_server = s.recv(4096)
                from_server = from_server.decode()
                if "OK" in from_server:
                    print("\nThe following are emails in your inbox:\n" + from_server[3:] + "\n\n")
            # Search will search all of the mail in the mailbox and return all mail that contains
            # the search query in either the email name or in the body of the email
            elif "Search" in var:
                var = input("Type the keyword or phrase you're searching for:\n")
                request = "SEARCH " + var
                s.send(request.encode())
                time.sleep(1)
                from_server = s.recv(4096)
                from_server = from_server.decode()
                if "OK" in from_server:
                    print(from_server[2:] + "\n\n")
            # Reaed will display the email body of a specific email
            elif "Read" in var:
                var = input("\nWhich email would you like to read?\n")
                request = "FETCH " + var + ".txt"
                s.send(request.encode())
                time.sleep(1)
                from_server = s.recv(4096)
                from_server = from_server.decode()
                if "OK" in from_server:
                    print(from_server[2:])
                elif "NO" in from_server:
                    print(from_server[2:])
            # Logout will end the session with the server and stop the application process.
            elif "Logout" in var:
                request = "LOGOUT "
                s.send(request.encode())
                from_server = s.recv(4096);
                response = from_server.decode()
                if "BYE" in response:
                    print("The server got your message and is sad to see you go!")
                    print("Have a good day! Closing SEAT.")
                    sys.exit()
                else:
                    print("The server did not receive your goodbye.")
                    sys.exit()
            # Close closes the mailbox and returns the user to the Authenticated state.
            elif "Close" in var:
                request = "CLOSE"
                s.send(request.encode())
                time.sleep(1)
                from_server = s.recv(4096)
                from_server = from_server.decode()
                if "OK" in from_server:
                    print("Closing " + mailbox + "\n")
                    authenticated(s, username)


# The send state is the SMTP portion of SEAT. It is a bit more complex in implementation than the IMAP portion.
# Here a user has the opportunity to create and send some new mail to another user on either the connected SEAT
# or to the connected SEAT server to pass along to the real destination user.
def send(s, addr, username):
    while True:
        options = "Send an email\nClose send mode and return to your mailboxes\nLogout of SEAT\n"
        var = input("Here are your available options:\n" + options)
        # The MAIL command begins the process of creating an email.
        # STATEFUL
        if "Send" in var:
            print("Starting to send an email\n")
            reversepath = username + "@" + addr
            request = "MAIL " + reversepath
            s.send(request.encode())
            from_server = s.recv(4096)
            from_server = from_server.decode()
            if "OK" in from_server:
                sendrcpt(s, addr, username, reversepath)
        # Logout will end the session with the server and stop the application process.
        elif "Logout" in var:
            request = "LOGOUT "
            s.send(request.encode())
            from_server = s.recv(4096);
            response = from_server.decode()
            if "BYE" in response:
                print("The server got your message and is sad to see you go!")
                print("Have a good day! Closing SEAT.")
                sys.exit()
            else:
                print("The server did not receive your goodbye.")
                sys.exit()
        # Close returns the user to the Authenticated state.
        elif "Close" in var:
            request = "CLOSE"
            s.send(request.encode())
            time.sleep(1)
            from_server = s.recv(4096)
            from_server = from_server.decode()
            if "OK" in from_server:
                print("Closing send mode and returning to your mailboxes")
                authenticated(s, username)
        else:
            print("I don't understand what you're saying. Try again choosing from the options.")


# The second stage of a mail request. This is still within the Send state, but the commands to send mail should
# be received to the SEAT server within a certain order (MAIL > RCPT > DATA)
def sendrcpt(s, addr, username, reversepath):
    while True:
        # The RCPT command accepts some user input on one or more email addresses to send mail to
        # format for an email address is "someuser@somedomain".
        var = input("Type the name of the recipient for this email\n")
        if "@" in var:
            request = "RCPT " + var
            s.send(request.encode())
            time.sleep(1)
            from_server = s.recv(4096)
            from_server = from_server.decode()
            if "OK" in from_server:
                var2 = input("Want to add another recipient? y/n\n")
                if "y" in var2 or "Yes" in var2 or "yes" in var2:
                    sendrcpt(s, addr, username, reversepath)
                elif "n" in var2 or "No" in var2 or "no" in var2:
                    request = "DATA"
                    s.send(request.encode())
                    senddata(s, addr, username, reversepath)
                else:
                    print("Not a valid answer. Try again.")
                    sendrcpt(s, addr, username, reversepath)
        # Close returns the user to the Authenticated state, interrupting the current mail creation
        elif "CLOSE" in var:
            request = "CLOSE"
            s.send(request.encode())
            time.sleep(1)
            from_server = s.recv(4096)
            from_server = from_server.decode()
            if "OK" in from_server:
                print("Closing send mode and returning to your mailboxes\n")
                authenticated(s, username)
            else:
                print("The server did not receive your goodbye.")
                sys.exit()
        # Logout will end the session with the server and stop the application process.
        elif "Logout" in var:
            request = "LOGOUT "
            s.send(request.encode())
            from_server = s.recv(4096);
            response = from_server.decode()
            if "BYE" in response:
                print("The server got your message and is sad to see you go!")
                print("Have a good day! Closing SEAT.")
                sys.exit()
            else:
                print("The server did not receive your goodbye.")
                sys.exit()
        else:
            print("Not a valid email address. Try again.")


# Send data is the crux of the SMTP functionality of SEAT. This is the 3rd step of the mail process (MAIL > RCPT > DATA)
# DATA will either store the mail in the mailbox of the recipient right away if the mailbox is on this localhost, or
# DATA will pass the mail along to another SEAT server to handle the request.
def senddata(s, addr, username, reversepath):
    print("Go ahead and type your email to send. When you're finished, type 'Send Email'")
    while True:
        var2 = input()
        # The user may continually send in information for the email body as much as they would like.
        # The user notifies the SEAT Application that they are done the email by typing 'Send Email'
        if 'Send Email' in var2:
            emailsplit = var2.split('Send Email')
            endofemail = emailsplit[0]
            endofemail = endofemail + "\n.\n"
            request = endofemail
            print("\nEmail has been sent!\n")
            s.send(request.encode())
            send(s, addr, username)
        # Logout will end the session with the server and stop the application process.
        elif "Logout" in var2:
            request = "LOGOUT "
            s.send(request.encode())
            from_server = s.recv(4096);
            response = from_server.decode()
            if "BYE" in response:
                print("The server got your message and is sad to see you go!")
                print("Have a good day! Closing SEAT.")
                sys.exit()
            else:
                print("The server did not receive your goodbye.")
                sys.exit()
        else:
            request = var2
            s.send(request.encode())


# this kicks off the main function, kicking off all other functions in the process :)
main()


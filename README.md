# (S)imple (E)mail (A)ccess (Transfer) Protocol
A client+server implementation of a theoretical all-in-one SMTP+IMAP Email Protocol


This implementation requires the installation of Python3. Specifically, Python 3.4 was used in writing this software. Python 2 is not compatible with this program and even earlier versions of Python 3 may not be compatible. Later versions of Python 3 after Python 3.4 are most likely compatible, but each release version has not been exhaustively tested with this project.
Python 3.4 can be downloaded from this web URL:
https://www.python.org/downloads/release/python-340/


This implementation can be run within any interface that can read Python files. For example, any IDE that supports Python such as PyCharm would work.
This implementation can also be run at the command line. One needs only to preface the main.py file with the Python 3.4 python.exe, either by referencing the fully qualified path to your Python 3.4 installation directory, or by adding the Python 3.4 python.exe to your Windows PATH. If using Linux, there are multiple ways you could reference it too, such as creating an alias to the python.exe like 'alias python="path/to/python.exe"

Note: This implementation has not been tested on a Linux machine, although there are no Windows dependencies that I am aware of.



The user should see two root level folders:
- SEATServer
- SEATClient

These contain the implementation of the server and the client respectively. Both start simply using the main.py file within each directory. The server must necessarily be started before starting the client. The SEATServer directory also contains some other files and directories that the server will use when servicing a user. During the server's interactions with the client, it may create more directories and files as well. You may edit these directories and files if you wish, but to ensure any bugs do not occur, they should be left alone except as the server decides to interact with them (which could be renaming, deleting, creating, editing, etc.)


SEATServer/trustedSEATaddresses.txt contains IP Addresses of those addresses which the server inherently trusts, and will send a PREAUTH message during the initiation of a connection accordingly. This PREAUTH message bypasses credential checking. You may edit this file if you wish. If a client is not pre-authenticated, he will have to log in using the credentials:
username: admin
password: pass



SEAT is relatively robust. It follows a simple-stream of error-checking for every individual action the user can take. For example, within each state only a few commands may be strictly allowed, and any other possible command will be responded to with a "BAD" response. Fuzzing a SEAT server, by sending massive amounts of random data, may cause errors at a Windows-level if the SEAT server is running on Windows. This is particularly true of all of the file and directory interactions SEAT has to perform. But that is a flaw in the operating system and implementation level of the application, not at the protocol level.

In fact, most of the difficulty in building SEAT's robustness was in defensively interacting with Windows. One problem, for example, is Windows filenames and filepaths not accepting many special characters, including colons which typically exist in datetime strings. This had to be resolved by converting colons to hyphens for the purposes of datetime strings. Other windows file level errors are typically resolved with simple try-except statements.

One way in which SEAT is very vulnerable is in simultaneous connections. SEAT does support concurrent connections, however some odd things may occur if two users are interacting with the same mailbox at the same time. This is also a common issue with IMAP as well, although most implementations of IMAP such as Outlook and Gmail most likely have much more defensive coding in place to handle this situation than my SEAT implementation does.

SEAT also relies on having a trusted network of SEAT servers to communicate with. This naturally has upsides and downsides. The upside is an intrinsic trust can be assumed to exist when forwarding emails to other trusted SEAT servers. The downside is that this opens up a malicious opportunity for man-in-the-middle attacks. A hijacked SEAT server could theoretically cause some damage to other SEAT servers all throughout its connected network, although the extent of how much damage is up to the individual implementation.
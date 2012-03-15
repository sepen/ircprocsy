import socket
import string
import asyncore

class forwarder(asyncore.dispatcher):

    debug = 0

    def __init__(self, debug, ip, port, remoteip, remoteport, backlog=5):
	asyncore.dispatcher.__init__(self)
        self.debug = debug
        self.remoteip=remoteip
        self.remoteport=remoteport
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((ip,port))
        self.listen(backlog)

    def handle_accept(self):
        conn, addr = self.accept()
        if (self.debug == 1): print('--- Connect --- ')
        sender(self.debug, receiver(self.debug, conn), self.remoteip, self.remoteport)

class receiver(asyncore.dispatcher):

    debug = 0

    def __init__(self, debug, conn):
        asyncore.dispatcher.__init__(self,conn)
        self.debug = debug
        self.from_remote_buffer=''
        self.to_remote_buffer=''
        self.sender=None

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(1024)
        if (self.debug == 1): print('[receiver] %04i ->>> :%s' % (len(read), read))
        # this is the point to manipulate data from client
        temp = string.split(read, "\n")
        temp2 = temp.pop( )
        for line in temp:
            line = string.rstrip(line)
            line = string.split(line)
            if (line[0] == "PRIVMSG"):
                read = " ".join(line) + " .... encode()\r\n"
        self.from_remote_buffer += read

    def writable(self):
        return (len(self.to_remote_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.to_remote_buffer)
        if (self.debug == 1): print('[receiver] %04i <<<- :%s' % (sent, self.to_remote_buffer))
        self.to_remote_buffer = self.to_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        if self.sender:
            self.sender.close()

class sender(asyncore.dispatcher):

    debug = 0

    def __init__(self, debug, receiver, remoteaddr,remoteport):
        asyncore.dispatcher.__init__(self)
        self.debug = debug
        self.receiver=receiver
        receiver.sender=self
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((remoteaddr, remoteport))

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(1024)
        if (self.debug == 1): print('[sender] <<<- %04i :%s' % (len(read), read))
        # this is the point to manipulate data from server
        temp = string.split(read, "\n")
        temp2 = temp.pop( )
        for line in temp:
            line = string.rstrip(line)
            line = string.split(line)
            if (line[1] == "PRIVMSG"):
                read = " ".join(line) + " .... decode()\r\n"
        self.receiver.to_remote_buffer += read

    def writable(self):
        return (len(self.receiver.from_remote_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.receiver.from_remote_buffer)
        if (self.debug == 1): print('[sender] ->>> %04i :%s' % (sent, self.receiver.from_remote_buffer))
        self.receiver.from_remote_buffer = self.receiver.from_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        self.receiver.close()

if __name__=='__main__':

    debug = 1

    import optparse
    parser = optparse.OptionParser()
    parser.add_option(
        '-l','--local-ip',
        dest='local_ip',default='127.0.0.1',
        help='Local IP address to bind to')
    parser.add_option(
        '-p','--local-port',
        type='int',dest='local_port',default=6667,
        help='Local port to bind to')
    parser.add_option(
        '-r','--remote-ip',dest='remote_ip',
        help='Local IP address to bind to')
    parser.add_option(
        '-P','--remote-port',
        type='int',dest='remote_port',default=6667,
        help='Remote port to bind to')
    options, args = parser.parse_args()

    forwarder(debug, options.local_ip, options.local_port, options.remote_ip, options.remote_port)
    asyncore.loop()

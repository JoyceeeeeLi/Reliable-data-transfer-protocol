import sys
import threading
from threading import *
from socket import *
from packet import Packet

# enable debugging messgaes
debug = 0 

N = 1
timestamp = 0
timer = None
seqnum = 0
ack = 31
idx = 0
ackDuplicate = 0

fileN = None
fileAck = None
fileSeq = None

hostAddr = None
emuPort = None
senderPort = None
timeout = 0
filename = None
packets = []

lock = threading.Lock()

def main(argv):
    if len(argv) != 6:
        print("ERROR: Mssing arguments: sender.py <host_addr> <emu_port> <sender_port> <timeout> <file_name>")
        sys.exit(1)

    global hostAddr
    global emuPort
    global senderPort
    global timeout
    global filename

    global fileN
    global fileAck
    global fileSeq

    global debug

    hostAddr = argv[1]
    emuPort = int(argv[2])
    senderPort = int(argv[3])
    timeout = int(argv[4])/1000
    filename = argv[5]

    t1 = threading.Thread(target=send)
    t2 = threading.Thread(target=receiveAck)
    t1.start()
    t2.start()

    t1.join()
    t2.join()

    if debug == 1:
        print("Exiting Main Thread")

def send():
    global hostAddr
    global emuPort
    global senderPort
    global timeout
    global filename

    global N
    global timestamp
    global timer
    global seqnum
    global ack
    global idx
    global lock
    global packets
    global ackDuplicate

    # udp socket
    socketUDP = socket(AF_INET, SOCK_DGRAM)

    log("N.log", timestamp, N)

    with open(filename, "r") as f:
        while True:
            data = f.read(500)
            if not data:
                break
            packets.append(data)

    while True:
        lock.acquire()
        d = diff(ack, seqnum)
        if idx >= len(packets):
            if ack == (len(packets)-1)%32:
                # EOT
                timestamp += 1
                log("seqnum.log", timestamp, "EOT")
                pkt = Packet(2, seqnum, 0, "")
                lock.release()

                socketUDP.sendto(pkt.encode(), (hostAddr, emuPort))
                socketUDP.close()
                if timer != None:
                    timer.cancel()
                break
            
            lock.release()
            continue
        elif d < N:
            # send packet
            data = packets[idx]
            pkt = Packet(1, seqnum, len(data), data)

            socketUDP.sendto(pkt.encode(), (hostAddr, emuPort))

            # seqnum.log
            timestamp += 1
            log("seqnum.log", timestamp, seqnum)
            idx += 1
            seqnum = (seqnum+1)%32
            if timer == None:
                timer = Timer(timeout, retransmit)
                timer.start()
            lock.release()
        else:
            lock.release()
        
def receiveAck():
    global N
    global ack
    global idx
    global timestamp
    global timer
    global lock
    global emuPort
    global hostAddr
    global senderPort
    global seqnum
    global ackDuplicate
    global debug

    # udp socket
    socketUDP = socket(AF_INET, SOCK_DGRAM)
    socketUDP.bind(('', senderPort))

    # receive ack
    while True:

        ackPkt, addr = socketUDP.recvfrom(2048)
        pktType, ackSeqnum, length, ackData = Packet(ackPkt).decode()
        if debug == 1:
            print("ack: pktType: {}, newack: {}, curack: {}, curseqnum: {}".format(pktType, ackSeqnum, ack, seqnum))

        if pktType == 2:
            lock.acquire()
            timestamp += 1
            log("ack.log", timestamp, "EOT")
            lock.release()

            socketUDP.close()
            if timer != None:
                timer.cancel()
            break

        
        lock.acquire()
        log("ack.log", timestamp, ackSeqnum)
        lock.release()

        if ackSeqnum == ack:
            lock.acquire()
            ackDuplicate += 1

            # check duplicate ack count == 3
            if ackDuplicate == 3:
                N = 1
                timestamp += 1
                ackDuplicate = 0
                log("N.log", timestamp, N)

                # retransmit ack+1
                d = diff(ack, seqnum)
                if (idx-d <= len(packets)-1):
                    data = packets[idx-d]
                    pkt = Packet(1, (idx-d)%32, len(data), data)
                    log("seqnum.log", timestamp, (ack+1)%32)
                    socketUDP.sendto(pkt.encode(), (hostAddr, emuPort))

                lock.release()

                # restart timer
                lock.acquire()
                if timer != None:
                    timer.cancel()
                timer = Timer(timeout, retransmit)
                timer.start()

            lock.release()

        elif ackSeqnum > ack or (seqnum < ack and ackSeqnum < ack):
            # new ack
            lock.acquire()
            ackDuplicate = 0
            ack = ackSeqnum
            if ack != (seqnum-1)%32:
                if timer != None:
                    timer.cancel()
                timer = Timer(timeout, retransmit)
                timer.start()
            else:
                timer.cancel()
                timer = None
            
            N = min(N+1, 10)
            timestamp += 1
            log("N.log", timestamp, N)
            lock.release()

def retransmit():
    global N
    global timestamp
    global timer
    global seqnum
    global ack
    global idx
    global lock
    global packets
    global emuPort
    global hostAddr
    global senderPort
    global debug

    # udp socket
    socketUDP = socket(AF_INET, SOCK_DGRAM)

    lock.acquire()
    N = 1
    timestamp += 1
    log("N.log", timestamp, N)

    # retransmit
    d = diff(ack, seqnum)
    if (idx-d <= len(packets)-1):
        data = packets[idx-d]
        if debug == 1:
            print("timeout-retransmit: {}, {}".format((idx-d)%32, (ack+1)%32))
        pkt = Packet(1, (idx-d)%32, len(data), data)

        socketUDP.sendto(pkt.encode(), (hostAddr, emuPort))
        log("seqnum.log", timestamp, (ack+1)%32)

    # restart timer
    if timer != None:
        timer.cancel()
    timer = Timer(timeout, retransmit)
    timer.start()
    lock.release()
            
def diff(ack, seqnum):
    d = seqnum-ack-1
    if ack > seqnum:
        d = 31-ack+seqnum
    return d

def log(filename, timestamp, val):
    with open(filename, "a") as file:
        file.write(f"t={timestamp} {val}\n")

if __name__ == "__main__":
    main(sys.argv)
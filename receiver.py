import sys
from socket import *
from packet import Packet

# enable debugging messgaes
debug = 0

def main(argv):
    global debug

    if len(argv) != 5:
        print("ERROR: Mssing arguments: sender.py <host_addr> <emu_port> <sender_port> <timeout> <file_name>")
        sys.exit(1)

    hostAddr = argv[1]
    emuPort = int(argv[2])
    receiverPort = argv[3]
    filename = argv[4]

    nextSeqnum = 0
    buffer = {}

    # udp socket
    socketUDP = socket(AF_INET, SOCK_DGRAM)
    socketUDP.bind(('', int(receiverPort)))

    output = open(filename, "w")

    while True:
        pkt, addr = socketUDP.recvfrom(2048)
        pktType, seqnum, length, data = Packet(pkt).decode()
        if debug == 1:
            print("ack: pktType: {}, seqnum: {}".format(pktType, seqnum))

        # log seqnum
        if seqnum == nextSeqnum:
            if pktType == 2:
                # EOT
                newPkt = Packet(2, seqnum, 0, "")
                socketUDP.sendto(newPkt.encode(), (hostAddr, emuPort))
                socketUDP.close()
                with open("arrival.log", "a") as file:
                    file.write(f"EOT\n")
                break
            else:
                with open("arrival.log", "a") as file:
                    file.write(f"{seqnum}\n")

                buffer[nextSeqnum] = data
                while nextSeqnum in buffer:

                    if debug == 1:
                        print(buffer)
                        print("move buffer to output: {}".format(nextSeqnum))

                    # write to output file
                    output.write(buffer[nextSeqnum])
                    buffer.pop(nextSeqnum)
                    nextSeqnum = (nextSeqnum+1)%32
                
                # send ack packet

                if debug == 1:
                    print("send ack: {}".format((nextSeqnum-1)%32))
                newPkt = Packet(0, (nextSeqnum-1)%32, 0, "")
                socketUDP.sendto(newPkt.encode(), (hostAddr, emuPort))
                continue

        with open("arrival.log", "a") as file:
            file.write(f"{seqnum}\n")
        window = [(nextSeqnum+i)%32 for i in range(10)]
        if seqnum in window:
            buffer[seqnum] = data
        
        # send ack packet
        if debug == 1:
            print("send ack: {}".format((nextSeqnum-1)%32))
        newPkt = Packet(0, (nextSeqnum-1)%32, 0, "")
        socketUDP.sendto(newPkt.encode(), (hostAddr, emuPort))
    output.close()

if __name__ == "__main__":
    main(sys.argv)
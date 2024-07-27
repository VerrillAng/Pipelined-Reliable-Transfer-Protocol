from socket import *
import random 


expected_seq_base = 0
highest_base = 0
serverSocket = 0

def three_way_handshake(serverSocket):
    global expected_seq_base
    syn_msg, clientAddress = serverSocket.recvfrom(2048)
    syn_msg = syn_msg.decode().split(',')
    if (syn_msg != None):
        print(f"Message Received! {syn_msg}")

    # Receive SYN msg
    if ((syn_msg[0] == '1') and (syn_msg[2] == '0')):
        print(f"Received: SYN, seq={syn_msg[1]}")
        ack_num = int(syn_msg[1]) + 1

        # Send SYNACK msg
        # seq = random.randint(0, 10000)
        seq = 0
        msg = f"1,{seq},1,{ack_num}"
        serverSocket.sendto(msg.encode(), clientAddress)
        print(f"Sent: SYNACK, seq={seq}, ACKnum={ack_num}")
        expected_seq_base = ack_num
        # Receive ACK(y)
        ack_msg, clientAddress = serverSocket.recvfrom(2048)
        ack_msg = ack_msg.decode().split(',')
        if (ack_msg != None):
            print(f"Message Received! {ack_msg}")

        if ((ack_msg[0] == '0') and (ack_msg[2] == '1')):
            print(f"Received: ACK, ACKnum={ack_msg[3]}")
            print(f"! Three-Way Handshake Completed with address {clientAddress}!\n")
            
            return True

    return False

#base: the base of the message
#ack number: the cumulative ack number
def reply_ack(serverSocket, clientAddress, acknumber, base):
    message = f"{base,acknumber}" #reply format: the base of the message, the cumulative ack number
    print(message)
    serverSocket.sendto(message.encode(), clientAddress)
    print(f"Sent: ACK={acknumber}")

def receive_msg():
    global expected_seq_base, highest_base, serverSocket

    while True:
        
        msg, clientAddress = serverSocket.recvfrom(2048)
        print("let's try")
        msg = msg.decode().split(':')
        base = int(msg[0].strip())
        message_string = msg[1].strip()
        message_length = len(message_string)
        print(f"Received: seq={base}")

        if base == expected_seq_base:
            print("Received packet is in order.")
            expected_seq_base += message_length
            highest_base = base
            reply_ack(serverSocket, clientAddress, expected_seq_base, base)    
        else:
            print("Packet out of order. Retransmitting highest in order-sequence number.")
            reply_ack(serverSocket, clientAddress, expected_seq_base, highest_base)
        


def main():
    global serverSocket
    # Define Server Port
    serverPort = 12000

    # Create UDP Socket
    serverSocket = socket(AF_INET, SOCK_DGRAM)

    # Bind socket
    serverSocket.bind(('', serverPort))

    print("The Server is Ready to Receive")

    if (three_way_handshake(serverSocket) == True):
        while True:
            receive_msg()
            # # Read from socket
            # message, clientAddress = serverSocket.recvfrom(2048)

            # # Upper Case
            # modifiedMessage = message.decode().upper()

            # # Send modified message to client
            # serverSocket.sendto(modifiedMessage.encode(), clientAddress)


if __name__ == '__main__':
    main()
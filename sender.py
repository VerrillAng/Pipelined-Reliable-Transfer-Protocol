from socket import *
import random

def three_way_handshake(clientSocket, serverName, serverPort):
    # Send TCP SYN msg
    seq_num = random.randint(0, 10000)
    msg = f"1,{seq_num},0,0" # message = (SYNbit, SeqNum, ACKbit, ACKnum)
    clientSocket.sendto(msg.encode(), (serverName, serverPort))
    print(f"Sent: SYN, seq={seq_num}")

    # Receive SYNAck
    synAck_msg, serverAddress = clientSocket.recvfrom(2048)
    synAck_msg = synAck_msg.decode().split(',')
    if (synAck_msg != None):
        print(f"Reply Received! {synAck_msg}")

    if ((synAck_msg[0] == '1') and (synAck_msg[2] == '1')):
        print(f"Received: SYNACK(x), seq={synAck_msg[1]}, ACKnum={synAck_msg[3]}")

        # Send ACK for SYNACK
        ack_num = int(synAck_msg[1]) + 1
        msg = f"0,0,1,{ack_num}"
        clientSocket.sendto(msg.encode(), (serverName, serverPort))
        print(f"Sent: ACK, ACKnum={ack_num}")
        print("! Three-Way Handshake Completed !\n")

        return True

    return False

def main():
    # Initialize the conenction
    init = input("Type '-I' to initialize the connection: ")
    if (init.strip() == '-I'):
        # Define Server IP Address and Port
        serverName = 'localhost'
        serverPort = 12000

        # Create UDP Socket for Client
        clientSocket = socket(AF_INET, SOCK_DGRAM)
        
        # Three-Way Handshake
        if (three_way_handshake(clientSocket, serverName, serverPort) == True):
            while True:
                # Get keyboard input 
                message = input("Input Lowercase Sentence or '-C' to close: ")
                if (message.strip() == '-C'):
                    # Close client socket
                    print("Connection Closed")
                    clientSocket.close()
                    break

                # Send message to receiver
                clientSocket.sendto(message.encode(), (serverName, serverPort))

                # Read reply characters from socket into string
                modifiedMessage, serverAddress = clientSocket.recvfrom(2048)

                # Print received string
                print(modifiedMessage.decode())




if __name__ == '__main__':
    main()
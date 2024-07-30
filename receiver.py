from socket import *
import random 
import sys
import time

expected_seq_base = 0
highest_base = 0
serverSocket = 0

# TODO: Add this code
def no_packet_loss():
    # 50% chance of no packet loss
    if random.random() > 0.1:
        # No loss
        return True
    else:
        # Loss
        print("- Packet Loss -")
        return False


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
        retransmit = False

        # seq = random.randint(0, 10000)
        seq = 0
        msg = f"1,{seq},1,{ack_num}"
        expected_seq_base = ack_num

        for i in range(5):
            serverSocket.settimeout(None)

            # Send SYNACK msg
            if no_packet_loss():
                serverSocket.sendto(msg.encode(), clientAddress)
                if retransmit:
                    print(f"Retransmitting... SYNACK, seq={seq}, ACKnum={ack_num}\n")
                else:
                    print(f"Sent: SYNACK, seq={seq}, ACKnum={ack_num}\n")
            
            else:
                print(f"Sending... SYNACK, seq={seq}, ACKnum={ack_num}")
                print(f"!Packet Loss! SYNACK, seq={seq}, ACKnum={ack_num}\n")

            # Wait 5 seconds for ACK
            serverSocket.settimeout(5)
            try:
                # Receive ACK(y)
                ack_msg, clientAddress = serverSocket.recvfrom(2048)
                ack_msg = ack_msg.decode().split(',')
                if (ack_msg != None):
                    print(f"Message Received! {ack_msg}")

                if ((ack_msg[0] == '0') and (ack_msg[2] == '1')):
                    print(f"Received: ACK, ACKnum={ack_msg[3]}")
                    if (int(ack_msg[3]) == seq + 1):
                        print(f"! Three-Way Handshake Completed with address {clientAddress}, Connection Established!\n")
                        serverSocket.settimeout(None)
                        return True
                    
                    else:
                        print(f"Incorrect pakcet received, expected ACKnum = {seq + 1}")
                
                else:
                    print("Packet received is not ACK packet")
                    retransmit = True

            except TimeoutError:
                 print("Timeout waiting for ACK")
                 retransmit = True

        print("Failed to receive ACK")
        retransmit = True

    return False

#base: the base of the message
#ack number: the cumulative ack number
def reply_ack(serverSocket, clientAddress, acknumber, base):
    message = f"{base,acknumber}" #reply format: the base of the message, the cumulative ack number
    serverSocket.sendto(message.encode(), clientAddress)
    print(f"Sent: ACK={acknumber}")

def receive_msg():
    global expected_seq_base, highest_base, serverSocket
    
    while True:
        msg, clientAddress = serverSocket.recvfrom(2048)
        print("\n")
        msg = msg.decode().split(':')

        # If Close Connection
        if msg[0] == "FIN":
            print(f"Message Received! {msg}")
            print(f"Received: FIN, seq={msg[1]}")
            close_connection(serverSocket, msg, clientAddress)
            sys.exit()

        # Data packet
        base = int(msg[0].strip())
        message_string = msg[1].strip()
        message_length = len(message_string)
        print(f"Received: seq={base} with length={message_length}")

        if base == expected_seq_base:
            print("Received packet is in order.")
            expected_seq_base += message_length
            highest_base = base
            time.sleep(2) #give time for receiver to deliver the packets to application layer 
            if no_packet_loss():
                reply_ack(serverSocket, clientAddress, expected_seq_base, base)    
        elif base < expected_seq_base: #Lost in ACK
            print(f"Packet out of order. Retransmitting ACK for sequence={base}")
            expected_seq_base = base + message_length
            highest_base = base
            if no_packet_loss():
                reply_ack(serverSocket, clientAddress, expected_seq_base, base) 
        else:
            print("Packet out of order. Retransmitting highest in order-sequence number.")
            if no_packet_loss():
                reply_ack(serverSocket, clientAddress, expected_seq_base, highest_base)

def reply_ack(serverSocket, clientAddress, acknumber, base):
    message = f"{base,acknumber}" #reply format: the base of the message, the cumulative ack number
    serverSocket.sendto(message.encode(), clientAddress)
    print(f"Sent: ACK={acknumber}")

def close_connection(serverSocket, fin_msg, clientAddress):     
    server_state = "ESTAB"
    retransmit = False
    fin_sender_seq = int(fin_msg[1])

    # Send ACK
    msg = f"ACK:{int(fin_msg[1]) + 1}"
    if no_packet_loss():
        serverSocket.sendto(msg.encode(), clientAddress)
        print(f"Sent: ACK, ACKnum = {int(fin_msg[1]) + 1}\n")
    else:
        print(f"Sending... ACK, ACKnum = {int(fin_msg[1]) + 1}")
        print(f"!Packet Loss! ACK, ACKnum = {int(fin_msg[1]) + 1}\n")
    server_state = "CLOSE_WAIT"

    for i in range(5):
        serverSocket.settimeout(None)

        # Send FIN
        msg = f"FIN:{expected_seq_base}"
        if no_packet_loss():    
            serverSocket.sendto(msg.encode(), clientAddress)
            if retransmit:
                print(f"Retransmitting... FIN, seq = {expected_seq_base}\n")
            else:
                print(f"Sent: FIN, seq = {expected_seq_base}\n")
            server_state = "LAST_ACK"
        else:
            print(f"Sending... FIN, seq = {expected_seq_base}")
            print(f"!Packet Loss! FIN, seq = {expected_seq_base}\n") 
        
        # Wait for ACK
        serverSocket.settimeout(5)

        try:
            # Receive ACK
            ack_msg, clientAddress = serverSocket.recvfrom(2048)
            ack_msg = ack_msg.decode().split(':') 
            if (ack_msg != None):
                print(f"Message Received! {ack_msg}")

            if (ack_msg[0] == 'ACK'):
                print(f"Received: ACK, ACKnum = {int(ack_msg[1])}")
                if (int(ack_msg[1]) == expected_seq_base + 1):
                    print("Receiver Successfully Closed!")
                    server_state = "CLOSED"
                    serverSocket.settimeout(None)
                    # serverSocket.close()
                    return

                else:
                    print(f"Incorrect packet received, expected ACKnum = {expected_seq_base + 1}")
                    retransmit = True

            # When Retransmission of sender FIN detected
            elif (ack_msg[0] == 'FIN' and int(ack_msg[1]) == fin_sender_seq):
                print(f"Received: FIN, seq = {int(ack_msg[1])}")
                print(f"Duplicate packet detected")
                print(f"Retransmitting... ACK, seq = {int(ack_msg[1]) + 1}")
                msg = f"ACK:{int(ack_msg[1]) + 1}"
                if no_packet_loss():
                    serverSocket.sendto(msg.encode(), clientAddress)
                    print(f"Sent: ACK, ACKnum = {int(ack_msg[1]) + 1}\n")
                else:
                    print(f"Sending... ACK, seq = {int(ack_msg[1]) + 1}")
                    print(f"!Packet Loss! ACK, seq = {int(ack_msg[1]) + 1}\n")
                retransmit = True
                
            else:
                print("Packet received is not ACK or FIN packet")
                retransmit = True

        except TimeoutError:
            print("Timeout waiting for ACK")
            retransmit = True

    # Failed to get ACK
    print("Error: Failed to receive ACK, shutting down...")
    serverSocket.settimeout(None)
    serverSocket.close()
    return


def main():
    global serverSocket
    # Define Server Port
    serverPort = 12006

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
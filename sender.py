from socket import *
import random
import threading
import time

TIME_OUT = 5


#Global variables
next_seq_num = 0 #Window Sequence Number
used_window = 0
msg_buffer = {}
active_timers = {}
base = 0
receiving_ack = True
clientSocket = 0
serverName = ""
serverPort = 0
expected_ack = 0
lock = threading.Lock()
thread_continue = True
cwnd = 4

# TODO: Add this code
def no_packet_loss():
    # 50% chance of packet loss
    if random.random() > 0.3:
        # No loss
        return True
    else:
        # Loss
        print("- Packet Loss -")
        return False

def three_way_handshake(clientSocket, serverName, serverPort):
    # Send TCP SYN msg
    # seq_num = random.randint(0, 10000)
    global next_seq_num, base
    seq_num = 0
    msg = f"1,{seq_num},0,0" # message = (SYNbit, SeqNum, ACKbit, ACKnum)
    retransmit = False

    for i in range(5):
        # Send SYN
        if no_packet_loss():
            clientSocket.sendto(msg.encode(), (serverName, serverPort))
            if retransmit:
                print(f"Retransmitting... SYN, seq={seq_num}\n")
            else:
                print(f"Sent: SYN, seq = {seq_num}\n")

        else:
            print(f"Sending... SYN, seq={seq_num}")
            print(f"!Packet Loss! SYN, seq={seq_num}\n")

        # Wait 5 seconds for SYNACK
        clientSocket.settimeout(5)
        try:
            clientSocket.settimeout(None)

            # Receive SYNAck
            synAck_msg, serverAddress = clientSocket.recvfrom(2048)
            synAck_msg = synAck_msg.decode().split(',')
            if (synAck_msg != None):
                print(f"Reply Received! {synAck_msg}")

            if ((synAck_msg[0] == '1') and (synAck_msg[2] == '1')):
                print(f"Received: SYNACK(x), seq={synAck_msg[1]}, ACKnum={synAck_msg[3]}\n")
                if (int(synAck_msg[3]) == seq_num + 1):
                    next_seq_num = int(synAck_msg[3])
                    base = next_seq_num
        
                    # Send ACK for SYNACK
                    if no_packet_loss():
                        ack_num = int(synAck_msg[1]) + 1
                        msg = f"0,0,1,{ack_num}"
                        clientSocket.sendto(msg.encode(), (serverName, serverPort))
                        print(f"Sent: ACK, ACKnum={ack_num}")
                        print("! Three-Way Handshake Completed, Connection Established !\n")
                        clientSocket.settimeout(None)

                        return True
                                    
                else:
                    print(f"Incorect packet received, expected ACKnum = {seq_num + 1}")
                    retransmit = True

            else:
                print("Packet received is not SYNACK packet")
                retransmit = True

        except TimeoutError:
            print("Timeout waiting for SYNACK")
            retransmit = True
    
    print("Failed to receive SYNACK! Terminating...")
    return False

def timeout():
    global base, next_seq_num, msg_buffer, active_timers, clientSocket, serverPort, serverName, cwnd, used_window
    with lock: 
        seq_nums = list(range(base, next_seq_num))
        print()
        print(f"Timeout for seq={base}. Resending packets: {list(msg_buffer.keys())}")
        for i in seq_nums:
            send_packet(i, clientSocket, serverName, serverPort)

        #Minimum number of cwnd will be 4
        if(cwnd >= 5):
            if(cwnd >= 8):
                cwnd = cwnd // 2
            else:
                cwnd = 4

            index = cwnd
            keys = list(msg_buffer.keys())
            keys_to_delete = keys[index:]
            for key in keys_to_delete:
                del msg_buffer[key]
            used_window = len(msg_buffer)


        init_timer(base)
    

def init_timer(seq_num):
    global active_timers
    timer = threading.Timer(TIME_OUT, timeout)
    active_timers[seq_num] = timer
    timer.start()

def terminate_timer(seq_num):
    global active_timers
    if seq_num in active_timers:
        active_timers[seq_num].cancel()
        del active_timers[seq_num]


def send_packet(seq, clientSocket, serverName, serverPort):
    global msg_buffer
    if seq in msg_buffer:
        message = msg_buffer[seq]
        message = f"{seq}:{message}" #Format message: seq num:message
        clientSocket.sendto(message.encode(), (serverName, serverPort))
        
        
def send_message(message, clientSocket, serverName, serverPort):
    global msg_buffer, next_seq_num, used_window, expected_ack, base, cwnd
    expectedSentSeq = 0
    with lock:
        msg_buffer[next_seq_num] = message
        message_length = len(message)
        
        # Send packets within the window size
        if used_window < cwnd:
            expectedSentSeq = next_seq_num 
            next_seq_num += message_length #have to be done first to account for probability of next packet loss
            used_window += 1
            print(f"Sent: seq={expectedSentSeq}")

            if no_packet_loss():
                send_packet(expectedSentSeq, clientSocket, serverName, serverPort)
            
            if base == expectedSentSeq:
                init_timer(expectedSentSeq)
                expected_ack = base + message_length
    
            
        else:
            print(f"CWND is full. Resend or wait for ACK reply.")

    
#TODO: Modify ACK: base num
#Format of ACK: {ACK={num}}
def receive_ack():
    global base, msg_buffer, active_timers, next_seq_num, receiving_ack, used_window, clientSocket, cwnd
    num = 0

    # while True: #ACK: base, acknum
    # while thread_continue == True: #ACK: base, acknum
    reply, _ = clientSocket.recvfrom(2048)
    reply = reply.decode()
    reply = reply.strip("()").split(',')
    reply_base = int(reply[0])
    num = int(reply[1])
    with lock:
        if expected_ack == num:
            print(f"Received ACK:{num}")
            terminate_timer(base)
            del msg_buffer[base]
            used_window -= 1
            base = num
            if(base == next_seq_num):
                print("All packets acked.\n")
            else:
                init_timer(base)

                cwnd = cwnd + 1

        elif num < expected_ack:
            print(f"Ignore duplicate ack:{num}")


def close_connection(clientSocket, serverName, serverPort):
    global next_seq_num
    client_state = "ESTAB"
    retransmit = False

    for i in range(5):
        clientSocket.settimeout(None)

        # Send FIN
        msg = f"FIN:{next_seq_num}"
        if no_packet_loss():
            clientSocket.sendto(msg.encode(), (serverName, serverPort))
            if retransmit:
                print(f"Retransmitting... FIN, seq={next_seq_num}")
            else:
                print(f"Sent: FIN, seq={next_seq_num}\n")
            client_state = "FIN_WAIT_1"

        else:
            print(f"Sending... FIN, seq={next_seq_num}")
            print(f"!Packet Loss! FIN, seq={next_seq_num}\n") 

        # Wait 5 seconds for ACK
        clientSocket.settimeout(5)
        try:
            # Receive ACK
            ack_msg, serverAddress = clientSocket.recvfrom(2048)
            ack_msg = ack_msg.decode().split(':')
            if (ack_msg != None):
                print(f"Message Received! {ack_msg}")

            if (ack_msg[0] == 'ACK'):
                print(f"Received: ACK, ACKnum = {ack_msg[1]}")

                # Correct packet received
                if (int(ack_msg[1]) == next_seq_num + 1):
                    client_state = "FIN_WAIT_2"
                    print("Now waiting for server FIN\n")
                    clientSocket.settimeout(None)
                    break

                # Incorrect packet received
                else:
                    print(f"Incorrect packet received, expected ACKnum = {next_seq_num + 1}")
                    retransmit = True

            else:
                print("Packet received is not ACK packet")
                retransmit = True

        except TimeoutError:
            print("Timeout waiting for ACK")
            retransmit = True

    if client_state == "FIN_WAIT_2":
        # Wait for Server FIN
        for i in range(5):
            clientSocket.settimeout(None)

            # Wait 5 seconds for FIN message
            clientSocket.settimeout(5)
            try:
                # Receive FIN
                fin_msg, serverAddress = clientSocket.recvfrom(2048)
                fin_msg = fin_msg.decode().split(':')
                if (fin_msg != None):
                    print(f"Message Received! {fin_msg}")

                if (fin_msg[0] == 'FIN'):
                    print(f"Received: FIN, seq = {fin_msg[1]}")

                    # Reply with ACK
                    msg = f"ACK:{int(fin_msg[1]) + 1}"

                    if no_packet_loss():
                        clientSocket.sendto(msg.encode(), (serverName, serverPort))
                        print(f"Sent: ACK, ACKnum = {int(fin_msg[1]) + 1}\n")
                    else:
                        print(f"Sending... ACK, ACKnum = {int(fin_msg[1]) + 1}")
                        print(f"!Packet Loss! ACK, ACKnum = {int(fin_msg[1]) + 1}\n")

                    client_state = "TIMED_WAIT"
                    break
                
                # # When it's a data packet
                # else:
                #     # TODO
                #     print("HELLO")

            except TimeoutError:
                print("Timeout waiting for FIN")

        # No FIN received
        if client_state != "TIMED_WAIT":
            print("Error: No FIN received from sender, shutting down...")
            clientSocket.settimeout(None)
            clientSocket.close()
            return

    # Failed getting ACK in FIN_WAIT_1
    else:
        print("Error: Failed receiving ACK packet, shutting down...")
        clientSocket.settimeout(None)
        clientSocket.close()
        return

    while client_state == "TIMED_WAIT":
        # Wait for 2*max segment lifetime (30 seconds)
        clientSocket.settimeout(30)

        try:
            # Receive any retransmission of FIN packet
            fin_msg, serverAddress = clientSocket.recvfrom(2048)
            fin_msg = fin_msg.decode().split(':')
            if (fin_msg != None):
                print(f"Message Received! {fin_msg}")

            if (fin_msg[0] == 'FIN'):
                print(f"Received: FIN, seq = {fin_msg[1]}")

                # Reply with ACK
                msg = f"ACK,{int(fin_msg[1]) + 1}"
                if no_packet_loss():    
                    clientSocket.sendto(msg.encode(), (serverName, serverPort))
                    print(f"Sent: ACK, ACKnum = {int(fin_msg[1]) + 1}\n")
                else:
                    print(f"Sending... ACK, ACKnum = {int(fin_msg[1]) + 1}")
                    print(f"!Packet Loss! ACK, ACKnum = {int(fin_msg[1]) + 1}\n")

                client_state = "TIMED_WAIT"               
                
            else:
                print("Packet received is not FIN packet")

        except TimeoutError:
            print("Sender closed connection")
            client_state = "CLOSED"
            clientSocket.settimeout(None)
            clientSocket.close()
            return
    
    # Failed receiving FIN
    print("Error: Failed receiving FIN packet, shutting down...")
    clientSocket.settimeout(None)
    clientSocket.close()
    return


def main():
    global serverName, serverPort, clientSocket
    # Initialize the conenction
    init = input("Type '-I' to initialize the connection: ")
    if (init.strip() == '-I'):
        # Define Server IP Address and Port
        serverName = 'localhost'
        serverPort = 12006

        # Create UDP Socket for Client
        clientSocket = socket(AF_INET, SOCK_DGRAM)
        
        # Three-Way Handshake
        if (three_way_handshake(clientSocket, serverName, serverPort) == True):
            # receivingAck_t = threading.Thread(target=receive_ack)
            # receivingAck_t.start()
            
            while True:
                # Get keyboard input
                time.sleep(0.1) 
                message = input("Input Lowercase Sentence or '-C' to close: ")
                if (message.strip() == '-C'):
                    # Close client socket
                    # receivingAck_t.join()
                    print("Closing connection...")
                    close_connection(clientSocket, serverName, serverPort)
                    # print("Connection Closed")
                    clientSocket.close()
                    break

                send_message(message, clientSocket, serverName, serverPort)
                receive_ack()
                # Read reply characters from socket into string
                # modifiedMessage, serverAddress = clientSocket.recvfrom(2048)

                # Print received string
                # print(modifiedMessage.decode())




if __name__ == '__main__':
    main()
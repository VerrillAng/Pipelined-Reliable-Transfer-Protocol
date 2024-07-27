from socket import *
import random
import threading
import time

TIME_OUT = 2
WINDOW_SIZE_N = 4

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



def three_way_handshake(clientSocket, serverName, serverPort):
    # Send TCP SYN msg
    # seq_num = random.randint(0, 10000)
    global next_seq_num
    seq_num = 0
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
        seq_num = synAck_msg[1]
        next_seq_num = int(seq_num) + 1

        # Send ACK for SYNACK
        ack_num = int(synAck_msg[1]) + 1
        msg = f"0,0,1,{ack_num}"
        clientSocket.sendto(msg.encode(), (serverName, serverPort))
        print(f"Sent: ACK, ACKnum={ack_num}")
        print("! Three-Way Handshake Completed !\n")

        return True

    return False

def timeout():
    global base, next_seq_num, msg_buffer, active_timers, clientSocket, serverPort, serverName
    seq_nums = list(range(base, next_seq_num))
    print(f"Timeout for seq={base}. Resending packets: {seq_nums}")
    for i in seq_nums:
        send_packet(i, clientSocket, serverName, serverPort)

    if base < next_seq_num:
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
        message = f"{seq}, {message}"
        print(f"Sending seq={seq}")
        clientSocket.sendto(message.encode(), (serverName, serverPort))
    return

def send_message(message, clientSocket, serverName, serverPort):
    global msg_buffer, next_seq_num, used_window, receiving_ack
    msg_buffer[next_seq_num] = message
    receiving_ack = True
    while used_window < WINDOW_SIZE_N:
        send_packet(next_seq_num, clientSocket, serverName, serverPort)
        if base == next_seq_num:
            init_timer(next_seq_num)
        message_length = len(message)
        next_seq_num = next_seq_num + message_length
        used_window = used_window + 1


    

#Format of ACK: {ACK={num}}
def receive_ack(clientSocket):
    global base, msg_buffer, active_timers, next_seq_num, receiving_ack, used_window
    num = 0
    while receiving_ack: 
        reply, _ = clientSocket.recvfrom(2048)
        reply = reply.decode().split('=')
        num = int(reply[1])
        if num >= base:
            for i in range(base, num + 1):
                terminate_timer(i)
                if i in msg_buffer:
                    del msg_buffer[i]
                used_window = used_window - 1
                base = num + 1
                print(f"Received ACK={num}")
                if base < next_seq_num:
                    init_timer(base)
        if base == next_seq_num:
            receiving_ack = False



def main():
    global serverName, serverPort, clientSocket
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


                send_message(message, clientSocket, serverName, serverPort)
                receive_ack(clientSocket)
                # Read reply characters from socket into string
                # modifiedMessage, serverAddress = clientSocket.recvfrom(2048)

                # Print received string
                # print(modifiedMessage.decode())




if __name__ == '__main__':
    main()
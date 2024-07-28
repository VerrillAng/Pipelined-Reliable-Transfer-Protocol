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
expected_ack = 0
lock = threading.Lock()
cwnd = 4


def three_way_handshake(clientSocket, serverName, serverPort):
    # Send TCP SYN msg
    # seq_num = random.randint(0, 10000)
    global next_seq_num, base
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
        base = next_seq_num
        
        # Send ACK for SYNACK
        ack_num = int(synAck_msg[1]) + 1
        msg = f"0,0,1,{ack_num}"
        clientSocket.sendto(msg.encode(), (serverName, serverPort))
        print(f"Sent: ACK, ACKnum={ack_num}")
        print("! Three-Way Handshake Completed !\n")

        return True

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
        if(cwnd >= 8):
            cwnd = cwnd // 2
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
        print(f"Sent: seq={seq}")
        clientSocket.sendto(message.encode(), (serverName, serverPort))
    

def send_message(message, clientSocket, serverName, serverPort):
    global msg_buffer, next_seq_num, used_window, expected_ack, base, cwnd
  
    with lock:
        msg_buffer[next_seq_num] = message
        message_length = len(message)
        
        # Send packets within the window size
        if used_window < cwnd:
            send_packet(next_seq_num, clientSocket, serverName, serverPort)
            
            if base == next_seq_num:
                init_timer(next_seq_num)
                expected_ack = base + message_length
    
            next_seq_num += message_length
            used_window += 1
        else:
            print(f"CWND is full. Resend or wait for ACK reply.")

    
#TODO: Modify ACK: base num
#Format of ACK: {ACK={num}}
def receive_ack():
    global base, msg_buffer, active_timers, next_seq_num, receiving_ack, used_window, clientSocket, cwnd
    num = 0

    while True: #ACK: base, acknum
       
        reply, _ = clientSocket.recvfrom(2048)
        reply = reply.decode()
        reply = reply.strip("()").split(',')
        reply_base = int(reply[0])
        num = int(reply[1])
        with lock:
            if expected_ack == num:
                print("\n")
                print(f"Received ACK:{num}")
                terminate_timer(base)
                del msg_buffer[base]
                used_window -= 1
                base = num
                if(base == next_seq_num):
                    print("All packets acked.")
                else:
                    init_timer(base)

                cwnd = cwnd + 1

            elif num < expected_ack:
                print(f"Ignore duplicate ack:{num}")



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
            receivingAck_t = threading.Thread(target=receive_ack)
            receivingAck_t.start()
            
            while True:
                # Get keyboard input 
                message = input("Input Lowercase Sentence or '-C' to close: ")
                if (message.strip() == '-C'):
                    # Close client socket
                    print("Connection Closed")
                    clientSocket.close()
                    break


                send_message(message, clientSocket, serverName, serverPort)
                
                # Read reply characters from socket into string
                # modifiedMessage, serverAddress = clientSocket.recvfrom(2048)

                # Print received string
                # print(modifiedMessage.decode())




if __name__ == '__main__':
    main()
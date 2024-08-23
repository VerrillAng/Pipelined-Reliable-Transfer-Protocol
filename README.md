# Pipelined-Reliable-Transfer-Protocol

Socket Type: UDP Socket
Mechanism:
● Connection-oriented: Three-Way Handshake
○ When starting both the receiver.py and sender.py, in the sender the user
needs to type “-I” to start the connection.
○ When the receiver starts, it will be open for connection, the sender needs
to initialize the connection with the receiver first, by sending a SYN packet
to the receiver, with seq number x. This will also set a timer in our code,
which is 5 seconds, this timer is to wait to receive a SYNACK packet with
the expected ACKnum (x + 1) from the receiver.
■ If the 5 seconds have passed, and no SYNACK packet with the
correct ACKnum is received, the sender will retransmit the SYN
packet to the receiver, for 5 attempts. If there’s still no correct
SYNACK packet, the sender will close, failing to connect to the
receiver.
○ After the receiver receives the SYN packet, it will respond with a SYNACK
packet with seq = y. This will start a 5 second timer in our code, expecting
an ACK packet from the sender with ACKnum y + 1.
■ If the 5 seconds have passed, and no ACK packet is received from
the sender with the correct ACKnum, the receiver will retransmit the
SYNACK packet for 5 tries. If still no correct ACK packet is
received, the receiver will close, failing to establish a connection.
● Pipelined Protocol: Go-Back-N
○ The pipeline protocol that we have chosen for this project is Go-Back-N.
Together with this mechanism, we incorporate the AIMD congestion
control and a flow control in the receiver side to control the sender.
○ For each sequence, the ACK number will be the base of the sequence +
the message length in bytes (1 character corresponds to 1 byte) .
○ The time out interval for each packet is 5 seconds.
○ The timer will only run for the base in the sender window. Time out in the
base will result in all packets in the window to be retransmitted.
○ The ACK will be cumulative, meaning that it will ACK the packet up to the
highest in order sequence that has been received by the receiver. Packets
out of order will result in the highest in order sequence’s ACK being
retransmitted.
○ For the sender window, I used the variable cwnd to indicate the number of
packets allowed in the sender window. With a minimum of 4 packets, the
AIMD will let the cwnd increase by 1 every RTT. As RTT stands for Round
Time Trip, I implemented the cwnd to be increasing every time an ack is
received. Whenever there is a loss detected (the packet’s ACK is still not
received even after the time out), the cwnd will be cut in half with a
minimum of it being 4. Window size greater than 4 but less than 8 will be
cut to 4 to satisfy this minimum condition.
○ For the flow control, as for Go-Back-N, there will be no buffer in the
receiver side and will only accept the expected packet, there will be no
change made based on the receiver to the size of the window of the
sender as receiver window size is static. However, as the receiver still
needs time to deliver data to the application layer, a delay of 2 seconds
are made before the ACK is sent to ensure reliable data transfer between
the layers (just in case the packet is lost during this process and without
sending the ACK, sender can retransmit the packet), delaying the sent of
ACK. This is implemented using time.sleep(2) function in Python.
● Closing
○ To initiate a closing sequence, in our code, the user needs to type “-C” and
send it from the sender.
○ The sender will send a FIN packet with seq=x, and the sender will change
state from ESTAB to FIN_WAIT_1
■ In this state, the sender will wait for an ACK packet with ACKnum=x
+ 1. A timer will start for 5 seconds
■ If there’s a packet loss, the sender won’t receive an ACK for the 5
seconds timer, if this happens, the sender will resend the FIN
packet, and restart the timer, for a limit of 5 attempts
■ If the limit has been reached, the sender will shutdown
○ In the receiver, when it receives a FIN packet from the sender, the receiver
will go to CLOSE_WAIT state
■ In this state, the receiver will send an ACK packet for the FIN
packet from the sender
■ Data still can be send, and still can receive ACKs
○ When the sender receives the correct ACK packet, it will go to
FIN_WAIT_2 state
■ In this state the sender will wait for a FIN packet from the receiver
○ After sending ACK for the FIN from sender, the receiver will send a FIN
packet and go to LAST_ACK packet
■ If the ACK packet is lost during transmission, the sender will
timeout (5 seconds) waiting for the ACK and resend the FIN packet
with limited to 5 tries
■ In this state, if it receives the resend FIN packet, it can still reply
with the correct ACK packet, and still waits for the ACK packet for
the receiver FIN
○ When the sender receives a FIN packet, it will go to TIMED_WAIT state,
where we set it to 30 seconds
■ Here, the sender will wait for 30 seconds, for any retransmissions
■ If there’s a packet loss either when receiver sends the FIN packet
or when the sender sends the ACK packet, the receiver will timeout
(5 seconds), and resends the FIN packet, limited to 5 attempts, the
timer resets back to 30 seconds
■ But, if 30 seconds has passed, and no packet is received, the
sender will close the connection
○ When receiver receives the last ACK packet, it will close the connection
■ If it doesn’t receive any packet, using up all the attempts of
resending, the server will shutdown

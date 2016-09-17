""" Implementation of the Client side of UDP File Transfer using Stop and Wait ARQ """

""" Buffer size of client should be smaller than the Server's. Otherwise data loss happens  """

from socket import *
import sys
import os
import math
import time

""" counts the number of digits in a given number """
def no_of_digits(a):
    count=0
    while(a!=0):
        a=a/10
        count=count+1
    return count


""" input : sequence number, output : 10 digit long formatted sequence number padded with zeroes"""
def get_seq_no(a):
    if(a==0):
        return '0'*10
    count=no_of_digits(a)
    no_of_zeroes=10-count
    val='0'*no_of_zeroes + '%d' %a
    return val

""" creates a datagram(UDP) socket with ipv4 addressing """
s=socket(AF_INET,SOCK_DGRAM)

""" stores the number of command line arguments """
no_of_arg=len(sys.argv)

""" MSS stands for maximum segment size, file can be of any file-format, but should be in the current directory  """
if(no_of_arg!=4):
    print "expected format python %s <number of hosts> <filename> <MSS> "%(sys.argv[0])

    """ 89 bytes are required for sequence number and checksum as python stores metadata as well """

elif int(sys.argv[3])<89 or int(sys.argv[3])>2048:
    print sys.agrv[2]," should be greater than 89 bytes and lesser than 2048 bytes"


else:
    host=[]
    """ addr is a list of the tuples (host_ip,port_no) """
    addr=[]
    port=[]
    no_of_hosts=int(sys.argv[1])
    """ Inputs host ips and port numbers one after the other """
    for i in range(no_of_hosts):
        host.append(raw_input("Enter hostname %d " %i))
        port.append(raw_input("Enter port of %d th host" %i))
        port[i]=int(port[i])
        addr.append((host[i],port[i]))

    
    """ t0 stores the starting time of the file transfer to the servers """
    t0=time.time()

    """ buff_size is the number of bytes of data read at a time from the file, 47 bytes for sequence no, 42 for checksum """
    buff_size=int(sys.argv[3])-47-42
    
    """ filename is obtained as command line argument """
    file_name=sys.argv[2]

    """ file_size contains total file size in bytes """
    file_size=os.stat(file_name).st_size
    print "File size of ",file_name," is ",file_size
    """ calculates the total number of packets that will be sent """
    seq_no=int(math.ceil(float(file_size)/buff_size))
    print "Total number of packets that will be sent is %d" %seq_no
    """ The first UDP packet will contain the information about the number of packets """
    for i in range(no_of_hosts):
        while(s.sendto("%d" %seq_no,addr[i])):
            break
    a=addr[:]

    """ this loop will run until ACKs are received from all the servers """
    while(len(a)!=0):
        d,ad=s.recvfrom(buff_size)
        a.remove(ad)


    seq=0
    curr_seq=get_seq_no(seq)
    """ file is read in binary format """
    f=open(file_name,'rb')

    data=f.read(buff_size)
    
    """ If within 0.5s ACKs are not received, it will be resent to the resepctive hosts """
    s.settimeout(0.5)
    
    """ this loop runs as long as there EOF is not reached """
    while(data):
        
        a=addr[:]
        data=curr_seq+data
        ascii_val=map(ord,data)
        group_val=[]
        
        """ groups 16bits together(2 ASCII characters) """
        for i in range(1,len(ascii_val)):
            group_val.append(ascii_val[i-1]*256+ascii_val[i])
         
        """ adds all the 16bit values together and obtains the 16LSBs and ignores the rest"""
        checksum=reduce(lambda x,y:(x+y)%65536,group_val)

        """ compliments this value to obtain UDP checksum """
        checksum=checksum^65535

        """ checksum is made 5 digits long and is appended with data """
        chksum_string='0'*5+'%d' %checksum
        chksum=chksum_string[-5:]
    
        data=data+chksum
    
        host_resp=0
        """ a is a list of all addresses. it becomes empty when the packet reaches all hosts """
        """ one of the following might occur when a packet is sent
        1. All hosts might receive the packets and send ACKs within the timeout period.
        2. Few hosts might not receive the packets. Hence packet to those hosts needs to be resent after 0.5s
        3. Few hosts might receive the packet but ACK might fail, in which case the client will resend the packet"""
        while(len(a) is not 0):
            #print "curr seq no is ",curr_seq

            """ packet is sent to all hosts in an iterative fashion """
            for i in range(len(a)):
                while(s.sendto(data,a[i])):
                    break
            
            """ the client waits for 0.5s to receive all ACKS. """
          
            while(host_resp<no_of_hosts):
                """ socket.Timeouterror occurs when timeout period is elapsed  """
                try:
                    ack,ad=s.recvfrom(buff_size)
                    
                    """ if out-of-sequence packet's ACK is obtained, it should be ignored """
                    if(int(curr_seq) == int(ack)):#understand 'is' functionality
                        host_resp=host_resp+1
                        a.remove(ad)
        
                except:
                    print "timeout, Sequence number = ",curr_seq
                    break
            


        """ more data is read from file """
        data=f.read(buff_size)

        """ sequence numbers is incremented """
        seq=seq+1
        curr_seq=get_seq_no(seq)
    
    """ Calculates the total time for UDP transfer """
    total_time=time.time()-t0
    print "Total time is %d"%total_time        
    
    """ close the socket """
    s.close()
    """ close the file """
    f.close()


""" Implementation of the Server side of the Point to Multipoint file tranfer using Stop and Wait ARQ"""

from socket import *
import sys
import random

""" Stores the number of command line arguments"""
no_of_arg=len(sys.argv)

""" probability refers to the probability loss service number """
if(no_of_arg!=4):
        print "expected format python %s <port no> <filename> <probability>" %(sys.argv[0])
	sys.exit(1)
""" specifies the IP of the server, hence the Network Interface is also known """
host="127.0.0.1"
""" Listening port of the server """
port=int(sys.argv[1])


randomList=[]

""" A datagram(UDP) socket is created and suports ipv4 addressing"""
s=socket(AF_INET,SOCK_DGRAM)
prob = float(sys.argv[3]);

""" contains the source host address and port number as a tuple """
addr=(host,port)

""" the server binds to this socket and waits for hosts """
s.bind(addr)
""" the input buffer size is fixed to 2048 bytes """
buff_size=2048


""" once the first packet regarding Seq No is sent, ACKs are sent back to the client"""
msg = 'sequence no. recieved!'
data,address=s.recvfrom(buff_size)
s.sendto(msg,address)


file_name=sys.argv[2]
""" A new file is open or an existing file is rewritten"""
f=open(file_name,'wb')
total = int(data)

""" though UDP is unreliable, very few packets are lost in reality. hence a few packets are made to be lost on purpose """
""" the probabilty of losing packets is taken as a command line input. and the losing-packets numbers are generated randomly and stored in randomList"""
prob = int(prob*total)
for i in range(prob):
    gen_no=random.randint(0,total-1)    
    randomList.append(gen_no)        

randomList.sort()
print randomList


try:
    """ blocked until it receives data from the client """
    data,address=s.recvfrom(buff_size)
    
    """ count keeps track of the number of packets received """
    count =0    
    while(True):
        """ if the packet number is not in randomList, it has to be accepted  """
        if(count not in randomList):
                       
            ack=data[0:10]
            ack_no=int(ack)
            """ if the received packet has already been received, it means ACK might have failed. Hence ACK is resent"""
            if(ack_no<count):
                while(not s.sendto(ack,address)):
                           continue
                count = count-1
                print "    ack < count "
            
            elif(ack_no==count):
                
                """ if the packet obtained is in-sequence, then checksum has to be verified"""
            
                
                ascii_val=map(ord,data[:-5])
                group_val=[]
                for i in range(1,len(ascii_val)):
                    group_val.append(ascii_val[i-1]*256+ascii_val[i])
                
                checksum=reduce(lambda x,y:(x+y)%65536,group_val)
                chk = data[-5:]
                checksum_calculate=(checksum+int(chk))%65535

                """ if the calculated checksum and the received checksums complement each other, then the packet is said to be error free. Hence ACK is sent """
                if(checksum_calculate==0):
                           while(not s.sendto(ack,address)):
                               continue
                           f.write(data[10:-5])
                else:
                    """ if checksums don't match, ACKs are not sent. Hence packet will be resent """
               
                    print "checksum didn't match!"
                    count =count-1

            else:
                """ this is a condition that never occurs in a Stop and Wait ARQ as only when ACKs for a packet is obtained, the next packet is sent """
            
                print "Sequence no didn't match"
                count = count-1
        else:
            """ when the packet number is in randomList, then the packet is rejected on purpose. Hence it will be resent"""
        
            print "Packet Loss, Sequence number = %d "%count            
            """ Once the packet is rejected, it is removed from the list"""
            randomList.remove(count)
            count =count-1
        """ when count is one less than total packet number, exception is raised as all packets are received."""
        """ count is one less than total as seq_no begins from zero"""
        if(count == total-1):
            #print count is total-1
            raise ValueError()
        
        """ read data from the input buffer """
        data,address=s.recvfrom(buff_size)
        count = count+1
except:
    """ once all packets are obtained, file is closed """
    f.close()
    print "File obtained"    

""" socket is closed """
s.close()

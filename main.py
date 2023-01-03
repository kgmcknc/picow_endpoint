import time
import network
import random
import socket
import secret
from machine import Pin
import arducam
import gc

led = Pin("LED", Pin.OUT)

def main():
    print('starting wifi')
    ssid = secret.SSID
    password = secret.PASSWORD
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        data = wlan.status()
        if data < 0 or data >= 3:
            break
        max_wait = max_wait - 1
        print('waiting for connection...')
        print(data)
        time.sleep(2)

    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print( 'ip = ' + status[0] )

    cam = arducam.camera_class()
    cam.init_camera()
    
    rand_int = random.randint(0,4095)
    rand_len = len(str(rand_int))
    UPNP_MCAST_IP = "239.255.255.250"
    UPNP_PORT = 1900
    BIND_IP = "0.0.0.0"
    REUSE_SOCKET = 0

    # serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # addr = socket.getaddrinfo(BIND_IP, UPNP_PORT, socket.AF_INET, socket.SOCK_DGRAM)[0][4]
    # serv_sock.bind(addr)
    # serv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, inet_aton(UPNP_MCAST_IP) + inet_aton(BIND_IP));
    # if REUSE_SOCKET:
    #     resp_sock = serv_sock
    # else:
    #    resp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while(wlan.status() == 3):
        #print("Status: ", wlan.status())
        fixed_string = "pycontroller:"
        connected = 0
        broadcast_port = 60000
        new_ip = 0
        while(connected == 0):
            broadcast_packet = "picow:"+str(rand_int)
            send_broadcast_packet(broadcast_port, broadcast_packet)
            #print("sent broadcast")
            packets = 5
            while(connected == 0 and packets > 0):
                ret_data = receive_broadcast_packet(broadcast_port+rand_int, 1024)
                if(ret_data == None):
                    #print("broadcast timeout")
                    pass
                else:
                    ret_string = ret_data[0].decode()
                    #print("got ", ret_string)
                    if(fixed_string in ret_string):
                        new_id = int(ret_string[len(fixed_string):len(fixed_string)+rand_len])
                        if(new_id == rand_int):
                            #print("Got: ", new_id, " Connected")
                            connected = 1
                            new_ip = ret_data[1][0]
                        else:
                            #print("Got: ", new_id, " Ignoring")
                            pass
                packets = packets - 1
        
        joystick_data = []
        #print("starting main controller loop")
        gc.collect()
        available = gc.mem_free()
        print(available)
        max_timeouts = 4
        while(connected):
            print("starting frame")
            cam.get_frame()
            print("Got frame")
            send_image_packet(new_ip, broadcast_port+rand_int, cam.hw_sm.image_array)
            # test_packet = "pycontroller:"+str(rand_int)
            # send_udp_packet(new_ip, broadcast_port+rand_int,test_packet)
            print("sent_udp_image")
            ret_data = receive_udp_packet(new_ip, broadcast_port+rand_int, 1024)
            if(ret_data == None):
                max_timeouts = max_timeouts - 1
                if(max_timeouts == 0):
                    connected = 0
            else:
                ret_ip = ret_data[1][0]
                if(ret_ip == new_ip):
                    ret_string = ret_data[0].decode()
                    if(fixed_string in ret_string):
                        new_id = int(ret_string[len(fixed_string):len(fixed_string)+rand_len])
                        if(new_id == rand_int):
                            packet_string = ret_string[len(fixed_string)+rand_len:]
                            joystick_data = packet_string.split(":")
                            #print(joystick_data)
                        else:
                            #print("Ignoring Packet: ", new_id)
                            pass
            if(len(joystick_data) > 7):
                if(joystick_data[7] == '0'):
                    led.off()
                else:
                    led.on()


def send_broadcast_packet(packet_port, packet_data):
    #BROADCAST_ADDR = '<broadcast>'
    BROADCAST_ADDR = '255.255.255.255'
    udp_tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_tx_sock.bind(('',0))
    udp_tx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_tx_sock.sendto(packet_data, (BROADCAST_ADDR, packet_port))
    udp_tx_sock.close()

def receive_broadcast_packet(packet_port, packet_length):
    global udp_rx_sock
    udp_rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_rx_sock.settimeout(1)
    udp_rx_sock.bind(('',packet_port))
    try:
        udp_packet_data = udp_rx_sock.recvfrom(packet_length)
    except:
        udp_packet_data = None
    udp_rx_sock.close()
    return udp_packet_data

def send_udp_packet(packet_ip, packet_port, packet_data):
    udp_tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_tx_sock.bind(('',0))
    udp_tx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_tx_sock.sendto(packet_data.encode(), (packet_ip, packet_port))
    udp_tx_sock.close()

def receive_udp_packet(packet_ip, packet_port, packet_length):
    global udp_rx_sock
    udp_rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_rx_sock.settimeout(1)
    udp_rx_sock.bind(('',packet_port))
    try:
        udp_packet_data = udp_rx_sock.recvfrom(packet_length)
    except:
        udp_packet_data = None
    udp_rx_sock.close()
    return udp_packet_data

def send_image_packet(packet_ip, packet_port, packet_data):
    udp_tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_tx_sock.bind(('',0))
    udp_tx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # udp_tx_sock.sendto(packet_data, (packet_ip, packet_port))
    # y_res = 324
    # x_res = 324
    # y_counter = 0
    # x_counter = 0
    # while(y_counter < y_res):
    #     print(y_counter)
    #     image_line = []
    #     image_line.append(y_counter & 0xff)
    #     image_line.append((y_counter >> 8) & 0xff)
    #     x_counter = 0
    #     while(x_counter < x_res):
    #         print(packet_data[x_res*y_counter+x_counter])
    #         image_line.append(packet_data[x_res*y_counter+x_counter])
    #         x_counter = x_counter + 1
    #     y_counter = y_counter + 1
    #     print("starting_send")
    #     udp_tx_sock.sendto(bytes(image_line), (packet_ip, packet_port))
    # for x in range(10):
    y_res = 324
    x_res = 324
    lines_per_packet = 4
    bytes_per_line_number = 4
    y_counter = 0
    index = 0
    while(y_counter < y_res):
        start = index
        end = index + lines_per_packet*(x_res+bytes_per_line_number)
        udp_tx_sock.sendto(packet_data[start:end], (packet_ip, packet_port))
        index = index + lines_per_packet*(x_res + bytes_per_line_number)
        y_counter = y_counter + lines_per_packet
    udp_tx_sock.close()

if __name__ == "__main__":
   main()
   time.sleep(2)
   print("Starting Main in 5 seconds")
   led.on()
   time.sleep(5)
   led.off()
   main()

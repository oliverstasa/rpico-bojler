import network
import socket
import time
import machine
import rp2
import sys
import json
import urequests
import gc

from picozero import pico_temp_sensor, pico_led



def connect(screen):
    # print('Connecting WLAN...')
    networks = [
        {"ssid": "106%_2.4Ghz", "password": "106Procent"},
        {"ssid": "Kapr", "password": "106Procent"}
    ]
    
    screen.writeToCenter("SEARCHING for WIFI")
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)
    wlan.disconnect()
    time.sleep(1)
    
    networksFound = [net[0].decode() for net in wlan.scan()]
    networkSelected = None
    for net in networks:
        if net["ssid"] in networksFound:
            networkSelected = [net]
            break
    if not networkSelected:
        screen.writeToCenter(["0 NETWORKS MATCH", "trying all..."])

    for net in networkSelected if networkSelected else networks:
        ssid, password = net["ssid"], net["password"]
        screen.writeToCenter(['CONNECTING to:', ssid])
        
        wlan.connect(ssid, password)
        for attempt in range(10):  # Adjust attempt count if needed
            screen.writeToCenter(f"CONNECTING... {str(attempt)}")
            if wlan.isconnected():
                ip = wlan.ifconfig()[0]
                screen.writeToCenter([f'DIALED AT {ssid}', ip]) # print(f'Dial {ip}')
                pico_led.on()
                return ip
            pico_led.on()
            time.sleep(0.5)
            pico_led.off()
            time.sleep(0.5)
    
    screen.writeToCenter("ALL NETWORKS FAILED")
    return None


def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection.bind(address)
    connection.listen(1)
    return connection



def webpage():
    html = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <link rel="icon" type="image/svg+xml" href="">
                </head>
                <body>
                    <form method="POST">
                        <input type="text" name="test1">
                        <input type="text" name="test2">
                        <input type="submit" value="SEND">
                    </form>
                </body>
            </html>
            """
    return str(html)



def urldecode(s):
    result = ''
    i = 0
    while i < len(s):
        if s[i] == '%':
            # %xx sequences
            hex_value = s[i+1:i+3]
            byte = int(hex_value, 16)
            result += chr(byte)
            i += 3
        elif s[i] == '+':
            result += ' '
            i += 1
        else:
            result += s[i]
            i += 1
    return result



def parse_query_string(query_string):
    params = {}
    for pair in query_string.split('&'):
        if '=' in pair:
            key, value = pair.split('=', 1)
            #print(f"{key} => {value}")
            params[key] = urldecode(value)
    return params



def decode_post_data(request):
    if request[0] != 'POST':
        #print(f"{request[0]} != POST")
        return []

    params = parse_query_string(request[-1])
    return params



def run(connection, screen):
    while True:
        client = connection.accept()[0]
        request = client.recv(4096)
        request = request.decode('UTF-8')
        request = request.split()
        params = decode_post_data(request)

        results = []

        if len(params):
            if 'test1' in params:
                value = params['test1']
                results.append(value)
                print(value)
            
            if 'test2' in params:
                value = params['test2']
                results.append(value)
                print(value)

            screen.writeToCenter(results)

        html = webpage()
        client.send(html)
        client.close()




def startServer(screen):
    ip = None
    wlan = network.WLAN(network.STA_IF)
    
    if not wlan.isconnected():
        ip = connect()
    else:
        ip = wlan.ifconfig()[0]
    
    if ip:
        screen.writeToCenter(["DIAL", ip])
        run(open_socket(ip), screen)
    else:
        screen.writeToCenter("ERROR")






def syncTime(screen):
    wlan = network.WLAN(network.STA_IF)

    # connect even when connected, must reset the connection
    connect(screen)
    
    screen.writeToCenter('FETCHING CURRENT TIME')

    try:
        response = urequests.get("http://worldclockapi.com/api/json/cet/now")
        if response.status_code == 200:
            data = response.json()
            timestamp = data['currentDateTime'].split('+')[0] # "2025-02-22T02:13+01:00"
            date, currentTime = timestamp.split('T')
            y, m, d = map(int, date.split('-'))
            hrs, min = map(int, currentTime.split(':'))
            gc.collect()
            
            # leave wifi
            wlan.disconnect()
            pico_led.off()
            
            rtc = machine.RTC()
            rtc.datetime((y, m, d, 0, hrs, min, 0, 0))
            print("Time:", rtc.datetime())
            screen.writeToCenter(['TIME SET', f"{hrs:02}:{min:02} {d}.{m}.{y}"])
            time.sleep(2)
            return True
        else:
            # print("Time API failed: Error n.", response.status_code)
            screen.writeToCenter(['TIME SERVER FAILED', response.status_code])
            return False
    except Exception as e:
        print("Time API failed request: ", e) # probbably no response
        screen.writeToCenter('TIME SYNC FAILED')
        return False

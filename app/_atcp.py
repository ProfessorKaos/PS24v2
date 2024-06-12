import network
import socket
import uasyncio as asyncio
from time import sleep, sleep_ms, ticks_ms
import secrets

class ATCP():
    def __init__(self, name):
        # Set up Network Connection
        network.hostname(name)
        self.wifi_creds = None
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.writer = None
        if self.check_wifis():
            self.wlan_connect()
        else:
            print("Failed to connect to a Knownetwork")
        self.data = b''
        self.buff = b''
        
    async def start_server(self):
        server = await asyncio.start_server(self.mess_rec, '0.0.0.0', 12345)
#         async for client in server:
#             await client
        print("Server started")


    async def mess_rec(self, reader, writer):
        self.writer = writer
        print("Client connected from:", writer.get_extra_info('peername'))
        try:
            while True:
                self.data = await reader.readline()  # read a single line
        except Exception as e:
            print(f"There was an error receiving the message: {e}")
        finally:
            print("Closing connection")
            writer.close()
            await writer.wait_closed()
    
    
    async def execute_atcp(self):
        while True:
            if self.data:
                print("ATCP message: ", self.data.decode().strip())
                try:
                    exec(self.data)
                except Exception as e:
                    print("Unable to execute ATCP message because: ", e)
                self.data = b''
            await asyncio.sleep_ms(200)
    
    
    async def send_message(self, message):
        try:
            if self.writer:
                msg = message.encode() + "\n"
                self.writer.write(msg)
                await self.writer.drain()
#                 print("Message sent:", message)
        except Exception as e:
            print(f"There was an error sending the message: {e}")
    
    
    def wlan_connect(self):
        try:
            self.wlan.connect(self.wifi_creds["User"], self.wifi_creds["Password"])
            
            timer = ticks_ms() + 5000

            while not self.wlan.isconnected() and ticks_ms() < timer:
                pass

            if self.wlan.isconnected():
                print("connected to Wifi", self.wifi_creds["User"])
                print("IP Address:", self.wlan.ifconfig()[0])
                return True
            else:
                print("Failed to connect to a Network")
                return False
            
        except Exception as e:
            print("Error connecting to network: ", e)
            return False


    def check_wifis(self):
        
        scan_results = self.wlan.scan()
        wifi_ssids = {ap[0]: ap for ap in scan_results}

#         wifi_networks = {
#             
#             b'donotuse': {"User": "donotuse", "Password": "ireallymeanit"},
#             b'Prof-Kaos': {"User": "Prof-Kaos", "Password": "joinme!haha"},
#             b'micho-leo': {"User": "micho-leo", "Password": "thedreamliveson"},
#             b'ThereIsGodInYou': {"User": "ThereIsGodInYou", "Password": "RightHereRightNow3210!"},
#         }

        for ssid, creds in secrets.wifi_networks.items():
            if ssid in wifi_ssids:
                self.wifi_creds = creds
                print(f"Changed wifi_config for: {creds['User']}")
                return True

        return False

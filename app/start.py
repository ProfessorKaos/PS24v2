from time import sleep_ms, ticks_ms
import uasyncio as asyncio
import ujson
import app._atcp as _atcp
import app._led as _led
import app._mic as _mic
import app._mpu as _mpu
import secrets
from app.ota_updater import OTAUpdater
import gc

def limit_map(x, in_min, in_max, out_min, out_max):
    return int(((max(in_min,min(in_max,x))) - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def update():
    try:
        token='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'
        updater = OTAUpdater('https://github.com/ProfessorKaos/Primordial-Stars-2024', headers={'Authorization': 'token {}'.format(token)})
        updater.install_update_if_available_after_boot(atcp.wifi_creds["User"], atcp.wifi_creds["Password"])
    except Exception as e:
        print("Something went wrong with updating: ", e)

print("UPDATED!")
 
async def sound():
    print("Starting sound")
    color_wheel = 1
    while True:
#         start_time = ticks_us()
        if color_wheel > 360:
            color_wheel = 1
        mic.rms_average()
        lighting = mic.rms_map(5,50)
        color_wheel += mic.rms_map(0,5)
#         print("lighting: ", lighting)
#         print("sound took : ", ticks_diff(ticks_us(), start_time), "us")
        led.hsl(color_wheel, 100, lighting)
        await asyncio.sleep_ms(mic.freq) 


async def touch():
    while True:
        if mpu.det_mov():
#             udp.sock.sendto(message.encode(), ("192.168.178.47", 65000))
            await atcp.send_message("Touched", "")
#             print("message sent")
            await asyncio.sleep(1)
        await asyncio.sleep_ms(50)

async def mpu_reading():
    while True:
#         xyz = mpu.map_accel(0,100)
        gyr = mpu.map_gyro(0,100)
#         print(xyz)
#         readings = mpu.sma_read_all()
#         json = ujson.dumps(readings)
#         await atcp.send_message("", json)
        
        await atcp.send_message("gyro", str(gyr))
#         await atcp.send_message("y", str(xyz[1]))
#         await atcp.send_message("z", str(xyz[2]))
        await asyncio.sleep_ms(50)


async def waiting_to_connect():
    while not atcp.writer:
        await asyncio.sleep(0)
    print("Connected to Client: ", atcp.writer.get_extra_info('peername'))
    print("Starting MPU Loop")
    loop.create_task(mpu_reading())

led = _led.LED()
mpu = _mpu.MPU()
mic = _mic.Microphone()
atcp = _atcp.ATCP(secrets.mDNS)
loop = asyncio.get_event_loop()
# connect_event = asyncio.Event()

async def main():
    led.active_effect = loop.create_task(sound())
    
    loop.create_task(atcp.execute_atcp())
    loop.create_task(touch())
    loop.create_task(mpu_reading())
    
    if atcp.wlan.isconnected():
        await atcp.start_server()
        print("This device is: ", secrets.mDNS)
#     loop.run_until_complete(waiting_to_connect())
    
    while True:
        await asyncio.sleep(30)
        gc.collect()
#         print(mpu.sma)



asyncio.run(main())
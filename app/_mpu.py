import machine
import uasyncio as asyncio


class accel():
    def __init__(self, i2c, addr=0x68):
        self.iic = i2c
        self.addr = addr
#         self.iic.start()
        self.iic.writeto(self.addr, bytearray([107, 0]))
#         self.iic.stop()

    def get_raw_values(self):
#         self.iic.start()
        a = self.iic.readfrom_mem(self.addr, 0x3B, 14)
#         self.iic.stop()
        return a

    def get_ints(self):
        b = self.get_raw_values()
        c = []
        for i in b:
            c.append(i)
        return c

    def bytes_toint(self, firstbyte, secondbyte):
        if not firstbyte & 0x80:
            return firstbyte << 8 | secondbyte
        return - (((firstbyte ^ 255) << 8) | (secondbyte ^ 255) + 1)

    def get_values(self):
        raw_ints = self.get_raw_values()
        vals = {}
        vals["AcX"] = self.bytes_toint(raw_ints[0], raw_ints[1])
        vals["AcY"] = self.bytes_toint(raw_ints[2], raw_ints[3])
        vals["AcZ"] = self.bytes_toint(raw_ints[4], raw_ints[5])
        vals["Tmp"] = self.bytes_toint(raw_ints[6], raw_ints[7]) / 340.00 + 36.53
        vals["GyX"] = self.bytes_toint(raw_ints[8], raw_ints[9])
        vals["GyY"] = self.bytes_toint(raw_ints[10], raw_ints[11])
        vals["GyZ"] = self.bytes_toint(raw_ints[12], raw_ints[13])
        return vals  # returned in range of Int16
        # -32768 to 32767

    def val_test(self):  # ONLY FOR TESTING! Also, fast reading sometimes crashes IIC
        from time import sleep
        while 1:
            print(self.get_values())
            sleep(0.05)
            
            
class MovementDetector:
    def __init__(self, i2c, threshold):
        self.sensor = accel(i2c)
        self.threshold = threshold
        self.last_readings = self.sensor.get_values()

    def detect_movement(self):
        current_readings = self.sensor.get_values()
        print("X: ", current_readings['AcX'], "Y: ", current_readings['AcY'], "Z: ", current_readings['AcZ'])
        dx = abs(self.last_readings['AcX'] - current_readings['AcX'])
        dy = abs(self.last_readings['AcY'] - current_readings['AcY'])
        dz = abs(self.last_readings['AcZ'] - current_readings['AcZ'])

        if dx > self.threshold or dy > self.threshold or dz > self.threshold:
            print("Movement detected")

        self.last_readings = current_readings
        


class MPU():
    def __init__(self):
        self.i2c = machine.SoftI2C(sda=machine.Pin(8), scl=machine.Pin(9))
        self.mpu = accel(self.i2c)
        self.calibration = {}
        self.threshold = 15000
        self.touched = False
        #Recording of the last reading made
        self.readings = {}
        # set up a dictionary that holds the memory of the last N readings to create a moving average reference
        self.memory = {'AcX':[],'AcY':[], 'AcZ':[],'GyX':[],'GyY':[], 'GyZ':[]}
        self.min_max_vals = {'AcX':(10,32000),'AcY':(10,32000), 'AcZ':(10,32000),'GyX':(10,32000),'GyY':(10,32000), 'GyZ':(10,32000)}
        self.sma = {'AcX':11,'AcY':11, 'AcZ':11,'GyX':11,'GyY':11, 'GyZ':11}
        self.N = 5 # Number of readings to be recorded in memory for the sma
        self.freq = 50 # sets the asyncio sleep_ms frequency for movement
        self.long_mem = {'AcX':[],'AcY':[], 'AcZ':[],'GyX':[],'GyY':[], 'GyZ':[]}
        self.long_len = 3000 // self.freq
        
        self.difficulty = 15
        self.mpu_reading = None
        
    def calibrate(self):
        self.calibration = self.mpu.get_values()
        
    def read(self): # reads the mpu and returns current reading. Takes ~1ms
        self.readings = self.mpu.get_values()
        return self.readings
    
    def det_mov(self): # Takes a reading, and if reading is above the Threshold to the sma, returns True. Takes ~1.5ms

        self.sma_read_all()

        dx = abs(self.sma['GyX'] - self.readings['GyX'])
        dy = abs(self.sma['GyY'] - self.readings['GyY'])
        dz = abs(self.sma['GyZ'] - self.readings['GyZ'])
#         dx = abs(self.sma['AcX'] - self.readings['AcX'])
#         dy = abs(self.sma['AcY'] - self.readings['AcY'])
#         dz = abs(self.sma['AcZ'] - self.readings['AcZ'])
        if dx > self.threshold or dy > self.threshold or dz > self.threshold:
#             print("jolt detected")
            return True
        else:
            return False

    def det_touch(self):
        self.touched = self.det_mov()
    
    def sma_read_all(self): # takes a reading and adds it to the memory dictionary. Pops the first value in the list of values, and appends the new reading value to the list. Takes ~1.4ms
        self.readings = self.mpu.get_values()
        
        for keys in self.readings:
            self.readings[keys] = int(abs(self.readings[keys]))
            
        for keys in self.memory:
            if len(self.memory[keys]) > self.N:             # remove entry to short term sma memory
                self.memory[keys].pop(0)
            if len(self.long_mem[keys]) > self.long_len:            # remove entry to long term min-max memory    
                self.long_mem[keys].pop(0)
            self.memory[keys].append(self.readings[keys])     # add entry to short term sma memory
            self.long_mem[keys].append(self.readings[keys])     # add entry to long term min-max memory
            
            min_val = min(self.long_mem[keys])
            max_val = max(self.long_mem[keys])
            self.min_max_vals[keys] = (min_val, max_val)       # add min and max values to the min-max dictionary of keys
            
            self.sma[keys] = (sum(self.memory[keys])//len(self.memory[keys]))
            
        return self.sma
        
    def sma_read(self, key): # takes a single reading and adds it to the memory dictionary. Pops the first value in the list of values, and appends the new reading value to the list. Takes ~1,1ms
        self.readings = self.mpu.get_values()

        if len(self.memory[key]) > self.N:             # remove entry to short term sma memory
            self.memory[key].pop(0)
        if len(self.long_mem[key]) > self.long_len:        # remove entry to long term min-max memory     
                self.long_mem[key].pop(0)
        self.memory[key].append(self.readings[key])     # add entry to short term sma memory
        self.long_mem[key].append(self.readings[key])     # add entry to long term min-max memory
        
        min_val = min(self.long_mem[key])
        max_val = max(self.long_mem[key])
        self.min_max_vals[key] = (min_val, max_val)       # add min and max values to the min-max dictionary of key
        
        self.sma[key] = sum(self.memory[key])//len(self.memory[key])    # re-calculate sma for this key
#         print(self.sma)
        return self.sma[key]
    
    def min_max(self): # temporary function to determin the min and max of each key:  -32512, 32767
#         self.sma_read_all()
#         for keys in self.memory:
#             self.min_max_vals[keys] = (min(self.memory[keys]), max(self.memory[keys]))
        
        for keys in self.long_mem:
            min_val = min(self.long_mem[keys])
            max_val = max(self.long_mem[keys])
            self.min_max_vals[keys] = (min_val, max_val)
#         print("Min-Max vals of mpu; ", self.min_max_vals)

    def limit_map(self, x, in_min, in_max, out_min, out_max):
        return int(((max(in_min,min(in_max,x))) - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
    
    
    def map_accel(self, x, y): # takes a reading, adds it to the sma, and maps the 3 acceleration values to some output, after filtering
        self.sma_read_all()
        minimum = 0
        maximum = 16150

        AcX = self.limit_map(self.sma['AcX'], minimum, maximum, x, y)
        AcY = self.limit_map(self.sma['AcY'], minimum, maximum, x, y)
        AcZ = self.limit_map(self.sma['AcZ'], minimum, maximum, x, y)
        xyz = (AcX, AcY, AcZ)
#         x, y, z = AcX, AcY, AcZ
        return xyz

    # maps the gyro readings to x and y, and then outputs the sum of all values
    def map_gyro(self, x, y):
        self.sma_read_all()
#         print(self.sma)
        
        minimum = 0
        maximum = 21000
        
        GyX = self.limit_map(self.sma['AcX'], minimum, maximum, x, y)
        GyY = self.limit_map(self.sma['AcY'], minimum, maximum, x, y)
        GyZ = self.limit_map(self.sma['AcZ'], minimum, maximum, x, y)
#         gyr_tup = (GyX, GyY, GyZ)
        gyr_ave = (GyX + GyY + GyZ) // 3
#         print(gyr_tup)
        return gyr_ave
        
        
    def map_raw_gyro(self, x, y):
        self.readings = self.mpu.get_values()
        
        minimum = 400
        maximum = 16258
        
        GyX = map((max(600,min(maximum,self.readings['GyX']))), 600, maximum, x, y)
        GyY = map((max(270,min(maximum,self.readings['GyY']))), 270, maximum, x, y)
        GyZ = map((max(180,min(maximum,self.readings['GyZ']))), 180, maximum, x, y)
#         gyr_tup = (GyX, GyY, GyZ)
        gyr_sum = GyX + GyY + GyZ
#         print(gyr_tup)
        return gyr_sum
    
    async def running_mpu(self):
        while True:
            self.sma_read_all()
#             print(self.sma)
            await asyncio.sleep_ms(100)
    

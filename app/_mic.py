from machine import Pin, ADC
from math import sqrt
import uasyncio as asyncio

class Microphone:
    
    def __init__(self):
        self.mic = ADC(Pin(5))
        self.mic.atten(ADC.ATTN_11DB)
        self.alpha = 10
        self.N = 20
        self.reading = 0
        self.readings = [self.mic.read()]
        self.rms_readings = []
        self.ema = self.rms = self.sma = self.mic.read()
        self.diff = self.diff_save = self.diff_abs = 1
        self.min = 10
        self.max = 500
        self.threshold = 150
        self.square_sum = 0
        self.square_readings = []  # Add a list to store squared values
        self.rms_min = 0
        self.rms_max = 600
        self.freq = 20 # sets the asyncio sleep_ms frequency for sound
        self.rms = 0
        self.mic_readings = None 

    def rms_average(self):
#         self.exp_average()
        self.reading = self.mic.read()
        self.diff = int(self.reading - self.ema)
        self.ema = int(self.ema + (self.diff // self.alpha))
        
        
        if len(self.square_readings) > self.N:
            old_square = self.square_readings.pop(0)
            self.square_sum -= old_square  # Remove the oldest squared value from the sum
        
        new_square = self.diff * self.diff
        self.square_readings.append(new_square)  # Add the squared difference to the list
        self.square_sum += new_square # Update the sum of squared values

        square_mean = self.square_sum / self.N
        square_root = int(sqrt(square_mean))
        self.rms = square_root

        return self.rms

    def exp_average(self):
        self.reading = self.mic.read()
        
        self.diff = int(self.reading - self.ema)
        self.min = min(self.readings)
        self.max = max(self.readings)
        self.diff_abs = abs(self.diff)
        
        if len(self.readings) > self.N:
            self.readings.pop(0)

        self.readings.append(self.diff_abs)
        self.ema = int(self.ema + (self.diff // self.alpha))
        return self.diff_abs
    
    def limit_map(self, x, in_min, in_max, out_min, out_max):
        return int(((max(in_min,min(in_max,x))) - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
    
    def rms_map(self, x, y):
        mapped_rms = self.limit_map(self.rms_average(), self.rms_min, self.rms_max, x, y)
        return mapped_rms
    
    
    def simple_average(self):
        self.exp_average()
        self.sma = sum(self.readings) // self.N  # integer division
        return self.sma
        
    def det_sound(self):
        self.exp_average()
        if self.diff_abs > self.threshold:
            return True
        else:
            return False

    def read_diff(self):
        self.exp_average()
        if self.diff_abs > self.max:
            self.max = self.diff_abs
        if self.diff_abs < self.min:
            self.min = self.diff_abs
        if self.diff_abs > self.simple_average():
            self.diff_save = self.diff_abs
        return self.diff_save
    

    
    def mic_map(self, x, y):
#         print("read_diff : ", self.read_diff(), "min : ",  self.min, "max : ",  self.max,"x : ",  x,"y : ",  y)
        return map(self.read_diff(), self.min, self.max, x, y)

    def mic_map_simple(self, x, y):
        self.exp_average()
        if self.diff_abs > self.max:
            self.max = self.diff_abs
        if self.diff_abs < self.min:
            self.min = self.diff_abs
#         print("read_diff : ", self.read_diff(), "min : ",  self.min, "max : ",  self.max,"x : ",  x,"y : ",  y)
        return map(self.diff_abs, self.min, self.max, x, y)
  
    async def running_mic(self):
        while True:
            self.rms_average()
#             print(self.rms)
            await asyncio.sleep_ms(100)


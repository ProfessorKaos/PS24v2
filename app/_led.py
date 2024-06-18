import uasyncio as asyncio

class LED:
    def __init__(self):
        from neopixel import NeoPixel
        from machine import Pin
        self.np = NeoPixel(Pin(2), 50) # Set up neopixels object
        self.active_effect = None
        self.interrupt_flicker = False
        self.transition_task = None
        self.freq = 0
        self.red = 0
        self.blue = 0
        self.green = 0

    def fill(self, col=(255, 0, 0)):
        self.np.fill(col)
        self.np.write()

    def clear(self):
        self.fill((0, 0, 0))
        
    def deactivate(self):
        try:
            if self.active_effect:
                self.active_effect.cancel()
                self.active_effect = None
                self.clear()
        except Exception as e:
            print(f'It looks like there is no active effect: ', e)
    
    def activate(self, coro):
        self.deactivate()
        self.active_effect = coro
            
    # function  that toggles one of the rgb elements based on a frequency (which is a ms input relative ot the Hz)
    def led_toggle(self, period=100, duration=20):
        if ticks_ms() % period < duration:       
            return 1
        else:
            return 0     
    
    async def flick(self):
        while True:
            if self.mode:
                self.led.fill((self.red,self.blue,self.green))
                self.led.write()
                await asyncio.sleep_ms(500//self.freq)
                self.clear()
                await asyncio.sleep_ms(500//self.freq)
            await asyncio.sleep_ms(10)
    
    #take a values from HSL and over time move the current value of the led towards the new value, duration in ms
    async def smooth_led_change(self, target_hsl, duration):
        cur_rgb = self.np[0]  # Get the current color as an RGB tuple
        cur_hsl = self.rgb_to_hsl(cur_rgb)
        step_count = duration // 10  # 10 ms per step
        step_diff = [(target - current) // step_count for target, current in zip(target_hsl, cur_hsl)]

        for step in range(step_count):
            cur_hsl = [current + diff for current, diff in zip(cur_hsl, step_diff)]
            self.hsl(*cur_hsl)  # Set the color based on the HSL tuple
            await asyncio.sleep_ms(10)
        
        # Ensure the final color is accurate
        self.hsl(*target_hsl)
    
    def hsl(self, hue, sat, light):
        sat = sat * 1024 // 100
        light = light * 1024 // 100
        c = (1024 - abs(2 * light - 1024)) * sat // 1024
        x = c * (1024 - abs((hue * 1024 // 60 % 2048) - 1024)) // 1024
        m = light - c // 2
        r, g, b = 0, 0, 0
        if 0 <= hue < 60:
            r, g, b = c, x, 0
        elif 60 <= hue < 120:
            r, g, b = x, c, 0
        elif 120 <= hue < 180:
            r, g, b = 0, c, x
        elif 180 <= hue < 240:
            r, g, b = 0, x, c
        elif 240 <= hue < 300:
            r, g, b = x, 0, c
        elif 300 <= hue < 360:
            r, g, b = c, 0, x
            
        self.red = (r + m) * 255 // 1024
        self.green = (g + m) * 255 // 1024
        self.blue = (b + m) * 255 // 1024
        
#         self.fill((r,g,b))
#         self.fill((self.red,self.green,self.blue))
#         return r, g, b
#         return (r, g, b)


    def rgb_to_hsl(self, rgb):
        r, g, b = rgb
        r, g, b = r / 255, g / 255, b / 255

        max_color = max(r, g, b)
        min_color = min(r, g, b)

        light = (max_color + min_color) / 2

        if max_color == min_color:
            hue = 0
            sat = 0
        else:
            d = max_color - min_color
            sat = d / (2 - max_color - min_color)
            if max_color == r:
                hue = (g - b) / d + (6 if g < b else 0)
            elif max_color == g:
                hue = (b - r) / d + 2
            else:
                hue = (r - g) / d + 4

            hue = int(hue * 60)

        sat = int(sat * 100)
        light = int(light * 100)

        return hue, sat, light



    def flicker_tests(self):
        for i in range(12, 22):
            self.flicker(freq=i)
            self.fill((0, 0, 255))
            sleep_ms(100)
        sleep(10)

    async def flicker_direction(self, beg=27, fin=10, tdur=150):
        ss = -1
        if beg < fin:
            ss = 1
        ran = range(beg, fin, ss)
        dur_seg = (tdur * 0.3) / len(ran)
        self.interrupt_flicker = False

        for i in ran:
            if self.interrupt_flicker:
                break
            await self.flicker(freq=i, dur=dur_seg)
        
        await self.flicker(freq=fin, dur=tdur * 0.7)

    def interrupt_flicker_func(self):
        self.interrupt_flicker = True

    async def flicker_with_interrupt(self, beg, fin, tdur):
        self.interrupt_flicker = False
        await self.flicker_direction(beg, fin, tdur)

    async def flicker_rotation(self):
        print("flicker_rotation activated")
        self.interrupt_flicker = False
        while not self.interrupt_flicker:
            map_tup = mpu.map_accel(1,25)
            print("map_tup: ", map_tup)
            x_y_sum = map_tup[0]# + map_tup[1] + map_tup[2]
            print("x_y_sum: ", x_y_sum)
            await self.flicker(freq=x_y_sum, dur=1)
            await asyncio.sleep_ms(50)

# pulses the lights on a win condition
    async def flicker(self, final_color=(255, 0, 0),  freq=12, dur=30):
        def pulse_brightness(t, freq, gamma=10):
            # t is the current time
            # frequency determines how fast the LED pulses
            # gamma is the gamma correction factor
            freq /= 1000
            brightness = (sin(2 * pi * freq * t) + 1) / 2
        #     print("brightness before gamma correction: ", brightness)
            return (brightness ** gamma)
#         rgb_freq = (freq-2, freq, freq+2)

        dur *= 1000
        start_time = ticks_ms()
        bright_time = ticks_ms() - start_time
        while bright_time < dur:
            bright_time = (ticks_ms() - start_time)
#             intensity = (self.mic.rms_map(150,255))
            red = (pulse_brightness(bright_time, freq))
#             green = int(intensity*pulse_brightness(bright_time, rgb_freq[1]))
#             blue = int(intensity*pulse_brightness(bright_time, rgb_freq[2]))
            rgb = (red,0, 0)
    #         print(rgb)
            return rgb
            await asyncio.sleep_ms(10)
            
    # pulses the lights on a win condition
    async def pulse(self, final_color=(0, 255, 0), duration=5, pulses=3):
        def pulse_brightness(t, frequency=1.0, gamma=2.2):
            # t is the current time
            # frequency determines how fast the LED pulses
            # gamma is the gamma correction factor
            frequency /= 1000
            brightness = (sin(2 * pi * frequency * t) + 1) / 2
        #     print("brightness before gamma correction: ", brightness)
            return int(255 * (brightness ** gamma))
        
        freq = pulses / duration
        duration *= 1000
        start_time = ticks_ms()
        while ticks_ms() - start_time < duration:
            bright_time = (ticks_ms() - start_time)
            brightness = pulse_brightness(bright_time, freq)

            rgb = (final_color[0] * brightness // 255, final_color[1] * brightness // 255, final_color[2] * brightness // 255)
    #         print(rgb)
            self.fill(rgb)
            await asyncio.sleep_ms(20)


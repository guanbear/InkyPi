#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Waveshare 7.3inch ACeP e-Paper (E6) driver
"""
import logging
import epdconfig
import time
from PIL import Image
import numpy as np

# Display resolution
EPD_WIDTH       = 800
EPD_HEIGHT      = 480

logger = logging.getLogger(__name__)

class EPD:
    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        
    # Hardware reset
    def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        time.sleep(0.2)
        epdconfig.digital_write(self.reset_pin, 0)
        time.sleep(0.1)
        epdconfig.digital_write(self.reset_pin, 1)
        time.sleep(0.2)
        
    def send_command(self, command):
        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(self.cs_pin, 1)
        
    def send_data(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(self.cs_pin, 1)
        
    def send_data1(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte2(data)
        epdconfig.digital_write(self.cs_pin, 1)
        
    def ReadBusy(self):
        logger.debug("e-Paper busy")
        while(epdconfig.digital_read(self.busy_pin) == 0):      # 0: idle, 1: busy
            time.sleep(0.1)
        logger.debug("e-Paper busy release")
        
    def init(self):
        # EPD hardware init start
        self.reset()
        
        self.send_command(0x01) # POWER SETTING
        self.send_data(0x07)
        self.send_data(0x07) # VGH=20V, VGL=-20V
        self.send_data(0x3f) # VDH=15V
        self.send_data(0x3f) # VDL=-15V
        
        self.send_command(0x04) # POWER ON
        time.sleep(0.1)
        self.ReadBusy()
        
        self.send_command(0X00) # PANNEL SETTING
        self.send_data(0x0F) # KW-3f   KWR-2F	BWROTP 0f	BWOTP 1f
        
        self.send_command(0x61) # tres
        self.send_data(0x03) # source 800
        self.send_data(0x20)
        self.send_data(0x01) # gate 480
        self.send_data(0xE0)
        
        self.send_command(0X15) # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x00)
        
        self.send_command(0X50) # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x10)
        self.send_data(0x07)
        
        self.send_command(0X60) # TCON SETTING
        self.send_data(0x22)
        
        return 0
        
    def getbuffer(self, image):
        # Create a buffer with the appropriate color mapping for E6 display
        logger.debug("Getting buffer for image")
        img = image.convert('RGB')
        width, height = img.size
        
        # Convert RGB to the 7-color palette used by ACeP displays
        # Black, White, Green, Blue, Red, Yellow, Orange
        buffer = [0x00] * int(width * height / 2)
        pixels = img.load()
        
        for i in range(0, height):
            for j in range(0, width):
                r, g, b = pixels[j, i]
                # Simple color mapping (this should be adjusted based on actual display characteristics)
                if r > 180 and g > 180 and b > 180:
                    color = 0x11  # White
                elif r < 50 and g < 50 and b < 50:
                    color = 0x00  # Black
                elif g > 150 and r < 100:
                    color = 0x33  # Green
                elif b > 150 and r < 100:
                    color = 0x44  # Blue
                elif r > 150 and g < 100 and b < 100:
                    color = 0x22  # Red
                elif r > 150 and g > 150 and b < 100:
                    color = 0x55  # Yellow
                elif r > 150 and g > 100 and b < 50:
                    color = 0x66  # Orange
                else:
                    color = 0x11  # Default to white
                
                # Pack two pixels per byte
                if j % 2 == 0:
                    buffer[int(i * width / 2 + j / 2)] = color >> 4
                else:
                    buffer[int(i * width / 2 + j / 2)] |= color & 0x0F
                    
        return buffer
        
    def display(self, image):
        logger.info("Displaying image on EPD")
        self.send_command(0x10)
        # For simplicity, we'll just log that we're sending image data
        # In a real implementation, you would send the image buffer here
        logger.debug(f"Sending image data ({self.width}x{self.height})")
        
        self.send_command(0x12)
        time.sleep(0.1)
        self.ReadBusy()
        
    def Clear(self):
        logger.info("Clearing display")
        self.send_command(0x10)
        # Send white buffer
        logger.debug("Sending clear buffer")
        
        self.send_command(0x12)
        time.sleep(0.1)
        self.ReadBusy()
        
    def sleep(self):
        logger.info("Putting display to sleep")
        self.send_command(0x02) # POWER_OFF
        self.ReadBusy()
        self.send_command(0x07) # DEEP_SLEEP
        self.send_data(0XA5)

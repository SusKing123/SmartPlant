# Include the library files
import RPi.GPIO as GPIO
import time, os 
import requests
from time import sleep
from datetime import datetime
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import glob, time

#Thingspeak will store the timestamps of plant watering
BASE_URL = 'https://api.thingspeak.com/update.json'
KEY = 'KYS2PQAUZXEBQGRD'

# Include the motor control pins
ENA = 17
IN1 = 27
IN2 = 22
moistureSensorPin = 18
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(ENA,GPIO.OUT)
GPIO.setup(IN1,GPIO.OUT)
GPIO.setup(IN2,GPIO.OUT)

q=GPIO.PWM(ENA,10)
q.start(20)

GPIO.setup(moistureSensorPin, GPIO.IN)
# Set up display
i2c = board.I2C()
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
small_font = ImageFont.truetype('FreeSans.ttf', 22)
large_font = ImageFont.truetype('FreeSans.ttf', 28)
disp.fill(0)
disp.show() 

# Make an image to draw on in 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Display a message on 3 lines, first line big font        
def display_message(top_line, line_2):
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    draw.text((10, 0),  top_line, font=large_font, fill=255)
    draw.text((10, 30),  line_2, font=small_font, fill=255)
    disp.image(image)
    disp.show()
    
    
    
#Turns on the pump
def forward():
    GPIO.output(ENA,GPIO.HIGH)
    GPIO.output(IN1,GPIO.HIGH)
    GPIO.output(IN2,GPIO.LOW)

def backward():
    GPIO.output(ENA,GPIO.HIGH)
    GPIO.output(IN1,GPIO.LOW)
    GPIO.output(IN2,GPIO.HIGH)

def off():
    GPIO.output(ENA,GPIO.LOW)
    GPIO.output(IN1,GPIO.LOW)
    GPIO.output(IN2,GPIO.LOW)
    
    
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


#Finds temperature
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

#Formats temperature
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

def send_data(temp_f):
	    data = {'api_key' : KEY, 'field1' : temp_f}
	    response = requests.post(BASE_URL, json=data)

while True:
    # Read digital output from the sensor
    moisture_level = GPIO.input(moistureSensorPin)
    
    # Displays the current time and temperature on the LED screen
    temp_c, temp_f = read_temp()
    now = datetime.now()
    temp_message = 'Temp: {: .0f}F'.format(temp_f)  # Fix: Use temp_f here, not now
    time_message = '{:%H:%M:%S}'.format(now)
    display_message(time_message, temp_message)
    sleep(0.2)
    if moisture_level == GPIO.HIGH:  # If plant is dry
        forward()
        send_data(int(temp_f))  # send current temperature to ThingSpeak
    else:
        off()


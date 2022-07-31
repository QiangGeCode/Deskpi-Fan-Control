#!/usr/bin/env python3
#############################################################################
# Filename    : pwmControlFan-mcb04-log.py
# Description : Control the fan on the Deskpi Pro, with logs
# Author      : Deskpi Team, modified by Mike Bartlet, add fan.log by QiangGe
# modification: 31/7/2022
version = "1.5"
########################################################################
import serial
import time

cpuTemp_config = []

#Read the deskpi.conf file which contains temperature thresholds and fanspeeds. Assign default values if it doesn't exist.
try:
    with open("/etc/deskpi.conf") as deskpiConf:
        configVals = deskpiConf.read().split()
        
    for c in range(0,8,2):                                                  #Odd values are temperature thresholds. Even values are fan speed
        cpuTemp_config.append((int(configVals[c]), int(configVals[c+1])))   #Rearrange them into 4 tuples of temperature, fanspeed
        
except:
    cpuTemp_config = [('40', '50'), ('50', '75'), ('55', '100'), ('60', '100')] #Format is (temperature, fanspeed)
    
def openSerPort():
    try:
        serPort = serial.Serial("/dev/ttyUSB0", 9600, timeout=30) #Open the serial port (ttyUSB0). Deskpi uses it to communicate with the Deskpi Pro fan.
    except Exception as errDetail:
        #If there is a problem opening the serial port
        deskpiError = f"{time.asctime()} - Unable to open serial port ttyUSB0. Error:{errDetail}\n"
        deskpiLog = open("/home/pi/deskpi.log", "a") #Open the error log for append.
        deskpiLog.write(deskpiError)
        deskpiLog.close()
        serPort = "ttyUSB0 Error"
    return serPort
    
def readCPU_temp():
    with open("/sys/class/thermal/thermal_zone0/temp") as cpu_temp_file:
        cpu_temp = round(int(cpu_temp_file.read())/1000)
    
    return cpu_temp

def getTimeStr():
    # Get current time
    now = int(time.time())
    # Change to string in format:"%Y-%m-%d %H:%M:%S"
    timeArray = time.localtime(now)
    timeStr = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

    return timeStr

def writeFanLog(logStr):
    fanLog = open("/home/pi/fan.log", "a") #Open the fan log for append.
    fanLog.write(logStr)
    fanLog.flush()
    fanLog.close()

serPort = openSerPort()
 
if serPort != "ttyUSB0 Error":
    
    # Write the service start message to fan.log
    writeFanLog("--------------------------------------------------------\n")
    writeFanLog(getTimeStr() + ", Deskpi Fan service started!\n")
    writeFanLog("--------------------------------------------------------\n")
    
    # Initialize the fan status to 0(turn off)
    fanStatus = 0
    
    while True:
        if serPort.isOpen():
            cpu_temp = readCPU_temp()
            
            if cpu_temp < cpuTemp_config[0][0]:
                fan = "Off"
                writeVal = bytearray("pwm_000", "utf-8")              #Turn fan off if temp is below temp1
                if fanStatus != 0:
                    writeFanLog(getTimeStr() + ", CPU Temp is " + str(cpu_temp) + "°C, turn off fan\n")
                    fanStatus = 0
            elif cpu_temp >= cpuTemp_config[0][0] and cpu_temp < cpuTemp_config[1][0]:
                fan = f"{cpuTemp_config[0][1]}%"
                writeVal = bytearray(f"pwm_{cpuTemp_config[0][1]:0>3}", "utf-8") #If temp is at or above temp1 but below temp2, set fan speed to speed1
                if fanStatus != 1:
                    writeFanLog(getTimeStr() + ", CPU Temp is " + str(cpu_temp) + "°C, adjust fan to " + str(cpuTemp_config[0][1]) + "%\n")
                    fanStatus = 1
            elif cpu_temp >= cpuTemp_config[1][0] and cpu_temp < cpuTemp_config[2][0]:
                fan = f"{cpuTemp_config[1][1]}%"
                writeVal = bytearray(f"pwm_{cpuTemp_config[1][1]:0>3}", "utf-8") #If temp is at or above temp2 but below temp3, set fan speed to speed2
                if fanStatus != 2:
                    writeFanLog(getTimeStr() + ", CPU Temp is " + str(cpu_temp) + "°C, adjust fan to " + str(cpuTemp_config[1][1]) + "%\n")
                    fanStatus = 2
            elif cpu_temp >= cpuTemp_config[2][0] and cpu_temp < cpuTemp_config[3][0]:
                fan = f"{cpuTemp_config[2][1]}%"
                writeVal = bytearray(f"pwm_{cpuTemp_config[2][1]:0>3}", "utf-8") #If temp is at or above temp3 but below temp4, set fan speed to speed3
                if fanStatus != 3:
                    writeFanLog(getTimeStr() + ", CPU Temp is " + str(cpu_temp) + "°C, adjust fan to " + str(cpuTemp_config[2][1]) + "%\n")
                    fanStatus = 3
            elif cpu_temp >= cpuTemp_config[3][0]:
                fan = f"{cpuTemp_config[3][1]}%"
                writeVal = bytearray(f"pwm_{cpuTemp_config[3][1]:0>3}", "utf-8") #If temp is at or above temp4, set fan speed to speed4
                if fanStatus != 4:
                    writeFanLog(getTimeStr() + ", CPU Temp is " + str(cpu_temp) + "°C, adjust fan to " + str(cpuTemp_config[3][1]) + "%\n")
                    fanStatus = 4
            
            serPort.write(writeVal)
        else:
            serPort = openSerPort()
            
        time.sleep(5)

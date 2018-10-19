import sys
import traceback
from datetime import datetime
import u3

MAX_REQUESTS = None
SCAN_FREQUENCY = 5000 # SCAN_FREQUENCY is the scan frequency of stream mode in Hz
d = None
d = u3.U3()

d.configU3() # To learn the if the U3 is an HV
d.getCalibrationData() # For applying the proper calibration to readings.
d.configIO(FIOAnalog=3) # Set the FIO0 and FIO1 to Analog (d3 = b00000011)

print("Configuring U3 stream")
d.streamConfig(NumChannels=2, PChannels=[0, 1], NChannels=[31, 31], Resolution=3, ScanFrequency=SCAN_FREQUENCY)
d.packetsPerRequest = 6 #Higher number = slower speed, but most likely higher accuracy. Default is 48

f = open("Project_Output_Readings.txt","w+")
g = open("Project_Output_Real_Hz.txt","w+")
#MAX_REQUESTS = int(input ("How many Values do you want to record? "))
#^ can comment uncomment this line to add a max request call to the program
#^ Along with the first comments under the for loop
input("Press Enter to begin stream, end with Ctrl + C")

if d is None:
    print("""Configure a device first. Please open streamTest.py in a text editor and uncomment the lines for your device. Exiting...""")
    sys.exit(0)

try:
    print("Start stream")
    d.streamStart()
    start = datetime.now()
    print("Start time is %s" % start)

    missed = 0
    dataCount = 0
    packetCount = 0

    for r in d.streamData():
        if r is not None:
            # Our stop condition if using MAX_REQUESTS
            #if dataCount >= MAX_REQUESTS:
            #    break

            if r["errors"] != 0:
                print("Errors counted: %s ; %s" % (r["errors"], datetime.now()))

            if r["numPackets"] != d.packetsPerRequest:
                print("----- UNDERFLOW : %s ; %s" %
                      (r["numPackets"], datetime.now()))

            if r["missed"] != 0:
                missed += r['missed']
                print("+++ Missed %s" % r["missed"])

            # Comment out these prints and do something with r
            print("Average of %s AIN0, %s AIN1 readings: %s, %s" %
                  (len(r["AIN0"]), len(r["AIN1"]), sum(r["AIN0"])/len(r["AIN0"]), sum(r["AIN1"])/len(r["AIN1"])))
            f.write(str(sum(r["AIN0"])/len(r["AIN0"])))
            f.write("\n")
            dataCount += 1
            packetCount += r['numPackets']

        else:
            # Got no data back from our read.
            # This only happens if your stream isn't faster than the USB read
            # timeout, ~1 sec.
            print("No data ; %s" % datetime.now())
except:
    print("".join(i for i in traceback.format_exc()))
finally:
    stop = datetime.now()
    d.streamStop()
    print("Stream stopped.\n")
    d.close()

    sampleTotal = packetCount * d.streamSamplesPerPacket

    scanTotal = sampleTotal / 2  # sampleTotal / NumChannels
    print("%s requests with %s packets per request with %s samples per packet = %s samples total." %
          (dataCount, (float(packetCount)/dataCount), d.streamSamplesPerPacket, sampleTotal))
    print("%s samples were lost due to errors." % missed)
    sampleTotal -= missed
    print("Adjusted number of samples = %s" % sampleTotal)

    runTime = (stop-start).seconds + float((stop-start).microseconds)/1000000
    print("The experiment took %s seconds." % runTime)
    print("Actual Scan Rate = %s Hz" % SCAN_FREQUENCY)
    print("Timed Scan Rate = %s scans / %s seconds = %s Hz" %
          (scanTotal, runTime, float(scanTotal)/runTime))
    print("Timed Sample Rate = %s samples / %s seconds = %s Hz" %
          (sampleTotal, runTime, float(sampleTotal)/runTime))
    f.close()
        
    g.write(str((float(sampleTotal)/runTime)/2))
    g.close()
    input("Press Enter to continue...")

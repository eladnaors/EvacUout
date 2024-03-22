import graphCalculation
from EvSensor import EvSensor
import RPi.GPIO as GPIO
import time
from datetime import datetime
import threading
import dbFirebase

db = dbFirebase.firebaseDB()


class EvFireSensorRasbery(EvSensor):
    _color = ""
    _lineWidth = 4
    _fireFound = False
    _blinkTime = datetime.fromtimestamp(time.time())

    def __init__(self,rasberyNumber, channel, sensorNumber, insideRasbery):
        EvSensor.__init__(self, "fire", rasberyNumber, channel, sensorNumber, insideRasbery)
        self.edgeNumber = graphCalculation.getedgefrom2vertex(sensorNumber, sensorNumber + 4)
        '''Setting sensor GPIO mode BSM and GPIO IN mode'''
        if insideRasbery==True:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(channel, GPIO.IN)

    def save2db(self):
        if (self._insideRasbery):
            print ("saving sensor with edge = " + str(self.edgeNumber) + " port = " + str(self.sensorNumber) +"id = ", self.sensorID)
            self._timestamp = datetime.fromtimestamp(time.time())
            db.collection(u'fireSensor').document(str(self.sensorID)).set(self.tojson)

    def startBlinking(self):
        self._color = "red"
        self._lineWidth = 8
        time.sleep(3)
        self._color = "yellow"
        self._lineWidth = 4
        time.sleep(6)
        self._color = "red"
        self._lineWidth = 8
        self._sensorDirty = False

    '''Function responsible for blink sensor on the screen (black red -> yellow ->red)
        We have 4 modes
        First mode -> called from start until 1 second - sensor found fire 
                        and it became red first time (for 1 second)
        Second mode -> called from 1 -> 2 second  called from 1 to 2 second -
                        sensor blinks and shows yellow color
        Third mode -> called after more than 2 seconds and sensor became not dirty
                        - sensor stop blink and shows red color again
        No Dirty mode -> sensor is not drawn red (only black) - no fire

        Blink is called every time and we check time in seconds
        if the time passes'''

    def change_blink_color(self):
        if self._sensorDirty == False:
            return
        dt2 = datetime.fromtimestamp(time.time())
        delta = dt2 - self._blinkTime
        difference = delta.total_seconds()
        if (difference < 1):
            self._color = "red"
            self._lineWidth = 8
        elif (difference >= 1 and difference <= 2):
            self._color = "yellow"
            self._lineWidth = 4
        else:
            self._color = "red"
            self._lineWidth = 8
            self._sensorDirty = False

    @property
    def color(self):
        return self._color

    @property
    def lineWidth(self):
        return self._lineWidth

    '''callback function been fire every time the sensor detect fire
    and the sensor detect no fire on the given channel
    GPIO input -> checks GPIO input to check 
    '' the fire detection on the edge'''
    def my_callback(self,channel):
            if GPIO.input(channel):     # if port 25 == 1
                 print ("Fire detected on edge = " + str(self.edgeNumber) + " port = " + str(self.sensorNumber) + " id = " + self.sensorID)
                 self.whenFire(channel)
                 s = threading.Thread(target=self.whenNoFire, args=())
                 s.start()

    '''fire Sensor - creates callback for function "self.my_callback" 
        this function,the sensor calls 
        when sensor detect that the fire is On or OFF (every state change)'''
    def findFire(self):
        print("wait for fire")
        GPIO.add_event_detect(self._channel, GPIO.BOTH )
        GPIO.add_event_callback(self._channel, self.my_callback)

    @property
    def callOnFireS(self):
        return self.callOnFire

    # a setter function
    @callOnFireS.setter
    def callOnFireS(self, a):
        self.callOnFire = a

    def whenNoFire(self):
        time.sleep(30)
        self.fireFound = False
        self._sensorDirty = False
        self.save2db()

    def whenFire(self, channel):
        self.fireFound = True
        self._sensorDirty = True
        self.save2db()
        # self.callOnFireS()

    @property
    def fireFound(self):
        return self._fireFound

    # a setter function
    @fireFound.setter
    def fireFound(self, a):
        self._fireFound = a

    @property
    def idx1Graph(self):
        return self._sensorNumber

    @property
    def idx2Graph(self):
        return self._sensorNumber + 4

    @property
    def fireMessage(self):
        return str(self.idx1Graph) + "--" + str(self.idx2Graph) + " (edge " + str(self.edgeNumber) + ")"

    ''' Function tojson and fromjson used to convert object 
        to string json format and from string json format'''
    @property
    def tojson(self):

        tojson = {
            u'rasberyId' : self.sensorID,
            u'rasberyNumber' : self._rasberyNumber ,
            u'channel': str(self._channel),
            u'sensorNumber': str(self._sensorNumber),
            u'sensorType': str(self._sensorType),
            u'fireFound': str(self._fireFound),
            u'edgeNumber': str(self.edgeNumber),
            u'sensorDirty': str(self._sensorDirty),
            u'timeStamp':str(self._timestamp)
        }

        return tojson

    @tojson.setter
    def fromjson(self, json):

        self._channel = int(json['channel'])
        self._rasberyNumber =json['rasberyNumber']
        self._sensorNumber = int(json['sensorNumber'])
        self._sensorType = json['sensorType']
        self._timestamp= datetime.strptime(json['timeStamp'],'%Y-%m-%d %H:%M:%S.%f')
        newFireFound = json['fireFound'] == "True"
        newDirty = json['sensorDirty'] == "True"
        if (newFireFound and newDirty):
            self._color = "red"
            self._lineWidth = 8
            self._blinkTime = datetime.fromtimestamp(time.time())

        self._fireFound = newFireFound

        self.edgeNumber = int(json['edgeNumber'])

        self._sensorDirty = newDirty




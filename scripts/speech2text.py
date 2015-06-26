#!/usr/bin/env python
import json

__author__ = 'daniel'

import roslib
roslib.load_manifest('speech2text')

import rospy
from std_msgs.msg import String
from std_msgs.msg import Float32

from os import environ as env, remove, system
import subprocess
import tempfile
import json


if __name__ == '__main__':
    rospy.init_node('speech2text')
    text = rospy.Publisher("~speech", String, queue_size=1)
    confidence = rospy.Publisher("~confidence", Float32, queue_size=1)
    rate = rospy.Rate(10)
    device = rospy.get_param("~device", "alsa default")
    silence = rospy.get_param("~silence", "0 1 00:00:01.0 8%")
    sox = rospy.get_param("~sox_command", 'sox -b 32 -e floating-point -r 44100 '
                                                     '-t {device} {file} vad silence {silence}')
    get = rospy.get_param("~google_command", "wget --post-file='{file}' "
                                             "--timeout=10 "
                                             "--header='Content-Type: audio/x-flac; rate=44100;' -O - "
                                             "'https://www.google.com/speech-api/v2/recognize?output=json&lang=en-us&key={key}'")
    key = rospy.get_param("~key", "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw")

    while not rospy.is_shutdown():
        rec = tempfile.NamedTemporaryFile('w+b', suffix='.flac')
        if subprocess.check_call(sox.format(device=device, file=rec.name, silence=silence), shell=True):
            system.exit(1)
        try:
            wget_output =  subprocess.check_output(get.format(file=rec.name, key=key), shell=True)
        except:
            rec.close()
            continue
        rec.close()
        try:
            parsed = json.loads(wget_output.split('\n')[-2])
            #print parsed
            first_res = parsed['result'][0]['alternative'][0]
            if "confidence" in first_res:
                confidence.publish(float(first_res["confidence"]))
            else:
                confidence.publish(-1.0)
            text.publish(first_res['transcript'])
        except:
            pass # no result
        rate.sleep()

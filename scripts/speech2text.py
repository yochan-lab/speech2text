#!/usr/bin/env python
import json

__author__ = 'daniel'

import roslib
roslib.load_manifest('speech2text')

import rospy
from std_msgs.msg import String
from std_msgs.msg import Float32
import std_srvs.srv

from os import environ as env, remove, system
import subprocess
import tempfile
import json

rate = None


def work(run_once=True):
    rospy.loginfo("Running. Singleton: %s" % str(run_once))
    tries = 1
    while not rospy.is_shutdown() and tries < 4:
        rec = tempfile.NamedTemporaryFile('w+b', suffix='.flac')
        rospy.loginfo('made temp file')
        rospy.loginfo('starting to listen')
        if subprocess.check_call(sox.format(device=device, file=rec.name, silence=silence), shell=True):
            system.exit(1)
        rospy.loginfo('finished listen')
        rospy.loginfo('starting web')
        try:
            wget_output =  subprocess.check_output(get.format(file=rec.name, key=key), shell=True)
        except:
	    rospy.loginfo('bad web stuff')
            rec.close()
            continue
        rospy.loginfo('finished web')
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
            if run_once:
               return std_srvs.srv.TriggerResponse(True, first_res['transcript'])
        except:
            pass
             # no result
        tries += 1
        rospy.loginfo("Trying the recognizer again")
        rate.sleep()
    return std_srvs.srv.TriggerResponse(False, "No result")


def work_srv(*args, **kwargs):
    return work(True)


if __name__ == '__main__':
    rospy.init_node('speech2text')
    rate = rospy.Rate(10)
    text = rospy.Publisher("~speech", String, queue_size=1)
    confidence = rospy.Publisher("~confidence", Float32, queue_size=1)
    device = rospy.get_param("~device", "alsa hw:1")
    silence = rospy.get_param("~silence", "0 1 00:00:01.0 8%")
    sox = rospy.get_param("~sox_command", 'sox -b 32 -e floating-point -r 44100 '
                                                     '-t {device} {file} vad silence {silence}')
    get = rospy.get_param("~google_command", "wget --post-file='{file}' "
                                             "--timeout=10 "
                                             "-t 1 "
                                             "--header='Content-Type: audio/x-flac; rate=44100;' -O - "
                                             "'https://www.google.com/speech-api/v2/recognize?output=json&lang=en-us&key={key}'")
    key = rospy.get_param("~key", "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw")
    listen_srv = rospy.Service("~nl_listen", std_srvs.srv.Trigger, work_srv)
    rospy.spin()

# -*- coding: utf-8 -*-
"""
@author: Marcos F. Caetano (mfcaetano@unb.br) 03/11/2020

@description: PyDash Project

An implementation example of a FIXED R2A Algorithm.

the quality list is obtained with the parameter of handle_xml_response() method and the choice
is made inside of handle_segment_size_request(), before sending the message down.

In this algorithm the quality choice is always the same.
"""

from player.parser import *
from r2a.ir2a import IR2A
from math import sqrt
import time
from statistics import mean
import numpy
import json

class R2AFDASH(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.timeToDownload = 0
        self.segmentSize = 0
        self.riList = []
        self.qi = []

        f = open('dash_client.json')
        self.stepSize = json.load(f)['playbak_step']       
        self.maxBufferSize = self.whiteboard.get_max_buffer_size()
        self.d = 21  # tal

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        pbs = self.whiteboard.get_playback_buffer_size()
        if (len(pbs) == 0):
            bufferSize = 0
        else:
            bufferSize = pbs[-1][1]

        if (self.segmentSize != 0):
          
          ri = (self.segmentSize * self.stepSize) / self.timeToDownload
          self.riList.insert(0, (ri, time.perf_counter(), bufferSize))
          
          currentTime = time.perf_counter()
          while (currentTime - self.riList[-1][1] > self.d):
            self.riList.pop(-1)

          rd = mean(x[0] for x in self.riList)

          if (len(self.riList) < 2):
            diff = 0
          else:
            diff = 1 / (self.riList[0][1] - self.riList[1][1])

          print(diff)
            
          short = 0
          close = 0
          big = 0
          fall = 0
          steady = 0
          rise = 0

          T = self.maxBufferSize * 0.2
          if (bufferSize < (2 * T)/3):
            short = 1

          elif (bufferSize < T):
            short = 1 - (bufferSize - 2 * T / 3) / (T/3)
            close = (bufferSize - 2 * T / 3) / (T/3) 
          
          elif (bufferSize < 4*T):
            close = 1 - (bufferSize - T) / (T*3)
            big = (bufferSize - T) / (T*3)

          else:
            big = 1

          if (diff < 0.85):
            fall = 1
          
          elif (diff < 1.5):
            fall = 1 - (diff - 0.75) / (1.5 - 0.75)
            steady = (diff - 0.75) / (1.5 - 0.75)
          
          elif (diff < 4):
            steady = 1 - (diff - 1.5) / (4 - 1.5)
            rise = (diff - 1.5) / (4 - 1.5)

          else:
            rise = 1

          r1 = min(short, fall)
          r2 = min(close, fall)
          r3 = min(big, fall)
          r4 = min(short, steady)
          r5 = min(close, steady)
          r6 = min(big, steady)
          r7 = min(short, rise)
          r8 = min(close, rise)
          r9 = min(big, rise)

          r = sqrt(pow(r1, 2))
          sr = sqrt(pow(r2, 2) + pow(r4, 2))
          nc = sqrt(pow(r3, 2) + pow(r5, 2) + pow(r7, 2))
          si = sqrt(pow(r6, 2) + pow(r8, 2))
          i = sqrt(pow(r9, 2))

          f = ((0.25 * r) + (0.5 * sr) + nc + (1.5 * si) + (2 * i)) / (r + sr + nc + si + i)

          nxtQuality = f * rd

          chosenQuality = self.qi[0]
          for q in self.qi:
            if (nxtQuality > q):
              chosenQuality = q
            else:
              break

        else:
          chosenQuality = self.qi[0]


        self.segmentSize = chosenQuality
        msg.add_quality_id(chosenQuality)

        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.timeToDownload = time.perf_counter() - self.request_time
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

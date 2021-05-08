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
        self.lastQuality = 0
        self.segmentSize = 0
        self.riList = []
        self.qi = []

        f = open('dash_client.json')
        self.stepSize = json.load(f)['playbak_step']       
        self.maxBufferSize = self.whiteboard.get_max_buffer_size()
        self.d = 30  # tal

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
            
          short = 0
          close = 0
          big = 0

          T = self.maxBufferSize * 0.45
          if (bufferSize < T/4):
            short = 1

          elif (bufferSize < T):
            short = 1 - (bufferSize - T/4)/(T - (T/4))
            close = (bufferSize - T/4)/(T - (T/4))
          
          elif (bufferSize < 2*T):
            close = 1 - (bufferSize - T)/(2*T - T)
            big = (bufferSize - T)/(2*T - T)

          else:
            big = 1

          f = ((0.25 * short) + (0.5 * close) + big) / (short + close + big)

          nxtQuality = f * rd

          chosenQuality = self.qi[0]
          for q in self.qi:
            if (nxtQuality > q):
              chosenQuality = q
            else:
              break

        else:
          chosenQuality = self.qi[0]

        self.lastQuality = chosenQuality
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

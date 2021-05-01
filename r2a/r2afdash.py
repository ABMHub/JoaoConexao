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
        self.sizeList = []
        self.riList = []
        self.parsed_mpd = ''
        self.qi = []

        self.f = open('dash_client.json')
        self.config = json.load(self.f)
        self.maxBufferSize = self.config['max_buffer_size']
        self.stepSize = self.config['playbak_step']       
        self.d = 10  # tal

        self.n1 = 0.25
        self.n2 = 0.5
        self.z  = 1
        self.t1 = 1.5
        self.t2 = 2

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        t = time.perf_counter() - self.request_time
        # self.throughputs.append(msg.get_bit_length() / t)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()

        pbs = self.whiteboard.get_playback_buffer_size()
        if (len(pbs) == 0):
            bufferSize = 0
        else:
            bufferSize = pbs[-1][1]

        if (len(self.sizeList) != 0):
          # limita a sizeList para tamanho 10
          while (len(self.sizeList) > 10):
            self.sizeList.pop(-1)
          
          bi = self.sizeList[0]
          ri = (bi * self.stepSize) / self.timeToDownload
          
          self.riList.insert(0, (ri, time.perf_counter(), bufferSize))
          
          currentTime = time.perf_counter()
          while (currentTime - self.riList[-1][1] > self.d):
            self.riList.pop(-1)

          rd = mean(x[0] for x in self.riList)

          if (len(self.riList) < 3):
            di = 0
          else:
            di = self.riList[1][2] - self.riList[2][2]

          fall = 0
          short = 0
          steady = 0
          close = 0
          rise = 0
          fast = 0

          T = self.maxBufferSize * 0.25
          if (bufferSize < (2 * T)/3):
            short = 1

          elif (bufferSize < T):
            short = 1 - 1/(T/3) * (bufferSize - 2 * T / 3)
            close = 1/(T/3) * (bufferSize - 2 * T / 3)
          
          elif (bufferSize < 4*T):
            close = 1 - 1/(T*3) * (bufferSize - T)
            fast = 1/(T*3) * (bufferSize - T)

          else:
            fast = 1

          if (di < -2 * T / 3):
            fall = 1
          
          elif (di < 0):
            fall = 1 - 1 / (2 * T / 3) * (di + 2 * T / 3)
            steady = 1 / (2 * T / 3) * (di + 2 * T / 3)
          
          elif (di < 4 * T):
            steady = 1 - 1 / (4 * T) * di
            rise = 1 / (4 * T) * di

          else:
            rise = 1

          r1 = min(short, fall)
          r2 = min(close, fall)
          r3 = min(fast, fall)
          r4 = min(short, steady)
          r5 = min(close, steady)
          r6 = min(fast, steady)
          r7 = min(short, rise)
          r8 = min(close, rise)
          r9 = min(fast, rise)

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

        self.sizeList.insert(0, chosenQuality)
        msg.add_quality_id(chosenQuality)

        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.timeToDownload = time.perf_counter() - self.request_time
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

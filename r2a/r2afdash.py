# -*- coding: utf-8 -*-
"""
Redes de Computadores - Turma A - 2020/2
Grupo: João Conexão

Lucas de Almeida Bandeira Macedo - 190047089
João Víctor Siqueira De Araujo - 190031026
João Pedro Felix de Almeida - 190015292
"""

from player.parser import *
from r2a.ir2a import IR2A
import time
from statistics import mean
import numpy

class R2AFDASH(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.timeToDownload = 0
        self.segmentSize = 0
        self.riList = []
        self.qi = []
 
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
          
          ri = self.segmentSize / self.timeToDownload
          self.riList.insert(0, (ri, time.perf_counter()))
          
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

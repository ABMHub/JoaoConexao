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
import time
from statistics import mean
import numpy


class R2ABola(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.throughputs = []
        self.parsed_mpd = ''
        self.qi = []

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        t = time.perf_counter() - self.request_time
        self.throughputs.append(msg.get_bit_length() / t)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()

        pbs = self.whiteboard.get_playback_buffer_size()
        if (len(pbs) == 0):
            bufferSize = 0
        else:
            bufferSize = pbs[-1][1]

        fator = 3
        control = 59/(numpy.log(self.qi[19] / self.qi[0]) + fator)
        maior = 0
        indiceMaior = 0

        for i in range (20):
            utility = numpy.log(self.qi[i] / self.qi[0])
            maiorCandidato = (((control*utility) + (control*fator)) - bufferSize) / self.qi[i]
            if (maiorCandidato > maior):
                maior = maiorCandidato
                indiceMaior = i

        msg.add_quality_id(self.qi[indiceMaior])
        self.send_down(msg)

        # utility = numpy.log(self.qi[19] / self.qi[0])
        # control = 59/(utility + 5) # v
        # # control * utility + control * 5 - 
        # bufferSize = 0
        # pbs = self.whiteboard.get_playback_buffer_size()
        # if (len(pbs) == 0):
        #     bufferSize = 0
        # else:
        #     bufferSize = self.whiteboard.get_playback_buffer_size()[-1][1]

        # print(bufferSize)

        # avg = mean(self.throughputs) / 2

        # selected_qi = self.qi[0]
        # for i in self.qi:
        #     if avg > i:
        #         selected_qi = i

        # # define a qualidade selecionada, provavelmente não iremos mudar
        # msg.add_quality_id(selected_qi)
        # self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

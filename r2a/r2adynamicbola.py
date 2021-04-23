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
import json
import time
from statistics import mean
import numpy
import os


class R2ADynamicBola(IR2A):

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

        if (bufferSize < 10):
            print(self.throughputs)

        f = open('dash_client.json')
        maxBufferSize = json.load(f)['max_buffer_size']

        # calculo vazao
        while (len(self.throughputs) > 5):
          self.throughputs.pop(0)

        pesos = []
        for i in range(len(self.throughputs)):
          pesos.append(i+1)

        avg = numpy.average(self.throughputs, weights = pesos)

        qi_mean = self.qi[0]
        for i in range(len(self.qi)):
            if avg > self.qi[i]:
                qi_mean = i

        # calculo bola
        fator = 5
        control = maxBufferSize/(numpy.log(self.qi[19] / self.qi[0]) + fator)
        maior = 0
        qi_bola = 0

        for i in range (20):
            utility = numpy.log(self.qi[i] / self.qi[0])
            maiorCandidato = (((control*utility) + (control*fator)) - bufferSize) / self.qi[i]
            if (maiorCandidato > maior):
                maior = maiorCandidato
                qi_bola = i

        chosen_qi = 0
        if (bufferSize > maxBufferSize * (1/3) and qi_bola < qi_mean):
          chosen_qi = self.qi[qi_mean]
        
        else:
          chosen_qi = self.qi[qi_bola]

        msg.add_quality_id(chosen_qi)
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
        t = time.perf_counter() - self.request_time
        self.throughputs.append(msg.get_bit_length() / t)
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

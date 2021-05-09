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

class R2ABola(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.parsed_mpd = ''
        self.qi = []
        self.maxBufferSize = self.whiteboard.get_max_buffer_size()

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

        fator = 5
        control = self.maxBufferSize/(numpy.log(self.qi[19] / self.qi[0]) + fator)
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

    def handle_segment_size_response(self, msg):
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass

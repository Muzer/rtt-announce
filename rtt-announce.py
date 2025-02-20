#!/usr/bin/env python3

import collections
import datetime
import json
import logging
import os
import pprint
import pyaudio
import requests
import soundfile
import sys
import time
import tomllib
import traceback
import typing

logger = logging.getLogger(__name__)

toc_map = {
    "Male1": {
        "AW": ("arriva trains wales", True), # TODO
        "CC": ("c2c", True),
        "CH": ("chiltern railways", True),
        # CS TODO
        "EM": ("east midlands", True), # TODO
        "ES": ("eurostar", True),
        "GC": ("grand central", True),
        "GN": ("great northern", True),
        "GR": ("gner", True), # TODO
        "GW": ("great western", True), # TODO
        "GX": ("gatwick express", True),
        "HT": ("hull trains", True),
        "HX": ("heathrow express", True),
        "IL": ("island line", True),
        # LD TODO
        "LE": ("anglia railways", True), # TODO
        "LM": ("london midland", True), # TODO
        "LO": ("london overground", True),
        # LS TODO
        "LT": ("london underground", True),
        "ME": ("merseyside electrics", True), # TODO, maybe, though this is actually fairly similar to how Atos Anne announces it
        # MV TODO
        "NT": ("northern rail", True), # TODO
        # NY TODO
        "SE": ("southeastern", True),
        # SJ TODO
        "SN": ("southern", True),
        # SO TODO
        "SP": ("the swanage railway", True), # TODO
        "SR": ("scotrail", True),
        "SW": ("south west trains", True), # TODO
        "TL": ("thameslink", True),
        "TP": ("first transpennine express", True), # TODO
        "TW": ("tyne and wear metro", True),
        # TY TODO
        "VT": ("virgin trains", True), # TODO
        "WR": ("west coast railway company", True),
        "XC": ("crosscountry", True),
        "XR": ("elizabeth line", True), # TODO improve
        # YG TODO
    },
    "Female1": {
        "AW": ("arriva trains wales", True), # TODO
        "CC": ("c2c", True),
        "CH": ("chiltern railways", True),
        # CS TODO
        "EM": ("east midlands trains", True), # TODO
        "ES": ("eurostar", False),
        "GC": ("grand central", True),
        "GN": ("great northern", True),
        "GR": ("gner", True), # TODO
        "GW": ("great western", True), # TODO
        "GX": ("gatwick express", True),
        "HT": ("hull trains", True),
        "HX": ("heathrow express", False),
        "IL": ("island line", False),
        # LD TODO
        "LE": ("anglia railways", True), # TODO
        "LM": ("london midland", True), # TODO
        "LO": ("london overground", True),
        # LS TODO
        "LT": ("london underground", True),
        "ME": ("merseyside electrics", False), # TODO, maybe, though this is actually fairly similar to how Atos Anne announces it
        # MV TODO
        "NT": ("northern rail", True), # TODO
        # NY TODO
        "SE": ("southeastern", True),
        # SJ TODO
        "SN": ("southern", True),
        # SO TODO
        "SP": ("the swanage railway", True), # TODO
        "SR": ("scotrail", True),
        "SW": ("south west trains", True), # TODO
        "TL": ("thameslink", True),
        "TP": ("arriva transpennine", False), # TODO
        "TW": ("tyne and wear metro", True),
        # TY TODO
        "VT": ("virgin trains", True), # TODO
        "WR": ("west coast railway company", False),
        "XC": ("crosscountry", True),
        # XR TODO
        # YG TODO
    },
    "Female2": {
        # AW TODO
        # CC TODO
        # CH TODO
        # CS TODO
        "EM": ("east midlands", True), # TODO
        # ES TODO
        "GC": ("grand central", True),
        # GN TODO
        "GR": ("gner", True), # TODO
        "GW": ("first great western", True), # TODO
        # GX TODO
        # HT TODO
        # HX TODO
        # IL TODO
        # LD TODO
        # LE TODO
        # LM TODO
        "LO": ("london overground", True),
        # LS TODO
        # LT TODO
        # ME TODO
        # MV TODO
        # NT TODO
        # NY TODO
        "SE": ("southeastern", True),
        # SJ TODO
        "SN": ("southern", True),
        # SO TODO
        # SP TODO
        "SR": ("scotrail", True),
        "SW": ("south west trains", True), # TODO
        # TL TODO
        # TP TODO
        # TW TODO
        # TY TODO
        "VT": ("virgin trains", False), # TODO
        # WR TODO
        # XC TODO
        # XR TODO
        # YG TODO
    }
}

station_map = {
    "Male1": {
        "CDN": "CDN - Smitham",
        "SDC": "SDC - Shoreditch",
        "BIT": "BIT - Bicester Town",
        "BUI": "BUI - Strathclyde",
        "CLT": "CLT - Clacton",
        "DFE": "DFE - Dunfermline",
        "GSC": "GSC - Lambhill",
        #"HXX": "HXX - Heathrow Airport", # Now have specific one for T2,3
        "LUA": "LUA - London Luton Airport",
        "SOF": "SOF - Woodham Ferrers",
        "WAV": "WAV - Wavertree",
        "WCF": "WCF - on sea",
        "COE": "CME",
    },
    "Female1": {
        "CDN": "CDN - Smitham",
        "SDC": "SDC - Shoreditch",
        "BIT": "BIT - Bicester Town",
        "CLT": "CLT - Clacton",
        "DFE": "DFE - Dunfermline",
        "GSC": "GSC - Lambhill",
        "HXX": "HXX - Heathrow Airport",
        "LUA": "LUA - London Luton Airport",
        "SOF": "SOF - Woodham Ferrers",
        "WCF": "WCF - on sea",
        "COE": "CME",
    },
    "Female2": {
        "CDB": "CDB - Cardiff Bute Road",
        "CHX": "CHX - Charing Cross",
        "DFE": "DFE - Dunfermline Town",
        "EDB": "EDB - Edinburgh Waverley",
        "GGJ": "GGJ - Georgemas",
        "MOG": "MOG - London Moorgate"
    }
}

cancel_map = {
    "Male1": {
        # AA acceptance into off-NR terminal or yard
        # AC train prep/TOPS
        "AD": ["a staff shortage"],
        "AE": ["congestion"],
        "AG": ["an incident on the line"],
        "AH": ["a fault on trackside equipment"],
        # AJ awaiting customer's traffic/doc
        "AK": ["an incident on the line"],
        "AX": ["a fault on trackside equipment"],
        "AZ": ["a currently unidentified reason which is under investigation"],
        # DA non-tech fleet
        # DB Train operations
        "DC": ["crewing difficulties"],
        # DD tech fleet
        # DE station
        "DF": ["an external cause beyond our control"],
        # DG terminals or yards
        "DH": ["slippery rail conditions"],
        "FA": ["an incident on the line"],
        "FC": ["an incident on the line"],
        "FE": ["awaiting a member of the train crew"],
        "FF": ["crewing difficulties"],
        # FG professional driving policy
        # FH FOC planning issue non-crewing
        "FI": ["signalling difficulties"],
        # FJ FOC control decision
        "FK": [
            "a slow-running preceding freight train running behind schedule"
        ],
        # FL FOC request
        "FM": ["a fault on the train"],
        "FO": ["a currently unidentified reason which is under investigation"],
        "FS": ["signalling difficulties"],
        "FW": ["a currently unidentified reason which is under investigation"],
        "FX": [
            "a slow-running preceding freight train running behind schedule"
        ],
        "FZ": ["a currently unidentified reason which is under investigation"],
        "IA": ["a signal failure"],
        "IB": ["a points failure"],
        "IC": ["a track circuit failure"],
        "ID": ["a fault on a level crossing"],
        "IE": ["a power supply problem"],
        "IF": ["a failure of signalling equipment"],
        "IG": ["a signalling apparatus failure"],
        "IH": ["a power supply problem"],
        "II": ["a technical fault to lineside equipment"],
        "IJ": ["a fault on trackside equipment"],
        "IK": ["a technical problem"],
        "IL": ["a signalling apparatus failure"],
        "IM": ["a technical fault to lineside equipment"],
        "IN": ["a technical fault to lineside equipment"],
        "IP": [
            "a points failure",
            "m/which has been caused by.wav",
            "snow",
            "m/and.wav",
            "a fault on trackside equipment"
        ],
        "IQ": ["a fault on trackside equipment"],
        "IR": ["a broken rail"],
        "IS": ["damaged track"],
        "IT": ["a currently unidentified reason which is under investigation"],
        "IV": ["a landslip"],
        "IW": ["adverse weather conditions"],
        "I0": ["a temporary fault with the signalling equipment"],
        "I1": [
            "overhead electric line problems",
            "m/or-2.wav",
            "third rail problems"
        ],
        "I2": ["an electrical power supply problem"],
        "I4": ["an electrical power supply problem"],
        "I5": ["overrunning engineering work"],
        "I6": ["overrunning engineering work"],
        "I7": ["overrunning engineering work"],
        "I8": ["animals on the railway line"],
        "I9": ["a lineside fire"],
        "JA": ["a temporary speed restriction because of track repairs"],
        # not sure how to end this so just add a random today
        "JB": ["a temporary speed restriction", "e/today.wav"],
        "JD": ["suspected damage to a railway bridge"],
        "JF": ["a fault on trackside equipment"],
        "JG": ["a temporary speed restriction because of track repairs"],
        "JH": ["the extreme heat"],
        "JK": ["flooding"],
        "JL": ["an incident on the line"],
        "JP": ["a fallen tree on the line"],
        "JR": ["signalling difficulties"],
        "JS": ["a temporary speed restriction because of track repairs"],
        "JT": [
            "a points failure",
            "m/which has been caused by.wav",
            "snow",
        ],
        "JX": ["objects on the line"],
        "J0": ["a technical problem"],
        "J2": ["a technical problem"],
        "J3": ["a temporary fault with the signalling equipment"],
        "J4": ["reports of a blockage on the line"],
        "J5": ["reports of a blockage on the line"],
        "J6": ["a lightning strike"],
        "J7": ["a temporary fault with the signalling equipment"],
        "J8": [
            "damaged track",
            "m/which has been caused by.wav",
            "engineering work"
        ],
        "J9": ["emergency engineering work"],
        "MB": ["a broken down train"],
        "MC": ["a broken down train"],
        "MD": ["a broken down train"],
        "ME": ["a broken down train"],
        "ML": ["a train failure"],
        "MN": ["a train failure"],
        "MP": ["slippery rail conditions"],
        "MR": ["a train failure"],
        "MS": ["short formation of this train"],
        "MT": ["a train failure"],
        "MU": ["additional maintenance requirements at the depot"],
        "MV": ["a fault on trackside equipment"],
        "MW": [
            "a train failure",
            "m/which has been caused by.wav",
            "adverse weather conditions"
        ],
        "MY": [
            "a fault that has occurred whilst attaching coaches to this train"
        ],
        "M1": ["a train failure"],
        "M7": ["train door problems"],
        "M8": ["a train failure"],
        "M0": ["a train failure"],
        "NA": ["a train failure"],
        "OA": ["a late-running preceding service"],
        "OB": ["signalling difficulties"],
        "OC": ["signalling difficulties"],
        "OD": ["a late-running preceding service"],
        "OE": ["slippery rail conditions"],
        "OF": ["signalling difficulties"],
        "OG": [
            "third rail problems",
            "m/which has been caused by.wav",
            "adverse weather conditions"
        ],
        "OH": ["signalling difficulties"],
        "OJ": ["a fire"],
        "OK": ["staff shortages"],
        "OL": ["staff shortages"],
        "OM": ["slippery rail conditions"],
        "ON": ["a currently unidentified reason which is under investigation"],
        "OQ": ["signalling difficulties"],
        "OR": ["a late-running preceding service"],
        "OS": ["slippery rail conditions"],
        "OT": [
            "a temporary speed restriction because of signalling equipment " +
            "repairs"
        ],
        "OU": ["a currently unidentified reason which is under investigation"],
        "OV": ["a fire"],
        "OW": [
            "being held awaiting a late running connection",
            "m/which has been caused by.wav",
            "a slow-running preceding freight train running behind schedule"
        ],
        "OZ": ["a currently unidentified reason which is under investigation"],
        "PA": [
            "a temporary speed restriction",
            "m/which has been caused by.wav",
            "engineering work"
        ],
        "PB": ["a temporary speed restriction because of track repairs"],
        # PD system generated cancellation
        "PF": ["engineering work"],
        # PG planned cancellation
        # PJ duplicate
        # PL exclusion agreed
        "PN": ["a late-running preceding service"],
        # PT TRUST anomalies
        "QA": [
            "a technical problem",
            "e/from the original timetable schedule.wav"
        ],
        "QB": ["engineering work"],
        "QH": ["poor rail conditions caused by leaf fall"],
        "QI": ["poor rail conditions caused by leaf fall"],
        "QJ": ["poor rail conditions caused by leaf fall"],
        # QM VAR/STP problem
        # QN VSTP problem
        "QP": ["engineering work"],
        # QT commercial delay accepted
        "RB": ["large numbers of passengers joining the trains"],
        "RC": ["a member of staff providing assistance to a passenger"],
        "RD": ["additional coaches being attached to the train"],
        # RE lift/escalator failure
        "RH": ["a fire"],
        "RI": ["being held awaiting a late running connection"],
        "RJ": ["this train making additional stops on its journey"],
        "RK": ["being held awaiting a late running connection"],
        "RL": ["this train making additional stops on its journey"],
        "RK": ["being held awaiting a replacement bus connection"],
        "RO": ["passenger illness"],
        "RP": ["a passenger incident"],
        "RQ": ["a member of staff providing assistance to a passenger"],
        "RR": ["large numbers of passengers joining the trains"],
        "RS": ["large numbers of passengers joining the trains"],
        "RT": ["large numbers of passengers joining the trains"],
        "RU": ["a passenger incident"],
        "RV": [
            "confusion caused by a fault with the station information board"
        ],
        "RW": ["flooding"],
        "RX": ["overcrowding"],
        "RY": ["a passenger incident"],
        "RZ": ["a currently unidentified reason which is under investigation"],
        "R1": ["an incident on the line"],
        "R2": ["an incident on the line"],
        "R3": ["a shortage of train dispatch staff"],
        "R4": ["a shortage of train dispatch staff"],
        "R5": ["an incident on the line"],
        "R7": ["overcrowding"],
        "R8": ["a currently unidentified reason which is under investigation"],
        "TA": ["crewing difficulties"],
        # TB operator request
        "TF": ["a fault on the train"],
        "TG": ["a temporary shortage of drivers"],
        "TH": ["a temporary shortage of train crews"],
        "TI": ["crewing difficulties"],
        "TJ": ["a fault on the train"],
        "TK": ["a temporary shortage of train crews"],
        "TM": ["being held awaiting a late running connection"],
        "TN": ["an external cause beyond our control"],
        "TO": ["a currently unidentified reason which is under investigation"],
        "TP": ["this train making additional stops on its journey"],
        # TR TOC directive
        "TS": ["signalling difficulties"],
        "TT": ["poor rail conditions caused by leaf fall"],
        # TW professional driving policy
        "TX": ["an external cause beyond our control"],
        "TY": ["an incident on the line"],
        "TZ": ["a currently unidentified reason which is under investigation"],
        # T2 non-DOO delay at unstaffed station
        "T3": ["being held awaiting a replacement bus connection"],
        # T4 loading supplies
        "T8": ["a currently unidentified reason which is under investigation"],
        "VA": ["trespass on the line"],
        "VB": ["vandalism"],
        "VC": ["an accident to a member of the public"],
        "VD": ["a passenger having been taken ill on this train"],
        "VE": ["a ticket irregularity on board this train"],
        "VF": [
            "a fire",
            "m/which has been caused by.wav",
            "vandalism"
        ],
        "VG": ["police activity on the line"],
        "VH": ["the emergency communication cord being activated"],
        "VI": ["a security alert"],
        "VR": ["severe weather conditions"],
        "VW": ["severe weather conditions"],
        "VX": ["an external cause beyond our control"],
        "VZ": ["a currently unidentified reason which is under investigation"],
        "V8": ["animals on the railway line"],
        "XA": ["trespass on the line"],
        "XB": ["vandalism"],
        "XC": ["a fatality"],
        "XD": ["an accident on a level crossing"],
        "XF": ["police activity on the line"],
        "XH": ["the extreme heat"],
        "XI": ["a security alert"],
        "XK": ["a major electrical power fault"],
        "XL": ["a fire"],
        "XM": ["an external cause beyond our control"],
        "XN": ["a road vehicle on the line"],
        "XO": ["objects on the line"],
        "XP": ["a road vehicle striking a railway bridge"],
        # XQ swing bridge
        "XR": ["vandalism"],
        "XT": ["snow"],
        "XU": ["adverse weather conditions"],
        "XV": ["a fire"],
        "XW": ["high winds"],
        "X1": ["fog"],
        "X2": ["flooding"],
        "X3": ["a lightning strike"],
        "X4": ["extreme weather conditions"],
        "X8": ["animals on the railway line"],
        "X9": [
            "a points failure",
            "m/which has been caused by.wav",
            "snow",
        ],
        "YA": ["a late-running preceding service"],
        "YB": ["a late-running preceding service"],
        "YC": ["a late-running preceding service"],
        "YD": ["a late-running preceding service"],
        "YE": ["a late-running preceding service"],
        "YG": ["a late-running preceding service"],
        "YI": ["the late arrival of an incoming train"],
        "YJ": ["awaiting a member of the train crew"],
        "YL": ["being held awaiting a late running connection"],
        "YM": ["this train making additional stops on its journey"],
        "YN": ["awaiting a member of the train crew"],
        "YO": ["awaiting an available platform because of service congestion"],
        "YP": ["the train being diverted from its scheduled route"],
        "YQ": [
            "overcrowding caused by the short formation of this service today"
        ],
        # YR tactical service recovery
        "YU": ["a shortage of available coaches"],
        "YT": ["an external cause beyond our control"],
        "YV": ["a line blockage"],
        "YX": [
            "overcrowding caused by the",
            "e/delay or cancellation.wav",
        ],
        # ZS sub-threshold delay
        # ZU no cause
        # ZW system roll-up
        # ZX system roll-up
        # ZY system roll-up
        # ZZ system roll-up
    },
    "Female1": {
        "AA": ["operational problems"],
        "AC": ["operational problems"],
        "AD": ["a staff shortage"],
        "AE": ["congestion"],
        "AG": ["an incident on the line"],
        "AH": ["a fault on trackside equipment"],
        "AJ": ["operational problems"],
        "AK": ["an incident on the line"],
        "AX": ["a fault on trackside equipment"],
        "AZ": ["a currently unidentified reason which is under investigation"],
        "DA": ["operational problems"],
        "DB": ["operational problems"],
        "DC": ["operational problems"],
        "DD": ["operational problems"],
        "DE": ["operational problems"],
        "DF": ["an external cause beyond our control"],
        "DG": ["operational problems"],
        "DH": ["slippery rail conditions"],
        "FA": ["an incident on the line"],
        "FC": ["an incident on the line"],
        "FE": ["awaiting a member of the train crew"],
        "FF": ["operational problems"],
        "FG": ["operational problems"],
        "FH": ["operational problems"],
        "FI": ["signalling difficulties"],
        "FJ": ["operational problems"],
        "FK": [
            "a slow-running preceding freight train running behind schedule"
        ],
        # FL FOC request
        "FM": ["a fault on the train"],
        "FO": ["a currently unidentified reason which is under investigation"],
        "FS": ["signalling difficulties"],
        "FW": ["a currently unidentified reason which is under investigation"],
        "FX": [
            "a slow-running preceding freight train running behind schedule"
        ],
        "FZ": ["a currently unidentified reason which is under investigation"],
        "IA": ["a failure of signalling equipment"],
        "IB": ["a points failure"],
        "IC": ["a track circuit failure"],
        "ID": ["a fault on a level crossing"],
        "IE": ["a power failure"],
        "IF": ["a failure of signalling equipment"],
        "IG": ["a failure of signalling equipment"],
        "IH": ["a power failure"],
        "II": ["a technical fault to lineside equipment"],
        "IJ": ["a fault on trackside equipment"],
        "IK": ["a technical fault to lineside equipment"],
        "IL": ["a failure of signalling equipment"],
        "IM": ["a technical fault to lineside equipment"],
        "IN": ["a technical fault to lineside equipment"],
        "IP": [
            "a points failure",
            "m/which has been caused by.wav",
            "snow",
            "m/and.wav",
            "a fault on trackside equipment"
        ],
        "IQ": ["a fault on trackside equipment"],
        "IR": ["a broken rail"],
        "IS": ["damaged track"],
        "IT": ["a currently unidentified reason which is under investigation"],
        "IV": ["a landslip"],
        "IW": ["adverse weather conditions"],
        "I0": ["a temporary fault with the signalling equipment"],
        "I1": [
            "overhead electric line problems",
            "m/or.wav",
            "third rail problems"
        ],
        "I2": ["an electrical power supply problem"],
        "I4": ["an electrical power supply problem"],
        "I5": ["overrunning engineering work"],
        "I6": ["overrunning engineering work"],
        "I7": ["overrunning engineering work"],
        "I8": ["animals on the railway line"],
        "I9": ["a lineside fire"],
        "JA": ["a temporary speed restriction because of track repairs"],
        # not sure how to end this so just add a random today
        "JB": ["a temporary speed restriction", "e/today.wav"],
        "JD": ["suspected damage to a railway bridge"],
        "JF": ["a fault on trackside equipment"],
        "JG": ["a temporary speed restriction because of track repairs"],
        "JH": ["the extreme heat"],
        "JK": ["flooding"],
        "JL": ["an incident on the line"],
        "JP": ["a fallen tree on the line"],
        "JR": ["signalling difficulties"],
        "JS": ["a temporary speed restriction because of track repairs"],
        "JT": [
            "a points failure",
            "m/which has been caused by.wav",
            "snow",
        ],
        "JX": ["objects on the line"],
        "J0": ["a technical fault to lineside equipment"],
        "J2": ["a technical fault to lineside equipment"],
        "J3": ["a temporary fault with the signalling equipment"],
        "J4": ["reports of a blockage on the line"],
        "J5": ["reports of a blockage on the line"],
        "J6": ["a lightning strike"],
        "J7": ["a temporary fault with the signalling equipment"],
        "J8": [
            "damaged track",
            "m/which has been caused by.wav",
            "engineering works"
        ],
        "J9": ["emergency engineering work"],
        "MB": ["a broken down train"],
        "MC": ["a broken down train"],
        "MD": ["a broken down train"],
        "ME": ["a broken down train"],
        "ML": ["a train failure"],
        "MN": ["a train failure"],
        "MP": ["slippery rail conditions"],
        "MR": ["a train failure"],
        "MS": ["short formation of this train"],
        "MT": ["a train failure"],
        "MU": ["additional maintenance requirements at the depot"],
        "MV": ["a fault on trackside equipment"],
        "MW": [
            "a train failure",
            "m/which has been caused by.wav",
            "adverse weather conditions"
        ],
        "MY": [
            "a fault that has occurred whilst attaching coaches to this train"
        ],
        "M1": ["a train failure"],
        "M7": ["train door problems"],
        "M8": ["a train failure"],
        "M0": ["a train failure"],
        "NA": ["a train failure"],
        "OA": ["a late-running preceding service"],
        "OB": ["signalling difficulties"],
        "OC": ["signalling difficulties"],
        "OD": ["a late-running preceding service"],
        "OE": ["slippery rail conditions"],
        "OF": ["signalling difficulties"],
        "OG": [
            "third rail problems",
            "m/which has been caused by.wav",
            "adverse weather conditions"
        ],
        "OH": ["signalling difficulties"],
        "OJ": ["a fire"],
        "OK": ["a staff shortage"],
        "OL": ["a staff shortage"],
        "OM": ["slippery rail conditions"],
        "ON": ["a currently unidentified reason which is under investigation"],
        "OQ": ["signalling difficulties"],
        "OR": ["a late-running preceding service"],
        "OS": ["slippery rail conditions"],
        "OT": [
            "a temporary speed restriction because of signalling equipment " +
            "repairs"
        ],
        "OU": ["a currently unidentified reason which is under investigation"],
        "OV": ["a fire"],
        "OW": [
            "being held awaiting a late running connection",
            "m/which has been caused by.wav",
            "a slow-running preceding freight train running behind schedule"
        ],
        "OZ": ["a currently unidentified reason which is under investigation"],
        "PA": [
            "a temporary speed restriction",
            "m/which has been caused by.wav",
            "engineering works"
        ],
        "PB": ["a temporary speed restriction because of track repairs"],
        # PD system generated cancellation
        "PF": ["engineering works"],
        # PG planned cancellation
        # PJ duplicate
        # PL exclusion agreed
        "PN": ["a late-running preceding service"],
        # PT TRUST anomalies
        "QA": ["operational problems"],
        "QB": ["engineering works"],
        "QH": ["poor rail conditions caused by leaf fall"],
        "QI": ["poor rail conditions caused by leaf fall"],
        "QJ": ["poor rail conditions caused by leaf fall"],
        # QM VAR/STP problem
        # QN VSTP problem
        "QP": ["engineering works"],
        # QT commercial delay accepted
        "RB": ["large numbers of passengers joining the trains"],
        "RC": ["a member of staff providing assistance to a passenger"],
        "RD": ["additional coaches being attached to the train"],
        # RE lift/escalator failure
        "RH": ["a fire"],
        "RI": ["being held awaiting a late running connection"],
        "RJ": ["this train making additional stops on its journey"],
        "RK": ["being held awaiting a late running connection"],
        "RL": ["this train making additional stops on its journey"],
        "RK": ["being held awaiting a replacement bus connection"],
        "RO": ["passenger illness"],
        "RP": ["a passenger incident"],
        "RQ": ["a member of staff providing assistance to a passenger"],
        "RR": ["large numbers of passengers joining the trains"],
        "RS": ["large numbers of passengers joining the trains"],
        "RT": ["large numbers of passengers joining the trains"],
        "RU": ["a passenger incident"],
        "RV": [
            "confusion caused by a fault with the station information board"
        ],
        "RW": ["flooding"],
        "RX": ["overcrowding"],
        "RY": ["a passenger incident"],
        "RZ": ["a currently unidentified reason which is under investigation"],
        "R1": ["an incident on the line"],
        "R2": ["an incident on the line"],
        "R3": ["a shortage of train dispatch staff"],
        "R4": ["a shortage of train dispatch staff"],
        "R5": ["an incident on the line"],
        "R7": ["overcrowding"],
        "R8": ["a currently unidentified reason which is under investigation"],
        "TA": ["operational problems"],
        # TB operator request
        "TF": ["a fault on the train"],
        "TG": ["a temporary shortage of drivers"],
        "TH": ["a temporary shortage of train crews"],
        "TI": ["operational problems"],
        "TJ": ["a fault on the train"],
        "TK": ["a temporary shortage of train crews"],
        "TM": ["being held awaiting a late running connection"],
        "TN": ["an external cause beyond our control"],
        "TO": ["a currently unidentified reason which is under investigation"],
        "TP": ["this train making additional stops on its journey"],
        "TR": ["operational problems"],
        "TS": ["signalling difficulties"],
        "TT": ["poor rail conditions caused by leaf fall"],
        "TW": ["operational problems"],
        "TX": ["an external cause beyond our control"],
        "TY": ["an incident on the line"],
        "TZ": ["a currently unidentified reason which is under investigation"],
        "T2": ["operational problems"],
        "T3": ["being held awaiting a replacement bus connection"],
        "T4": ["operational problems"],
        "T8": ["a currently unidentified reason which is under investigation"],
        "VA": ["trespass on the line"],
        "VB": ["vandalism"],
        "VC": ["an accident to a member of the public"],
        "VD": ["passenger illness"],
        "VE": ["a ticket irregularity on board this train"],
        "VF": [
            "a fire",
            "m/which has been caused by.wav",
            "vandalism"
        ],
        "VG": ["police activity on the line"],
        "VH": ["the emergency communication cord being activated"],
        "VI": ["a security alert"],
        "VR": ["severe weather conditions"],
        "VW": ["severe weather conditions"],
        "VX": ["an external cause beyond our control"],
        "VZ": ["a currently unidentified reason which is under investigation"],
        "V8": ["animals on the railway line"],
        "XA": ["trespass on the line"],
        "XB": ["vandalism"],
        "XC": ["a fatality"],
        "XD": ["an accident on a level crossing"],
        "XF": ["police activity on the line"],
        "XH": ["the extreme heat"],
        "XI": ["a security alert"],
        "XK": ["a major electrical power fault"],
        "XL": ["a fire"],
        "XM": ["an external cause beyond our control"],
        "XN": ["a road vehicle on the line"],
        "XO": ["objects on the line"],
        "XP": ["a road vehicle striking a railway bridge"],
        "XQ": ["operational problems"],
        "XR": ["vandalism"],
        "XT": ["snow"],
        "XU": ["adverse weather conditions"],
        "XV": ["a fire"],
        "XW": ["high winds"],
        "X1": ["fog"],
        "X2": ["flooding"],
        "X3": ["a lightning strike"],
        "X4": ["extreme weather conditions"],
        "X8": ["animals on the railway line"],
        "X9": [
            "a points failure",
            "m/which has been caused by.wav",
            "snow",
        ],
        "YA": ["a late-running preceding service"],
        "YB": ["a late-running preceding service"],
        "YC": ["a late-running preceding service"],
        "YD": ["a late-running preceding service"],
        "YE": ["a late-running preceding service"],
        "YG": ["a late-running preceding service"],
        "YI": ["the late arrival of an incoming train"],
        "YJ": ["awaiting a member of the train crew"],
        "YL": ["being held awaiting a late running connection"],
        "YM": ["this train making additional stops on its journey"],
        "YN": ["awaiting a member of the train crew"],
        "YO": ["awaiting an available platform because of service congestion"],
        "YP": ["the train being diverted from its scheduled route"],
        "YQ": [
            "overcrowding caused by the short formation of this service today"
        ],
        "YR": ["operational problems"],
        "YU": ["a shortage of available coaches"],
        "YT": ["an external cause beyond our control"],
        "YV": ["reports of a blockage on the line"],
        "YX": ["overcrowding"],
        # ZS sub-threshold delay
        # ZU no cause
        # ZW system roll-up
        # ZX system roll-up
        # ZY system roll-up
        # ZZ system roll-up
    },
    "Female2": {
        # AA acceptance into off-NR terminal or yard
        # AC train prep/TOPS
        "AD": ["a staff shortage"],
        "AE": ["signalling difficulties"],
        "AG": ["an incident on the line"],
        "AH": ["a technical problem"],
        # AJ awaiting customer's traffic/doc
        "AK": ["an incident on the line"],
        "AX": ["a technical problem"],
        # AZ other FOC cause
        # DA non-tech fleet
        # DB Train operations
        "DC": ["a staff shortage"],
        # DD tech fleet
        # DE station
        # DF external causes
        # DG terminals or yards
        "DH": ["poor rail conditions"],
        "FA": ["an incident on the line"],
        "FC": ["an incident on the line"],
        "FE": ["a staff shortage"],
        "FF": ["a staff shortage"],
        # FG professional driving policy
        # FH FOC planning issue non-crewing
        "FI": ["signalling difficulties"],
        # FJ FOC control decision
        # FK FOC divert request
        # FL FOC request
        "FM": ["a train failure"],
        # FO believed to be operator caused
        "FS": ["signalling difficulties"],
        # FW unexplained late start
        # FX freight running at lower speed than specified
        # FZ other FOC cause
        "IA": ["a signalling apparatus failure"],
        "IB": ["a points failure"],
        "IC": ["a signalling apparatus failure"],
        "ID": ["a technical problem"],
        "IE": ["a technical problem"],
        "IF": ["a signalling apparatus failure"],
        "IG": ["a signalling apparatus failure"],
        "IH": ["a technical problem"],
        "II": ["a technical problem"],
        "IJ": ["a technical problem"],
        "IK": ["a technical problem"],
        "IL": ["a signalling apparatus failure"],
        "IM": ["a technical problem"],
        "IN": ["a technical problem"],
        "IP": ["a points failure"],
        "IQ": ["a technical problem"],
        "IR": ["poor rail conditions"], # broken is poor, right?
        "IS": ["poor rail conditions"],
        "IT": ["poor rail conditions"],
        "IV": ["an incident on the line"],
        "IW": ["adverse weather conditions"],
        "I0": ["a signalling apparatus failure"],
        "I1": ["overhead electric line problems"],
        "I2": ["a technical problem"],
        "I4": ["a technical problem"],
        "I5": ["engineering work"],
        "I6": ["engineering work"],
        "I7": ["engineering work"],
        "I8": ["an incident on the line"],
        "I9": ["an incident on the line"],
        "JA": ["engineering work"],
        "JB": ["engineering work"],
        "JD": ["suspected damage to a railway bridge"],
        "JF": ["a technical problem"],
        "JG": ["engineering work"],
        "JH": ["adverse weather conditions"],
        "JK": ["bad weather conditions"],
        "JL": ["an incident on the line"],
        "JP": ["an incident on the line"],
        "JR": ["signalling difficulties"],
        "JS": ["engineering works"],
        "JT": ["a points failure"],
        "JX": ["an incident on the line"],
        "J0": ["a technical problem"],
        "J2": ["a technical problem"],
        "J3": ["a signalling apparatus failure"],
        "J4": ["an incident on the line"],
        "J5": ["an incident on the line"],
        "J6": ["bad weather conditions"],
        "J7": ["a signalling apparatus failure"],
        "J8": ["engineering work"],
        "J9": ["engineering work"],
        "MB": ["a train failure"],
        "MC": ["a train failure"],
        "MD": ["a train failure"],
        "ME": ["a train failure"],
        "ML": ["a train failure"],
        "MN": ["a train failure"],
        "MP": ["poor rail conditions"],
        "MR": ["a train failure"],
        # MS short formation
        "MT": ["a train failure"],
        "MU": ["a train failure"],
        "MV": ["a technical problem"],
        "MW": ["a train failure"],
        "MY": ["a train failure"],
        "M1": ["a train failure"],
        "M7": ["a train failure"],
        "M8": ["a train failure"],
        "M0": ["a train failure"],
        "NA": ["a train failure"],
        "OA": ["signalling difficulties"],
        "OB": ["signalling difficulties"],
        "OC": ["signalling difficulties"],
        "OD": ["signalling difficulties"],
        "OE": ["poor rail conditions"],
        "OF": ["signalling difficulties"],
        "OG": ["adverse weather conditions"],
        "OH": ["signalling difficulties"],
        "OJ": ["an incident on the line"],
        "OK": ["staff shortages"],
        "OL": ["staff shortages"],
        "OM": ["poor rail conditions"],
        # ON delays not investigated
        "OQ": ["signalling difficulties"],
        "OR": ["signalling difficulties"],
        "OS": ["poor rail conditions"],
        "OT": ["a signalling apparatus failure"],
        # OU delays not investigated
        "OV": ["an incident on the line"],
        "OW": ["the late arrival of an incoming train"],
        # OZ other NR
        "PA": ["engineering work"],
        "PB": ["engineering work"],
        # PD system generated cancellation
        "PF": ["engineering work"],
        # PG planned cancellation
        # PJ duplicate
        # PL exclusion agreed
        # PN VSTP delay under 5 minutes
        # PT TRUST anomalies
        "QA": ["a technical problem"],
        "QB": ["engineering work"],
        "QH": ["poor rail conditions"],
        "QI": ["poor rail conditions"],
        "QJ": ["poor rail conditions"],
        # QM VAR/STP problem
        # QN VSTP problem
        "QP": ["engineering work"],
        # QT commercial delay accepted
        # RB passengers joining/alighting
        # RC pre-booked assistance
        # RD attaching/detaching
        # RE lift/escalator failure
        "RH": ["an incident on the line"],
        "RI": ["the late arrival of an incoming train"],
        # RJ unauthorised special stop orders
        "RK": ["the late arrival of an incoming train"],
        # RL authorised special stop orders
        "RK": ["the late arrival of an incoming train"],
        "RO": ["an incident on the line"],
        "RP": ["an incident on the line"],
        # RQ unbooked assistance
        # RR reserved cycles
        # RS unreserved cycles
        # RT luggage
        "RU": ["an incident on the line"],
        "RV": ["a technical problem"],
        "RW": ["bad weather conditions"],
        "RX": ["an incident on the line"],
        "RY": ["an incident on the line"],
        # RZ other station
        "R1": ["an incident on the line"],
        "R2": ["an incident on the line"],
        "R3": ["a staff shortage"],
        "R4": ["a staff shortage"],
        "R5": ["an incident on the line"],
        # R7 overcrowding planned event
        # R8 delay at station believed to be TOC
        "TA": ["a staff shortage"],
        # TB operator request
        "TF": ["a train failure"],
        "TG": ["a staff shortage"],
        "TH": ["a staff shortage"],
        "TI": ["a staff shortage"],
        "TJ": ["a train failure"],
        "TK": ["a staff shortage"],
        "TM": ["the late arrival of an incoming train"],
        "TN": ["the late arrival of an incoming train"],
        # TO time lost en route believed to be TOC
        # TP special stop orders
        # TR TOC directive
        "TS": ["signalling difficulties"],
        "TT": ["poor rail conditions"],
        # TW professional driving policy
        "TX": ["the late arrival of an incoming train"],
        "TY": ["an incident on the line"],
        # TZ other passenger TOC causes
        # T2 non-DOO delay at unstaffed station
        "T3": ["the late arrival of an incoming train"],
        # T4 loading supplies
        # T8 delay at station believed to be operator
        "VA": ["trespass on the line"],
        "VB": ["vandalism"],
        "VC": ["an incident on the line"],
        "VD": ["an incident on the line"],
        "VE": ["an incident on the line"],
        "VF": ["vandalism"],
        "VG": ["an incident on the line"],
        "VH": ["an incident on the line"],
        "VI": ["a security alert"],
        "VR": ["bad weather conditions"],
        "VW": ["bad weather conditions"],
        "VX": ["the late arrival of an incoming train"],
        # VZ other pax/external causes
        "V8": ["an incident on the line"],
        "XA": ["trespass on the line"],
        "XB": ["vandalism"],
        "XC": ["an incident on the line"],
        "XD": ["an incident on the line"],
        "XF": ["an incident on the line"],
        "XH": ["adverse weather conditions"],
        "XI": ["a security alert"],
        "XK": ["a technical problem"],
        "XL": ["an incident on the line"],
        "XM": ["an incident on the line"],
        "XN": ["an incident on the line"],
        "XO": ["an incident on the line"],
        "XP": ["suspected damage to a railway bridge"],
        # XQ swing bridge
        "XR": ["vandalism"],
        "XT": ["adverse weather conditions"],
        "XU": ["adverse weather conditions"],
        "XV": ["an incident on the line"],
        "XW": ["bad weather conditions"],
        "X1": ["bad weather conditions"],
        "X2": ["bad weather conditions"],
        "X3": ["bad weather conditions"],
        "X4": ["bad weather conditions"],
        "X8": ["an incident on the line"],
        "X9": ["a points failure"],
        "YA": ["the late arrival of an incoming train"],
        "YB": ["the late arrival of an incoming train"],
        "YC": ["the late arrival of an incoming train"],
        "YD": ["the late arrival of an incoming train"],
        "YE": ["the late arrival of an incoming train"],
        "YG": ["the late arrival of an incoming train"],
        "YI": ["the late arrival of an incoming train"],
        "YJ": ["the late arrival of an incoming train"],
        "YL": ["the late arrival of an incoming train"],
        # YM special stop order
        "YN": ["the late arrival of an incoming train"],
        "YO": ["the late arrival of an incoming train"],
        "YP": ["the late arrival of an incoming train"],
        # YQ overcrowding due to short formation
        # YR tactical service recovery
        "YU": ["a train failure"],
        "YT": ["the late arrival of an incoming train"],
        "YV": ["an incident on the line"],
        "YX": ["the late arrival of an incoming train"],
        # ZS sub-threshold delay
        # ZU no cause
        # ZW system roll-up
        # ZX system roll-up
        # ZY system roll-up
        # ZZ system roll-up
    },
}

class WavPlayer:
    def __init__(self, config: dict):
        self.last_played = None
        self.audio = pyaudio.PyAudio()
        self.config = config
        self.stream = self.audio.open(
            format = self.audio.get_format_from_width(1),
            channels = 1,
            rate = 16000,
            output = True
        )


    def play_wav(self, file: str, play_last: bool = True) -> None:
        path = os.path.join(
            self.config["system"]["path"],
            self.config["general"]["voice"]
        )
        try:
            logging.info(os.path.join(path, file))
            data, rate = soundfile.read(os.path.join(path, file))
            data2 = bytearray()
            for i, x in enumerate(data):
                try:
                    data2.append(int((x + 1.0) * 128))
                except:
                    logging.info(x, exc_info=1)

            self.stream.write(bytes(data2))

            self.last_played = file
        except:
            logging.info("Missing file", exc_info=1)
            if (
                self.last_played and
                play_last and
                self.config["general"]["repeat_missing_announcement"]
            ):
                logging.info("Playing last file")
                self.play_wav(self.last_played, False)


def load_config(filename: str) -> dict:
    with open(filename, "rb") as f:
        config = tomllib.load(f)

        if len(sys.argv) >= 2:
            config["general"]["station"] = sys.argv[1]

        if not config["system"]["rtt_user"]:
            config["system"]["rtt_user"] = os.environ["RTT_USER"]
        if not config["system"]["rtt_pass"]:
            config["system"]["rtt_pass"] = os.environ["RTT_PASS"]

        # Disable unsupported features for Alison
        if config["general"]["voice"] == "Female2":
            enablements = config["announcements_enabled"]
            enablements["arrivals_next_train"] = False
            enablements["arrivals_now_approaching"] = False
            enablements["arrivals_now_standing"] = False
            enablements["arrivals_trust_triggered"] = False
            enablements["arrivals_platform_alteration"] = False
            enablements["safety"] = False
            config["departures_next_train"]["no_platform"] = False
            config["departures_now_standing"]["now_standing_script"] = False
            config["departures_now_standing"]["no_platform"] = False
            config["departures_trust_triggered"]["no_platform"] = False
            config["departures_next_train"]["mind_the_gap"] = False
            config["departures_now_approaching"]["mind_the_gap"] = False
            config["departures_now_standing"]["mind_the_gap"] = False
            config["departures_trust_triggered"]["mind_the_gap"] = False

        return config


def fetch_lineup(url: str) -> dict:
    response = requests.get(url)

    content = json.loads(response.content)

    if not content["services"]:
        content["services"] = []

    return content


def fetch_lineups(config: dict, now: datetime.datetime) -> tuple[dict]:
    strftime = now.strftime("%Y/%m/%d/%H%M")

    user = config["system"]["rtt_user"]
    password = config["system"]["rtt_pass"]

    station = config["general"]["station"]

    deps_url = (
        f"https://{user}:{password}@api.rtt.io/api/v1/json/search/{station}" +
        f"/{strftime}"
    )
    deps_content = fetch_lineup(deps_url)

    arrs_url = deps_url + "/arrivals"
    arrs_content = fetch_lineup(arrs_url)

    return (deps_content, arrs_content)


def fetch_train_content_by_uid(config: dict, uid: str, run_date: str) -> dict:
    user = config["system"]["rtt_user"]
    password = config["system"]["rtt_pass"]

    url_rundate = run_date.replace("-", "/")

    train_url = (
        f"https://{user}:{password}@api.rtt.io/api/v1/json/" +
        f"service/{uid}/{url_rundate}"
    )
    response = requests.get(train_url)
    
    return json.loads(response.content)


def fetch_train_content(config: dict, service: dict) -> dict:
    uid = service["serviceUid"]
    run_date = service["runDate"]

    return fetch_train_content_by_uid(config, uid, run_date)


def get_hour_minute(time: str, now: datetime.datetime) -> tuple[int, int]:
    hour = int(time[:2])
    minute = int(time[2:])

    if hour < 6 and now.hour > 18:
        hour += 24

    return (hour, minute)


def time_diff(hour: int, minute: int, now: datetime.datetime) -> int:
    return (hour * 60 + minute) - (now.hour * 60 + now.minute)


def get_booked_hour_minute(
    service: dict,
    now: datetime.datetime
) -> tuple[int, int]:
    booked_dep = service["locationDetail"].get("gbttBookedDeparture")
    if not booked_dep:
        booked_dep = service["locationDetail"].get("gbttBookedArrival")
    return get_hour_minute(booked_dep, now)


def get_realtime_hour_minute(
    service: dict,
    now: datetime.datetime
) -> tuple[int, int]:
    realtime_dep = service["locationDetail"].get("realtimeDeparture")
    if not realtime_dep:
        realtime_dep = service["locationDetail"].get("realtimeArrival")
        if not realtime_dep:
            realtime_dep = service["locationDetail"].get("gbttBookedDeparture")
            if not realtime_dep:
                realtime_dep = service["locationDetail"].get(
                    "gbttBookedArrival"
                )
    return get_hour_minute(realtime_dep, now)


def get_delay(
    realtime_hour: int,
    realtime_minute: int,
    booked_hour: int,
    booked_minute: int
) -> int:
    return (
        (realtime_hour * 60 + realtime_minute) -
        (booked_hour * 60 + booked_minute)
    )


def get_chunked_time(now_to_booked: int, interval: int) -> int:
    return ((now_to_booked - 1) // interval) * interval


def is_departing(service: dict) -> bool:
    display_as = service["locationDetail"]["displayAs"]

    return display_as in ("CALL", "ORIGIN", "STARTS") or (
        display_as == "DESTINATION" and
        "associations" in service["locationDetail"] and
        "join" in [
            assoc["type"] for
            assoc in service["locationDetail"]["associations"]
        ]
    )


def is_arriving(service: dict) -> bool:
    display_as = service["locationDetail"]["displayAs"]

    return display_as != "CANCELLED_CALL" and not is_departing(service)


def should_announce_departure_delay(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    service_location = service["locationDetail"].get("serviceLocation")
    display_as = service["locationDetail"]["displayAs"]
    service_type = service["serviceType"]

    booked_hour, booked_minute = get_booked_hour_minute(service, now)
    realtime_hour, realtime_minute = get_realtime_hour_minute(service, now)

    realtime_dep_actual = (
        service["locationDetail"].get("realtimeDepartureActual")
    )
    if service["locationDetail"].get("realtimeDepartureNoReport"):
        realtime_dep_actual = True
    realtime_arr_actual = (
        service["locationDetail"].get("realtimeArrivalActual")
    )
    if service["locationDetail"].get("realtimeArrivalNoReport"):
        realtime_arr_actual = True

    now_to_booked = time_diff(booked_hour, booked_minute, now)

    delay = get_delay(
        realtime_hour,
        realtime_minute,
        booked_hour,
        booked_minute
    )

    interval = config["departures_delay"]["interval"]
    chunked_time = get_chunked_time(now_to_booked, interval)
    if (uid, run_date) in service_last_announcement:
        old_now_to_booked = service_last_announcement[(uid, run_date)][
            "now_to_booked"
        ]
        old_chunked_time = get_chunked_time(old_now_to_booked, interval)

    return (
        config["announcements_enabled"]["departures_delay"] and
        # In this case, delays will be handled by the "parent" service so we
        # do actually want this, not is_departing
        display_as in ("CALL", "ORIGIN", "STARTS") and
        (
            (
                delay >= config["departures_delay"]["delay_threshold"] and
                (
                    delay + 1 >= -now_to_booked or
                    config["departures_delay"]["being_delayed"]
                )
            ) or
            (
                now_to_booked <=
                -config["departures_delay"]["delay_threshold"] and
                config["departures_delay"]["being_delayed_undelayed"]
            )
        ) and
        (
            (uid, run_date) not in service_last_announcement or
            (
                service_last_announcement[(uid, run_date)]["delay"] <
                config["departures_delay"]["delay_threshold"] and
                delay > config["departures_delay"]["delay_threshold"]
            ) or
            (
                service_last_announcement[(uid, run_date)]["now_to_booked"] >
                -config["departures_delay"]["delay_threshold"] and
                now_to_booked <=
                -config["departures_delay"]["delay_threshold"] and
                config["departures_delay"]["being_delayed_undelayed"]
            ) or
            (
                config["departures_delay"]["announce_updated_delays"] and 
                service_last_announcement[(uid, run_date)]["delay"] != delay
            ) or
            (
                config["departures_delay"]["timed_announcements"] and
                chunked_time != old_chunked_time and
                (
                    config["departures_delay"]["always_repeat_before"] or
                    now_to_booked <=
                    config["departures_delay"]["minutes_before"]
                ) and
                (
                    config["departures_delay"]["always_repeat_after"] or
                    -now_to_booked <=
                    config["departures_delay"]["minutes_after"]
                )
            )
        ) and
        (
            config["departures_delay"]["always_announce_before"] or
            now_to_booked <= config["departures_delay"]["minutes_before"]
        ) and
        (
            config["departures_delay"]["always_announce_after"] or
            -now_to_booked <= config["departures_delay"]["minutes_after"]
        ) and
        not service_location and
        (
            not realtime_arr_actual or
            not config["announcements_enabled"]["departures_trust_triggered"]
        ) and
        not realtime_dep_actual and
        service_type == "train"
    )


def should_announce_arrival_delay(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    service_location = service["locationDetail"].get("serviceLocation")
    display_as = service["locationDetail"]["displayAs"]
    service_type = service["serviceType"]

    booked_hour, booked_minute = get_booked_hour_minute(service, now)
    realtime_hour, realtime_minute = get_realtime_hour_minute(service, now)

    realtime_arr_actual = (
        service["locationDetail"].get("realtimeArrivalActual")
    )
    if service["locationDetail"].get("realtimeArrivalNoReport"):
        realtime_arr_actual = True

    now_to_booked = time_diff(booked_hour, booked_minute, now)

    delay = get_delay(
        realtime_hour,
        realtime_minute,
        booked_hour,
        booked_minute
    )

    interval = config["arrivals_delay"]["interval"]
    chunked_time = get_chunked_time(now_to_booked, interval)
    if (uid, run_date) in service_last_announcement:
        old_now_to_booked = service_last_announcement[(uid, run_date)][
            "now_to_booked"
        ]
        old_chunked_time = get_chunked_time(old_now_to_booked, interval)

    return (
        config["announcements_enabled"]["arrivals_delay"] and
        # We use actual is_arriving here, we should probably suppress
        # confusing announcements for joining trains.
        is_arriving(service) and
        (
            (
                delay >= config["arrivals_delay"]["delay_threshold"] and
                (
                    delay + 1 >= -now_to_booked or
                    config["arrivals_delay"]["being_delayed"]
                )
            ) or
            (
                now_to_booked <=
                -config["arrivals_delay"]["delay_threshold"] and
                config["arrivals_delay"]["being_delayed_undelayed"]
            )
        ) and
        (
            (uid, run_date) not in service_last_announcement or
            (
                service_last_announcement[(uid, run_date)]["delay"] <
                config["arrivals_delay"]["delay_threshold"] and
                delay > config["arrivals_delay"]["delay_threshold"]
            ) or
            (
                service_last_announcement[(uid, run_date)]["now_to_booked"] >
                -config["arrivals_delay"]["delay_threshold"] and
                now_to_booked <=
                -config["arrivals_delay"]["delay_threshold"] and
                config["arrivals_delay"]["being_delayed_undelayed"]
            ) or
            (
                config["arrivals_delay"]["announce_updated_delays"] and 
                service_last_announcement[(uid, run_date)]["delay"] != delay
            ) or
            (
                config["arrivals_delay"]["timed_announcements"] and
                chunked_time != old_chunked_time and
                (
                    config["arrivals_delay"]["always_repeat_before"] or
                    now_to_booked <=
                    config["arrivals_delay"]["minutes_before"]
                ) and
                (
                    config["arrivals_delay"]["always_repeat_after"] or
                    -now_to_booked <=
                    config["arrivals_delay"]["minutes_after"]
                )
            )
        ) and
        (
            config["arrivals_delay"]["always_announce_before"] or
            now_to_booked <= config["arrivals_delay"]["minutes_before"]
        ) and
        (
            config["arrivals_delay"]["always_announce_after"] or
            -now_to_booked <= config["arrivals_delay"]["minutes_after"]
        ) and
        not service_location and
        not realtime_arr_actual and
        service_type == "train"
    )


def should_announce_cancellation(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    display_as = service["locationDetail"]["displayAs"]

    booked_hour, booked_minute = get_booked_hour_minute(service, now)

    now_to_booked = time_diff(booked_hour, booked_minute, now)

    interval = config["cancellation"]["interval"]
    chunked_time = get_chunked_time(now_to_booked, interval)
    if (uid, run_date) in service_last_announcement:
        old_now_to_booked = service_last_announcement[(uid, run_date)][
            "now_to_booked"
        ]
        old_chunked_time = get_chunked_time(old_now_to_booked, interval)

    return (
        config["announcements_enabled"]["cancellation"] and
        display_as in ("TERMINATES", "CANCELLED_CALL") and
        (
            (uid, run_date) not in service_last_announcement or
            not service_last_announcement[(uid, run_date)]["is_cancel"] or
            (
                config["cancellation"]["timed_announcements"] and
                chunked_time != old_chunked_time and
                (
                    config["cancellation"][
                        "always_repeat_before"
                    ] or
                    now_to_booked <=
                    config["cancellation"]["minutes_before"]
                ) and
                (
                    config["cancellation"]["always_repeat_after"] or
                    -now_to_booked <=
                    config["cancellation"]["minutes_after"]
                )
            )
        ) and
        (
            config["cancellation"]["always_announce_before"] or
            now_to_booked <=
            config["cancellation"]["minutes_before"]
        ) and
        (
            config["cancellation"]["always_announce_after"] or
            -now_to_booked <=
            config["cancellation"]["minutes_after"]
        )
    )


def should_announce_departure_platform_alteration(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime,
    services: list[dict]
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    display_as = service["locationDetail"]["displayAs"]
    platform_alteration = service["locationDetail"].get("platformChanged")
    service_location = service["locationDetail"].get("serviceLocation")

    realtime_dep_actual = (
        service["locationDetail"].get("realtimeDepartureActual")
    )
    if realtime_dep_actual is None:
        realtime_dep_actual = (
            service["locationDetail"].get("realtimeArrivalActual")
        )
    if service["locationDetail"].get("realtimeDepartureNoReport"):
        realtime_dep_actual = True

    return (
        # We do want is_departing here, as a platform alteration on the joining
        # portion will usually indicate one for the whole train.
        is_departing(service) and
        platform_alteration and
        (
            (uid, run_date) not in service_last_announcement or
            not service_last_announcement[
                (uid, run_date)
            ]["platform_alteration"]
        ) and
        not realtime_dep_actual and
        # if realtime announcements are enabled with platform alterations and
        # we are about to make one of those, suppress the platform alteration
        # as it will just duplicate information. TODO maybe revise this once
        # we get multiple announcement channels.
        (
            service_location != "APPR_STAT" or
            not config["announcements_enabled"]["departures_next_train"] or
            not config["departures_next_train"]["platform_alterations"] or
            not should_announce_realtime(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        ) and
        (
            service_location != "APPR_PLAT" or
            not config["announcements_enabled"][
                "departures_now_approaching"
            ] or
            not config["departures_now_approaching"]["platform_alterations"] or
            not should_announce_realtime(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        ) and
        (
            not (
                service_location == "AT_PLAT" or
                (
                    not service_location and
                    (uid, run_date) in service_last_announcement and
                    service_last_announcement.get((uid, run_date))[
                        "service_location"
                    ]
                )
            ) or
            not config["announcements_enabled"]["departures_now_standing"] or
            not config["departures_now_standing"]["platform_alterations"] or
            not should_announce_realtime(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        ) and
        (
            display_as != "ORIGIN" or
            "associations" not in service["locationDetail"] or
            "divide" not in [
                assoc["type"] for
                assoc in service["locationDetail"]["associations"]
            ] or
            not assoc_service_has_location(service, services)
        )
    )


def should_announce_arrival_platform_alteration(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime,
    services: list[dict]
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    display_as = service["locationDetail"]["displayAs"]
    platform_alteration = service["locationDetail"].get("platformChanged")
    service_location = service["locationDetail"].get("serviceLocation")

    realtime_arr_actual = (
        service["locationDetail"].get("realtimeArrivalActual")
    )
    if service["locationDetail"].get("realtimeArrivalNoReport"):
        realtime_arr_actual = True

    return (
        is_arriving(service) and
        platform_alteration and
        (
            (uid, run_date) not in service_last_announcement or
            not service_last_announcement[
                (uid, run_date)
            ]["platform_alteration"]
        ) and
        (not realtime_arr_actual or service_location) and
        # if realtime announcements are enabled with platform alterations and
        # we are about to make one of those, suppress the platform alteration
        # as it will just duplicate information. TODO maybe revise this once
        # we get multiple announcement channels.
        (
            service_location != "APPR_STAT" or
            not config["announcements_enabled"]["arrivals_next_train"] or
            not config["arrivals_next_train"]["platform_alterations"] or
            not should_announce_realtime(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        ) and
        (
            service_location != "APPR_PLAT" or
            not config["announcements_enabled"]["arrivals_now_approaching"] or
            not config["arrivals_now_approaching"]["platform_alterations"] or
            not should_announce_realtime(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        ) and
        (
            service_location or
            (uid, run_date) not in service_last_announcement or
            not service_last_announcement.get((uid, run_date))[
                "service_location"
            ] or
            not config["announcements_enabled"]["arrivals_now_standing"] or
            not config["arrivals_now_standing"]["platform_alterations"] or
            not should_announce_realtime(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        )
    )


def assoc_service_has_location(
    service: dict,
    services: list[dict]
) -> bool:
    for assoc in service["locationDetail"]["associations"]:
        if assoc["type"] == "divide":
            for other_service in services:
                if (
                    other_service["serviceUid"] == assoc["associatedUid"] and
                    other_service["runDate"] == assoc["associatedRunDate"]
                ):
                    return "serviceLocation" in other_service["locationDetail"]

    return False


# Note: for now, just one function for all realtime announcements, as the type
# of realtime announcement to be made can be determined fairly trivially, and
# there should be strictly zero or one per train per loop. This is with the
# exception of TRUST-triggered which are impossible to distinguish without
# looking back at service_last_announcement, and so get their own function.
# Also repeated now_standing announcements get their own script but again can't
# be easily distinguished so also get their own function.
def should_announce_realtime(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime,
    services: list[dict]
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    service_location = service["locationDetail"].get("serviceLocation")
    display_as = service["locationDetail"]["displayAs"]
    platform = service["locationDetail"].get("platform")
    realtime_arr_actual = (
        service["locationDetail"].get("realtimeArrivalActual")
    )
    plat_actual = service["locationDetail"].get("platformConfirmed")
    realtime_dep_actual = (
        service["locationDetail"].get("realtimeDepartureActual")
    )
    if service["locationDetail"].get("realtimeDepartureNoReport"):
        realtime_dep_actual = True

    booked_hour, booked_minute = get_booked_hour_minute(service, now)

    now_to_booked = time_diff(booked_hour, booked_minute, now)

    return (
        (
            (
                is_departing(service) and
                config["announcements_enabled"]["departures_next_train"] and
                service_location == "APPR_STAT" and
                (
                    platform or
                    config["departures_next_train"]["no_platform"]
                )
            ) or
            (
                is_arriving(service) and
                config["announcements_enabled"]["arrivals_next_train"] and
                service_location == "APPR_STAT" and
                (
                    platform or
                    config["arrivals_next_train"]["no_platform"]
                )
            ) or
            (
                is_departing(service) and
                config["announcements_enabled"][
                    "departures_now_approaching"
                ] and
                service_location == "APPR_PLAT" and
                (
                    platform or
                    config["departures_now_approaching"]["no_platform"]
                )
            ) or
            (
                is_arriving(service) and
                config["announcements_enabled"]["arrivals_now_approaching"] and
                service_location == "APPR_PLAT" and
                (
                    platform or
                    config["arrivals_now_approaching"]["no_platform"]
                )
            ) or
            (
                is_departing(service) and
                config["announcements_enabled"]["departures_now_standing"] and
                (
                    service_location == "AT_PLAT" or
                    (
                        not service_location and
                        (uid, run_date) in service_last_announcement and
                        service_last_announcement.get((uid, run_date))[
                            "service_location"
                        ] and
                        not realtime_dep_actual
                    )
                ) and
                (
                    config["departures_now_standing"][
                        "always_announce_before"
                    ] or
                    now_to_booked <=
                    config["departures_now_standing"]["minutes_before"]
                ) and
                (
                    platform or
                    config["departures_now_standing"]["no_platform"]
                )
            ) or
            (
                is_arriving(service) and
                config["announcements_enabled"]["arrivals_now_standing"] and
                not service_location and
                (uid, run_date) in service_last_announcement and
                service_last_announcement.get((uid, run_date))[
                    "service_location"
                ] and
                (
                    platform or
                    config["arrivals_now_standing"]["no_platform"]
                )
            )
        ) and
        (
            (uid, run_date) not in service_last_announcement or
            service_location != service_last_announcement[
                (uid, run_date)
            ]["service_location"]
        ) and
        (
            display_as != "ORIGIN" or
            "associations" not in service["locationDetail"] or
            "divide" not in [
                assoc["type"] for
                assoc in service["locationDetail"]["associations"]
            ] or
            not assoc_service_has_location(service, services)
        )
    )


def should_announce_realtime_repeat(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime,
    services: list[dict]
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    service_location = service["locationDetail"].get("serviceLocation")
    display_as = service["locationDetail"]["displayAs"]
    platform = service["locationDetail"].get("platform")

    booked_hour, booked_minute = get_booked_hour_minute(service, now)

    now_to_booked = time_diff(booked_hour, booked_minute, now)
    if (uid, run_date) in service_last_announcement:
        old_now_to_booked = service_last_announcement[(uid, run_date)][
            "now_to_booked"
        ]

    return (
        (
            is_departing(service) and
            config["announcements_enabled"]["departures_now_standing"] and
            service_location == "AT_PLAT" and
            now_to_booked <=
            config["departures_now_standing"]["minutes_before"] and
            (
                platform or
                config["departures_now_standing"]["no_platform"]
            )
        ) and
        # Some sanity to stop this returning true when we should also be doing
        # a realtime
        (uid, run_date) in service_last_announcement and
        service_location == service_last_announcement[(uid, run_date)][
            "service_location"
        ] and
        (
            (
                config["departures_now_standing"]["timed_announcements"] or
                not config["departures_now_standing"][
                    "always_announce_before"
                ] # if this is switched off, it won't have been announced
                  # first time. If another type of announcement caused this
                  # to be written to service_last_announcement it would
                  # then otherwise never be announced.
            ) and
            old_now_to_booked >
            config["departures_now_standing"]["minutes_before"]
        ) and
        (
            display_as != "ORIGIN" or
            "associations" not in service["locationDetail"] or
            "divide" not in [
                assoc["type"] for
                assoc in service["locationDetail"]["associations"]
            ] or
            not assoc_service_has_location(service, services)
        )
    )


def should_announce_realtime_trust_triggered(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime,
    services: list[dict]
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    service_location = service["locationDetail"].get("serviceLocation")
    display_as = service["locationDetail"]["displayAs"]
    platform = service["locationDetail"].get("platform")
    realtime_arr_actual = (
        service["locationDetail"].get("realtimeArrivalActual")
    )
    plat_actual = service["locationDetail"].get("platformConfirmed")
    realtime_dep_actual = (
        service["locationDetail"].get("realtimeDepartureActual")
    )
    if service["locationDetail"].get("realtimeDepartureNoReport"):
        realtime_dep_actual = True

    booked_hour, booked_minute = get_booked_hour_minute(service, now)

    now_to_booked = time_diff(booked_hour, booked_minute, now)

    return (
        not service_location and
        (
            (
                is_departing(service) and
                config["announcements_enabled"][
                    "departures_trust_triggered"
                ] and
                (realtime_arr_actual or plat_actual) and
                (
                    config["departures_trust_triggered"][
                        "always_announce_before"
                    ] or
                    now_to_booked <=
                    config["departures_trust_triggered"]["minutes_before"]
                ) and
                (
                    platform or
                    config["departures_trust_triggered"]["no_platform"]
                ) and
                not realtime_dep_actual
            ) or
            (
                is_arriving(service) and
                config["announcements_enabled"]["arrivals_trust_triggered"] and
                (realtime_arr_actual or plat_actual) and
                (
                    platform or
                    config["arrivals_trust_triggered"]["no_platform"]
                )
            )
        ) and
        (
            (uid, run_date) not in service_last_announcement or
            (
                (realtime_arr_actual or plat_actual) !=
                (
                    service_last_announcement[(uid, run_date)][
                        "realtime_arr_actual"
                    ] or
                    service_last_announcement[(uid, run_date)]["plat_actual"]
                ) and
                (
                    config["announcements_enabled"][
                        "departures_trust_triggered"
                    ] or
                    config["announcements_enabled"]["arrivals_trust_triggered"]
                )
            )
        ) and
        (
            display_as != "ORIGIN" or
            "associations" not in service["locationDetail"] or
            "divide" not in [
                assoc["type"] for
                assoc in service["locationDetail"]["associations"]
            ] or
            not assoc_service_has_location(service, services)
        )
    )


def should_announce_realtime_trust_triggered_repeat(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime,
    services: list[dict]
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    service_location = service["locationDetail"].get("serviceLocation")
    display_as = service["locationDetail"]["displayAs"]
    platform = service["locationDetail"].get("platform")
    realtime_arr_actual = (
        service["locationDetail"].get("realtimeArrivalActual")
    )
    plat_actual = service["locationDetail"].get("platformConfirmed")
    realtime_dep_actual = (
        service["locationDetail"].get("realtimeDepartureActual")
    )
    if service["locationDetail"].get("realtimeDepartureNoReport"):
        realtime_dep_actual = True

    booked_hour, booked_minute = get_booked_hour_minute(service, now)

    now_to_booked = time_diff(booked_hour, booked_minute, now)
    if (uid, run_date) in service_last_announcement:
        old_now_to_booked = service_last_announcement[(uid, run_date)][
            "now_to_booked"
        ]

    return (
        not service_location and
        (
            is_departing(service) and
            config["announcements_enabled"][
                "departures_trust_triggered"
            ] and
            (realtime_arr_actual or plat_actual) and
            now_to_booked <=
            config["departures_trust_triggered"]["minutes_before"] and
            (
                platform or
                config["departures_trust_triggered"]["no_platform"]
            ) and
            not realtime_dep_actual
        ) and
        (uid, run_date) not in service_last_announcement and
        (realtime_arr_actual or plat_actual) ==
        (
            service_last_announcement[(uid, run_date)][
                "realtime_arr_actual"
            ] or
            service_last_announcement[(uid, run_date)]["plat_actual"]
        ) and
        (
            (
                config["departures_trust_triggered"][
                    "timed_announcements"
                ] or
                not config["departures_trust_triggered"][
                    "always_announce_before"
                ] # if this is switched off, it won't have been announced
                  # first time. If another type of announcement caused this
                  # to be written to service_last_announcement it would
                  # then otherwise never be announced.
            ) and
            old_now_to_booked >
            config["departures_trust_triggered"]["minutes_before"]
        ) and
        (
            display_as != "ORIGIN" or
            "associations" not in service["locationDetail"] or
            "divide" not in [
                assoc["type"] for
                assoc in service["locationDetail"]["associations"]
            ] or
            not assoc_service_has_location(service, services)
        )
    )


def should_announce_departure_bus(
    config: dict,
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime
) -> bool:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    display_as = service["locationDetail"]["displayAs"]
    service_type = service["serviceType"]

    booked_hour, booked_minute = get_booked_hour_minute(service, now)

    now_to_booked = time_diff(booked_hour, booked_minute, now)
    if (uid, run_date) in service_last_announcement:
        old_now_to_booked = service_last_announcement[(uid, run_date)][
            "now_to_booked"
        ]

    return (
        is_departing(service) and
        service_type == "bus" and
        now_to_booked <= config["departures_bus"]["minutes_before"] and
        now_to_booked >= 0 and
        (
            (uid, run_date) not in service_last_announcement or
            old_now_to_booked > config["departures_bus"]["minutes_before"]
        )
    )


def update_service_last_announcement(
    service: dict,
    service_last_announcement: dict,
    now: datetime.datetime
) -> None:
    uid = service["serviceUid"]
    run_date = service["runDate"]
    service_location = service["locationDetail"].get("serviceLocation")
    display_as = service["locationDetail"]["displayAs"]
    platform_alteration = service["locationDetail"].get("platformChanged")
    realtime_arr_actual = (
        service["locationDetail"].get("realtimeArrivalActual")
    )
    plat_actual = service["locationDetail"].get("platformConfirmed")

    booked_hour, booked_minute = get_booked_hour_minute(service, now)
    realtime_hour, realtime_minute = get_realtime_hour_minute(service, now)

    now_to_booked = time_diff(booked_hour, booked_minute, now)

    delay = get_delay(
        realtime_hour,
        realtime_minute,
        booked_hour,
        booked_minute
    )

    service_last_announcement[(uid, run_date)] = {
        "service_location": service_location,
        "now_to_booked": now_to_booked,
        "delay": delay,
        "platform_alteration": platform_alteration,
        "is_cancel": display_as in ("TERMINATES", "CANCELLED_CALL"),
        "realtime_arr_actual": realtime_arr_actual,
        "plat_actual": plat_actual,
    }


def extract_crs(config: dict, location: dict) -> tuple[str, str]:
    crs = None
    if "crs" in location:
        crs = location["crs"]
    elif not config["general"]["repeat_missing_announcement"]:
        crs = "XXX"
    if not crs:
        crs = "XXX"
    orig_crs = crs
    if crs in station_map[config["general"]["voice"]]:
        crs = station_map[config["general"]["voice"]][crs]
    return crs, orig_crs


ORIGINAL = 0
DIVIDING_PORTION = 1
JOINING_PORTION = 2
JOINING_MAIN_TRAIN = 3


def check_add_origin(
    location: dict,
    crs: str,
    what: int,
    origins: list[str]
) -> None:
    if location["displayAs"] in ("STARTS", "ORIGIN"):
        if what != DIVIDING_PORTION and what != JOINING_MAIN_TRAIN:
            origins.append(crs)


def check_add_destination(
    location: dict,
    crs: str,
    what: int,
    later_cancelled: bool,
    destinations: list[str]
) -> tuple[str, bool]:
    if location["displayAs"] in ("TERMINATES", "DESTINATION"):
        if (
            what != JOINING_PORTION and
            not later_cancelled and
            (
                location["displayAs"] != "DESTINATION" or
                "associations" not in location or
                "join" not in [
                    assoc["type"] for assoc in location["associations"]
                ]
            )
        ):
            destinations.append(crs)
            if location["displayAs"] == "TERMINATES":
                return location.get("cancelReasonCode"), True

    return None, False


def handle_divisions(
    config: dict,
    location: dict,
    what: int,
    divides: bool,
    uids_seen: set[str],
    all_calling_points: dict,
    trains_to_check: list[tuple]
) -> tuple[typing.Optional[list[str]], typing.Optional[str]]:
    list_to_write = None
    later_cancel_reason = None
    if (
        "associations" in location and
        location["displayAs"] != "ORIGIN"
    ):
        for assoc in location["associations"]:
            if assoc["type"] == "divide":
                logging.info("Divides")

                uid = assoc["associatedUid"]

                if uid in uids_seen:
                    continue

                uids_seen.add(uid)
                dividing_train_content = fetch_train_content_by_uid(
                    config,
                    uid,
                    assoc["associatedRunDate"]
                )

                pp = pprint.PrettyPrinter(indent=4)
                logging.debug(pp.pformat(dividing_train_content))

                # Possible with some divide-to-ECS
                if "locations" not in dividing_train_content:
                    continue

                # We now need to check that the new train is not cancelled
                if (
                    dividing_train_content["locations"][0]["displayAs"] ==
                    "CANCELLED_CALL"
                ):
                    logging.info("Doesn't divide, is actually cancelled")
                    trains_to_check.append((
                        dividing_train_content,
                        all_calling_points["cancelled"],
                        DIVIDING_PORTION,
                        True
                    ))
                    later_cancel_reason = (
                        dividing_train_content["locations"][0].get(
                            "cancelReasonCode"
                        )
                    )
                    continue

                assoc_list_to_write = all_calling_points["rear"]
                if divides:
                    # in this case, the front portion divides
                    # again so we are still the front, we now
                    # need to write the middle
                    if what == ORIGINAL:
                        # the new middle portion will get seeded
                        # from this as calling points up to the
                        # second division point will be the
                        # same; Amey didn't announce two
                        # division points
                        all_calling_points["middle"] = (
                            all_calling_points["front"].copy()
                        )
                        assoc_list_to_write = all_calling_points["middle"]
                    else:
                        # we will continue writing to this as
                        # this is now the middle portion
                        all_calling_points["middle"] = (
                            all_calling_points["rear"]
                        )
                        # the new rear portion will get seeded
                        # from this as calling points up to the
                        # second division point will be the
                        # same; Amey didn't announce two
                        # division points
                        all_calling_points["rear"] = (
                            all_calling_points["rear"].copy()
                        )
                        assoc_list_to_write = all_calling_points["rear"]
                else:
                    list_to_write = all_calling_points["front"]

                divides = True

                trains_to_check.append((
                    dividing_train_content,
                    assoc_list_to_write,
                    DIVIDING_PORTION,
                    False
                ))

    return list_to_write, later_cancel_reason


def handle_pre_attachments(
    config: dict,
    location: dict,
    what: int,
    uids_seen: set[str],
    trains_to_check: list[tuple]
) -> bool:
    done_pre_attachment = False
    # This is better handled as a main train attachment
    if location["displayAs"] == "DESTINATION":
        return done_pre_attachment

    if "associations" in location:
        for assoc in location["associations"]:
            if assoc["type"] == "join":
                logging.info("Joins")
                uid = assoc["associatedUid"]

                if uid in uids_seen:
                    continue

                uids_seen.add(uid)

                joining_train_content = fetch_train_content_by_uid(
                    config,
                    uid,
                    assoc["associatedRunDate"]
                )

                pp = pprint.PrettyPrinter(indent=4)
                logging.debug(pp.pformat(joining_train_content))

                trains_to_check.append((
                    joining_train_content,
                    None,
                    JOINING_PORTION,
                    False
                ))

                done_pre_attachment = True
    
    return done_pre_attachment


def handle_main_train_attachments(
    config: dict,
    service: dict,
    location: dict,
    what: int,
    uids_seen: set[str],
    list_to_write: list[str],
    trains_to_check: list[tuple]
) -> bool:
    joins_main_train = False
    if location["displayAs"] != "DESTINATION":
        return joins_main_train

    if "associations" in location:
        for assoc in location["associations"]:
            if assoc["type"] == "join":
                logging.info("Joins")
                uid = assoc["associatedUid"]

                if uid in uids_seen:
                    continue

                uids_seen.add(uid)

                joining_train_content = fetch_train_content_by_uid(
                    config,
                    uid,
                    assoc["associatedRunDate"]
                )

                pp = pprint.PrettyPrinter(indent=4)
                logging.debug(pp.pformat(joining_train_content))

                # Possible with some divide-to-ECS
                if "locations" not in joining_train_content:
                    continue

                # We need to check if the joining train also terminates here,
                # as we might have the wrong one.
                our_uid = service["serviceUid"]
                last_loc = joining_train_content["locations"][-1]
                if (
                    last_loc["crs"] == location["crs"] and
                    "associations" in last_loc and
                    our_uid in [
                        assoc["associatedUid"] for
                        assoc in last_loc["associations"] if
                        assoc["type"] == "join"
                    ]
                ):
                    continue

                trains_to_check.append((
                    joining_train_content,
                    list_to_write,
                    JOINING_MAIN_TRAIN,
                    False
                ))

                joins_main_train = True

    return joins_main_train


def calculate_calling_points(
    config: dict,
    service: dict,
    train_content: dict
) -> tuple[dict, list[str], list[str], dict, dict]:
    uid = service["serviceUid"]

    reached_home = False
    divides_here = False
    joins_here = False
    joins_main_train = False
    joining_train_here_departs = None
    divides = False
    # we have no way of knowing from RTT which is front/middle/rear, so
    # naively assume they go in order.
    all_calling_points = {
        "whole_train": [],
        "cancelled": [],
        "rear": [],
        "middle": [],
        "front": []
    }

    later_cancel_reason = None

    destinations = []
    origins = []

    trains_to_check = [
        (train_content, all_calling_points["whole_train"], ORIGINAL, False)
    ]

    uids_seen = {uid}

    new_list_to_write = None

    for (
        train_to_check,
        list_to_write,
        what,
        later_cancelled
    ) in trains_to_check:
        # we need to always skip writing the first location even though we
        # should apply the rest of the logic to it
        if what == JOINING_MAIN_TRAIN:
            found_joining_station = False
        if "locations" in train_to_check:
            locations = train_to_check["locations"]
        else:
            locations = []
        for location in locations:
            crs, orig_crs = extract_crs(config, location)

            check_add_origin(location, crs, what, origins)

            tmp_cancel_reason, tmp_later_cancelled = check_add_destination(
                location,
                crs,
                what,
                later_cancelled,
                destinations
            )
            if tmp_later_cancelled:
                later_cancel_reason = tmp_cancel_reason
                later_cancelled = True
                new_list_to_write = all_calling_points["cancelled"]

            if what == JOINING_MAIN_TRAIN and not found_joining_station:
                if "associations" in location:
                    for assoc in location["associations"]:
                        if assoc["type"] == "join":
                            if assoc["associatedUid"] == uid:
                                found_joining_station = True
                                if joins_here:
                                    joining_train_here_departs = (
                                        location.get("gbttBookedDeparture")
                                    )
                continue

            if (
                orig_crs == config["general"]["station"] and
                not reached_home and
                location.get("gbttBookedDeparture") ==
                service["locationDetail"].get("gbttBookedDeparture")
            ):
                reached_home = True
                if not later_cancelled:
                    division_list_to_write, new_later_cancel_reason = (
                        handle_divisions(
                            config,
                            location,
                            what,
                            divides,
                            uids_seen,
                            all_calling_points,
                            trains_to_check
                        )
                    )
                    if new_later_cancel_reason:
                        later_cancel_reason = new_later_cancel_reason
                    if division_list_to_write is not None:
                        list_to_write = division_list_to_write
                        divides = True
                        divides_here = True

                if handle_main_train_attachments(
                    config,
                    service,
                    location,
                    what,
                    uids_seen,
                    list_to_write,
                    trains_to_check
                ):
                    joins_main_train = True
                    joins_here = True

                # we want to report if a pre-attachment happens here for "joins
                # here" purposes, but we don't want to actually write another
                # origin. In theory as each train arrives its own origin will
                # then be announced.
                if handle_pre_attachments(
                    config,
                    location,
                    what,
                    uids_seen,
                    []
                ):
                    joins_here = True
                continue
            if not reached_home or what == JOINING_PORTION:
                # Attaching trains here affect origin list, but nothing else.
                handle_pre_attachments(
                    config,
                    location,
                    what,
                    uids_seen,
                    trains_to_check
                )
                continue

            if "gbttBookedArrival" in location:
                list_to_write.append(crs)

            if handle_main_train_attachments(
                config,
                service,
                location,
                what,
                uids_seen,
                list_to_write,
                trains_to_check
            ):
                joins_main_train = True

            if not later_cancelled:
                division_list_to_write, new_later_cancel_reason = (
                    handle_divisions(
                        config,
                        location,
                        what,
                        divides,
                        uids_seen,
                        all_calling_points,
                        trains_to_check
                    )
                )
                if new_later_cancel_reason:
                    later_cancel_reason = new_later_cancel_reason
                if division_list_to_write is not None:
                    list_to_write = division_list_to_write
                    divides = True

            if new_list_to_write:
                list_to_write = new_list_to_write
                new_list_to_write = None

    division = {
        "divides": divides,
        "divides_here": divides_here,
        "joins_here": joins_here,
        "joins_main_train": joins_main_train,
        "joining_train_here_departs": joining_train_here_departs
    }

    cancellation = {
        "later_cancel_reason": later_cancel_reason
    }

    if config["general"]["reverse_division"]:
        all_calling_points["rear"], all_calling_points["front"] = (
            all_calling_points["front"], all_calling_points["rear"]
        )

    return (all_calling_points, origins, destinations, division, cancellation)


def destinations_valid(config: dict, destinations: list[str]) -> bool:
    if config["general"]["play_if_destination_unavailable"]:
        return True
    for destination in destinations:
        if not os.path.exists(os.path.join(
            config["system"]["path"],
            config["general"]["voice"],
            f"station/e/{destination}.wav"
        )):
            logging.info("Invalid destination, aborting")
            return False
    return True


def calculate_dep_time_from_booked_dep(booked_dep: str) -> tuple[str, str]:
    dep_hour = booked_dep[0:2]
    if dep_hour == "00":
        dep_hour = "00 - midnight"
    dep_min = booked_dep[2:]
    if dep_min == "00":
        dep_min = "00 - hundred-hours"

    return dep_hour, dep_min


def calculate_announcement_dep_time(service: dict) -> tuple[str, str]:
    booked_dep = service["locationDetail"].get("gbttBookedDeparture")
    if not booked_dep:
        booked_dep = service["locationDetail"].get("gbttBookedArrival")

    return calculate_dep_time_from_booked_dep(booked_dep)


def play_chime(
    config: dict,
    sub_config: dict,
    wavplayer: WavPlayer
) -> None:
    if sub_config["chime"]:
        num_chimes = (
            "three" if config["general"]["voice"] == "Female1" else "four"
        )
        wavplayer.play_wav(f"sfx - {num_chimes} chimes.wav")


def announce_cancellation(
    config: dict,
    train_content: dict,
    service: dict,
    wavplayer: WavPlayer
) -> None:
    logging.info("Cancel")
    dep_hour, dep_min = calculate_announcement_dep_time(service)
    cancel_reason = service["locationDetail"].get("cancelReasonCode")
    # TODO support portion working here?
    orig_destination = train_content["locations"][-1]["crs"]
    orig_origin = train_content["locations"][0]["crs"]

    booked_arr = service["locationDetail"].get("gbttBookedArrival")

    arrival = False
    if (
        orig_destination == config["general"]["station"] and
        booked_arr == train_content["locations"][-1].get("gbttBookedArrival")
    ):
        arrival = True

    if orig_destination in station_map[config["general"]["voice"]]:
        orig_destination = station_map[config["general"]["voice"]][
            orig_destination
        ]

    if orig_origin in station_map[config["general"]["voice"]]:
        orig_origin = station_map[config["general"]["voice"]][orig_origin]

    play_chime(config, config["cancellation"], wavplayer)

    if config["cancellation"]["apologise_before"]:
        wavplayer.play_wav("s/were sorry to announce that the.wav")
    else:
        wavplayer.play_wav("s/the.wav")
    announce_time_and_toc(
        config,
        config["departures_delay"],
        service,
        None,
        wavplayer,
        None,
        arrival
    )
    if arrival:
        wavplayer.play_wav(f"station/m/{orig_origin}.wav")
    else:
        wavplayer.play_wav(f"station/m/{orig_destination}.wav")
    if cancel_reason in cancel_map[config["general"]["voice"]]:
        if config["general"]["voice"] == "Female2":
            wavplayer.play_wav("e/has been cancelled.wav")
            wavplayer.play_wav("m/due to (old).wav")
        else:
            wavplayer.play_wav("m/has been cancelled due to.wav")
        announce_cancel_reason(config, cancel_reason, wavplayer)
        if arrival and not config["general"]["voice"] == "Female2":
            time.sleep(0.7)
            wavplayer.play_wav(
                "w/this train was due to terminate at this station.wav"
            )
        if config["cancellation"]["please_listen_reason"]:
            time.sleep(0.7)
            wavplayer.play_wav(
                "w/please listen for further announcements.wav"
            )
    else:
        wavplayer.play_wav("e/has been cancelled.wav")
        if arrival and not config["general"]["voice"] == "Female2":
            time.sleep(0.7)
            wavplayer.play_wav(
                "w/this train was due to terminate at this station.wav"
            )
        if config["cancellation"]["please_listen_no_reason"]:
            time.sleep(0.7)
            wavplayer.play_wav(
                "w/please listen for further announcements.wav"
            )

    if config["cancellation"]["apologise_after"]:
        time.sleep(0.7)
        if arrival or config["general"]["voice"] == "Female2":
            wavplayer.play_wav(
                "w/we apologise for the inconvenience caused.wav"
            )
        else:
            wavplayer.play_wav(
                "w/were sorry for the delay this will cause to your " +
                "journey.wav"
            )

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"])


def announce_delay_time(
    config: dict,
    delay: int,
    wavplayer: WavPlayer
) -> None:
    delay_hour = delay // 60
    delay_minute = delay % 60
    announced_is_delayed = False
    if delay_hour > 0:
        announced_is_delayed = True
        if config["general"]["voice"] == "Female2":
            # No "hours" for Alison so we can only do this
            if delay_hour > 1:
                wavplayer.play_wav("e/is delayed.wav")
            else:
                wavplayer.play_wav(
                    "e/is delayed by approximately 1 hour.wav"
                )
        else:
            wavplayer.play_wav("m/is delayed by approximately.wav")
            wavplayer.play_wav(f"platform/s/{delay_hour}.wav")
            style = "e" if delay_minute == 0 else "m"
            # Celia has no "e" hours
            if config["general"]["voice"] == "Female1":
                style = "m"
            if delay_hour > 1:
                wavplayer.play_wav(f"{style}/ours.wav")
            else:
                wavplayer.play_wav(f"{style}/our.wav")
            if delay_minute != 0:
                wavplayer.play_wav(f"m/and.wav")
    if delay_minute != 0 and (
        delay_hour <= 1 or config["general"]["voice"] != "Female2"
    ):
        if not announced_is_delayed:
            wavplayer.play_wav("m/is delayed by approximately.wav")
        if delay_minute <= 20:
            wavplayer.play_wav(f"platform/s/{delay_minute}.wav")
            if (
                delay_minute == 1 and
                config["general"]["voice"] != "Female2"
            ):
                wavplayer.play_wav("e/minute.wav")
            else:
                wavplayer.play_wav("e/minutes.wav")
        else:
            wavplayer.play_wav(f"mins/m/{delay_minute}.wav")
            wavplayer.play_wav("e/minutes.wav")


def announce_departure_delay(
    config: dict,
    service: dict,
    destinations: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    logging.info("Departure delay")
    booked_hour, booked_minute = get_booked_hour_minute(service, now)
    realtime_hour, realtime_minute = get_realtime_hour_minute(service, now)

    now_to_booked = time_diff(booked_hour, booked_minute, now)

    delay = get_delay(
        realtime_hour,
        realtime_minute,
        booked_hour,
        booked_minute
    )

    play_chime(config, config["departures_delay"], wavplayer)

    if (
        config["departures_delay"]["apologise_before_threshold"] > -1 and
        delay >= config["departures_delay"]["apologise_before_threshold"]
    ):
        wavplayer.play_wav("s/were sorry to announce that the.wav")
    else:
        wavplayer.play_wav("s/the.wav")
    announce_time_and_toc(
        config,
        config["departures_delay"],
        service,
        now,
        wavplayer
    )
    announce_destinations(destinations, False, wavplayer)
    if (delay + 1) < (-now_to_booked):
        wavplayer.play_wav("e/is being delayed (old).wav")
    else:
        announce_delay_time(config, delay, wavplayer)

    if config["departures_delay"]["please_listen_no_reason"]:
        time.sleep(0.7)
        wavplayer.play_wav("w/please listen for further announcements.wav")

    if (
        config["departures_delay"][
            "extremely_apologise_after_threshold"
        ] > -1 and
        delay >= config["departures_delay"][
            "extremely_apologise_after_threshold"
        ] and
        config["general"]["voice"] != "Female2"
    ):
        time.sleep(0.7)
        wavplayer.play_wav(
            "w/were extremely sorry for the severe delay to this service.wav"
        )
    elif (
        config["departures_delay"]["apologise_after_threshold"] > -1 and
        delay >= config["departures_delay"]["apologise_after_threshold"]
    ):
        time.sleep(0.7)
        if config["general"]["voice"] == "Female2":
            wavplayer.play_wav(
                "w/we apologise for the inconvenience caused.wav"
            )
        else:
            wavplayer.play_wav(
                "w/were sorry for the delay to this service.wav"
            )

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"])


def announce_arrival_delay(
    config: dict,
    service: dict,
    origins: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    logging.info("Arrival delay")
    booked_hour, booked_minute = get_booked_hour_minute(service, now)
    realtime_hour, realtime_minute = get_realtime_hour_minute(service, now)

    now_to_booked = time_diff(booked_hour, booked_minute, now)

    delay = get_delay(
        realtime_hour,
        realtime_minute,
        booked_hour,
        booked_minute
    )

    play_chime(config, config["arrivals_delay"], wavplayer)

    if (
        config["arrivals_delay"]["apologise_before_threshold"] > -1 and
        delay >= config["arrivals_delay"]["apologise_before_threshold"]
    ):
        wavplayer.play_wav("s/were sorry to announce that the.wav")
    else:
        wavplayer.play_wav("s/the.wav")
    announce_time_and_toc(
        config,
        config["arrivals_delay"],
        service,
        now,
        wavplayer,
        None,
        True
    )
    announce_destinations(origins, False, wavplayer)
    if (delay + 1) < (-now_to_booked):
        wavplayer.play_wav("e/is being delayed (old).wav")
    else:
        announce_delay_time(config, delay, wavplayer)

    if config["general"]["voice"] != "Female2":
        time.sleep(0.7)
        wavplayer.play_wav("w/this train will terminate here.wav")

    if config["arrivals_delay"]["please_listen_no_reason"]:
        time.sleep(0.7)
        wavplayer.play_wav("w/please listen for further announcements.wav")

    if (
        config["arrivals_delay"][
            "extremely_apologise_after_threshold"
        ] > -1 and
        delay >= config["arrivals_delay"][
            "extremely_apologise_after_threshold"
        ] and
        config["general"]["voice"] != "Female2"
    ):
        time.sleep(0.7)
        wavplayer.play_wav(
            "w/were extremely sorry for the severe delay to this service.wav"
        )
    elif (
        config["arrivals_delay"]["apologise_after_threshold"] > -1 and
        delay >= config["arrivals_delay"]["apologise_after_threshold"]
    ):
        time.sleep(0.7)
        if config["general"]["voice"] == "Female2":
            wavplayer.play_wav(
                "w/we apologise for the inconvenience caused.wav"
            )
        else:
            wavplayer.play_wav(
                "w/were sorry for the delay to this service.wav"
            )

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"])


def announce_departure_bus(
    config: dict,
    calling_points: list,
    wavplayer: WavPlayer
) -> None:
    logging.info("Bus")
    repeat_number = 1
    if config["departures_bus"]["repeat"]:
        repeat_number = 2
    replacement_bus_location = config["general"]["replacement_buses"]

    play_chime(config, config["departures_bus"], wavplayer)

    for i in range(repeat_number):
        if config["general"]["voice"] == "Female2":
            wavplayer.play_wav("s/customers for.wav")
        else:
            wavplayer.play_wav("s/any customers for.wav")
        if len(calling_points) == 1:
            wavplayer.play_wav(f"station/m/{calling_points[0]}.wav")
        else:
            # thankfully buses shouldn't divide lol
            for i in range(len(calling_points) - 2):
                calling_point = calling_points[i]
                wavplayer.play_wav(f"station/m/{calling_point}.wav")
                time.sleep(0.3)
            wavplayer.play_wav(f"station/m/{calling_points[-2]}.wav")
            time.sleep(0.1)
            wavplayer.play_wav("m/and.wav")
            time.sleep(0.1)
            wavplayer.play_wav(f"station/m/{calling_points[-1]}.wav")
        if config["general"]["voice"] == "Female2": # this is the best I can do
            wavplayer.play_wav(
                "s/there will be a special bus service in operation.wav"
            )
        else:
            wavplayer.play_wav(f"s/would you please make your way to the " +
                f"{replacement_bus_location} of the station.wav")
            wavplayer.play_wav("e/for a replacement bus service.wav")
        time.sleep(0.7)

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"] - 0.7)


def announce_destinations(
    destinations: str,
    end_of_sentence: bool,
    wavplayer: WavPlayer
) -> None:
    for i, destination in enumerate(destinations):
        if i == len(destinations) - 1 and end_of_sentence:
            wavplayer.play_wav(f"station/e/{destination}.wav")
        else:
            wavplayer.play_wav(f"station/m/{destination}.wav")
        if i == len(destinations) - 2:
            time.sleep(0.1)
            wavplayer.play_wav("m/and.wav")
            time.sleep(0.1)
        elif i < len(destinations) - 2:
            time.sleep(0.3)


def get_platform_and_int(service: dict) -> tuple[str, typing.Optional[int]]:
    platform = service["locationDetail"].get("platform")
    plat_int = None
    plat_letter = None
    if platform:
        platform = platform.lower()
        plat_int = int(''.join(c for c in platform if c.isdigit()))
        plat_letter = ''.join(c for c in platform if not c.isdigit())

    return platform, plat_int, plat_letter


def is_platform_zero(service: dict) -> bool:
    platform, plat_int, plat_letter = get_platform_and_int(service)
    return plat_int == 0


def announce_platform_number(
    config: dict,
    service: dict,
    end_of_sentence: bool,
    wavplayer: WavPlayer
) -> None:
    platform, plat_int, plat_letter = get_platform_and_int(service)

    style = "e" if end_of_sentence else "m"

    letter_style = style

    if style == "m" and (
        str(plat_int) == platform or
        plat_int > 12 or
        config["general"]["voice"] == "Female2"
    ) and plat_int < 21 and plat_int > 0:
        style = "s"

    if plat_int == 0:
        # Alison doesn't have a detached zero, so her platform 0 will be
        # handled in other code
        if config["general"]["voice"] != "Female2":
            if config["general"]["voice"] == "Male1":
                # Phil has no end-of-sentence 0
                style = "m"
            wavplayer.play_wav(f"{style}/0.wav")
            if str(plat_int) != platform:
                wavplayer.play_wav(
                    f"platform/{letter_style}/{plat_letter}.wav"
                )
    elif plat_int < 21:
        if (
            plat_int <= 12 and
            config["general"]["voice"] != "Female2"
        ) or str(plat_int) == platform:
            wavplayer.play_wav(f"platform/{style}/{platform}.wav")
        else:
            wavplayer.play_wav(f"platform/{style}/{plat_int}.wav")
            if config["general"]["voice"] != "Female2":
                wavplayer.play_wav(
                    f"platform/{letter_style}/{plat_letter}.wav"
                )
    else:
        if str(plat_int) == platform:
            wavplayer.play_wav(f"mins/{style}/{platform}.wav")
        else:
            wavplayer.play_wav(f"mins/{style}/{platform}.wav")
            if config["general"]["voice"] != "Female2":
                wavplayer.play_wav(
                    f"platform/{letter_style}/{plat_letter}.wav"
                )


def announce_time_and_toc(
    config: dict,
    sub_config: dict,
    service: dict,
    now: typing.Optional[datetime.datetime],
    wavplayer: WavPlayer,
    division: typing.Optional[dict] = None,
    service_from: bool = False,
) -> None:
    if now:
        booked_hour, booked_minute = get_booked_hour_minute(service, now)
        realtime_hour, realtime_minute = get_realtime_hour_minute(service, now)

        now_to_booked = time_diff(booked_hour, booked_minute, now)

        delay = get_delay(
            realtime_hour,
            realtime_minute,
            booked_hour,
            booked_minute
        )

    dep_hour, dep_min = calculate_announcement_dep_time(service)
    if division and division["joining_train_here_departs"]:
        dep_hour, dep_min = calculate_dep_time_from_booked_dep(
            division["joining_train_here_departs"]
        )
    toc_tuple = toc_map[config["general"]["voice"]].get(
        service.get("atocCode")
    )
    toc = None
    if toc_tuple:
        toc, integrated_service_from_to = toc_tuple

    delay_threshold = sub_config.get("delay_threshold")
    delayed = sub_config.get("delayed")

    if (
        delayed and
        (
            delay >= delay_threshold or now_to_booked <= -delay_threshold
        )
    ):
        wavplayer.play_wav("m/delayed.wav")
    if not division or not division["divides_here"]:
        wavplayer.play_wav(f"hour/s/{dep_hour}.wav")
        wavplayer.play_wav(f"mins/m/{dep_min}.wav")

    from_or_to = "from" if service_from else "to"

    if toc and sub_config["toc"]:
        if integrated_service_from_to:
            wavplayer.play_wav(f"toc/m/{toc} service {from_or_to}.wav")
        else:
            wavplayer.play_wav(f"toc/m/{toc}.wav")
            wavplayer.play_wav(f"m/service {from_or_to}.wav")
    else:
        wavplayer.play_wav(f"m/service {from_or_to}.wav")


def announce_departure_platform_alteration_intro(
    config: dict,
    sub_config: dict,
    service: dict,
    destinations: list[str],
    division: typing.Optional[dict],
    announce_attention: bool,
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    if announce_attention:
        wavplayer.play_wav("w/attention please.wav")
        time.sleep(0.7)
        wavplayer.play_wav("w/this is a platform alteration.wav")
        time.sleep(0.7)
    wavplayer.play_wav("s/the.wav")
    announce_time_and_toc(
        config,
        sub_config,
        service,
        now,
        wavplayer,
        division
    )
    announce_destinations(destinations, False, wavplayer)
    if config["general"]["voice"] == "Female2" and is_platform_zero(service):
        wavplayer.play_wav("m/will now depart from.wav")
        wavplayer.play_wav("e/platform 0.wav")
    else:
        wavplayer.play_wav("m/will now depart from platform.wav")
        announce_platform_number(config, service, True, wavplayer)


def announce_arrival_platform_alteration_intro(
    config: dict,
    sub_config: dict,
    service: dict,
    origins: list[str],
    announce_attention: bool,
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    if announce_attention:
        wavplayer.play_wav("w/attention please.wav")
        time.sleep(0.7)
        wavplayer.play_wav("w/this is a platform alteration.wav")
        time.sleep(0.7)
    wavplayer.play_wav("s/the.wav")
    announce_time_and_toc(
        config,
        sub_config,
        service,
        now,
        wavplayer,
        None,
        True
    )
    announce_destinations(origins, False, wavplayer)
    wavplayer.play_wav("m/will now arrive on platform.wav")
    announce_platform_number(config, service, True, wavplayer)


def announce_platform_intro(
    config: dict,
    sub_config: dict,
    service: dict,
    destinations: list[str],
    division: typing.Optional[dict],
    no_platform_files: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    platform, plat_int, plat_letter = get_platform_and_int(service)

    if platform:
        if config["general"]["voice"] == "Female2" and plat_int == 0:
            wavplayer.play_wav("e/platform 0.wav")
            wavplayer.play_wav("m/for the.wav")
        elif plat_int > 12 or plat_int < 1 or (
            config["general"]["voice"] == "Female2" and (
                plat_int > 8 or str(plat_int) != platform
            )
        ):
            wavplayer.play_wav("s/platform.wav")
            announce_platform_number(config, service, False, wavplayer)
            wavplayer.play_wav("m/for the.wav")
        else:
            wavplayer.play_wav(f"s/platform {platform} for the.wav")
    else:
        for no_platform_file in no_platform_files:
            wavplayer.play_wav(no_platform_file)

    announce_time_and_toc(
        config,
        sub_config,
        service,
        now,
        wavplayer,
        division
    )
    announce_destinations(destinations, True, wavplayer)


def announce_departure_platform_alteration(
    config: dict,
    service: dict,
    destinations: list[str],
    division: dict,
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    logging.info("Platform alteration")

    play_chime(config, config["departures_platform_alteration"], wavplayer)

    announce_departure_platform_alteration_intro(
        config,
        config["departures_platform_alteration"],
        service,
        destinations,
        division,
        True,
        now,
        wavplayer
    )

    if config["departures_platform_alteration"]["repeat"]:
        time.sleep(0.7)
        announce_platform_intro(
            config,
            config["departures_platform_alteration"],
            service,
            destinations,
            division,
            None,
            now,
            wavplayer
        )

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"])


def announce_arrival_platform_alteration(
    config: dict,
    service: dict,
    origins: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    logging.info("Platform alteration")

    play_chime(config, config["arrivals_platform_alteration"], wavplayer)

    announce_arrival_platform_alteration_intro(
        config,
        config["arrivals_platform_alteration"],
        service,
        origins,
        True,
        now,
        wavplayer
    )

    if config["general"]["voice"] != "Female2":
        time.sleep(0.7)
        wavplayer.play_wav("w/this train will terminate here.wav")

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"])


def announce_realtime_arrival_next_train_intro(
    config: dict,
    service: dict,
    origins: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    platform, plat_int, plat_letter = get_platform_and_int(service)
    platform_alteration = service["locationDetail"].get("platformChanged")

    to_arrive = (
        "to arrive " if config["arrivals_next_train"]["to_arrive"] else ""
    )

    logging.info("Approaching station realtime")

    play_chime(config, config["arrivals_next_train"], wavplayer)

    if (
        platform_alteration and
        config["arrivals_next_train"]["platform_alterations"]
    ):
        announce_arrival_platform_alteration_intro(
            config,
            config["arrivals_next_train"],
            service,
            origins,
            True,
            now,
            wavplayer
        )
    elif platform:
        if (
            plat_int > 12 or
            plat_int < 1 or
            str(plat_int) != platform
        ):
            wavplayer.play_wav(f"s/the next train {to_arrive}at platform.wav")
            announce_platform_number(config, service, False, wavplayer)
        else:
            wavplayer.play_wav(
                f"s/the next train {to_arrive}at platform {platform}.wav"
            )

        time.sleep(0.3)
        wavplayer.play_wav("e/terminates here.wav")
        if config["arrivals_next_train"]["service_from"]:
            time.sleep(0.7)
            wavplayer.play_wav("s/this train is the service from.wav")
            announce_destinations(origins, True, wavplayer)
    else:
        if to_arrive:
            wavplayer.play_wav("s/the next train to arrive at.wav")
            wavplayer.play_wav("m/this station.wav")
            time.sleep(0.3)
            wavplayer.play_wav("e/terminates here.wav")
        else:
            wavplayer.play_wav("w/the next train terminates here.wav")
        if config["arrivals_next_train"]["service_from"]:
            time.sleep(0.7)
            wavplayer.play_wav("s/this train is the service from.wav")
            announce_destinations(origins, True, wavplayer)


def announce_realtime_arrival_trust_triggered_intro(
    config: dict,
    service: dict,
    origins: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    platform, plat_int, plat_letter = get_platform_and_int(service)
    platform_alteration = service["locationDetail"].get("platformChanged")

    logging.info("TRUST triggered")

    play_chime(config, config["arrivals_trust_triggered"], wavplayer)

    if (
        platform_alteration and
        config["arrivals_trust_triggered"]["platform_alterations"]
    ):
        announce_arrival_platform_alteration_intro(
            config,
            config["arrivals_trust_triggered"],
            service,
            origins,
            True,
            now,
            wavplayer
        )
    elif platform:
        if (
            plat_int > 12 or
            plat_int < 1 or
            str(plat_int) != platform
        ):
            wavplayer.play_wav(f"s/the next train at platform.wav")
            announce_platform_number(config, service, False, wavplayer)
        else:
            wavplayer.play_wav(
                f"s/the next train at platform {platform}.wav"
            )

        time.sleep(0.3)
        wavplayer.play_wav("e/terminates here.wav")
        if config["arrivals_trust_triggered"]["service_from"]:
            time.sleep(0.7)
            wavplayer.play_wav("s/this train is the service from.wav")
            announce_destinations(origins, True, wavplayer)
    else:
        wavplayer.play_wav("w/the next train terminates here.wav")
        if config["arrivals_trust_triggered"]["service_from"]:
            time.sleep(0.7)
            wavplayer.play_wav("s/this train is the service from.wav")
            announce_destinations(origins, True, wavplayer)


def announce_realtime_arrival_now_approaching_intro(
    config: dict,
    service: dict,
    origins: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    platform, plat_int, plat_letter = get_platform_and_int(service)
    platform_alteration = service["locationDetail"].get("platformChanged")

    logging.info("Approaching platform realtime")

    play_chime(config, config["arrivals_now_approaching"], wavplayer)

    if (
        platform_alteration and
        config["arrivals_now_approaching"]["platform_alterations"]
    ):
        announce_arrival_platform_alteration_intro(
            config,
            config["arrivals_now_approaching"],
            service,
            origins,
            True,
            now,
            wavplayer
        )
    elif platform:
        if (
            plat_int > 20 or
            plat_int < 1 or
            str(plat_int) != platform
        ):
            wavplayer.play_wav("s/the train now approaching platform.wav")
            announce_platform_number(config, service, False, wavplayer)
        else:
            wavplayer.play_wav(
                f"s/the train now approaching platform {platform}.wav"
            )

        wavplayer.play_wav("e/terminates here.wav")
        if config["arrivals_now_approaching"]["service_from"]:
            time.sleep(0.7)
            wavplayer.play_wav("s/this train is the service from.wav")
            announce_destinations(origins, True, wavplayer)
    else:
        wavplayer.play_wav("s/the train now approaching terminates here.wav")
        if config["arrivals_now_approaching"]["service_from"]:
            time.sleep(0.7)
            wavplayer.play_wav("s/this train is the service from.wav")
            announce_destinations(origins, True, wavplayer)


def announce_this_is(
    config: dict,
    sub_config: dict,
    service: dict,
    wavplayer: WavPlayer
) -> None:
    display_as = service["locationDetail"]["displayAs"]
    station_announce = config["general"]["station"]
    if station_announce in station_map[config["general"]["voice"]]:
        station_announce = station_map[config["general"]["voice"]][
            station_announce
        ]

    if not sub_config["this_is"]:
        return

    if (
        display_as not in ("STARTS", "ORIGIN") or
        sub_config.get("this_is_origin")
    ):
        wavplayer.play_wav(f"station/m/{station_announce}.wav")
        wavplayer.play_wav("s/this is.wav")
        wavplayer.play_wav(f"station/e/{station_announce}.wav")
        time.sleep(0.7)


def announce_realtime_arrival_now_standing_intro(
    config: dict,
    service: dict,
    origins: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    platform, plat_int, plat_letter = get_platform_and_int(service)
    platform_alteration = service["locationDetail"].get("platformChanged")

    logging.info("At platform realtime")

    play_chime(config, config["arrivals_now_standing"], wavplayer)

    announce_this_is(
        config,
        config["arrivals_now_standing"],
        service,
        wavplayer
    )

    if (
        platform_alteration and
        config["arrivals_now_standing"]["platform_alterations"]
    ):
        announce_arrival_platform_alteration_intro(
            config,
            config["arrivals_now_standing"],
            service,
            origins,
            True,
            now,
            wavplayer
        )
    elif platform:
        wavplayer.play_wav("s/the train now standing at platform.wav")
        announce_platform_number(config, service, False, wavplayer)
        wavplayer.play_wav("e/terminates here.wav")
        if config["arrivals_now_standing"]["service_from"]:
            time.sleep(0.7)
            wavplayer.play_wav("s/this train is the service from.wav")
            announce_destinations(origins, True, wavplayer)

    else:
        wavplayer.play_wav(
            "w/the train now standing at this station terminates here.wav"
        )
        if config["arrivals_now_standing"]["service_from"]:
            time.sleep(0.7)
            wavplayer.play_wav("s/this train is the service from.wav")
            announce_destinations(origins, True, wavplayer)


def announce_realtime_arrival(
    config: dict,
    service: dict,
    origins: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    service_location = service["locationDetail"].get("serviceLocation")

    logging.info("Doing arrivals")
    if service_location == "APPR_STAT":
        announce_realtime_arrival_next_train_intro(
            config,
            service,
            origins,
            now,
            wavplayer
        )
        sub_config = config["arrivals_next_train"]

    elif service_location == "APPR_PLAT":
        announce_realtime_arrival_now_approaching_intro(
            config,
            service,
            origins,
            now,
            wavplayer
        )
        sub_config = config["arrivals_now_approaching"]

    else:
        announce_realtime_arrival_now_standing_intro(
            config,
            service,
            origins,
            now,
            wavplayer
        )
        sub_config = config["arrivals_now_standing"]

    if sub_config["all_change"]:
        time.sleep(0.7)
        wavplayer.play_wav("w/all change please all change.wav")

    if sub_config["repeat_terminates"]:
        time.sleep(0.7)
        wavplayer.play_wav("w/this train terminates here.wav")

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"])


def announce_realtime_arrival_trust_triggered(
    config: dict,
    service: dict,
    origins: list[str],
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    announce_realtime_arrival_trust_triggered_intro(
        config,
        service,
        origins,
        now,
        wavplayer
    )
    sub_config = config["arrivals_trust_triggered"]

    if sub_config["all_change"]:
        time.sleep(0.7)
        wavplayer.play_wav("w/all change please all change.wav")

    if sub_config["repeat_terminates"]:
        time.sleep(0.7)
        wavplayer.play_wav("w/this train terminates here.wav")

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"])


def announce_cancel_reason(
    config: dict,
    cancel_reason: str,
    wavplayer: WavPlayer
) -> None:
    for i, reason_sub in enumerate(
        cancel_map[config["general"]["voice"]][cancel_reason]
    ):
        if "/" in reason_sub:
            # allow non-cancellation-reason announcements
            wavplayer.play_wav(reason_sub)
        elif i == len(
            cancel_map[config["general"]["voice"]][cancel_reason]
        ) - 1:
            wavplayer.play_wav(f"disruption-reason/e/{reason_sub}.wav")
        else:
            wavplayer.play_wav(f"disruption-reason/m/{reason_sub}.wav")


def announce_calling_points(
    config,
    sub_config: dict,
    all_calling_points: dict,
    division: dict,
    cancellation: dict,
    wavplayer: WavPlayer
) -> None:
    calling_points = all_calling_points["whole_train"]
    cancelled_calling_points = all_calling_points["cancelled"]
    later_cancel_reason = cancellation["later_cancel_reason"]

    if not sub_config["calling_points"]:
        return

    time.sleep(0.7)
    if division["divides_here"] and config["general"]["voice"] != "Female2":
        # I have to get this right because both are fairly distinctive
        # announcements and I'll feel bad if I don't
        if config["general"]["voice"] == "Male1":
            wavplayer.play_wav("w/this train divides here-2.wav")
        else:
            wavplayer.play_wav("w/this train divides here.wav")
    else:
        wavplayer.play_wav("m/calling at.wav")
        if len(calling_points) == 1:
            wavplayer.play_wav(f"station/m/{calling_points[0]}.wav")
            if not division["divides"]:
                wavplayer.play_wav("e/only.wav")
        elif len(calling_points) != 0:
            for i in range(len(calling_points) - 2):
                calling_point = calling_points[i]
                wavplayer.play_wav(f"station/m/{calling_point}.wav")
                time.sleep(0.3)
            wavplayer.play_wav(f"station/m/{calling_points[-2]}.wav")
            time.sleep(0.1)
            wavplayer.play_wav("m/and.wav")
            time.sleep(0.1)
            if division["divides"]:
                wavplayer.play_wav(f"station/m/{calling_points[-1]}.wav")
            else:
                wavplayer.play_wav(f"station/e/{calling_points[-1]}.wav")
        if division["divides"] and config["general"]["voice"] != "Female2":
            wavplayer.play_wav("e/where the train will divide.wav")

    if division["divides"] and config["general"]["voice"] != "Female2":
        time.sleep(0.7)
        wavplayer.play_wav("s/please make sure you travel.wav")
        wavplayer.play_wav("e/in the correct part of this train.wav")
        for portion in ("front", "middle", "rear"):
            portion_calling_points = all_calling_points[portion]
            if portion_calling_points:
                time.sleep(0.7)
                wavplayer.play_wav("s/customers for.wav")
                if len(portion_calling_points) == 1:
                    wavplayer.play_wav(
                        f"station/m/{portion_calling_points[0]}.wav"
                    )
                else:
                    for i in range(len(portion_calling_points) - 2):
                        calling_point = portion_calling_points[i]
                        wavplayer.play_wav(f"station/m/{calling_point}.wav")
                        time.sleep(0.3)
                    wavplayer.play_wav(
                        f"station/m/{portion_calling_points[-2]}.wav"
                    )
                    time.sleep(0.1)
                    wavplayer.play_wav("m/and.wav")
                    time.sleep(0.1)
                    wavplayer.play_wav(
                        f"station/m/{portion_calling_points[-1]}.wav"
                    )
                wavplayer.play_wav(
                    f"e/should travel in the {portion} " +
                    "coaches of the train.wav"
                )
    if cancelled_calling_points:
        time.sleep(0.7)
        if config["general"]["voice"] == "Female2":
            wavplayer.play_wav(
                "s/please note that this train will not call at.wav"
            )
        else:
            wavplayer.play_wav("s/please note this train will not call at.wav")
        if len(cancelled_calling_points) == 1:
            wavplayer.play_wav(f"station/m/{cancelled_calling_points[0]}.wav")
        else:
            for i in range(len(cancelled_calling_points) - 2):
                calling_point = cancelled_calling_points[i]
                wavplayer.play_wav(f"station/m/{calling_point}.wav")
                time.sleep(0.3)
            wavplayer.play_wav(f"station/m/{cancelled_calling_points[-2]}.wav")
            time.sleep(0.1)
            wavplayer.play_wav("m/and.wav")
            time.sleep(0.1)
            wavplayer.play_wav(f"station/m/{cancelled_calling_points[-1]}.wav")
        if config["general"]["voice"] != "Female2":
            wavplayer.play_wav("e/today.wav")
        if later_cancel_reason in cancel_map[config["general"]["voice"]]:
            if config["general"]["voice"] == "Female2":
                wavplayer.play_wav("m/due to (old).wav")
            else:
                time.sleep(0.7)
                wavplayer.play_wav("s/this is due to.wav")
            announce_cancel_reason(config, later_cancel_reason, wavplayer)


def announce_realtime_departure_next_train_intro(
    config: dict,
    sub_config: dict,
    service: dict,
    destinations: list[str],
    division: dict,
    announce_attention: bool,
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    platform_alteration = service["locationDetail"].get("platformChanged")
    platform, plat_int, plat_letter = get_platform_and_int(service)

    if (
        platform_alteration and
        sub_config["platform_alterations"]
    ):
        announce_departure_platform_alteration_intro(
            config,
            sub_config,
            service,
            destinations,
            division,
            announce_attention,
            now,
            wavplayer
        )
    else:
        if sub_config["the_next_train_script"]:
            if platform:
                if (
                    plat_int > 12 or
                    plat_int < 1 or
                    str(plat_int) != platform or (
                        config["general"]["voice"] == "Female2" and
                        plat_int > 8
                    )
                ):
                    wavplayer.play_wav("s/the next train at platform.wav")
                    # Bug: no isolated "zero" so if it's zero we should just
                    # say "platform 0" as silly as it sounds
                    if (
                        config["general"]["voice"] == "Female2" and
                        is_platform_zero(service)
                    ):
                        wavplayer.play_wav("e/platform 0.wav")
                    else:
                        announce_platform_number(
                            config,
                            service,
                            False,
                            wavplayer
                        )
                    wavplayer.play_wav("m/is the.wav")
                else:
                    if config["general"]["voice"] == "Female2":
                        wavplayer.play_wav(
                            f"s/the next train at platform {platform} " +
                            "is the.wav"
                        )
                    else:
                        wavplayer.play_wav(
                            f"s/the next train at platform {platform}.wav"
                        )
                        wavplayer.play_wav("m/is the.wav")
            else:
                wavplayer.play_wav("s/the next train is the.wav")


            announce_time_and_toc(
                config,
                sub_config,
                service,
                now,
                wavplayer,
                division
            )
            announce_destinations(destinations, True, wavplayer)
        else:
            announce_platform_intro(
                config,
                sub_config,
                service,
                destinations,
                division,
                ["s/the next train is the.wav"],
                now,
                wavplayer
            )


def announce_realtime_departure_now_approaching_intro(
    config: dict,
    sub_config: dict,
    service: dict,
    destinations: list[str],
    division: dict,
    announce_attention: bool,
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    platform_alteration = service["locationDetail"].get("platformChanged")
    platform, plat_int, plat_letter = get_platform_and_int(service)

    if (
        platform_alteration and
        sub_config["platform_alterations"]
    ):
        announce_departure_platform_alteration_intro(
            config,
            sub_config,
            service,
            destinations,
            division,
            announce_attention,
            now,
            wavplayer
        )
    else:
        if sub_config["the_train_now_approaching_script"]:
            if platform:
                if (
                    plat_int > 20 or
                    plat_int < 1 or
                    str(plat_int) != platform or (
                        config["general"]["voice"] == "Female2" and
                        plat_int > 8
                    )
                ):
                    if (
                        config["general"]["voice"] == "Female2" and
                        is_platform_zero(service)
                    ):
                        wavplayer.play_wav("s/the train now approaching.wav")
                        wavplayer.play_wav("e/platform 0.wav")
                    else:
                        wavplayer.play_wav(
                            "s/the train now approaching platform.wav"
                        )
                        announce_platform_number(
                            config,
                            service,
                            False,
                            wavplayer
                        )
                else:
                    wavplayer.play_wav(
                        f"s/the train now approaching platform {platform}.wav"
                    )
                wavplayer.play_wav("m/is the.wav")
            else:
                if config["general"]["voice"] == "Female2":
                    wavplayer.play_wav("s/the train now approaching.wav")
                    wavplayer.play_wav("m/is the.wav")
                else:
                    wavplayer.play_wav(
                        "s/the train now approaching is the.wav"
                    )

            announce_time_and_toc(
                config,
                sub_config,
                service,
                now,
                wavplayer,
                division
            )
            announce_destinations(destinations, True, wavplayer)
        else:
            if config["general"]["voice"] == "Female2":
                announce_platform_intro(
                    config,
                    sub_config,
                    service,
                    destinations,
                    division,
                    ["s/the train now approaching.wav", "m/is the.wav"],
                    now,
                    wavplayer
                )
            else:
                announce_platform_intro(
                    config,
                    sub_config,
                    service,
                    destinations,
                    division,
                    ["s/the train now approaching is the.wav"],
                    now,
                    wavplayer
                )


def announce_realtime_departure_now_standing_intro(
    config: dict,
    sub_config: dict,
    service: dict,
    destinations: list[str],
    division: dict,
    announce_attention: bool,
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    platform_alteration = service["locationDetail"].get("platformChanged")
    platform, plat_int, plat_letter = get_platform_and_int(service)

    if announce_attention:
        announce_this_is(
            config,
            sub_config,
            service,
            wavplayer
        )

        if (
            division["divides_here"] and
            config["general"]["voice"] != "Female2"
        ):
            for i in range(sub_config["stand_clear_detaching"]):
                wavplayer.play_wav(
                    "w/please stand clear while the train is being " +
                    "detached.wav"
                )
                time.sleep(0.7)

        if division["joins_here"] and config["general"]["voice"] != "Female2":
            for i in range(sub_config["stand_clear_attaching"]):
                wavplayer.play_wav(
                    "w/in the interests of safety please stand clear while " +
                    "the train attaches.wav"
                )
                time.sleep(0.7)

    if (
        platform_alteration and
        sub_config["platform_alterations"]
    ):
        announce_departure_platform_alteration_intro(
            config,
            sub_config,
            service,
            destinations,
            division,
            announce_attention,
            now,
            wavplayer
        )
    else:
        if sub_config["now_standing_script"]:
            if platform:
                wavplayer.play_wav("s/the train now standing at platform.wav")
                announce_platform_number(config, service, False, wavplayer)
                wavplayer.play_wav("m/is the.wav")
            else:
                wavplayer.play_wav(
                    "s/the train now standing at this station is the.wav"
                )

            announce_time_and_toc(
                config,
                sub_config,
                service,
                now,
                wavplayer,
                division
            )
            announce_destinations(destinations, True, wavplayer)
        else:
            announce_platform_intro(
                config,
                sub_config,
                service,
                destinations,
                division,
                ["s/the train now standing at this station is the.wav"],
                now,
                wavplayer
            )


def announce_realtime_departure_trust_triggered_intro(
    config: dict,
    sub_config: dict,
    service: dict,
    destinations: list[str],
    division: dict,
    announce_attention: bool,
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> None:
    platform_alteration = service["locationDetail"].get("platformChanged")
    platform, plat_int, plat_letter = get_platform_and_int(service)

    if announce_attention:
        announce_this_is(
            config,
            sub_config,
            service,
            wavplayer
        )

        if (
            division["divides_here"] and
            config["general"]["voice"] != "Female2"
        ):
            for i in range(sub_config["stand_clear_detaching"]):
                wavplayer.play_wav(
                    "w/please stand clear while the train is being " +
                    "detached.wav"
                )
                time.sleep(0.7)

        if division["joins_here"] and config["general"]["voice"] != "Female2":
            for i in range(sub_config["stand_clear_attaching"]):
                wavplayer.play_wav(
                    "w/in the interests of safety please stand clear while " +
                    "the train attaches.wav"
                )
                time.sleep(0.7)

    if (
        platform_alteration and
        sub_config["platform_alterations"]
    ):
        announce_departure_platform_alteration_intro(
            config,
            sub_config,
            service,
            destinations,
            division,
            announce_attention,
            now,
            wavplayer
        )
    else:
        announce_platform_intro(
            config,
            sub_config,
            service,
            destinations,
            division,
            ["s/the next train is the.wav"],
            now,
            wavplayer
        )


def announce_realtime_departure_generic(
    config: dict,
    sub_config: dict,
    service: dict,
    all_calling_points: dict,
    origins: list[str],
    destinations: list[str],
    division: dict,
    cancellation: dict,
    intro_function: typing.Callable,
    now: datetime.datetime,
    repeat: bool,
    wavplayer: WavPlayer
) -> None:

    play_chime(config, sub_config, wavplayer)

    intro_function(
        config,
        sub_config,
        service,
        destinations,
        division,
        not repeat,
        now,
        wavplayer
    )

    announce_calling_points(
        config,
        sub_config,
        all_calling_points,
        division,
        cancellation,
        wavplayer
    )

    if sub_config["service_from"]:
        time.sleep(0.7)
        if config["general"]["voice"] == "Female2":
            wavplayer.play_wav("m/this train.wav")
            wavplayer.play_wav("m/is the.wav")
            wavplayer.play_wav("m/service from.wav")
        else:
            wavplayer.play_wav("s/this train is the service from.wav")
        announce_destinations(origins, True, wavplayer)

    if sub_config["mind_the_gap"]:
        time.sleep(0.7)
        wavplayer.play_wav(
            "w/mind the gap between the train and the platform.wav"
        )
        wavplayer.play_wav("w/mind the gap.wav")
    
    if sub_config["repeat"]:
        time.sleep(0.7)
        intro_function(
            config,
            sub_config,
            service,
            destinations,
            division,
            False,
            now,
            wavplayer
        )


def announce_realtime_departure(
    config: dict,
    service: dict,
    all_calling_points: dict,
    origins: list[str],
    destinations: list[str],
    division: dict,
    cancellation: dict,
    now: datetime.datetime,
    repeat: bool,
    wavplayer: WavPlayer
) -> None:
    service_location = service["locationDetail"].get("serviceLocation")

    if service_location == "APPR_STAT":
        logging.info("Approaching station realtime")
        announce_realtime_departure_generic(
            config,
            config["departures_next_train"],
            service,
            all_calling_points,
            origins,
            destinations,
            division,
            cancellation,
            announce_realtime_departure_next_train_intro,
            now,
            repeat,
            wavplayer
        )

    elif service_location == "APPR_PLAT":
        logging.info("Approaching platform realtime")
        announce_realtime_departure_generic(
            config,
            config["departures_now_approaching"],
            service,
            all_calling_points,
            origins,
            destinations,
            division,
            cancellation,
            announce_realtime_departure_now_approaching_intro,
            now,
            repeat,
            wavplayer
        )


    elif service_location == "AT_PLAT":
        logging.info("At platform realtime")
        announce_realtime_departure_generic(
            config,
            config["departures_now_standing"],
            service,
            all_calling_points,
            origins,
            destinations,
            division,
            cancellation,
            announce_realtime_departure_now_standing_intro,
            now,
            repeat,
            wavplayer
        )

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"])


def announce_realtime_departure_trust_triggered(
    config: dict,
    service: dict,
    all_calling_points: dict,
    origins: list[str],
    destinations: list[str],
    division: dict,
    cancellation: dict,
    now: datetime.datetime,
    repeat: bool,
    wavplayer: WavPlayer
) -> None:
    logging.info("TRUST triggered")
    announce_realtime_departure_generic(
        config,
        config["departures_trust_triggered"],
        service,
        all_calling_points,
        origins,
        destinations,
        division,
        cancellation,
        announce_realtime_departure_trust_triggered_intro,
        now,
        repeat,
        wavplayer
    )

    # after playing an announcement we want a gap to the next one
    time.sleep(config["general"]["announcement_delay"])


def announce_realtime(
    config: dict,
    service: dict,
    all_calling_points: dict,
    origins: list[str],
    destinations: list[str],
    division: dict,
    cancellation: dict,
    now: datetime.datetime,
    repeat: bool,
    wavplayer: WavPlayer
) -> None:
    display_as = service["locationDetail"]["displayAs"]

    if (
        display_as in ("DESTINATION", "TERMINATES") and
        not division["joins_main_train"]
    ):
        announce_realtime_arrival(config, service, origins, now, wavplayer)
    else:
        announce_realtime_departure(
            config,
            service,
            all_calling_points,
            origins,
            destinations,
            division,
            cancellation,
            now,
            repeat,
            wavplayer
        )


def announce_realtime_trust_triggered(
    config: dict,
    service: dict,
    all_calling_points: dict,
    origins: list[str],
    destinations: list[str],
    division: dict,
    cancellation: dict,
    now: datetime.datetime,
    repeat: bool,
    wavplayer: WavPlayer
) -> None:
    display_as = service["locationDetail"]["displayAs"]

    if (
        display_as in ("DESTINATION", "TERMINATES") and
        not division["joins_main_train"]
    ):
        announce_realtime_arrival_trust_triggered(
            config,
            service,
            origins,
            now,
            wavplayer
        )
    else:
        announce_realtime_departure_trust_triggered(
            config,
            service,
            all_calling_points,
            origins,
            destinations,
            division,
            cancellation,
            now,
            repeat,
            wavplayer
        )


def announce_cases_and_parcels(
    config: dict,
    wavplayer: WavPlayer
) -> None:
    wavplayer.play_wav("s/please do not leave cases or parcels.wav")
    wavplayer.play_wav("e/unattended anywhere on the station.wav")
    time.sleep(0.35)
    wavplayer.play_wav(
        "s/any unattended articles are likely to be removed.wav"
    )
    wavplayer.play_wav("e/without warning.wav")



def announce_cctv_remote(
    config: dict,
    wavplayer: WavPlayer
) -> None:
    wavplayer.play_wav("w/may i have your attention please (2).wav")
    time.sleep(0.7)
    wavplayer.play_wav("m/please note that.wav")
    wavplayer.play_wav(
        "m/closed circuit television and remote video monitoring.wav"
    )
    wavplayer.play_wav("m/is in use at this station.wav")
    wavplayer.play_wav("e/for your personal safety and security.wav")


def announce_safety(
    config: dict,
    safety_last_announcement: dict,
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> bool:
    announced = False

    if not config["announcements_enabled"]["safety"]:
        return announced

    for (safety_type, announce_function) in [
        ("cases_and_parcels", announce_cases_and_parcels),
        ("cctv_remote", announce_cctv_remote)
    ]:
        frequency = config["safety"][f"{safety_type}_frequency"]
        offset = config["safety"][f"{safety_type}_offset"]
        if not frequency:
            continue

        if safety_type in safety_last_announcement:
            last_hour = safety_last_announcement[safety_type]["hour"]
            last_minute = safety_last_announcement[safety_type]["minute"]

            if now.hour != last_hour:
                if now.minute < offset:
                    continue
            elif now.minute < last_minute + frequency:
                continue
        else:
            # make sure we start after a nice offset from the hour
            if now.minute < offset:
                continue

        announced = True
        logging.info(f"Announcing {safety_type}")
        play_chime(config, config["safety"], wavplayer)
        announce_function(config, wavplayer)
        time.sleep(config["general"]["announcement_delay"])
        safety_last_announcement[safety_type] = {
            "hour": now.hour,
            "minute": (
                ((now.minute - offset) // frequency) * frequency + offset
            ),
        }

    return announced


def announce_services(
    config: dict,
    services: list[dict],
    service_last_announcement: dict,
    safety_last_announcement: dict,
    now: datetime.datetime,
    wavplayer: WavPlayer
) -> bool:
    pp = pprint.PrettyPrinter(indent=4)

    announced = False
    for service in services:
        logging.debug(pp.pformat(service))

        should_do_departure_delay = should_announce_departure_delay(
            config,
            service,
            service_last_announcement,
            now
        )

        should_do_arrival_delay = should_announce_arrival_delay(
            config,
            service,
            service_last_announcement,
            now
        )

        should_do_cancellation = should_announce_cancellation(
            config,
            service,
            service_last_announcement,
            now
        )

        should_do_departure_platform_alteration = (
            should_announce_departure_platform_alteration(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        )

        should_do_arrival_platform_alteration = (
            should_announce_arrival_platform_alteration(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        )

        should_do_realtime = should_announce_realtime(
            config,
            service,
            service_last_announcement,
            now,
            services
        )

        should_do_realtime_repeat = should_announce_realtime_repeat(
            config,
            service,
            service_last_announcement,
            now,
            services
        )

        should_do_realtime_trust_triggered = (
            should_announce_realtime_trust_triggered(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        )

        should_do_realtime_trust_triggered_repeat = (
            should_announce_realtime_trust_triggered_repeat(
                config,
                service,
                service_last_announcement,
                now,
                services
            )
        )

        should_do_departure_bus = should_announce_departure_bus(
            config,
            service,
            service_last_announcement,
            now
        )

        if not (
            should_do_departure_delay or
            should_do_arrival_delay or
            should_do_realtime or
            should_do_realtime_repeat or
            should_do_realtime_trust_triggered or
            should_do_realtime_trust_triggered_repeat or
            should_do_departure_bus or
            should_do_departure_platform_alteration or
            should_do_arrival_platform_alteration or
            should_do_cancellation
        ):
            continue

        logging.info("Should do announcement")

        # At this point, only silly admin issues can stop us, so act as if we
        # have made an announcement and update the map
        update_service_last_announcement(
            service,
            service_last_announcement,
            now
        )

        train_content = fetch_train_content(config, service)

        logging.debug(pp.pformat(train_content))

        all_calling_points, origins, destinations, division, cancellation = (
            calculate_calling_points(config, service, train_content)
        )

        # Sanity check, if no destination we shouldn't announce (eg buses to
        # airports)
        if not destinations_valid(config, destinations):
            continue

        # At this point we will have announced a train
        announced = True

        if should_do_cancellation:
            announce_cancellation(
                config,
                train_content,
                service,
                wavplayer
            )

        if should_do_departure_delay:
            announce_departure_delay(
                config,
                service,
                destinations,
                now,
                wavplayer
            )

        if should_do_arrival_delay:
            announce_arrival_delay(
                config,
                service,
                origins,
                now,
                wavplayer
            )

        if should_do_departure_bus:
            announce_departure_bus(
                config,
                all_calling_points["whole_train"],
                wavplayer
            )

        if should_do_departure_platform_alteration:
            announce_departure_platform_alteration(
                config,
                service,
                destinations,
                division,
                now,
                wavplayer
            )

        if should_do_arrival_platform_alteration:
            announce_arrival_platform_alteration(
                config,
                service,
                origins,
                now,
                wavplayer
            )

        if should_do_realtime:
            announce_realtime(
                config,
                service,
                all_calling_points,
                origins,
                destinations,
                division,
                cancellation,
                now,
                False,
                wavplayer
            )
        elif should_do_realtime_repeat:
            announce_realtime(
                config,
                service,
                all_calling_points,
                origins,
                destinations,
                division,
                cancellation,
                now,
                True,
                wavplayer
            )
        elif should_do_realtime_trust_triggered:
            announce_realtime_trust_triggered(
                config,
                service,
                all_calling_points,
                origins,
                destinations,
                division,
                cancellation,
                now,
                False,
                wavplayer
            )
        elif should_do_realtime_trust_triggered_repeat:
            announce_realtime_trust_triggered(
                config,
                service,
                all_calling_points,
                origins,
                destinations,
                division,
                cancellation,
                now,
                True,
                wavplayer
            )

    # Safety announcements being uniquely time-based have one function that
    # both decides whether to announce, and announces.
    safety_announced = announce_safety(
        config,
        safety_last_announcement,
        now,
        wavplayer
    )
    announced = announced or safety_announced
    return announced


def main() -> int:
    logging.basicConfig(filename="rtt-announce.log", level=logging.DEBUG)
    config = load_config("rtt-announce.toml")
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(
        logging.DEBUG if config["general"]["debug"] else logging.INFO
    )
    logging.getLogger().addHandler(handler)

    service_last_announcement = {}
    safety_last_announcement = {}

    wavplayer = WavPlayer(config)

    while True:
        now = datetime.datetime.now()
        deps_content, arrs_content = fetch_lineups(config, now)

        services = arrs_content["services"] + deps_content["services"]

        if not announce_services(
            config,
            services,
            service_last_announcement,
            safety_last_announcement,
            now,
            wavplayer
        ):
            time.sleep(config["general"]["poll_delay"])


if __name__ == '__main__':
    sys.exit(main())

import sys
import copy
import json
import numpy as np
import sympy as sym

from ...device.dmm import Dmm
from ...device.cdg import InfCdg, Cdg
from ...device.srg import Srg

from ...constants import Constants
from ...calibration_devices import CalibrationObject
from ...values import Temperature, Pressure, Time, AuxSe3, OutGasRate, Position, Expansion, Date
from ..standard import Standard


class Se3(Standard):
    """Configuration and methodes of static expansion system SE3.

    There is a need to define the  ``no_of_meas_points``:
    the time: ``amt_fill`` (absolut measure time of filling pressure)
    is used for this purpose if doc is a calibration. For the analysis of
    state measurements ``amt`` is used.
    """
    name = "SE3"
    unit = "Pa"
    temp_dev_name = "SE3_Temperature_Keithley"
    small_temp_types = ["ch_3001_before", "ch_3002_before", "ch_3003_before", ]

    medium_temp_types = ["ch_3004_before", "ch_3005_before", "ch_3006_before",
                        "ch_3007_before", "ch_3008_before", "ch_3009_before",
                        "ch_3010_before", "ch_3011_before", "ch_3012_before",
                        "ch_3013_before", ]

    large_temp_types = ["ch_3014_before", "ch_3015_before", "ch_3016_before",
                        "ch_3017_before", "ch_3018_before", "ch_3019_before",
                        "ch_3020_before", "ch_3021_before", "ch_3022_before",
                        "ch_3023_before", "ch_3024_before", "ch_3025_before",
                        "ch_3026_before", "ch_3027_before", "ch_3028_before",
                        "ch_3029_before", "ch_3030_before", ]

    vessel_temp_types = ["ch_1001_after", "ch_1002_after", "ch_1003_after",
                        "ch_1004_after", "ch_1005_after", "ch_1006_after",
                        "ch_1007_after", "ch_1008_after", "ch_1009_after",
                        "ch_1010_after", "ch_1011_after", "ch_1012_after",
                        "ch_1013_after", "ch_1014_after", "ch_1015_after",
                        "ch_1016_after", "ch_1017_after", "ch_1018_after",
                        "ch_1019_after", "ch_1020_after", "ch_1020_after",
                        "ch_1021_after", "ch_1022_after", "ch_1023_after",
                        "ch_1024_after", "ch_1025_after", "ch_1026_after",
                        "ch_1027_after", "ch_1028_after", "ch_1029_after",
                        "ch_1030_after", "ch_2001_after", "ch_2002_after",
                        "ch_2003_after", "ch_2004_after", "ch_2005_after",
                        "ch_2006_after", "ch_2007_after", "ch_2008_after",
                        "ch_2009_after", "ch_2010_after", "ch_2011_after",
                        "ch_2012_after", "ch_2013_after", "ch_2014_after",
                        "ch_2015_after", "ch_2016_after", "ch_2017_after",
                        "ch_2018_after", "ch_2019_after", "ch_2020_after",
                        "ch_2020_after", "ch_2021_after", "ch_2022_after",
                        "ch_2023_after", "ch_2024_after", "ch_2025_after",
                        "ch_2026_after", "ch_2027_after", "ch_2028_after", ]

    fill_dev_names = ["CDG_1T_1",  "CDG_1T_2", "CDG_1T_3",
                    "CDG_10T_1",  "CDG_10T_2",  "CDG_10T_3",
                    "CDG_100T_1", "CDG_100T_2", "CDG_100T_3",
                    "CDG_1000T_1", "CDG_1000T_2", "CDG_1000T_3", ]

    
    fill_types = ["1T_1-fill", "1T_2-fill", "1T_3-fill",
                  "10T_1-fill",  "10T_2-fill", "10T_3-fill",
                  "100T_1-fill", "100T_2-fill", "100T_3-fill",
                  "1000T_1-fill", "1000T_2-fill", "1000T_3-fill", ]
    
    state_types = ["1T_1-state", "1T_2-state", "1T_3-state",
                  "10T_1-state",  "10T_2-state", "10T_3-state",
                  "100T_1-state", "100T_2-state", "100T_3-state",
                  "1000T_1-state", "1000T_2-state", "1000T_3-state", ]

    offset_types = ["1T_1-offset", "1T_2-offset", "1T_3-offset",
                    "10T_1-offset",  "10T_2-offset", "10T_3-offset",
                    "100T_1-offset", "100T_2-offset", "100T_3-offset",
                    "1000T_1-offset", "1000T_2-offset", "1000T_3-offset", ]
   
    analysis_check = {
        "Error":{
            "Customer":{"Type":"ind", "Unit": "1", "Max":0.25, "Min":-0.25, "Description":"Error of the Customer gauge."},
            "FillDeviation": {"Type":"dev_fill", "Unit": "1", "Max":0.05, "Min":-0.05, "Description":"deviation between calculated and measured filling pressure."},           
            "CalDeviation": {"Type":"dev_cal", "Unit": "1", "Max":0.05, "Min":-0.05, "Description":"deviation between calculated and target calibration pressure."}, 
            "PressureRise": {"Type":"rise", "Unit": "1", "Max":0.05, "Min":-0.05, "Description":"relative contribution of pressure rise to the calibration pressure."}, 
                      
        },
        "Temperature":{
            "Vessel":{"Type":"after", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Vessel Temperature"},        
            "StartVolume":{"Type":"before", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Temperature of the starting Volume"}, 
        }
    }

    state_check = {
        "Volume": {
          "Branch":{"Type":"add_branch", "Unit": "cm^3" , "Max":550.0, "Min":450.0, "Description":"Additional volume of dut-branch. All dut valves are closed."},
          "BranchDutA":{"Type":"add_a", "Unit": "cm^3" , "Max":1100.0, "Min":500.0, "Description":"Additional volume of dut a"},
          "BranchDutB":{"Type":"add_ab", "Unit": "cm^3" , "Max":1700.0, "Min":500.0, "Description":"Additional volume of dut a and b together"},
          "BranchDutC":{"Type":"add_abc", "Unit": "cm^3" , "Max":2100.0, "Min":500.0, "Description":"Additional volume of dut a,b and c together"},
          "DutA":{"Type":"a", "Unit": "cm^3" , "Max":600.0, "Min":10.0, "Description":"Additional volume of dut a only"},
          "DutB":{"Type":"b", "Unit": "cm^3" , "Max":600.0, "Min":10.0, "Description":"Additional volume of dut b only"},
          "DutC":{"Type":"c", "Unit": "cm^3" , "Max":600.0, "Min":10.0, "Description":"Additional volume of dut c only"}
        },
        "Pressure":{
          "CDG1T1":{"Type":"1T_1-state", "Unit": "Pa" , "Max":1, "Min": -1,"Description":"Offset of 1st 1T CDG"},
          "CDG1T2":{"Type":"1T_2-state", "Unit": "Pa" , "Max":1, "Min": -1,"Description":"Offset of 2nd 1T CDG"},
          "CDG1T3":{"Type":"1T_3-state", "Unit": "Pa" , "Max":1, "Min": -1,"Description":"Offset of 3rd 1T CDG"},
          "CDG10T1":{"Type":"10T_1-state", "Unit": "Pa" , "Max":2, "Min": -2,"Description":"Offset of 1st 10T CDG"},
          "CDG10T2":{"Type":"10T_2-state", "Unit": "Pa" , "Max":2, "Min": -2,"Description":"Offset of 2nd 10T CDG"},
          "CDG10T3":{"Type":"10T_3-state", "Unit": "Pa" , "Max":2, "Min": -2,"Description":"Offset of 3rd 10T CDG"},
          "CDG100T1":{"Type":"100T_1-state", "Unit": "Pa" , "Max":3, "Min": -3,"Description":"Offset of 1st 100T CDG"},
          "CDG100T2":{"Type":"100T_2-state", "Unit": "Pa" , "Max":3, "Min": -3,"Description":"Offset of 2nd 100T CDG"},
          "CDG100T3":{"Type":"100T_3-state", "Unit": "Pa" , "Max":3, "Min": -3,"Description":"Offset of 3rd 100T CDG"},
          "CDG1000T1":{"Type":"1000T_1-state", "Unit": "Pa" , "Max":5, "Min": -5,"Description":"Offset of 1st 1000T CDG"},
          "CDG1000T2":{"Type":"1000T_2-state", "Unit": "Pa" , "Max":5, "Min": -5,"Description":"Offset of 2nd 1000T CDG"},
          "CDG1000T3":{"Type":"1000T_3-state", "Unit": "Pa" , "Max":5, "Min": -5,"Description":"Offset of 3rd 1000T CDG"}
        },
        "OutGasRate":{
          "Vessel":{"Type":"outgas_v", "Unit": "mbar/s" , "Max":1e-9, "Min": 1e-11,"Description":"Outgasig rate of vessel only"},
          "VesselBranch":{"Type":"outgas_u", "Unit": "mbar/s" , "Max":5e-9, "Min": 1e-11, "Description":"Outgasig rate of vessel and dut branch (all dut branches closed)"},
          "VesselDutABC":{"Type":"outgas_abc", "Unit": "mbar/s" , "Max":5e-9, "Min": 1e-11,"Description":"Outgasig rate of vessel, dut branch and dut-abc"},
          "VesselDutBC":{"Type":"outgas_bc", "Unit": "mbar/s" , "Max":5e-9, "Min": 1e-11,"Description":"Outgasig rate of vessel, dut branch and dut-bc"},
          "VesselDutC":{"Type":"outgas_c", "Unit": "mbar/s" , "Max":5e-9, "Min": 1e-11,"Description":"Outgasig rate of vessel, dut branch and dut-c"},
        },
        "Temperature":{
          "Ch1001":{"Type":"ch_1001state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1001"},
          "Ch1002":{"Type":"ch_1002state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1002"},
          "Ch1003":{"Type":"ch_1003state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1003"},
          "Ch1004":{"Type":"ch_1004state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1004"},
          "Ch1005":{"Type":"ch_1005state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1005"},
          "Ch1006":{"Type":"ch_1006state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1006"},
          "Ch1007":{"Type":"ch_1007state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1007"},
          "Ch1008":{"Type":"ch_1008state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1008"},
          "Ch1009":{"Type":"ch_1009state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1009"},
          "Ch1010":{"Type":"ch_1010state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1010"},
          "Ch1011":{"Type":"ch_1011state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1011"},
          "Ch1012":{"Type":"ch_1012state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1012"},
          "Ch1013":{"Type":"ch_1013state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1013"},
          "Ch1014":{"Type":"ch_1014state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1014"},
          "Ch1015":{"Type":"ch_1015state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1015"},
          "Ch1016":{"Type":"ch_1016state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1016"},
          "Ch1017":{"Type":"ch_1017state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1017"},
          "Ch1018":{"Type":"ch_1018state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1018"},
          "Ch1019":{"Type":"ch_1019state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1019"},
          "Ch1020":{"Type":"ch_1020state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1020"},
          "Ch1021":{"Type":"ch_1021state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1021"},
          "Ch1022":{"Type":"ch_1022state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1022"},
          "Ch1023":{"Type":"ch_1023state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1023"},
          "Ch1024":{"Type":"ch_1024state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1024"},
          "Ch1025":{"Type":"ch_1025state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1025"},
          "Ch1026":{"Type":"ch_1026state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1026"},
          "Ch1027":{"Type":"ch_1027state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1027"},
          "Ch1028":{"Type":"ch_1028state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1028"},
          "Ch1029":{"Type":"ch_1029state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1029"},
          "Ch1030":{"Type":"ch_1030state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 1030"},
          "Ch2001":{"Type":"ch_2001state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2001"},
          "Ch2002":{"Type":"ch_2002state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2002"},
          "Ch2003":{"Type":"ch_2003state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2003"},
          "Ch2004":{"Type":"ch_2004state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2004"},
          "Ch2005":{"Type":"ch_2005state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2005"},
          "Ch2006":{"Type":"ch_2006state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2006"},
          "Ch2007":{"Type":"ch_2007state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2007"},
          "Ch2008":{"Type":"ch_2008state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2008"},
          "Ch2009":{"Type":"ch_2009state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2009"},
          "Ch2010":{"Type":"ch_2010state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2010"},
          "Ch2011":{"Type":"ch_2011state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2011"},
          "Ch2012":{"Type":"ch_2012state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2012"},
          "Ch2013":{"Type":"ch_2013state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2013"},
          "Ch2014":{"Type":"ch_2014state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2014"},
          "Ch2015":{"Type":"ch_2015state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2015"},
          "Ch2016":{"Type":"ch_2016state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2016"},
          "Ch2017":{"Type":"ch_2017state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2017"},
          "Ch2018":{"Type":"ch_2018state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2018"},
          "Ch2019":{"Type":"ch_2019state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2019"},
          "Ch2020":{"Type":"ch_2020state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2020"},
          "Ch2021":{"Type":"ch_2021state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2021"},
          "Ch2022":{"Type":"ch_2022state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2022"},
          "Ch2023":{"Type":"ch_2023state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2023"},
          "Ch2024":{"Type":"ch_2024state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2024"},
          "Ch2025":{"Type":"ch_2025state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2025"},
          "Ch2026":{"Type":"ch_2026state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2026"},
          "Ch2027":{"Type":"ch_2027state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2027"},
          "Ch2028":{"Type":"ch_2028state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2028"},
          "Ch2029":{"Type":"ch_2029state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2029"},
          "Ch2030":{"Type":"ch_2030state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 2030"},
          "Ch3001":{"Type":"ch_3001state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3001"},
          "Ch3002":{"Type":"ch_3002state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3002"},
          "Ch3003":{"Type":"ch_3003state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3003"},
          "Ch3004":{"Type":"ch_3004state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3004"},
          "Ch3005":{"Type":"ch_3005state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3005"},
          "Ch3006":{"Type":"ch_3006state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3006"},
          "Ch3007":{"Type":"ch_3007state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3007"},
          "Ch3008":{"Type":"ch_3008state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3008"},
          "Ch3009":{"Type":"ch_3009state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3009"},
          "Ch3010":{"Type":"ch_3010state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3010"},
          "Ch3011":{"Type":"ch_3011state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3011"},
          "Ch3012":{"Type":"ch_3012state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3012"},
          "Ch3013":{"Type":"ch_3013state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3013"},
          "Ch3014":{"Type":"ch_3014state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3014"},
          "Ch3015":{"Type":"ch_3015state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3015"},
          "Ch3016":{"Type":"ch_3016state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3016"},
          "Ch3017":{"Type":"ch_3017state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3017"},
          "Ch3018":{"Type":"ch_3018state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3018"},
          "Ch3019":{"Type":"ch_3019state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3019"},
          "Ch3020":{"Type":"ch_3020state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3020"},
          "Ch3021":{"Type":"ch_3021state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3021"},
          "Ch3022":{"Type":"ch_3022state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3022"},
          "Ch3023":{"Type":"ch_3023state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3023"},
          "Ch3024":{"Type":"ch_3024state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3024"},
          "Ch3025":{"Type":"ch_3025state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3025"},
          "Ch3026":{"Type":"ch_3026state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3026"},
          "Ch3027":{"Type":"ch_3027state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3027"},
          "Ch3028":{"Type":"ch_3028state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3028"},
          "Ch3029":{"Type":"ch_3029state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3029"},
          "Ch3030":{"Type":"ch_3030state", "Unit": "K" , "Max":297.15, "Min":295.15, "Description":"Pt-100 sensor of channel 3030"}
        }
    }

    def __init__(self, doc):
        super().__init__(doc, self.name)

        # measurement values
        self.Temp = Temperature(doc)
        self.Pres = Pressure(doc)
        self.Time = Time(doc)
        self.Aux = AuxSe3(doc)
        self.Pos = Position(doc)
        self.Exp = Expansion(doc)
        self.Date = Date(doc)

        if 'State' in doc:
            self.OutGas = OutGasRate(doc)
            self.no_of_meas_points = len(self.Time.get_value("amt", "ms"))
        
        if 'Calibration' in doc:
            # define model
            self.no_of_meas_points = len(self.Time.get_value("amt_fill", "ms"))
            
            # costomer device
            if 'CustomerObject' in doc['Calibration']:
                customer_device = doc['Calibration']['CustomerObject']
                dev_class = customer_device.get('Class', "generic")

                if dev_class == 'SRG':
                    self.CustomerDevice = Srg(doc, customer_device)
                if dev_class == 'CDG':
                    self.CustomerDevice = Cdg(doc, customer_device)
                if dev_class == 'generic':
                    self.CustomerDevice = Cdg(doc, {})
        
        self.TDev = Dmm(doc, self.Cobj.get_by_name(self.temp_dev_name))
        self.FillDevs =[]
        for d in self.fill_dev_names:
            self.FillDevs.append(InfCdg(doc, self.Cobj.get_by_name(d)))
        
    def get_gas(self):
        """Returns the name of the calibration gas.

        .. todo::

                get gas from todo if nothing found in AuxValues

        :returns: gas (N2, He etc.)
        :rtype: str
        """

        gas=self.Aux.get_gas()
        if gas is not None:
            return gas

    def get_expansion_name(self):
        """Returns an np.array containing
        the expansion name (``f_s``, ``f_m`` or ``f_l``)
        of the length: ``self.no_of_meas_points```

        :returns: array of expansion names
        :rtype: np.array of strings
        """

        f_name = self.Exp.get_str("name")
        if f_name is None:
            f_name = np.full(self.no_of_meas_points, self.Aux.get_expansion())

        return f_name


    def expansion(self, res):
        """Builds a vector containing the expansion factors
        and stores it.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """

        f=np.full(self.no_of_meas_points, np.nan)
        f_name=self.get_expansion_name()
        i_s=np.where(f_name == "f_s")
        i_m=np.where(f_name == "f_m")
        i_l=np.where(f_name == "f_l")

        if np.shape(i_s)[1] > 0:
            f[i_s]=self.get_value("f_s", "1")

        if np.shape(i_m)[1] > 0:
            f[i_m]=self.get_value("f_m", "1")

        if np.shape(i_l)[1] > 0:
            f[i_l]=self.get_value("f_l", "1")

        res.store("Expansion", "uncorr", f, "1")

    def time_meas(self, res):
        """Builds a vector containing the measurement time.

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :type: class
        """
        conv2s = self.Cons.get_conv(from_unit="ms", to_unit="s")
        conv2min = self.Cons.get_conv(from_unit="s", to_unit="min")
        t = self.Time.get_rmt("amt_meas", "ms")*conv2s *conv2min

        res.store("Time", "meas", t, "min")

    def insert_state_results(self, res, state_doc):
        """Takes the volume, outgasing rate and time out of the 
        analysis of preliminary state measurements and
        stores it under the AuxValues section of the *res*

        :param: Class with methode
                store(quantity, type, value, unit, [stdev], [N])) and
                pick(quantity, type, unit)
        :param: state doc, must contain lists under: 
                * State.Analysis.Values.Volume 
                * State.Analysis.Values.OutgasRate 
                * State.Analysis.Values.Time
        :type: dict
        """ 
        doc_id = state_doc.get('_id')

        values = state_doc.get('State', {}).get('Analysis',{}).get('Values', {})
        if 'Volume' in values:
            for volume in values.get('Volume'):
                res.store_dict('Volume', volume, dest="AuxValues")
        else:
            sys.exit('missing volume section in state doc {}'.format(doc_id))

        if 'OutGasRate' in values:
            for outgasrate in values.get('OutGasRate'):
                res.store_dict('OutGasRate', outgasrate, dest="AuxValues")
        else:
            sys.exit('missing outGas rate section in state doc {}'.format(doc_id))

        if 'Time' in values:
            for time in values.get('Time'):
                res.store_dict('Time', time, dest="AuxValues")
        else:
            sys.exit('missing time section in state doc {}'.format(doc_id))
        
        
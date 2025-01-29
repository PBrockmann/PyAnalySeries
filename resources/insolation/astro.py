#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 11:38:33 2022

@author: didier
"""

import os
import numpy as np
from numpy import loadtxt
import io
from scipy.interpolate import interp1d
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
from pathlib import Path

class Astro(ABC):

    def __init__(self):
        module_dir = Path(__file__).parent
        self.path_Laskar2004 = module_dir / "astrofiles" / "Laskar2004"
        self.path_Laskar1993 = module_dir / "astrofiles" / "Laskar1993"
        self.path_Laskar2010 = module_dir / "astrofiles" / "Laskar2010"

    @abstractmethod
    def in_range(self,time):
        pass

    @abstractmethod
    def eccentricity(self,time):
        pass

    # en radians
    def obliquity(self,time):
        pass

    def precession_angle(self,time):
        pass

    def precession_parameter(self,time):
        return self.eccentricity(time)*np.sin(self.precession_angle(time))

#
#   Berger 1978
#    
class AstroBerger1978(Astro):
    def __init__(self):
        piDeg = np.pi/180    
        piSec = piDeg/3600
            #    19 terms for Ecc
        self.EccA = np.array([0.01860798,0.01627522,-0.01300660,0.00988829,-0.00336700,0.00333077,-0.00235400,0.00140015,0.00100700,0.00085700,0.00064990,0.00059900,0.00037800,-0.00033700,0.00027600,0.00018200,-0.00017400,-0.00012400,0.00001250])	
        self.EccB = piSec*np.array([4.207205,7.346091,17.857263,17.220546,16.846733,5.199079,18.231076,26.216758,6.359169,16.210016,3.065181,16.583829,18.493980,6.190953,18.867793,17.425567,6.186001,18.417441,0.667863])
        self.EccC = piDeg*np.array([28.620089,193.788772,308.307024,320.199637,279.376984,87.195000,349.129677,128.443387,154.143880,291.269597,114.860583,332.092251,296.414411,145.769910,337.237063,152.092288,126.839891,210.667199,72.108838])
            #    18 terms for Obl
        self.Obl1 = piDeg*23.320556;
        self.OblA = piSec*np.array([-2462.22,-857.32,-629.32,-414.28,-311.76,308.94,-162.55,-116.11,101.12,-67.69,24.91,22.58,-21.16,-15.65,15.39,14.67,-11.73,10.27])	
        self.OblB = piSec*np.array([31.609970,32.620499,24.172195,31.983780,44.828339,30.973251,43.668243,32.246689,30.599442,42.681320,43.836456,47.439438,63.219955,64.230484,1.010530,7.437771,55.782181,0.373813])	
        self.OblC = piDeg*np.array([251.9025,280.8325,128.3057,292.7251,15.3747,263.7952,308.4258,240.0099,222.9725,268.7810,316.7998,319.6023,143.8050,172.7351,28.9300,123.5968,20.2042,40.8226])
            #    9 terms for Pre
        self.Pre1 = piDeg*3.392506;
        self.Pre2 = piSec*50.439273;
        self.PreA = piSec*np.array([7391.02,2555.15,2022.76,-1973.65,1240.23,953.87,-931.75,872.38,606.35])
        self.PreB = piSec*np.array([31.609970,32.620499,24.172195,0.636717,31.983780,3.138886,30.973251,44.828339,0.991874])
        self.PreC = piDeg*np.array([251.9025,280.8325,128.3057,348.1074,292.7251,165.1686,263.7952,15.3747,58.5749])
        
    def eccAndpi(self,t):
        xes = 0         #-> e sin(π)
        xec = 0         #-> e cos(π)
        for i in range(19):
            arg = self.EccB[i] * t + self.EccC[i]
            xes += self.EccA[i] * np.sin( arg )
            xec += self.EccA[i] * np.cos( arg )
        return (xes,xec)
    def general_precession(self,t):
        p = self.Pre2 * t
        for i in range(9):
            p += self.PreA[i] * np.sin( self.PreB[i] * t + self.PreC[i] )
        return p + self.Pre1
        
    def precession_angle(self,time):
        t = 1000*time
        xes,xec = self.eccAndpi(t)
        perh = np.arctan2(xes,xec) + self.general_precession(t)
        q,r = divmod(perh, 2*np.pi)
        return r
    def eccentricity(self,time):
        xes,xec = self.eccAndpi(1000*time)
        return np.sqrt(xes*xes+xec*xec)
    def obliquity(self,time):
        t = 1000*time
        x = self.Obl1
        for i in range(18):
            x += self.OblA[i] * np.cos( self.OblB[i] * t + self.OblC[i] )
        return x
    def in_range(self,time):
        return True
    
        
#
#   Laskar 2004
#    
class AstroLaskar2004(Astro):
    def __init__(self):
        super().__init__()
        data = np.load(self.path_Laskar2004 / "Laskar2004.npz")
        a = data['a']
        self.ecc_function = interp1d(a[:,0],a[:,1],kind='cubic')
        self.obl_function = interp1d(a[:,0],a[:,2],kind='cubic')
        self.pre_function = interp1d(a[:,0],a[:,3],kind='cubic')
    def eccentricity(self,time):
        return self.ecc_function(time)
    def obliquity(self,time):
        return self.obl_function(time)
    def precession_angle(self,time):
        return self.pre_function(time)
    def in_range(self,time):
        return (time >= -101000.)and(time <= 21000.)
    
#######################     END     #######################
#
#test when running: $ python astro.py

if __name__ == '__main__':
    
    t0,t1 = (-1000,0)
    t=np.arange(t0,t1,1)

    a1 = AstroBerger1978()
    o1 = a1.precession_parameter(t)
    plt.plot(t,o1)
    a2 = AstroLaskar2004()
    o2 = a2.precession_parameter(t)
    plt.plot(t,o2)
    plt.show()

    plt.plot(t,o2-o1)
    plt.show()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on      Thu Jun 17 15:20:13 2021
Last modified   Wed Jan 22 13:18:00 2025

@author:    Didier Paillard (LSCE)
"""


import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize
from scipy.special import elliprd, elliprf, elliprj, ellipeinc, ellipkinc, ellipe

#
#  solve the Kepler equation: x - e*sinx = v
#     e = eccentricity in [0,1[
#     v = mean anomaly (time from perihelion) in radian, in [0,2π]
#
#Mathematica
#  solveKepler[e_, v_] := x /. FindRoot[v == x - e Sin[x], {x, v}];
#
def solveKepler(e,v):
    return optimize.newton(lambda x: x-v - e*np.sin(x), v, fprime2=lambda x: 1 - e*np.cos(x))

#
#  computes the true anomaly (angular position from perihelion, in radian)
#     from the mean anomaly  (time from perihelion = 2πt/T, in radian)
#
def trueAnomalie(e,meanA):
    (n,vm) = np.divmod(meanA+np.pi, 2*np.pi)
    vm -= np.pi                                # vm in [-π, π[
    sg = np.sign(vm)
    cosE = np.cos(solveKepler(e,vm))
    v = sg * np.arccos((cosE-e)/(1-e*cosE))
    return v + meanA - vm

#
#  computes the mean anomaly  (time from perihelion = 2πt/T, in radian)
#     from the true anomaly (angular position from perihelion, in radian)
#
def meanAnomalie(e,trueA):
    (n,v) = np.divmod(trueA+np.pi, 2*np.pi)
    v -= np.pi                                # v in [-π, π[
    sqte = np.sqrt(1-e*e)
    E = 2*np.arctan(np.tan(v/2)*(1-e)/sqte)+trueA-v
    return E - e*sqte*np.sin(v)/(1+e*np.cos(v))

#
#  computes the true longitude from the mean longitude (=time from refL)
#      the default reference longitude refL is 0 (vernal point, used for perL)
#      the true anomaly of the reference point is: refA = refL-perL+np.pi = position of spring equinox (or other ref) versus perihelion
#      the mean anomaly of our point is meanL+meanAnomalie(e,refA) = time since reference point
#
def trueLongitude(meanL,e,perL,refL=0):
    return trueAnomalie(e,meanL+meanAnomalie(e,refL-perL+np.pi))+perL-np.pi


###################
#
#  length of season, in days, function of true longitudes
#
def length_of_season(lon1,lon2,e,per):
    d_ano = meanAnomalie(e,lon2-per+np.pi)- meanAnomalie(e,lon1-per+np.pi)
    return d_ano*365.2425/2/np.pi



#
#  elliptic integral of the 2nd kind = integral from 0 to phi of sqrt(Max(0,1-m (sinx)^2))dx
#  Note:
#    the scipy implementation 'ellipeinc' does not work for m>1, therefore the use of Carlson
#    integrals 'elliprf' and 'elliprd'
#  Note:
#    the integrand sqrt( 1-m (sinx)^2 ) becomes complex (imaginary) when 1-m (sinx)^2 < 0
#    (this corresponds to 'polar night' cases) therefore the Max(0,...) cut-off
#    To have a nice continuous function for all values of 'phi' it is necessary to add periodically
#    the "complete elliptic" part ellipE(π/2,m):
#      n = (phi+π/2) div π
#      ellipE(phi,m) = 2 n ellipE(m) + ellipE(phi - nπ, m)
#  This corresponds to the Mathematica function Re[EllipticE[phi,m]]
#
def ellipE(phi,m):
    (n,xphi) = np.divmod(phi+np.pi/2, np.pi)
    xphi -= np.pi/2           #  phi == xphi + n*pi   &&   -pi/2 <= xphi < pi/2
    s = 1 - 2*(n%2)           #  s = (-1)^n
    sg = np.sign(xphi)
    
    def ellipE_(z,m):
        if z==0 and m==1:
            return 1
        else:
            return elliprf(z+m-1,z,z+m)-m*elliprd(z+m-1,z,z+m)/3
    
    if xphi==0:   # probably a test like 'abs(xphi)<verysmall' would be safer...
        e = 0
    else:
        c = np.square(1/np.sin(xphi))
        z = max(0,c-m)
        #e = sg*(elliprf(z+m-1,z,z+m)-m*elliprd(z+m-1,z,z+m)/3)
        e = sg * ellipE_(z,m)
    
    #e = sg*(elliprf(c-1,c-m,c)-m*elliprd(c-1,c-m,c)/3)
    #e = (sg/np.sqrt(c))*(elliprf(1-1/c,1-m/c,1)-(m/c)*elliprd(1-1/c,1-m/c,1)/3)
    #sinphi = np.sin(xphi)
    #sinphi2 = np.square(sinphi)
    #e = sg*sinphi*(elliprf(1-sinphi2,1-m*sinphi2,1)-m*sinphi2*elliprd(1-sinphi2,1-m*sinphi2,1)/3)
    #print('e = ',sg*sinphi*(elliprf(1-sinphi2,1-m*sinphi2,1)-m*sinphi2*elliprd(1-sinphi2,1-m*sinphi2,1)/3))
    if n==0:
        k = 0
    else:
        z = max(0,1-m)
        #k = (elliprf(z+m-1,z,z+m)-m*elliprd(z+m-1,z,z+m)/3)
        k = ellipE_(z,m)
    return 2*n*k + e
'''
#Mathematica
#  Re[EllipticF[phi,m]]
#
def ellipF(phi,m):
    (n,xphi) = np.divmod(phi+np.pi/2, np.pi)
    xphi -= np.pi/2           #  phi == xphi + n*pi   &&   -pi/2 <= xphi < pi/2
    s = 1 - 2*(n%2)           #  s = (-1)^n
    sg = np.sign(xphi)

    if xphi==0:   # probably a test like 'abs(xphi)<verysmall' would be safer...
        e = 0
    else:
        c = np.square(1/np.sin(xphi))
        z = max(0,c-m)
        e = sg*elliprf(z+m-1,z,z+m)
        #print("e,z+m-1,z,z+m = ",e,' ',z+m-1,' ',z,' ',z+m)
    if n==0:
        k = 0
    else:
        z = max(0,1-m)
        k = elliprf(z+m-1,z,z+m)
    return 2*n*k + e
    
#Mathematica
#  Re[EllipticPi[s2,phi,m]]
#
def ellipPi(s2,phi,m):
    (n,xphi) = np.divmod(phi+np.pi/2, np.pi)
    xphi -= np.pi/2           #  phi == xphi + n*pi   &&   -pi/2 <= xphi < pi/2
    s = 1 - 2*(n%2)           #  s = (-1)^n
    sg = np.sign(xphi)
    
    if xphi==0:   # probably a test like 'abs(xphi)<verysmall' would be safer...
        e = 0
    else:
        c = np.square(1/np.sin(xphi))
        z = max(0,c-m)
        e = sg*(elliprf(z+m-1,z,z+m)+s2*elliprj(z+m-1,z,z+m,z+m-s2)/3)
    if n==0:
        k = 0
    else:
        z = max(0,1-m)
        k = (elliprf(z+m-1,z,z+m)+s2*elliprj(z+m-1,z,z+m,z+m-s2)/3)
    return 2*n*k + e
'''
def ellipP(s2,phi,m):     # = ellipF(phi,m)-(1-s2)*ellipPi(s2,phi,m)
    (n,xphi) = np.divmod(phi+np.pi/2, np.pi)
    xphi -= np.pi/2           #  phi == xphi + n*pi   &&   -pi/2 <= xphi < pi/2
    s = 1 - 2*(n%2)           #  s = (-1)^n
    sg = np.sign(xphi)
    
    def ellipP_(z,m):
        if z==0 and m==1:
            sq = np.sqrt(s2)
            return sq*np.arctanh(sq)
        else:
            return s2*elliprf(z+m-1,z,z+m)-(1-s2)*s2*elliprj(z+m-1,z,z+m,z+m-s2)/3

    if xphi==0:   # probably a test like 'abs(xphi)<verysmall' would be safer...
        e = 0
    else:
        c = np.square(1/np.sin(xphi))
        z = max(0,c-m)
        #e = sg*(s2*elliprf(z+m-1,z,z+m)-(1-s2)*s2*elliprj(z+m-1,z,z+m,z+m-s2)/3)
        e = sg*ellipP_(z,m)
    if n==0:
        k = 0
    else:
        z = max(0,1-m)
        #k = s2*elliprf(z+m-1,z,z+m)-(1-s2)*s2*elliprj(z+m-1,z,z+m,z+m-s2)/3
        k = ellipP_(z,m)
    return 2*n*k + e


#  useful functions
#    p = sin_phi*sin_lon*sin_obl
#    s = np.maximum( 0, 1 - sin_phi*sin_phi - sin_lon*sin_lon*sin_obl*sin_obl )
#    ac = arccos( -p/sqrt(s+p*p) ) = hour (in radians) of sunrise/sunset
#
def inso_ac(a,b):
    s = max(0,1-a*a-b*b)
    p = a*b
    sp2 = s+p*p
    if sp2>0 :
        return s, p, np.arccos( -p/np.sqrt(sp2) )
    else:
        return s, p, np.pi/2
#
#  dimensionless dayly inso at distance 'semi-major axis' of the Sun
#
def inso_g(a,b):
    s,p,ac = inso_ac( a, b )
    return (np.sqrt(s) + p*ac)/np.pi
#
#  h(a,b) = integral(g(a,x)dx) from 0 to b
#
def inso_h(a,b):
    s,p,ac = inso_ac( a,b )  #np.arccos( -a*b/np.sqrt(s+a*b*a*b) )
    sb2 = s+b*b
    if sb2>0 :
        return (np.arccos( -b/np.sqrt(sb2) ) + b*np.sqrt(s) - a*(1-b*b)*ac)/np.pi/2 + (a-1)/4
    else:
        return b/4

def inso_irrad(lon,phi,eps):
    sineps = np.sin(eps)
    sinphi = np.sin(phi)
    sinlon = np.sin(lon)
    s,p,ac = inso_ac( sineps*sinlon, sinphi )
    sp2 = s+p*p
    r1 = np.where(sp2>0, sinphi*sineps*(np.pi/2 - np.cos(lon)*ac), 0)
    cosphi = np.cos(phi)
    m = np.where(cosphi>0, np.square(sineps/cosphi), 0)
    r2 = np.where(cosphi>0, sinphi*sinphi*ellipP(sineps*sineps,lon,m)/cosphi + cosphi*ellipE(lon,m), 0)
    return r1+r2

###################
#
#  length of day, in hours, function of true longitude, latitude and obliquity (in radians)
#
def inso_length_of_day(lon,phi,eps):
    sineps = np.sin(eps)
    sinphi = np.sin(phi)
    sinlon = np.sin(lon)
    s,p,ac = inso_ac( sineps*sinlon, sinphi )
    return 24*ac/np.pi

###################
#
#   dimensionless (instantaneous) insolation - should be multiplied by solar constant
#   inputs
#       h: hour angle (radians) with noon = 0
#       lon: true longitude (radians)
#       phi: latitude (radians)
#       eps: obliquity (radians)
#       e: eccentricity
#       per: true longitude of perihelion (=climatic precession) (radians)
#
def inso_radians(h,lon,phi,eps,e,per):
    sindelta = np.sin(lon)*np.sin(eps)
    g = np.sin(phi)*sindelta + np.cos(h)*np.sin(phi)*np.sqrt(1-sindelta*sindelta)
    if g<=0:
        return 0
    else:
        ar = (1-e*np.cos(lon-per))/(1-e*e)    # ratio a/r
        return ar*ar*g

###################
#
#   dimensionless dayly insolation - should be multiplied by solar constant
#   inputs
#       lon: true longitude (radians)
#       phi: latitude (radians)
#       eps: obliquity (radians)
#       e: eccentricity
#       per: true longitude of perihelion (=climatic precession) (radians)
#
def inso_dayly_radians(lon,phi,eps,e,per):
    sineps = np.sin(eps)
    sinphi = np.sin(phi)
    sinlon = np.sin(lon)
    g = inso_g( sineps*sinlon, sinphi )
    ar = (1-e*np.cos(lon-per))/(1-e*e)    # ratio a/r
    return ar*ar*g
#
#   idem with
#       tr: time of the year (in radians) from reference refL (0 = spring equinox)
#
def inso_dayly_time_radians(tr,phi,eps,e,per,refL=0):
    return inso_dayly_radians(trueLongitude(tr,e,per,refL),phi,eps,e,per)

###################
#
#   integrated (dimensionless) insolation between 2 true longitudes - should be multiplied by solar constant
#
def inso_mean_radians(lon1,lon2,phi,eps,e,per):
    d_irrad = inso_irrad(lon2,phi,eps)-inso_irrad(lon1,phi,eps)
    d_ano = meanAnomalie(e,lon2-per+np.pi)- meanAnomalie(e,lon1-per+np.pi)
    pisq = np.pi*np.sqrt(1-e*e)
    return d_irrad/d_ano/pisq
#
#   idem between 2 mean longitudes (= time of the year)
#       tr: time of the year (in radians) from reference refL (0 = spring equinox)
#
def inso_mean_time_radians(tr1,tr2,phi,eps,e,per,refL=0):
    return inso_mean_radians(trueLongitude(tr1,e,per,refL),trueLongitude(tr2,e,per,refL),phi,eps,e,per)
#
#   ... the corresponding "Milankovitch" caloric seasons
#          = mean between 1/4 of a year before (-π/2) and after (+π/2) the soltice (summer or winter) (π/2 or 3π/2 vs vernal point)
#
def inso_caloric_summer_NH(phi,eps,e,per):
    return inso_mean_time_radians(-np.pi/2,np.pi/2,phi,eps,e,per,np.pi/2)

def inso_caloric_winter_NH(phi,eps,e,per):
    return inso_mean_time_radians(-np.pi/2,np.pi/2,phi,eps,e,per,3*np.pi/2)


###################
#
#   integrated (dimensionless) dayly insolation between 2 latitudes - should be multiplied by solar constant
#
def inso_mean_lat_radians(lon,phi1,phi2,eps,e,per):
    sineps = np.sin(eps)
    sinphi1 = np.sin(phi1)
    sinphi2 = np.sin(phi2)
    sinlon = np.sin(lon)
    g = (inso_h(sineps*sinlon,sinphi2) - inso_h(sineps*sinlon,sinphi1))/(sinphi2 - sinphi1)
    ar = (1-e*np.cos(lon-per))/(1-e*e)    # ratio a/r
    return ar*ar*g



#######################     END     #######################
#
#test when running: $ python inso.py

if __name__ == '__main__':

    deg_to_rad = np.pi/180.
    
    #  define timescale : between 0 and 1000 kyrBP, included... (the time unit in astro.py is 1000 years, from past to future)
    t0,t1 = (-1000,0.)
    t=np.arange(t0,t1+1,1)                     # -1000 to 0 included !
   
    
    #  choose astronomical solution
    astro_params = astro.AstroLaskar2004()
    #astro_params = astro.AstroBerger1978()
    
    #   check if in range
    if (not(astro_params.in_range(t0)) or not(astro_params.in_range(t1))):
        print("resquested timescale is beyond the available range")
        exit()
    
    #   get the astronomical parameters on the requested time scale
    ecc = astro_params.eccentricity(t)
    pre = astro_params.precession_angle(t)     #in radians
    obl = astro_params.obliquity(t)            #in radians

    #   print obliquity value at time t1 = 0 (today)
    print("obliquity = ",obl[-1]/deg_to_rad)

    #   print obliquity
    #obliq = obl/deg_to_rad
    #plt.plot(-t,obliq)
    #plt.show()
    
    #  choose solar constant, latitude and true longitude (simplified calendar?)
    solar_constante = 1365
    latitude = 65*deg_to_rad
    trueLon = 90*deg_to_rad

    #   print dayly inso, summer solstice 65°N, at time t1 = 0 (today)
    print("dayly inso, summer solstice 65°N = ",solar_constante*inso_dayly_radians(trueLon,latitude,obl[-1],ecc[-1],pre[-1]))
    inso65 = np.empty(len(t))
    for i in range(len(t)):
        inso65[i] = solar_constante*inso_dayly_radians(trueLon,latitude,obl[i],ecc[i],pre[i])
    plt.plot(-t,inso65)
    plt.show()

    print("dayly inso 65°N spring + 1/4 year = ",solar_constante*inso_dayly_radians(trueLongitude(np.pi/2,ecc[-1],pre[-1]),latitude,obl[-1],ecc[-1],pre[-1]))

    latitude2 = 75*deg_to_rad
    print("dayly inso, summer solstice 65-75°N = ",solar_constante*inso_mean_lat_radians(trueLon,latitude,latitude2,obl[-1],ecc[-1],pre[-1]))
    Minso65 = np.empty(len(t))
    for i in range(len(t)):
        Minso65[i] = solar_constante*inso_mean_lat_radians(trueLon,latitude,latitude2,obl[i],ecc[i],pre[i])
    plt.plot(-t,Minso65)
    plt.show()

    trueLon2 = 180*deg_to_rad
    print("mean inso 65°N (90-180°)= ",solar_constante*inso_mean_radians(trueLon,trueLon2,latitude,obl[-1],ecc[-1],pre[-1]))
    mean_inso65 = np.empty(len(t))
    for i in range(len(t)):
        mean_inso65[i] = solar_constante*inso_mean_radians(trueLon,trueLon2,latitude,obl[i],ecc[i],pre[i])
    plt.plot(-t,mean_inso65)
    plt.show()

    print("caloric summer inso 65°N = ",solar_constante*inso_caloric_summer_NH(latitude,obl[-1],ecc[-1],pre[-1]))
    caloricSummer = np.empty(len(t))
    for i in range(len(t)):
        caloricSummer[i] = solar_constante*inso_caloric_summer_NH(latitude,obl[i],ecc[i],pre[i])
    plt.plot(-t,caloricSummer)
    plt.show()





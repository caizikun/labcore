# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 16:49:36 2013

@author: zah
"""
from collections import defaultdict, namedtuple

from django.core.exceptions import ObjectDoesNotExist

from device_adapters import TestDevice, USBDevice


active_interfaces = ( 
                     TestDevice,
                     USBDevice,
            )
            
def test_mode():
    global active_interfaces
    active_interfaces = (TestDevice,)
            
active_devices = None

def find_all():    
    if active_devices is None:
        refresh_devices()
    return active_devices

def refresh_devices():
    global active_devices
    active_devices = defaultdict(list)
    for iface in active_interfaces:
        for name, product, device in iface.get_instruments():
            DevObj = namedtuple(name, ['product_id', 'device'])
            active_devices[name] += [DevObj(product, device)]
    active_devices = {name:device for iface in active_interfaces
            for (name, device) in iface.get_instruments() 
            }
                

def associate_known():
    from instruments import models
    instruments = []
    for devlist, device in find_all().items():
        try:
            ins = models.Instrument.objects.get(device_id = devname)
            ins.associate(device)
            instruments.append(ins)            
        except ObjectDoesNotExist:
            pass
    
    return instruments

def find_unknown():
    from instruments import models
    alldevs = find_all()
    unknown = {k: v for k,v in alldevs.items() 
        if not models.Instrument.objects.filter(device_id = k).exists()}
    return unknown
    

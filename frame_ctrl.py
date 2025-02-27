#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import struct
import sys
import time
import logging as LOGGER
import usb.core
from usb.util import *
from array import array
# the image must be in 1024x600 JPEG format

vendorId = 0x04e8 #Samsung

#List of codes taken from here: https://github.com/MOA-2011/3rdparty-plugins/blob/f11349bc643ac9664276734897c6ab9a4e1d58ba/LCD4linux/src/Photoframe.py
models = {
  'SPF72H':(0x200a, 0x200b),
  'SPF75H/76H':(0x200e, 0x200f),
  'SPF83H':(0x200c, 0x200d),
  'SPF85H/86H':(0x2012, 0x2013),
  'SPF85P/86P':(0x2016, 0x2017),
  'SPF87Hold':(0x2025, 0x2026), #old firmware
  'SPF105P':(0x201c, 0x201b),
  'SPF107H':(0x2035, 0x2036),
  'SPF107Hold':(0x2027, 0x2028), #old firmware
  'SPF700T':(0x204f, 0x2050)
  }

chunkSize = 0x4000
bufferSize = 0x20000

def storageToDisplay(dev):
  LOGGER.debug("Setting device to display mode")
  try:
    dev.ctrl_transfer(CTRL_TYPE_STANDARD | CTRL_IN | CTRL_RECIPIENT_DEVICE, 0x06, 0xfe, 0xfe, 0xfe)
  except usb.core.USBError as e:
    if e.errno not in [5,19]: #switching command always disconnect the device. 5 = I/O Error. Seems to be generated during disconnect. 19 = No such device
      raise e

def displayModeSetup(dev):
  LOGGER.debug("Sending setup commands to device")
  expected = array('B',[3])
  result = dev.ctrl_transfer(CTRL_TYPE_VENDOR | CTRL_IN | CTRL_RECIPIENT_DEVICE, 0x04, 0x00, 0x00, 0x01)
  if result != expected:
    LOGGER.error(f"Warning: Expected  {expected}  but got {result}")

def paddedBytes(buf, size):
  diff = size - len(buf)
  return buf + bytes(b'\x00') * diff

def chunkyWrite(dev, buf):
  for pos in range(0, bufferSize, chunkSize):
    dev.write(0x02, buf[pos:pos+chunkSize])

def writeImage(dev, content : bytes):
  size = struct.pack('I', len(content))
  header = b'\xa5\x5a\x09\x04' + size + b'\x46\x00\x00\x00'
  content = header + content

  for pos in range(0, len(content), bufferSize):
    buf = paddedBytes(content[pos:pos+bufferSize], bufferSize)
    chunkyWrite(dev, buf)
  
def showImageModel(content : bytes, model : str) -> bool:
  v=models[model]
  dev = usb.core.find(idVendor=vendorId, idProduct=v[0])
  if dev:
    LOGGER.debug(f"Found {model} in storage mode")
    storageToDisplay(dev)
    time.sleep(2)
    dev = None
  if not dev:
    dev = usb.core.find(idVendor=vendorId, idProduct=v[1])

  if dev:
    LOGGER.debug(f"Found {model} in display mode")
    if not dev.get_active_configuration():
      dev.set_configuration() #lock the USB port
    displayModeSetup(dev)
    writeImage(dev, content)
    usb.util.dispose_resources(dev) #release the USB port
    return True   

def showImage(content : bytes, frameModel : str = None) -> bool:
  ret = False
  if content:
    if frameModel:
      ret = showImageModel(content, frameModel)
    else:
      for model in models:
        ret = showImageModel(content, model)
        if ret: return ret
    if not ret:
      LOGGER.error("No supported devices found")
  return ret

def main():
  inBuffer = None
  if len(sys.argv) < 2 or sys.argv[1] == "-":
    inBuffer = sys.stdin
  else:
    with  open(sys.argv[1],"rb") as file:
      inBuffer = file.read()
  ret = showImage(inBuffer)
  if ret: return 0 #success
  return 1 # failure

if __name__ == '__main__':
  LOGGER.basicConfig(level=config.LOGLEVEL, format="%(asctime)s %(levelname)s:%(name)s:%(message)s")
  sys.exit(main())

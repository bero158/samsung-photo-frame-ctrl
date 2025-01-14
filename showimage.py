#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import frame_ctrl
import sys
import logging as LOGGER
import imgutils as imgutils
import argparse
import txt2img
from os import path as osp
from dynaconf import Dynaconf
from PIL import Image, ImageColor

myPath = osp.realpath(osp.dirname(__file__))
settings = Dynaconf(
    envvar_prefix="FRAME",
    settings_files=[osp.join(myPath,'settings.toml'), osp.join(myPath,'.secrets.toml') ]
)
def main():
   parser = argparse.ArgumentParser(
                    prog='show-image',
                    description='This software renders image on Samsung Photo Frame connected to a USB port',
                    epilog="""
                    If there's no --input or specified the software reads from stdin.
                    """)
   parser.add_argument('-i','--input', help="Input image file")
   parser.add_argument('-t','--text', help="Reads text from stdin")
   parser.add_argument('-ti','--textinput', help="Input text file. '-' reads text from stdin")
   parser.add_argument('-v', '--verbose', action='store_true') 
   parser.add_argument('-bc', '--backcolor', help="Back color (black, white etc.)", type=ImageColor.colormap.get)
   parser.add_argument('-tc', '--textcolor', help="Text color", default='white', type=ImageColor.colormap.get)
   parser.add_argument('-pw', '--pwidth', help="Picture Width", default=settings.FRAME.IMG_SIZE[0], type=int)
   parser.add_argument('-ph', '--pheight', help="Picture Height", default=settings.FRAME.IMG_SIZE[1], type=int)
  
    
   args = parser.parse_args()
   logLevel : LOGGER = LOGGER.DEBUG if args.verbose else LOGGER.ERROR
   LOGGER.basicConfig(level=logLevel, format="%(asctime)s %(levelname)s:%(name)s:%(message)s")
   LOGGER.info("Starting")
   size = (int(args.pwidth),int(args.pheight))
   backcolor : str = args.backcolor if args.backcolor else 'black' #set default color
   if args.input:
      backcolor = (*ImageColor.getrgb(backcolor),128) if backcolor else (0, 0, 0, 0) #half transparency if backcolor is set. Othervise full transparency

   show : Image = None
   inBuffer = None
   if args.input:
     LOGGER.debug(f"Reading {args.input}")
     show = imgutils.resize_and_center(args.input)
   elif args.textinput:
     LOGGER.debug(f"Creating Image from text {args.textinput}")
     # create the image from the text
     txtImg : Image = txt2img.createImage(text=args.textinput,size=size)
     if args.input:
      txt2img.addBgImage(txtImg, args.input)
     show = imgutils.resize_and_centerImg(txtImg)
   elif args.text:
     # create the image from text from stdin
     inputText = sys.stdin.read()
     LOGGER.debug(f"Creating Image from text {args.inputText}")
     txtImg : Image = txt2img.createImage(inputText,size=size)
     if args.bgimage:
      txt2img.addBgImage(txtImg, args.input)
     show = imgutils.resize_and_centerImg(txtImg)
   else:
      LOGGER.debug("Reading image from stdin")
      show = imgutils.resize_and_center(sys.stdin.buffer, targetSize=settings.FRAME.IMG_SIZE)
   return frame_ctrl.showImage(imgutils.imgToBytes(show))

if (__name__ == "__main__"):
   main()
#!/usr/bin/env python3
"""Capture a still + 3 s H.264 clip from Camera Module 3 to microSD #1 (video card)."""
import os, time
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
VID = "/mnt/sd_video"  # uSD#1 mount
os.makedirs(VID, exist_ok=True)
cam = Picamera2()
cam.configure(cam.create_video_configuration(main={"size":(1920,1080)}))
cam.start(); time.sleep(1)
cam.capture_file(f"{VID}/selftest_{int(time.time())}.jpg")
enc = H264Encoder(bitrate=10_000_000)
cam.start_recording(enc, f"{VID}/selftest_{int(time.time())}.h264")
time.sleep(3); cam.stop_recording(); cam.stop()
print("camera OK: still + 3s clip written to", VID)

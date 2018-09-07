import numpy as np
import camerica_hw as hw
import sys
import time

udmabuf = hw.UDMABuf("udmabuf0")
regs = hw.Registers()
fq = hw.Framequeue(udmabuf, regs)

fq.start()

frames = 0
dropped = 0

fout = open(sys.argv[1], "wb")

try:
	while True:
		frame_data, just_dropped = fq.get_new_frames()
		dropped += just_dropped
		frames += len(frame_data)
		for frame, histo in frame_data:
			fout.write(frame.data)
			fout.write(histo.data)
		print("\rFrames: {:6d}    Dropped: {:6d}".format(frames, dropped), end="")
		sys.stdout.flush()
		time.sleep(0.03)
except:
	fq.stop()
	raise
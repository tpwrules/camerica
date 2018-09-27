import numpy as np
import camerica_hw as hw
import sys
import time
import vidfile

vf = vidfile.VidfileWriter(sys.argv[1], 320, 256, 60)

udmabuf = hw.UDMABuf("udmabuf0")
regs = hw.Registers()
fq = hw.Framequeue(udmabuf, regs)

fq.start()

frames = 0
dropped = 0

try:
    while True:
        frame_data, just_dropped = fq.get_new_frames()
        dropped += just_dropped
        for frame, histo in frame_data:
            vf.write(frames, frame, histo)
            frames += 1
        print("\rFrames: {:6d}    Dropped: {:6d}".format(frames, dropped), end="")
        sys.stdout.flush()
        time.sleep(0.03)
except:
    fq.stop()
    print("\nFLUSHING VIDFILE. THIS WILL TAKE A BIT.")
    vf.close()
    raise
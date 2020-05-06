import time
import pyaudio
import numpy as np
from threading import Thread, Lock

class SoundStream(object):
    def __init__(self, src=0):
        self.started = False
        self.read_lock = Lock()
        self.sound = 0
        self.chunk = np.zeros(1024, dtype=np.int16)

        self.p = pyaudio.PyAudio()
        input_index = self.get_channels(self.p)

        self.channels = 1
        self.rate = 16000
        self.format = pyaudio.paInt16
        self.stream = self.p.open(
                        format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input_device_index = input_index,
                        input=True,
                        stream_callback=self.callback)
    
    def start(self):
        if self.started:
            print("already started!!")
            return None

        self.started = True
        self.thread = Thread(target=self.update, args=())
        self.thread.start()

        return self

    def update(self):
        while self.started:
            self.read_lock.acquire()
            self.sound = int(self.chunk.max())
            self.read_lock.release()

    def read(self):
        self.read_lock.acquire()
        sound = self.sound
        self.read_lock.release()
        return sound

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stream.release()

    def get_channels(self, p):
        output_index = self.p.get_default_input_device_info()['index']
        for idx in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(idx)
            if 'BlackHole' in info['name']:
                output_index = info['index']
        return output_index
    
    def callback(self, in_data, frame_count, time_info, status):
        self.chunk = np.frombuffer(in_data, np.int16).copy()
        return (in_data, pyaudio.paContinue)


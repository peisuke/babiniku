import pyaudio
import time
import numpy as np
import threading
import librosa

class WorkerThread(threading.Thread):
    def __init__(self):
        super(WorkerThread, self).__init__()
        self.is_stop = False
        self.lock = threading.Lock()
        self.buffer = []
        self.result = []

    def stop(self):
        self.is_stop = True
        self.join()

    def run(self):
        while not self.is_stop:
            if len(self.buffer) > 0:
                with self.lock:
                    buf = self.buffer[0]
                    self.buffer = self.buffer[1:]

                sample = np.concatenate([b['data'] for b in buf])

                # pitch sift
                sample = sample.astype(np.float)
                sample = librosa.effects.pitch_shift(sample.astype(np.float), 16000, n_steps=16)
                sample = sample.astype(np.int16)

                # fft
                #orig = sample.copy()
                #spec = np.fft.rfft(sample)
                #sample = np.fft.irfft(spec).real.astype(np.int16)

                sample = sample.reshape(16, -1)
                buf = [{'data': s, 'index': b['index']} for b, s in zip(buf, sample)]

                with self.lock:
                    self.result.append(buf[4:-4])

            time.sleep(0.01)

    def push_chunk(self, chunk):
        with self.lock:
            self.buffer.append(chunk)
    
    def pop_chunk(self):
        result = [] 
        with self.lock:
            if len(self.result) > 0:
                result.extend(self.result)
                self.result = []

        return result

class AudioFilter():
    def __init__(self, worker):
        self.p = pyaudio.PyAudio()
        input_index, output_index = self.get_channels(self.p)

        self.channels = 1
        self.rate = 16000
        self.format = pyaudio.paInt16
        self.stream = self.p.open(
                        format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input_device_index = input_index,
                        output_device_index = output_index,
                        output=True,
                        input=True,
                        stream_callback=self.callback)

        # Status:0が待ち
        self.age = 0
        self.index = 0
        self.chunk = []
        self.buffer = []
        self.worker = worker

    def get_channels(self, p):
        input_index = self.p.get_default_input_device_info()['index']
        for idx in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(idx)
            if 'BlackHole' in info['name']:
                output_index = info['index']
        return input_index, output_index

    def callback(self, in_data, frame_count, time_info, status):
        decoded_data = np.frombuffer(in_data, np.int16).copy()

        self.chunk.append({'data': decoded_data, 'index': self.index})
        self.index += 1

        if decoded_data.max() > 1000:
            self.age = 16 
        else:
            self.age = max(0, self.age - 1)

        if self.age == 0:
            self.chunk = self.chunk[-4:]
        else:
            if len(self.chunk) >= 16:
                # push self.chunk[0:16]
                self.worker.push_chunk(self.chunk[0:16])

                # remove self.chunk[0:8]
                self.chunk = self.chunk[8:]

        # Pop chunk to current list
        ret = self.worker.pop_chunk()
        for r in ret:
            self.buffer.extend(r)
        
        # Get head from current list
        if len(self.buffer) > 0:
            ret = self.buffer[0]
            print(ret['index'], self.index)
            self.buffer = self.buffer[1:]
            data = ret['data']
        else:
            data = np.zeros(1024, dtype=np.int16)
        
        out_data = data.tobytes()

        return (out_data, pyaudio.paContinue)

    def close(self):
        self.p.terminate()

if __name__ == "__main__":
    worker_th = WorkerThread()
    worker_th.setDaemon(True)
    worker_th.start()

    af = AudioFilter(worker_th)

    af.stream.start_stream()

    while af.stream.is_active():
        time.sleep(0.1)

    worker_th.stop()
    af.stream.stop_stream()
    af.stream.close()
    af.close()

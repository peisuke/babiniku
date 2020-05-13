import pyaudio
import time
import numpy as np
from scipy.stats import norm
import threading
import librosa
import pyworld

# https://tam5917.hatenablog.com/entry/2019/04/28/123934 
def convert(signal):
    f0_rate = 2.4
    sp_rate = 0.78
    sample_rate = 16000

    f0, t = pyworld.dio(signal, sample_rate)
    f0 = pyworld.stonemask(signal, f0, t, sample_rate)
    sp = pyworld.cheaptrick(signal, f0, t, sample_rate)
    ap = pyworld.d4c(signal, f0, t, sample_rate)

    modified_f0 = f0_rate * f0

    # フォルマントシフト（周波数軸の一様な伸縮）
    modified_sp = np.zeros_like(sp)
    sp_range = int(modified_sp.shape[1] * sp_rate)
    for f in range(modified_sp.shape[1]):
        if (f < sp_range):
            if sp_rate >= 1.0:
                modified_sp[:, f] = sp[:, int(f / sp_rate)]
            else:
                modified_sp[:, f] = sp[:, int(sp_rate * f)]
        else:
            modified_sp[:, f] = sp[:, f]

    y = pyworld.synthesize(modified_f0, modified_sp, ap, sample_rate)

    return y

class WorkerThread(threading.Thread):
    def __init__(self, block_length, margin_length):
        super(WorkerThread, self).__init__()
        self.is_stop = False
        self.lock = threading.Lock()
        self.buffer = []
        self.result = []

        self.prev_samples = []
        
    def stop(self):
        self.is_stop = True
        self.join()

    def run(self):
        while not self.is_stop:
            if len(self.buffer) > 0:
                with self.lock:
                    buf = self.buffer[0]
                    self.buffer = self.buffer[1:]
               
                chunk_size = len(buf[0]['data'])
                sample = np.concatenate([b['data'] for b in buf])

                # pitch sift
                sample = sample.astype(np.float64)
                sample = convert(sample)

                # overlap
                self.prev_samples.append(sample)

                length = len(sample)
                weight = norm.pdf(np.arange(0, length), length/2, length/8)

                caches = []
                wcaches = []
                for i, sample in enumerate(self.prev_samples):
                    pos = (len(self.prev_samples) - i) * chunk_size
                    if len(sample) >= pos + chunk_size:
                        cache = sample[pos:pos+chunk_size]
                        wcache = weight[pos:pos+chunk_size]
                        caches.append(cache)
                        wcaches.append(wcache)

                caches = np.asarray(caches)
                wcaches = np.asarray(wcaches)
                wcaches /= wcaches.sum(axis=0)
                sample = np.sum(wcaches * caches, axis=0)

                if len(self.prev_samples) >= 16:
                    self.prev_samples = self.prev_samples[1:]
            
                with self.lock:
                    self.result.extend(sample.tolist())
            else:
                time.sleep(0.01)

    def push_chunk(self, chunk):
        with self.lock:
            self.buffer.append(chunk)
    
    def pop_chunk(self, chunk_size):
        result = None
        with self.lock:
            if len(self.result) >= chunk_size:
                result = np.array(self.result[:chunk_size])
                self.result = self.result[chunk_size:]

        return result

class AudioFilter():
    def __init__(self, worker, block_length, margin_length):
        self.p = pyaudio.PyAudio()
        input_index, output_index = self.get_channels(self.p)

        self.channels = 1
        self.rate = 16000
        self.format = pyaudio.paInt16
        self.stream = self.p.open(
                        format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        frames_per_buffer=1024,
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

        self.block_length = block_length
        self.margin_length = margin_length

    def get_channels(self, p):
        input_index = self.p.get_default_input_device_info()['index']
        output_index = self.p.get_default_output_device_info()['index']
        #output_index = p.get_default_output_device_info()['index']
        for idx in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(idx)
            if 'BlackHole' in info['name']:
                output_index = info['index']
        return input_index, output_index

    def callback(self, in_data, frame_count, time_info, status):
        decoded_data = np.frombuffer(in_data, np.int16).copy()
        chunk_size = len(decoded_data)

        decoded_data = decoded_data.reshape(-1, 1024)
        for c in decoded_data:
            self.chunk.append({'data': c, 'index': self.index})
            self.index += 1
        
        #if decoded_data.max() > 1000:
        if decoded_data.max() > 0:
            self.age = self.block_length
        else:
            self.age = max(0, self.age - 1)

        if self.age == 0:
            self.chunk = self.chunk[-self.margin_length:]
        else:
            while len(self.chunk) >= self.block_length:
                # push self.chunk[0:16]
                self.worker.push_chunk(self.chunk[0:self.block_length])

                # remove self.chunk[0:8]
                self.chunk = self.chunk[1:]
        
        ## Pop chunk to current list
        ret = self.worker.pop_chunk(chunk_size)
        
        # Get head from current list
        if ret is not None:
            data = ret.astype(np.int16)
            print(len(data), data.dtype, data.max())
        else:
            data = np.zeros(chunk_size, dtype=np.int16)
        
        out_data = data.tobytes()

        return (out_data, pyaudio.paContinue)

    def close(self):
        self.p.terminate()

if __name__ == "__main__":
    block_length = 8
    margin_length = 1

    worker_th = WorkerThread(block_length, margin_length)
    worker_th.setDaemon(True)
    worker_th.start()

    af = AudioFilter(worker_th, block_length, margin_length)

    af.stream.start_stream()

    while af.stream.is_active():
        time.sleep(0.1)

    worker_th.stop()
    af.stream.stop_stream()
    af.stream.close()
    af.close()

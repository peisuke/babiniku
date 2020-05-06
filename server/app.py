from flask import Flask, jsonify
from camera import CameraStream
from sound import SoundStream
import cv2

app = Flask(__name__)

cap = CameraStream(1).start()
scap = SoundStream().start()

@app.route('/')
def index():
    """Video streaming home page."""
    direction, sound = gen_frame().__next__()
    return jsonify({'face': direction, 'sound': sound})

def gen_frame():
    """Video streaming generator function."""
    while cap:
        direction = cap.read()
        sound = scap.read()
       
        yield direction, sound

if __name__ == '__main__':

    app.run(host='0.0.0.0', debug=True, threaded=True)

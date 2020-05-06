from threading import Thread, Lock
import dlib
from imutils import face_utils
import numpy as np
import cv2

def face_landmark_find(img, face_detector, face_predictor):
    # 顔検出
    img_gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_detector(img_gry, 1)

    # 検出した全顔に対して処理
    landmarks = []
    for face in faces:
        # 顔のランドマーク検出
        landmark = face_predictor(img_gry, face)

        # 処理高速化のためランドマーク群をNumPy配列に変換(必須)
        landmark = face_utils.shape_to_np(landmark)
        landmarks.append(landmark)

        # ランドマーク描画
        for (x, y) in landmark:
            cv2.circle(img, (x, y), 1, (0, 0, 255), -1)

    return img, landmarks

def select_largest_landmark(lms):
    vs = []
    for lm in lms:
        x = lm[:,0].max() - lm[:,0].min()
        y = lm[:,1].max() - lm[:,1].min()
        v = x * y
        vs.append(v)
    idx = np.argmax(np.array(vs))
    
    return lms[idx]

def convert_to_direction(lm):
    object_pts = np.float32([[6.825897, 6.760612, 4.402142],
                             [1.330353, 7.122144, 6.903745],
                             [-1.330353, 7.122144, 6.903745],
                             [-6.825897, 6.760612, 4.402142],
                             [5.311432, 5.485328, 3.987654],
                             [1.789930, 5.393625, 4.413414],
                             [-1.789930, 5.393625, 4.413414],
                             [-5.311432, 5.485328, 3.987654],
                             [2.005628, 1.409845, 6.165652],
                             [-2.005628, 1.409845, 6.165652],
                             [2.774015, -2.080775, 5.048531],
                             [-2.774015, -2.080775, 5.048531],
                             [0.000000, -3.116408, 6.097667],
                             [0.000000, -7.415691, 4.070434]])
    
    image_pts = np.float32([lm[17], lm[21], lm[22], lm[26], lm[36], lm[39], lm[42], lm[45], lm[31], lm[35], lm[48], lm[54], lm[57], lm[8]])
    K = [6.5308391993466671e+002, 0.0, 3.1950000000000000e+002, 
        0.0, 6.5308391993466671e+002, 2.3950000000000000e+002,
        0.0, 0.0, 1.0]
    D = [7.0834633684407095e-002, 6.9140193737175351e-002, 0.0, 0.0, -1.3073460323689292e+000]
    cam_matrix = np.array(K).reshape(3, 3).astype(np.float32)
    dist_coeffs = np.array(D).reshape(5, 1).astype(np.float32)
    _, rotation_vec, translation_vec = cv2.solvePnP(object_pts, image_pts, cam_matrix, dist_coeffs)

    rotation_mat, _ = cv2.Rodrigues(rotation_vec)
    pose_mat = cv2.hconcat((rotation_mat, translation_vec))
    _, _, _, _, _, _, euler_angle = cv2.decomposeProjectionMatrix(pose_mat)
    return euler_angle.reshape(3).tolist()

class CameraStream(object):
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)

        predictor_path = 'shape_predictor_68_face_landmarks.dat'
        self.face_detector = dlib.get_frontal_face_detector()
        self.face_predictor = dlib.shape_predictor(predictor_path)

        self.direction = []
        self.started = False
        self.read_lock = Lock()

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
            grabbed, frame = self.stream.read()

            h, w, c = frame.shape
            h = h * 640 // w 
            img = cv2.resize(frame, (640, h))

            img, lms = face_landmark_find(img, self.face_detector, self.face_predictor)
            
            if len(lms) > 0:
                lm = select_largest_landmark(lms)
                direction = convert_to_direction(lm)
            
                self.read_lock.acquire()
                self.direction = direction
                self.read_lock.release()

    def read(self):
        self.read_lock.acquire()
        direction = self.direction.copy()
        self.read_lock.release()
        return direction

    def stop(self):
        self.started = False
        self.thread.join()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stream.release()

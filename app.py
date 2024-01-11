from flask import Flask, render_template, Response
from Camera.Stream import CameraStream
# from ai.model import YOLOV5 
from flask_executor import Executor
from Camera.HKcam import HKCam
import time
import os
import cv2


# === 全局变量 ===
# CLASSES = ['down', 'person']
# tumble_predict = YOLOV5("./ai/onnx/tumble.onnx", CLASSES)
# localCamera = camera([tumble_predict])
camIP ='192.168.1.64'
DEV_PORT = 8000
username ='admin'
password = 'haut2023'

HIK= HKCam(camIP,username,password)
os.chdir(os.path.dirname(__file__))
# === 全局变量 ===

app = Flask(__name__)
executor = Executor(app)

camera_stream = CameraStream()

def read_camera(HIK):
    # 创建一个循环，用于不断地读取摄像头的图像并调用 camera_stream.update_frame
    try:
        print("摄像头开启")
        while True:
            n_stamp, img = HIK.read()

            """
                TODO: 
            """
            
            _, bytes_arr = cv2.imencode('.jpg', img)

            camera_stream.update_frame(bytes_arr.tobytes())
    finally:
        print("摄像头关闭")
        HIK.release()


# === 全局变量 ===


@app.route("/")
def index():
    return render_template('index.html') 

@app.route('/video_feed')
def video_feed():
    global camera_stream
    frames = camera_stream.subscribe()
    def generate():
        while True:
            nonlocal frames
            frame = frames.get_frame() # queue为空会阻塞线程
            yield (b'--frame\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace;boundary=frame')
    

with app.test_request_context():
    executor.submit(read_camera, HIK)


if __name__ == '__main__':

    app.run(host='0.0.0.0', debug=False, threaded=True)
    
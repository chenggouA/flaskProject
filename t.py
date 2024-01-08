from flask import Flask, render_template, Response
from Camera.LocalCamera import camera
from Camera.Stream import CameraStream
from ai.model import YOLOV5 
import cv2
app = Flask(__name__)


# === 全局变量 ===
CLASSES = ['down', 'person']
tumble_predict = YOLOV5("./ai/onnx/tumble.onnx", CLASSES)
localCamera = camera([tumble_predict])

camera_stream = CameraStream()

def read_camera():
    # 创建一个循环，用于不断地读取摄像头的图像并调用 camera_stream.update_frame
    cap = cv2.VideoCapture(0)
    try:
        while True:
            flag, frame = cap.read()
            if not flag:
                break
            _, bytes_arr = cv2.imencode('.jpg', frame)
            camera_stream.update_frame(bytes_arr.tobytes())
    finally:
        cap.release()



# === 全局变量 ===
import threading    
@app.route("/a")
def bfr():
    print("开启线程")
    t = threading.Thread(target=read_camera)
    t.start()
    return 1123

@app.route("/")
def index():
    return render_template('index.html') 


# def gen(camera):
#     for frame in camera.get_frame():
#         yield (b'--frame\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
@app.route('/video_feed')
def video_feed():
    print("用户开始播放")
    queue = camera_stream.subscribe()
    try:
        def generate():
            while True:
                frame = queue.get() # queue为空会阻塞线程
                yield (b'--frame\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        return Response(generate(), mimetype='multipart/x-mixed-replace;boundary=frame')
    finally:
        print("用户停止播放")
        camera_stream.unsubscribe(queue)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, threaded=True)
    # while True:
    #     for i in gen(localCamera):
    #         print(i)
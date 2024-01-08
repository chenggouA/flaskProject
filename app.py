from flask import Flask, render_template, Response
from Camera.LocalCamera import camera
from Camera.Stream import CameraStream
from ai.model import YOLOV5 
from flask_executor import Executor
import cv2
app = Flask(__name__)
executor = Executor(app)


# === 全局变量 ===
# CLASSES = ['down', 'person']
# tumble_predict = YOLOV5("./ai/onnx/tumble.onnx", CLASSES)
# localCamera = camera([tumble_predict])

camera_stream = CameraStream(0)



# === 全局变量 ===


@app.route("/")
def index():
    return render_template('index.html') 

@app.route('/video_feed')
def video_feed():
    # try:
    def gen():
        print("用户开始播放")
        frame = camera_stream.subscribe()
        while True:
            yield camera_stream.get_frame(frame)
    return Response(gen(), mimetype='multipart/x-mixed-replace;boundary=frame')
    # finally:
    #     print("用户停止播放")
        # camera_stream.unsubscribe(frame)



if __name__ == '__main__':

    app.run(host='0.0.0.0', debug=False, threaded=True)
    
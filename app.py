from flask import Flask, render_template, Response
from Camera.LocalCamera import camera
from ai.model import YOLOV5 
app = Flask(__name__)


# === 全局变量 ===
CLASSES = ['down', 'person']
tumble_predict = YOLOV5("./ai/onnx/tumble.onnx", CLASSES)
localCamera = camera([tumble_predict])

# === 全局变量 ===

@app.route("/")
def index():
    return render_template('index.html') 


def gen(camera):
    for frame in camera.get_frame():
        yield (b'--frame\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
@app.route('/video_feed')
def video_feed():
    return Response(gen(localCamera), mimetype='multipart/x-mixed-replace;boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
    
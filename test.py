from Camera.HKcam import HKCam
import time
import cv2
import os


camIP ='192.168.1.64'
DEV_PORT = 8000
username ='admin'
password = 'haut2023'

HIK= HKCam(camIP,username,password)
# 切换工作目录到当前代码文件
os.chdir(os.path.dirname(__file__))

last_stamp = 0
while True:
    t0 =time.time()
    n_stamp, img = HIK.read()
    last_stamp=n_stamp
    
    cv2.imshow("frame", img)
    kkk = cv2.waitKey(1)
    if kkk ==ord('q'):
        break
HIK.release()

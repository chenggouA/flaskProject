import onnxruntime
import cv2
import numpy as np
from .utils import Annotator, letterbox, colors
from time import time
class YOLOV5():
    def __init__(self, onnxpath, classes, img_size=640, stride=32):
        self.classes = classes
        self.onnx_session=onnxruntime.InferenceSession(onnxpath, providers=['CUDAExecutionProvider'])
        self.input_name=self.get_input_name()
        self.output_name=self.get_output_name()
        self.img_size = img_size
        self.stride = stride
    #-------------------------------------------------------
	#   获取输入输出的名字
	#-------------------------------------------------------
    def get_input_name(self):
        input_name=[]
        for node in self.onnx_session.get_inputs():
            input_name.append(node.name)
        return input_name
    def get_output_name(self):
        output_name=[]
        for node in self.onnx_session.get_outputs():
            output_name.append(node.name)
        return output_name
    #-------------------------------------------------------
	#   输入图像
	#-------------------------------------------------------
    def get_input_feed(self,img_tensor):
        input_feed={}
        for name in self.input_name:
            input_feed[name]=img_tensor
        return input_feed
    
    

    def xywh2xyxy(self, x):
        # [x, y, w, h] to [x1, y1, x2, y2]
        y = np.copy(x)
        y[:, 0] = x[:, 0] - x[:, 2] / 2
        y[:, 1] = x[:, 1] - x[:, 3] / 2
        y[:, 2] = x[:, 0] + x[:, 2] / 2
        y[:, 3] = x[:, 1] + x[:, 3] / 2
        return y
    
    def nms(self, dets, thresh):
        x1 = dets[:, 0]
        y1 = dets[:, 1]
        x2 = dets[:, 2]
        y2 = dets[:, 3]
        #-------------------------------------------------------
        #   计算框的面积
        #	置信度从大到小排序
        #-------------------------------------------------------
        areas = (y2 - y1 + 1) * (x2 - x1 + 1)
        scores = dets[:, 4]
        keep = []
        index = scores.argsort()[::-1] 

        while index.size > 0:
            i = index[0]
            keep.append(i)
            #-------------------------------------------------------
            #   计算相交面积
            #	1.相交
            #	2.不相交
            #-------------------------------------------------------
            x11 = np.maximum(x1[i], x1[index[1:]]) 
            y11 = np.maximum(y1[i], y1[index[1:]])
            x22 = np.minimum(x2[i], x2[index[1:]])
            y22 = np.minimum(y2[i], y2[index[1:]])

            w = np.maximum(0, x22 - x11 + 1)                              
            h = np.maximum(0, y22 - y11 + 1) 

            overlaps = w * h
            #-------------------------------------------------------
            #   计算该框与其它框的IOU，去除掉重复的框，即IOU值大的框
            #	IOU小于thresh的框保留下来
            #-------------------------------------------------------
            ious = overlaps / (areas[i] + areas[index[1:]] - overlaps)
            idx = np.where(ious <= thresh)[0]
            index = index[idx + 1]
        return keep
    def filter_box(self, org_box, conf_thres, iou_thres): #过滤掉无用的框
        #-------------------------------------------------------
        #   删除为1的维度
        #	删除置信度小于conf_thres的BOX
        #-------------------------------------------------------
        org_box=np.squeeze(org_box)
        conf = org_box[..., 4] > conf_thres
        box = org_box[conf == True]
        #-------------------------------------------------------
        #	通过argmax获取置信度最大的类别
        #-------------------------------------------------------
        cls_cinf = box[..., 5:]
        cls = []
        for i in range(len(cls_cinf)):
            cls.append(int(np.argmax(cls_cinf[i])))
        all_cls = list(set(cls))     
        #-------------------------------------------------------
        #   分别对每个类别进行过滤
        #	1.将第6列元素替换为类别下标
        #	2.xywh2xyxy 坐标转换
        #	3.经过非极大抑制后输出的BOX下标
        #	4.利用下标取出非极大抑制后的BOX
        #-------------------------------------------------------
        output = []
        for i in range(len(all_cls)):
            curr_cls = all_cls[i]
            curr_cls_box = []
            curr_out_box = []
            for j in range(len(cls)):
                if cls[j] == curr_cls:
                    box[j][5] = curr_cls
                    curr_cls_box.append(box[j][:6])
            curr_cls_box = np.array(curr_cls_box)
            # curr_cls_box_old = np.copy(curr_cls_box)
            curr_cls_box = self.xywh2xyxy(curr_cls_box)
            curr_out_box = self.nms(curr_cls_box,iou_thres)
            for k in curr_out_box:
                output.append(curr_cls_box[k])
        output = np.array(output)

        return output
    
    def scale_coords(self, img1_shape, coords, img0_shape, ratio_pad=None):
    # 将坐标(xyxy)从img1_shape重新缩放到img0_shape
        if ratio_pad is None:  # calculate from img0_shape
            gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])  # gain  = old / new
            pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2  # wh padding
        else:
            gain = ratio_pad[0][0]
            pad = ratio_pad[1]

        coords[:, [0, 2]] -= pad[0]  # x padding
        coords[:, [1, 3]] -= pad[1]  # y padding
        coords[:, :4] /= gain
        self.clip_coords(coords, img0_shape)
        return coords


    def clip_coords(self, boxes, shape):
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, shape[1])  # x1, x2
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, shape[0])  # y1, y2

    def draw(self, image, box_data):  
        #-------------------------------------------------------
        #	取整，方便画框
        #-------------------------------------------------------
        boxes=box_data[...,:4].astype(np.int32) 
        scores=box_data[...,4]
        classes=box_data[...,5].astype(np.int32) 

        for box, score, cl in zip(boxes, scores, classes):
            top, left, right, bottom = box
            print('class: {}, score: {}'.format(self.classes[cl], score))
            print('box coordinate left,top,right,down: [{}, {}, {}, {}]'.format(top, left, right, bottom))

            cv2.rectangle(image, (top, left), (right, bottom), (255, 0, 0), 2)
            cv2.putText(image, '{0} {1:.2f}'.format(self.classes[cl], score),
                        (top, left ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 2)
            
    #-------------------------------------------------------
	#   1.cv2读取图像并resize
	#	2.图像转BGR2RGB和HWC2CHW
	#	3.图像归一化
	#	4.图像增加维度
	#	5.onnx_session 推理
	#-------------------------------------------------------
    def process(self, img0):
        img = letterbox(img0, [self.img_size] * 2, stride=self.stride, auto=False)[0]

        img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        img = img.astype(np.float32)
        img = np.ascontiguousarray(img) # ascontiguousarray 返回一个内存连续的数组。

        return img, img0

    
    def inference(self, _img):



        img, im0s = self.process(_img)

        img /= 255 # 0 - 255 to 0.0 - 1.0

        if len(img.shape) == 3:
            img = img[None] # 添加一个batch维度
        input_feed = self.get_input_feed(img)

        s = time()
        pred = self.onnx_session.run(None, input_feed)[0]



        pred = self.filter_box(pred, 0.5, 0.5)

        e = time()
        
        if len(pred) == 0:
            return im0s
        im0 = im0s.copy()
        annotator = Annotator(im0, example=str(self.classes))
        # 重新缩放从img_size到im0大小的框
        pred[:, :4] = self.scale_coords((self.img_size, self.img_size), pred[:, :4], im0.shape).round()

        for *xyxy, conf, cls in reversed(pred):
            c= int(cls)

            print(f'{self.classes[c]} {conf:.2f}')
            label = f'{self.classes[c]} {conf:.2f}'
            # label = f'{conf:.2f}'
            # label = ""

            annotator.box_label(xyxy, label, color=colors(c, True))
        
        im0 = annotator.result()
        # print(f"fps: {int(1.0 / (e - s))}")
        return im0


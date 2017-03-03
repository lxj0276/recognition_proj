#!/usr/bin/env python
#coding:utf-8
import cv2
import numpy as np

def readImg(path):
	return cv2.imread(path)

def grayImg(img):
	return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 图片宽度对应数组列数，高度对应数组行数
def getImgSize(img):
	return (img.shape[1], img.shape[0])

# 根据宽高创建纯白图，宽高对应数组的列数和行数
def createWhiteImg(size):
	return np.uint8(np.ones((size[1], size[0])) * 255)

def createBlackImg(size):
	return np.uint8(np.zeros((size[1], size[0])))

def findContours(grayImg, mode = cv2.RETR_EXTERNAL, method = cv2.CHAIN_APPROX_SIMPLE):
	_, contours, hierarchy = cv2.findContours(grayImg, mode, method)
	return contours, hierarchy

def drawContours(img, contours, color = (0, 0, 0), thickness = -1):
	cv2.drawContours(img, contours, -1, color, thickness)  
	return img

def binaryInv(grayImg):
	thresh, bimg = cv2.threshold(grayImg, 0, 255, cv2.THRESH_OTSU)
	return bimg

def binaryThresh(grayImg, thresh1 = 0, thresh2 = 255):
	thresh, bimg = cv2.threshold(grayImg, thresh1, thresh2, cv2.THRESH_BINARY)
	return bimg

def getKernel(size):
	kernel = np.uint8(np.zeros(size))
	kw, kh = kernel.shape
	for x in range(kh):  
		kernel[x, kw / 2] = 1 
	for x in range(kw):  
		kernel[kh / 2, x] = 1 
	return kernel

# 将矩形定点按top-left, top-right, bottom-right, bottom-left顺序排列
def order_points(pts):
	rect = np.zeros((4, 2), dtype = "float32")
	# the top-left point will have the smallest sum, whereas
	# the bottom-right point will have the largest sum
	s = pts.sum(axis = 1)
	rect[0] = pts[np.argmin(s)]
	rect[2] = pts[np.argmax(s)]
	# top-right point will have the smallest difference,
	# whereas the bottom-left will have the largest difference
	diff = np.diff(pts, axis = 1)
	rect[1] = pts[np.argmin(diff)]
	rect[3] = pts[np.argmax(diff)]
	return rect

def erosion(grayImg, kernel = getKernel((4, 4)), iterations = 1):
	return cv2.erode(grayImg, kernel, iterations = iterations)

def dilation(grayImg, kernel = getKernel((4, 4)), iterations = 1):
	return cv2.dilate(grayImg, kernel, iterations = iterations)  

def sobel(grayImg):
	gradX = cv2.Sobel(grayImg, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
	gradY = cv2.Sobel(grayImg, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
	gradient = cv2.subtract(gradX, gradY)
	gradient = cv2.convertScaleAbs(gradient)
	return gradient

def showImg(*imgs):
	index = 0
	for img in imgs:
		cv2.imshow("img" + str(index), img)
		index += 1
	cv2.waitKey(10)
	cv2.destroyAllWindows()

def showImgSingle(img, wname = "img"):
	cv2.imshow(wname, img)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

# 获取轮廓的包围矩形
def getBoundingRect(contours):
	boundingRect = []
	for contour in contours:
		boundingRect.append(cv2.boundingRect(contour))
	return boundingRect

# lines[ line[ subline[]], ...]
def drawLines(img, lines, color = (0, 0, 0), thickness = 1):
	for line in lines:
		for subline in line:
			cv2.line(img, (subline[0], subline[1]), (subline[2], subline[3]), color, thickness)

# boundingBox = [x, y, w, h] -> [x1, y1, x2, y2]
def convertBoundingBoxToBox(boundingBox):
	realBox = []
	for box in boundingBox:
		realBox.append([box[0], box[1], box[0] + box[2], box[1] + box[3]])
	return realBox

def drawBox(img, boxes, color = (0, 0, 0), thickness = 1):
	for box in boxes:
		cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), color, thickness)

def drawRectP4(img, points, color = (0, 0, 0), thickness = 1):
	lines = [[points[0], points[1]], [points[1], points[2]], [points[2], points[3]], [points[3], points[0]]]
	for line in lines:
		cv2.line(img, (line[0][0], line[0][1]), (line[1][0], line[1][1]), color, thickness)

# 从极坐标获取线段端点
def getLinesFromPolarCoord(polarLines, thresh = 4000):
	lines = []
	for rhoThetaPack in polarLines:
		subline = []
		for rho,theta in rhoThetaPack:
		    a = np.cos(theta)
		    b = np.sin(theta)
		    x0 = a * rho
		    y0 = b * rho
		    x1 = int(x0 + thresh * (-b))
		    y1 = int(y0 + thresh * (a))
		    x2 = int(x0 - thresh * (-b))
		    y2 = int(y0 - thresh * (a))
		    subline.append([x1, y1, x2, y2])
		lines.append(subline)
	return lines

# 找出面积大于一定阈值的矩形
def findMainBox(boundingBox, size, thresh = 2):
	boxes = []
	S = size[0] * size[1]
	for box in boundingBox:
		for x1, y1, x2, y2 in box:
			w = np.abs(x2 - x1)
			h = np.abs(y2 - y1)
			s = w * h
			if s > S / thresh:
				boxes.append(box)
	return boxes			

# 将短线段加长, d == 0(垂直)
def expandLine(lines, thresh):
	newLines = []
	if lines is None:
		return newLines
	for sublines in lines:
		newSublines = []
		for x1, y1, x2, y2 in sublines:
			if x1 > x2:
				x1, x2 = swap(x1, x2)
				y1, y2 = swap(y1, y2)
			newLine = [0] * 4 
			d1 = float(x2 - x1)
			d2 = float(y2 - y1)
			# 垂直
			if d1 >= -5 and d1 <= 5:
				newLine = [x1, y1, x2, y2]
				f = newLine[1] - newLine[3]
				newLine[1] = newLine[1] + f * thresh
				newLine[3] = newLine[3] - f * thresh
			else:
				deltaY1 = d2 / d1 * x1
				deltaY2 = d2 / d1 * thresh
				newLine[0] = 0
				newLine[1] = int(y1 - deltaY1)
				newLine[2] = int(x2 + thresh)
				newLine[3] = int(y2 + deltaY2)
			newSublines.append(newLine) 
		newLines.append(newSublines)
	return newLines

# 保留一定角度的直线, 自动取角度绝对值
def remainLine(lines, angles = [[0, 10], [80, 90]]):
	if lines is None:
		return lines
	PI_DEGREE = 180.0 / np.pi
	newLines = []
	for sublines in lines:
		newSublines = []
		for x1, y1, x2, y2 in sublines:
			newLine = [x1, y1, x2, y2]
			if x1 - x2 == 0:
				theta = 90
			else:
				theta = np.arctan(np.abs(float(y1 - y2) / (x1 - x2))) * PI_DEGREE
			for angle in angles:
				if theta in range(angle[0], angle[1] + 1):
					newSublines.append(newLine)
					break
		if len(newSublines) != 0:
			newLines.append(newSublines)
	return newLines

# 两条直线交点
def computeIntersect(a, b):
	x1 = a[0]; y1 = a[1]; x2 = a[2]; y2 = a[3]; x3 = b[0]; y3 = b[1]; x4 = b[2]; y4 = b[3]  
	d = float((x1 - x2) * (y3 - y4)) - (y1 - y2) * (x3 - x4)
	if d != 0: 
		pt = [0, 0]
		pt[0] = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / d
		pt[1] = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / d  
		return pt
	else:
		return [-1, -1]

# 直线交点
def getIntersectPoints(lines, filterSize = None, thresh1 = 0, thresh2 = 0):
	length = len(lines)
	points = []
	for i in range(length):
		for n in range(i, length):
			point = computeIntersect(lines[i][0], lines[n][0])
			if point[0] != -1:
				if filterSize:
					if point[0] >= 0 and point[0] <= filterSize[0] - thresh1 and point[1] >= 0 and point[1] <= filterSize[1] - thresh2:
						points.append(point)
				else:
					points.append(point)
	return points

# 边角点
def getBoundingCornerPoints(points, size):
	centerP = (size[0] / 2.0, size[1] / 2.0)
	topLeftPx = []
	topLeftPy = []
	topRightPx = []
	topRightPy = []
	bottomRightPx = []
	bottomRightPy = []
	bottomLeftPx = []
	bottomLeftPy = []
	for point in points:
		# topLeft
		if point[0] <= centerP[0] and point[1] <= centerP[1]:
			topLeftPx.append(point[0])
			topLeftPy.append(point[1])
		# topRight
		elif point[0] >= centerP[0] and point[1] <= centerP[1]:
			topRightPx.append(point[0])
			topRightPy.append(point[1])
		# bottomRight
		elif point[0] >= centerP[0] and point[1] >= centerP[1]:
			bottomRightPx.append(point[0])
			bottomRightPy.append(point[1])
		# bottomLeft
		else:
			bottomLeftPx.append(point[0])
			bottomLeftPy.append(point[1])
	if topLeftPx == []:
		topLeftPx.append(0)
	if bottomLeftPx == []:
		bottomLeftPx.append(0)
	if topLeftPy == []:
		topLeftPy.append(0)
	if topRightPy == []:
		topRightPy.append(0)
	if topRightPx == []:
		topRightPx.append(size[0])
	if bottomRightPx == []:
		bottomRightPx.append(size[0])
	if bottomRightPy == []:
		bottomRightPy.append(size[1])
	if bottomLeftPy == []:
		bottomLeftPy.append(size[1])

	topLeftPoint = [min(topLeftPx), min(topLeftPy)]
	topRightPoint = [max(topRightPx), min(topRightPy)]
	bottomRightPoint = [max(bottomRightPx), max(bottomRightPy)]
	bottomLeftPoint = [min(bottomLeftPx), max(bottomLeftPy)]
	return np.array([topLeftPoint, topRightPoint, bottomRightPoint, bottomLeftPoint], dtype = np.float32)

# main function
def houghRectify(img):
	img = cv2.resize(img, (600, 700))
	originalImg = img
	# 灰度图
	img = grayImg(img)
	imgSize = getImgSize(img)
	minW = min(img.shape)
	maxW = max(img.shape)
	img = cv2.blur(img, (4, 4))
	# 画出轮廓
	edges = cv2.Canny(img, 50, 200, apertureSize = 3)
	# 调试: 整体轮廓
	# wimg = createWhiteImg(getImgSize(img))
	lines = cv2.HoughLinesP(edges, 1, np.pi / 360, 50, minLineLength = 10, maxLineGap = 20)
	lines = expandLine(lines, int(maxW))
	# 过滤掉不符合角度要求的线段
	lines = remainLine(lines)
	# 调试：画出边线
	# drawLines(wimg, lines)
	# 计算交点
	intersectPoints = getIntersectPoints(lines, imgSize)
	cornerPoints = getBoundingCornerPoints(intersectPoints, imgSize)
	transPs = np.array([[0, 0], [imgSize[0], 0], [imgSize[0], imgSize[1]], [0, imgSize[1]]], dtype = np.float32)
	transform = cv2.getPerspectiveTransform(cornerPoints, transPs)
	# 调试:画出边框
	# wimg2 = createWhiteImg(imgSize)
	# drawRectP4(wimg2, np.array(cornerPoints).astype(np.int32))
	# 画出前景
	wimg3 = cv2.warpPerspective(src = originalImg, M = transform, dsize =  imgSize)
	# showImg(edges, wimg, wimg2, wimg3)
	return wimg3

# 从填涂区域包围框中选出正确的填涂框, 并计算中心坐标
# hierarchy结构：(前一个框序号，后一个框序号，第一个子框序号，父框序号)
# 序号为-1表示无
# 返回所有填涂区域的中心坐标和区域框
def findAnswerBoxCenter(rectangles, hierarchy):
	hierarchy = hierarchy[0]
	ansBoxCenter = []
	topBoundingBox = []
	for index, item in enumerate(hierarchy):
		if item[3] != -1:
			x1, y1, w, h = rectangles[index]
			# centerX， centerY，S
			ansBoxCenter.append(((x1 + x1 + w) / 2, (y1 + y1 + h) / 2, w * h))
		elif rectangles[index][2] != -1:
			topBoundingBox = rectangles[index]
	return ansBoxCenter, topBoundingBox

# 通过填涂区域坐标确定填涂的答案
# ansBoxCenter为填涂区域中心坐标
# questionCount为竖排的题目数
# answerCount为每个题目备选答案数目
# W,H为作答区域的宽高
# 返回答题结果，questionCount * answerCount的二位数组，置1位代表填涂，置0位代表未填涂
def determineAnswer(ansBoxCenter, questionCount, answerCount, W, H, restrictArea = True, restrictAreaThresh = 0.2):
	baseX = baseY = 0
	stepX = int(float(W) / questionCount)
	stepY = int(float(H) / answerCount)
	standardS = stepX * stepY
	answerMap = np.zeros((questionCount, answerCount))
	for anSenter in ansBoxCenter:
		ansX, ansY, S = anSenter
		# 填涂面积至少为判定方格面积的20%
		if restrictArea and S <= restrictAreaThresh * standardS:
			continue
		ansIndex = int((ansY - baseY) / stepY)
		quesIndex = int((ansX - baseX) / stepX)
		# 位于边线上，按最后一题或选项算
		if quesIndex < questionCount and ansIndex < answerCount:
			answerMap[quesIndex][ansIndex] = 1
		elif ansIndex == answerCount:
			answerMap[quesIndex][answerCount - 1] = 1
		elif quesIndex == questionCount:
			answerMap[questionCount - 1][ansIndex] = 1
	return answerMap

# 横跨整个答题卡的长条形作答区域，包含多个题组
# 通过填涂区域坐标确定填涂的答案
# ansBoxCenter为填涂区域中心坐标
# questionCount为[!每个!]题组的竖排的题目数
# answerCount为每个[!每个!]题组的题目备选答案数目
# groupCount为题组个数
# W,H为作答区域的宽高
# spaceStep为每个题组的间隔长度，默认一个填涂区域大小
# 返回答题结果，questionCount * answerCount的二位数组，置1位代表填涂，置0位代表未填涂
def determineAnswerBar(ansBoxCenter, questionCount, answerCount, groupCount, W, H, spaceStep = 1, restrictArea = True, restrictAreaThresh = 0.2):
	baseX = baseY = 0
	stepX = int(float(W) / (questionCount * groupCount + groupCount - 1))
	stepY = int(float(H) / answerCount)
	standardS = stepX * stepY
	answerMap = np.zeros((questionCount * groupCount, answerCount))
	for anSenter in ansBoxCenter:
		ansX, ansY, S = anSenter
		# 填涂面积至少为判定方格面积的20%
		if restrictArea and S <= restrictAreaThresh * standardS:
			continue
		ansIndex = int((ansY - baseY) / stepY)
		quesIndePre = int((ansX - baseX) / stepX)
		# gapIndex 填涂区域所属组序号， 从1编号
		# determine spacegap index
		# quesIndex -> [q * (i - 1) + 1, (q + 1) * i - 1], where q:questionCount, i:gapIndex
		# q * (i - 1) + 1 <= x and (q + 1) * i - 1 >= x, where x: quesIndex
		# resolve this euqation
		# i -> [(x + 1) / (q + 1), (x + q) / (q + 1)]
		gapIndex = np.ceil(float((quesIndePre + 1)) / (questionCount + 1)) # or np.floor(float((quesIndePre + questionCount)) / (questionCount + 1))
		quesIndex = int(quesIndePre - gapIndex + 1)
		# 位于边线上，按最后一题或选项算
		if quesIndex < questionCount and ansIndex < answerCount:
			answerMap[quesIndex][ansIndex] = 1
		elif ansIndex == answerCount:
			answerMap[quesIndex][answerCount - 1] = 1
		elif quesIndex == questionCount:
			answerMap[questionCount - 1][ansIndex] = 1
	return answerMap

# main function
def readCard(img, details = []):
	# 增加亮度和对比度, 加高光可以突出黑色区域， 弱化灰色区域
	# img = cv2.convertScaleAbs(img, alpha = 1.3, beta = 20)
	# 确定裁剪范围，row1,row2,col1,col2
	# areas = [[245, 325, 320, 480], [250, 325, 485, 615], [245, 325, 10, 615]]
	if "area" not in details or not details["area"]:
		area = None 
	else:
		area = details["area"]
	groupCount = details["groupCount"]
	questionCount = details["questionCount"]
	answerCount = details["answerCount"]
	# 灰度图
	img = grayImg(img)
	w, h = img.shape
	# otsu二值化
	img = binaryInv(img)
	# 低通滤波
	img = cv2.blur(img, (3, 3))
	# 腐蚀, 实际效果为涂抹填涂区域
	# img = erosion(img)
	# 膨胀， 实际效果为缩小填涂区域
	img = dilation(img, iterations = 1)
	# 裁剪
	if area:
		rectImg01 = img[area[0]: area[1], area[2]: area[3]]
	else:
		rectImg01 = img
	# 白边框，防止贴近边缘的填涂区域被并入外围边框中
	row, col = rectImg01.shape
	rectImg01[0] = 255
	rectImg01[row - 1] = 255
	rectImg01[:, col - 1] = 255
	rectImg01[:, 0] = 255
	# 调试:寻找并在白色底图上画出轮廓
	# whiteImg = createWhiteImg(rectImg01.shape)
	# 找出轮廓
	contours, hierarchy = findContours(rectImg01, cv2.RETR_TREE)
	# 调试:画出轮廓
	# drawContours(whiteImg, contours, (0, 0, 0), 2)
	# 得到填涂答案
	boundingBox = getBoundingRect(contours)
	ansBoxCenter, topBoundingBox = findAnswerBoxCenter(boundingBox, hierarchy)
	# 单个题组
	# ansMap = determineAnswer(ansBoxCenter, 5, 4, topBoundingBox[2] - topBoundingBox[0], topBoundingBox[3] - topBoundingBox[1])
	# 四个题组
	ansMap = determineAnswerBar(ansBoxCenter, questionCount, answerCount, groupCount, topBoundingBox[2] - topBoundingBox[0], topBoundingBox[3] - topBoundingBox[1]
		, restrictArea = True, restrictAreaThresh = 0.05)
	# 调试:画出轮廓
	# showImg(rectImg01, whiteImg)	
	return ansMap

# if __name__ == "__main__":
# 	img = readImg("/Volumes/SD/ML/scantron/pics/card01.jpg")
# 	#houghTest(img)
# 	readCard(img)
	
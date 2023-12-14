# Generate each column of tri/hexagons following these rules for each shape index (row, column, shape)
# 1. Each column alternates between up and down facing triangles when they appear
# 2. At each index of each row, the shape can either be a triangle or half of a trapezoid
# 3. If one index is the start of a trapezoid, the index to its right must complete it
# 4. A triangle or trapezoid must point at the flat face of each trapezoid
# 5. Never have 2 triangles in a row, but trapezoids can chain endlessly (but flip directions each time to maintain #4)
# 6. The lines between each row of shapes must be parallel

# Triangles are equilateral, each with height = sqrt(3) * side * 0.5
# If triangles face left, trapezoid flat sides are on the right. likewise, left for triangles facing right rows

# TD notes:
# - should generate one points DAT, one vertex DAT (optional?) and one primitives DAT
import random

# Organized so that shapes with parallel lines (on their underside) match even/odd
TRIANGLE_LEFT = 0  # <
TRIANGLE_RIGHT = 1 # >
TRAPEZOID_DOWN = 2 # \ \
TRAPEZOID_UP = 3   # / /

def shapeToStr(shape):
	if shape == TRIANGLE_LEFT:
		return "<"
	elif shape == TRIANGLE_RIGHT:
		return ">"
	elif shape == TRAPEZOID_UP:
		return "/ /"
	elif shape == TRAPEZOID_DOWN:
		return "\\ \\"

def matchTilt(shapeAbove, triangleLeft, canBeTri = True):
	if shapeAbove % 2 == 0:
		# Tilt right \ \
		if triangleLeft or not canBeTri:
			# Has to be \ \
			newShape = TRAPEZOID_DOWN
		else:
			# Either > or \ \
			newShape = random.randint(0, 1) + 1
	else:
		# Tilt left / /
		if not triangleLeft or not canBeTri:
			# Has to be / /
			newShape = TRAPEZOID_UP
		else:
			# Either < or / /
			newShape = random.randint(0, 1) * 3
	return newShape

def generateShapes(scriptOp):
	width = scriptOp.par.Width.eval()
	height = scriptOp.par.Height.eval()
	resolution = scriptOp.par.Resolution.eval()
	nRows = round(resolution / 4) + 1
	shapes = []
	#nShapesPerRow = round(width / shapeSize) + 1
	nShapesPerRow = max(1, resolution)
	triangleLeft = False
	for i in range(nRows):
		#print("row " + str(i))

		row = []
		# Choose starting shape for this row
		if i == 0:
			# Either triangle right, trap down or up
			lastShape = random.randint(0, 2) # Either triangle right, trap down or up
			if lastShape == 0:
				lastShape = int(not triangleLeft)
			#print(shapeToStr(lastShape) + ": first row random")
		else:
			lastShape = matchTilt(shapes[-1][0], triangleLeft)
			#print(shapeToStr(lastShape) + ": first matched to " + shapeToStr(shapes[-1][0]))
		row.append(lastShape)
		for j in range(1, nShapesPerRow):
			if i == 0:
				shapeAbove = random.randint(0, 1)
				shapeAboveNext = shapeAbove
			else:
				shapeAbove = shapes[-1][j]
				if j == nShapesPerRow - 1:
					shapeAboveNext = shapeAbove
				else:
					shapeAboveNext = shapes[-1][j + 1]
			if lastShape < 2: # Last shape was triangle
				if j > 1 and row[-2] < 2: # Last 2 shapes were triangles, need a trapezoid
					newShape = matchTilt(shapeAbove, triangleLeft, False)
					row.append(newShape)
					#print(shapeToStr(row[-1]) + ": matching but not tri")
				else:
					# Match tilt of row above
					row.append(matchTilt(shapeAbove, triangleLeft, shapeAboveNext > 1))
					#print(shapeToStr(row[-1]) + ": matched to " + shapeToStr(shapeAbove))
			else: # Last shape was trapezoid, just append a triangle
				row.append(int(not triangleLeft))
				#print(shapeToStr(row[-1]) + ": left is trap")
			lastShape = row[-1]
		shapes.append(row)
		triangleLeft = not triangleLeft
	return shapes

def generatePoints(scriptOp, shapes):
	width = scriptOp.par.Width.eval()
	height = scriptOp.par.Height.eval()
	resolution = scriptOp.par.Resolution.eval()
	nRows = round(resolution / 4) + 1
	points = []
	triWidth = width / resolution
	shapeSize = (triWidth * math.sqrt(3)) / 2.0
	gapHeight = (height - (shapeSize * nRows)) / (nRows - 1)
	curY = 1 - (shapeSize / 2.0)
	for row in shapes:
		triangleLeft = TRIANGLE_LEFT in row
		curX = 0
		for shape in row:
			shapePoints = []
			if shape == TRIANGLE_LEFT:
					# <
					shapePoints.append([curX + triWidth, curY - (shapeSize / 2.0)])
					shapePoints.append([curX + triWidth, curY + (shapeSize / 2.0)])
					shapePoints.append([curX, curY])
			elif shape == TRIANGLE_RIGHT:
					# >
					shapePoints.append([curX, curY - (shapeSize / 2.0)])
					shapePoints.append([curX + triWidth, curY])
					shapePoints.append([curX, curY + (shapeSize / 2.0)])
			elif shape == TRAPEZOID_UP:
				#  / /
				# / /
				addY = 0.0 if triangleLeft else (-shapeSize / 2.0)
				shapePoints.append([curX, curY - (shapeSize / 2.0) + addY])
				shapePoints.append([curX + triWidth, curY + addY])
				shapePoints.append([curX + triWidth, curY + shapeSize + addY])
				shapePoints.append([curX, curY + (shapeSize / 2.0) + addY])
			else: # Trapezoid down
				# \ \
				#  \ \
				addY = 0.0 if triangleLeft else (shapeSize / 2.0)
				shapePoints.append([curX, curY - (shapeSize / 2.0) + addY])
				shapePoints.append([curX + triWidth, curY - shapeSize + addY])
				shapePoints.append([curX + triWidth, curY + addY])
				shapePoints.append([curX, curY + (shapeSize / 2.0) + addY])
			points.append(shapePoints)
			curX = curX + triWidth
		curY = curY - shapeSize - gapHeight
	# Now make the parallelogram points between each shape's rows
	parallelogramPoints = []
	for i in range(resolution, len(points)):
		# Get shape above and connect its first 2 points to our last 2 points
		shapePoints = []
		shapePtsAbove = points[i - resolution]
		shapePoints.append(points[i][-1])
		shapePoints.append(points[i][-2])
		if shapes[int(i / resolution) - 1][i % resolution] == TRIANGLE_LEFT:
			shapePoints.append(shapePtsAbove[0])
			shapePoints.append(shapePtsAbove[2])
		else:
			shapePoints.append(shapePtsAbove[1])
			shapePoints.append(shapePtsAbove[0])
		parallelogramPoints.append(shapePoints)
	# Insert the parallelograms in the right spots in the points list
	finalPoints = []
	for i in range(0, len(points), resolution):
		if i >= resolution:
			finalPoints.extend(parallelogramPoints[i - resolution: i])
		finalPoints.extend(points[i:i+resolution])
	return finalPoints

# me - this DAT
# scriptOp - the OP which is cooking
#
# press 'Setup Parameters' in the OP to call this function to re-create the parameters.
def onSetupParameters(scriptOp):
	page = scriptOp.appendCustomPage('Pattern')
	page.appendFloat('Width', label='Width')
	page.appendFloat('Height', label='Height')
	page.appendInt('Resolution', label='Resolution')
	scriptOp.par.Width = 1
	scriptOp.par.Height = 1
	scriptOp.par.Resolution = 10
	return

# called whenever custom pulse parameter is pushed
def onPulse(par):
	return

def onCook(scriptOp):
	print("Generating pattern")
	shapes = generateShapes(scriptOp)
	points = generatePoints(scriptOp, shapes)
	print(len(points))
	pointsOp = scriptOp
	vertexOp = op('patternVertices')
	primitivesOp = op('patternPrimitives')

	width = scriptOp.par.Width.eval()
	height = scriptOp.par.Height.eval()

	# Points DAT
	pointsOp.clear()
	pointsOp.insertRow(['index', 'P(0)', 'P(1)', 'P(2)', 'Pw', 'N(0)', 'N(1)', 'N(2)', 'groups'], 0)
	for shape in points:
		for i, point in enumerate(shape):
			pointsOp.appendRow([i, point[0], point[1], 0, 1, 0, 0, 1, ""])
	# Vertex DAT
	vertexOp.clear()
	vertexOp.insertRow(['index', 'vindex', 'uv(0)', 'uv(1)', 'uv(2)'], 0)
	for i, shape in enumerate(points):
		for j, point in enumerate(shape):
			vertexOp.appendRow([i, j, min(1.0, point[0] / width), min(1.0, point[1] / height), 0])
	# Primitives DAT
	primitivesOp.clear()
	primitivesOp.insertRow(['index', 'vertices', 'close', 'groups'], 0)
	i = 0
	for p, shape in enumerate(points):
		verts = range(i, i + len(shape))
		primitivesOp.appendRow([p, ' '.join(str(s) for s in verts), 1, ""])
		i = i + len(shape)

	return


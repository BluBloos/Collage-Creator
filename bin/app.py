# TODO(Noah):

# Known bugs
	# I need to ensure that scaling and croping never happens in such a way where the image overlaps itself. Basically, just have rigorous bounds checking.
	
# Known Issues
	# The menu system causes me to miss the framerate. Odd... I suppose it needs some optimization. I would go as far as to say that the majority of the program needs some optimization. I have been not very caring throughout the entirety of the project. I was like "yo, let's just get this stuff done."
	# I have a hypothesis. The drawing of the text is most likely the bottleneck. Text is like, pretty hard to draw. Also, for each submenu of the menu, I do a seperate paste operation. I wonder if paste is slow as well, maybe I can use the imageDraw module to draw rectangles. I will have to do some testing because I am not quite sure.	
	
# Backburner
	# The user should be able to do the banding effect for every filter that exists. Currently, it only works for negate red. This type of things is a user interface thing.
	# Instead of doing this thing where I hold all the transforms maybe I can change it to a thing where I hold the transformation deltas
	# Make a slider menu which inherits from menu or smnth so that we can do image filters with inputs from the user
	# The user should be able to make the app go fullscreen
	# There should be hotkeys for the commands (import image, export, save, open, etc)
	# Make a "delete nulls" command. This command goes through each image and finds images who would not be otherwise visible (their left and right cropPercentages are equal for example). Once it finds these images, it deletes them. I believe this is a good feature because I can forsee the possiblity that someone will forget about these so called null images that they accidentally created.
	# Use the C backend to blit the FPS onto the screen like a fraps program lmao
	# Dynamic canvas size (new menu title canvas)
		# resize command
	# Canvas loading and saving
	# Add image snaping, so I can snap the sides of images to the sides of other images. (This sounds like a crazy feature. I need to like, for each image, go through all other images. n^2). It's basically like I need to make images collide with each other.

# Current
	# Do some significant speed ups for vignette and pixelate (utilize C backend and present case to Mr.yantho)

#################### IMPORTS #################	
from PIL import Image, ImageFilter, ImageFont, ImageDraw, ImageChops
from recordclass import recordclass, dataobject
import math
import random 

#################### CONSTANTS ################
FUNCTION_TOP_LEFT_VERTEX = 0
FUNCTION_TOP_RIGHT_VERTEX = 1
FUNCTION_BOTTOM_LEFT_VERTEX = 8
FUNCTION_BOTTOM_RIGHT_VERTEX = 9
FUNCTION_BOTTOM_EDGE = 2
FUNCTION_TOP_EDGE = 3
FUNCTION_LEFT_EDGE = 4
FUNCTION_RIGHT_EDGE = 5
FUNCTION_NULL = 6
FUNCTION_WHOLE = 7
TRANSFORMATION_SCALE = 0
TRANSFORMATION_CROP = 1
PANEL_WIDTH = 80
PANEL_ARROW_PEEK = 5
CANVAS_COLOUR = (155,162,176)

################### FUNCTIONS ####################

# This function returns the val clamped between the low and the high value 
def Clamp(val, low, high):
	return min(high, max(val, low))

# This function returns if the key at keyIndex has just been pressed down (it is down, but it was not down last frame).
def KeyHot(platform, keyIndex):
	return platform.keys[keyIndex].isDown and not platform.keys[keyIndex].wasDown 

# This function return a boolean corresponding to if the mouse coordinates can be found inside box. 
def BoundingBoxPrimitiveCollision(box, mouseX, mouseY):
	left, top, right, bottom = box
	
	if left <= mouseX <= right and top <= mouseY <= bottom:
		return True
	
	return False

# NOTE(Noah): Each element of the boundingBox tuple must be an integer. 
# This function does not check this at all. This is the duty of the caller.
# This function writes directly into the memory of the image dest to draw a rectangle according to boundingBox of the specified color 
def DrawRect(dest, boundingBox, color):
	dest.paste(color, boundingBox)

# This function will open the image on disk as specified by fileName, convert it to RGBA, and return a handle to it.
def ImageLoad(fileName):
	# NOTE(Noah): The Image.open() function is lazy. 
	# It uses the memory allocated at the file read time until an image operation is performed. 
	# Image.load() forces the newly opened image to commit itself to memory
	fileImage = Image.open(fileName)
	fileImage.load()
	return fileImage.convert(mode="RGBA")

############### MENU CALLBACKS ################

# NOTE(Noah): These functions acts as callbacks for registered menus. When the corresponding menu button is pressed, these functions will be called. 

# Moves the parent image above all other images on the canvas
def MenuImageMoveUp(platform, storage, menu):
	image = storage.images.pop(menu.parent)
	storage.images.append(image)

# Moves the parent image below all other images on the canvas
def MenuImageMoveDown(platform, storage, menu):
	image = storage.images.pop(menu.parent)
	storage.images.insert(0, image)

# Moves the parent image up one layer on the canvas
def MenuImageStepUp(platform, storage, menu):
	image = storage.images.pop(menu.parent)
	storage.images.insert(menu.parent + 1, image)

# Moves the parent image own on layer on the canvas
def MenuImageStepDown(platform, storage, menu):
	image = storage.images.pop(menu.parent)
	storage.images.insert(menu.parent - 1, image)

# Remove the parent image from the global list of collage images.
def MenuImageRemove(platform, storage, menu):
	storage.images.pop(menu.parent)

# Reset all transformation applied to the collage image such that its the same as if were just pulled of the pool. Place the middle of the image at the mouse coordinates.
def MenuImageResetTransform(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	collageImage.transformationSets = [CollageImageTransformation()]
	collageImage.left = platform.mouseX - collageImage.image.width // 2
	collageImage.top = platform.mouseY - collageImage.image.height // 2
	
# Removes all applied filters to the parent image	
def MenuImageResetFilter(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	collageImage.filterImage.paste(collageImage.image)

# Flips the parent image across the vertical
def MenuImageFlipHorizontal(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	collageImage.filterImage = collageImage.filterImage.transpose(Image.FLIP_LEFT_RIGHT)

# Flips the parent image across the horizontal
def MenuImageFlipVertical(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	collageImage.filterImage = collageImage.filterImage.transpose(Image.FLIP_TOP_BOTTOM)

# Applies fancy emboss filter to the parent image
def MenuImageEmboss(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	collageImage.filterImage = collageImage.filterImage.filter(ImageFilter.EMBOSS)

# Returns the image but where the red channel has been negated
def ImageNegateRed(image):
	def NegateChannel(byte):
		return 255 - byte
	
	red, green, blue, alpha = image.split()
	red = Image.eval(red, NegateChannel)
	return Image.merge("RGBA", (red, green, blue, alpha))

# Pastes spaced bands of the image but with the red channel negated on each band and the spaces maintating the original image color
def MenuImageBandingNegateRed(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	notRedImage = ImageNegateRed(collageImage.filterImage)
	
	# TODO(Noah): The user should be able to select the width of the banding  
	bandingWidth = 10	
		
	for x in range(collageImage.image.width // bandingWidth):
		left = x * bandingWidth
		right = min(left + bandingWidth, collageImage.image.width)	
		
		if x % 2 == 0:
			imageSlice = notRedImage.crop( (left, 0, right, collageImage.image.height) )
			collageImage.filterImage.paste(imageSlice, ( left, 0))	

# Negates the red channel of the parent image
def MenuImageNegateRed(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	collageImage.filterImage = ImageNegateRed(collageImage.filterImage)

# Greyscales the parent image
def MenuImageMonochrome(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	red, green, blue, alpha = collageImage.filterImage.split()

	def Scale(byte):
		return byte // 3

	red = Image.eval(red, Scale)
	blue = Image.eval(blue, Scale)
	green = Image.eval(green, Scale)
	avg = ImageChops.add(red, green)
	avg = ImageChops.add(avg, blue)
	collageImage.filterImage = Image.merge("RGBA", (avg, avg, avg, alpha))

# Pixelates the parent image
def MenuImagePixelate(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	image = collageImage.filterImage
	pixelSize = 8
	pixelX = int(math.ceil(image.width / pixelSize))
	pixelY = int(math.ceil(image.height / pixelSize))

	for x in range(pixelX):
		for y in range(pixelY):
			blue = 0
			red = 0
			green = 0
			count = 0
			
			# Add to running sums for each channel for each pixel in pixel block defined by pixelSize
			for i in range(pixelSize):
				for j in range(pixelSize):
					absPixelX = x * pixelSize + i
					absPixelY = y * pixelSize + j
					
					if absPixelX < image.width and absPixelY < image.height:
						pRed, pGreen, pBlue, pAlpha = image.getpixel((absPixelX, absPixelY))
						red += pRed
						blue += pBlue
						green += pGreen
						count += 1
			
			# average the channels
			blue = blue // count
			red = red // count
			green = green // count

			# write the average value to each pixel in pixel block defined by pixelSize
			for i in range(pixelSize):
				for j in range(pixelSize):
					absPixelX = x * pixelSize + i
					absPixelY = y * pixelSize + j
					
					if absPixelX < image.width and absPixelY < image.height:
						# NOTE(Noah): This overwrites the alpha. Do I care?
						image.putpixel((absPixelX, absPixelY), (red, green, blue, 255))

# TODO(Noah): The user should be able to drag a slider, 
# or enter a value to specify the vignette radius. As of now, the vignette uses a constant radius of size 1.
# Applies a radial vignette to the parent image. At the pixel radius * 200 pixels away from the center pixel of the image, it will be absolutely black. 
# The full image is show at the center pixel of the image. Inbetween there is an exponential fade. 
def MenuImageVignette(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	image = collageImage.filterImage
	
	# the circle is placed in the middle of the image, which is defined as (0, 0)
	# the coordinate system is not in pixel, it uses the following conversion factor
	pixelsToUnits = 1 / 200
	radius = 2 # this is in units
	b = 2
	a = -1 / (math.pow(b, radius) - 1)
	c = 1 - a

	for x in range(image.width):
		for y in range(image.height):
			unitDistX = (x - image.width / 2) * pixelsToUnits
			unitDistY = (y - image.height / 2) * pixelsToUnits
			distToCentre = math.sqrt(math.pow(unitDistX, 2) + math.pow(unitDistY, 2))
			p = a * math.pow(b, distToCentre) + c
			red, green, blue, alpha = image.getpixel((x, y))
			image.putpixel((x, y), ( int(red * p) , int(green * p) , int(blue * p) , alpha ))

# Applies a banding-like filter to the parent image. Alternating light and dark bars are averaged with the source pixels of the image. 
# the resultant image appears like an image that would be seen on an old CRT monitor.
def MenuImageCRT(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	image = collageImage.filterImage
	
	for x in range(image.width):
		for y in range(image.height):
			red, green, blue, alpha = image.getpixel((x, y))
			
			if (y // 3) % 2 == 0:
				# Average the pixel with light green
				red = (9 + red) // 2 
				green = (76 + green) // 2
				blue = (39 + blue) // 2			
			else:
				# Average the pixel with dark green
				red = (3 + red) // 2 
				green = (22 + green) // 2
				blue = (14 + blue) // 2
				
			image.putpixel((x, y), (red, green, blue, alpha ))
 
# applies a gaussian blur to the parent image 
def MenuImageGaussianBlur(platform, storage, menu):
	collageImage = storage.images[menu.parent]
	collageImage.filterImage = collageImage.filterImage.filter(ImageFilter.GaussianBlur())

# removes the parent thumbnail form the global pool
def MenuThumbRemove(platform, storage, menu):
	storage.pool.pop(menu.parent)

# this function is not for the faint of heart, you have been warned
def MenuCollageGoBannanas(platform, storage, menu):
	storage.goBannanas = True

# TODO(Noah): Add the portion that checks the boxes to make sure that they are always the proper height
# generates a new set of collage images to be applied to the canvas that will replace the entire current set. 
# the new set of images are tightly packed and dynamiclly generated.
def MenuCollageGenerator(platform, storage, menu):
	
	boxes = [ (PANEL_WIDTH, 0, storage.backBufferWidth, storage.backBufferHeight) ]
	
	# Right now, the program defaults to 5 cuts :)
	cutCount = 0
	while cutCount < 4:
		boxIndex = int(random.random() * len(boxes))
		cutType = random.random() > 0.5
		cutPercentage = random.random() * 0.5 + 0.25
		left, top, right, bottom = boxes[boxIndex]
		
		if cutType: # vertical cut
			slice = left + int((right - left) * cutPercentage)
			box1 = ( left, top, slice, bottom )
			box2 = ( slice, top, right, bottom)
			boxes.pop(boxIndex)
			boxes.append(box1)
			boxes.append(box2)
			cutCount += 1
			
		else: # vertical cut
			slice = top + int((bottom - top) * cutPercentage)
			box1 = (left, top, right, slice)
			box2 = (left, slice, right, bottom)	
			boxes.pop(boxIndex)
			boxes.append(box1)
			boxes.append(box2)
			cutCount += 1
	
	platform.Log("boxes: {}".format(boxes))
	
	# now that we have the boxes, we need to generate the list of images that shall be placed into the storage.images list
	newImages = []
	
	def BoxWidth(box):
		return (box[2] - box[0])

	def BoxHeight(box):
		return (box[3] - box[1])

	def Rank(box, box2):
		# The rank is defined as the sum of the delta of the widths of the boxes and the delta of the height of the boxes
		return abs(BoxWidth(box2) - BoxWidth(box)) + abs(BoxHeight(box2) - BoxHeight(box))
	
	for box in boxes:
		lowestRank = 99999999
		selectedImageIndex = None
		
		for i in range(len(storage.pool)):	
			image, thumb = storage.pool[i]
			imageRank = Rank(box, (0,0, image.width, image.height) )
			
			if imageRank < lowestRank:
				lowestRank = imageRank
				selectedImageIndex = i
		
		image, thumb = storage.pool[selectedImageIndex]
		newImageWidth, newImageHeight = BoxWidth(box), BoxHeight(box)
		newImage = CollageImage(image.copy(), box[0], box[1])
		transform = newImage.TransformPeek()
		transform.scaleRightOffset = -(image.width - newImageWidth)
		transform.scaleBottomOffset = -(image.height - newImageHeight)
		newImage.lastTransformationType = TRANSFORMATION_SCALE		
		newImages.append(newImage)
	
	storage.images = newImages

#################### CLASSES #######################
class Menu:
	
	DEFAULT_MENU_PADDING = 5
	
	def __init__(self, parent, left, top, textPackage, backBufferWidth, backBufferHeight, actions, timeout=None, padding=DEFAULT_MENU_PADDING):
		self.parent = parent # reference to the object that created the menu
		self.left = left # x-coordinate of the top left corner of the menu 
		self.top = top # y-coordinate of the top left corner of the menu
		self.width = 0 # the maximum extent that any action button in the menu extends relative to self.left 
		self.height = 0 # the sum of the height of n actions + self.padding * (n - 1)  
		self.timeout = timeout # the amount of time, in seconds, that the menu should exist if the user never closed it
		self.padding = padding # the amount of space in pixels from the bottom of the text of a menu action to the top of the text of the next menu action	
		self.elapsed = 0 # the amount of time, in seconds, that the menu should exist. The menu should be closed once self.elapsed > self.timeout.
		self.offsetY = [] # offsetY is defined as the top coordinate of the bounding Box of each action relative to the top coordinate of the menu 
		self.actions = [] # list of tuples corresponding to each action button, where each element is (actionName, actionCallback)
		self.renderer, self.font = textPackage 
		
		# generate the offsetY and actions
		for action in actions:
			actionName, actionTask = action
			textSize = self.renderer.textsize(actionName, self.font)
			textX, textY = textSize
			
			if textX > self.width:
				self.width = textX
			
			self.actions.append( (actionName, actionTask) )
			self.offsetY.append(self.height)
			self.height += textY + self.padding
		
		self.offsetY.append(self.height)		

		if self.top + self.height > backBufferHeight:
			self.top = backBufferHeight - self.height
		
		if self.left + self.width > backBufferWidth:
			self.left = backBufferWidth - self.width
	
	# this fucntions return the boundingBox of the menu action at the specified actionIndex
	def ActionGetBoundingBox(self, actionIndex):
		posX = self.left
		posY = self.top + self.offsetY[actionIndex]
		return (posX, posY, posX + self.width, posY + (self.offsetY[actionIndex + 1] - self.offsetY[actionIndex]))
	
	# Draws the menu into the destination at the coordinates specified by self.left and self.top
	def Blit(self, dest, sType, sID):
		color = (220,152,164)
		color2 = (193,61,80)
		color3 = (180,112,124)
		color4 = (143,21,40)
		
		for i in range(len(self.actions)):
			actionName, actionTask = self.actions[i]
			boundingBox = self.ActionGetBoundingBox(i)

			if sType == 2 and sID == i:
				# Render the bit below the text, but darker because it is selected
				if i % 2 == 0:
					DrawRect(dest, boundingBox, color3)
				else:
					DrawRect(dest, boundingBox, color4)
			else:
				# Render the bit below the text, but lighter because it is not selected
				if i % 2 == 0:
					DrawRect(dest, boundingBox, color)
				else:
					DrawRect(dest, boundingBox, color2)

			# Render the action text
			self.renderer.text((self.left, boundingBox[1]), actionName, font=self.font, fill=(255, 255, 255, 255))

# create a new menu where the user can select the filter they want to apply to the parent image
def MenuImageFilter(platform, storage, menu):
	newMenu = Menu(menu.parent, platform.mouseX, platform.mouseY, (storage.renderer, storage.font), storage.backBufferWidth, storage.backBufferHeight, [("Negate red", MenuImageNegateRed), ("Negate red (banding)", MenuImageBandingNegateRed), ("Monochrome", MenuImageMonochrome), ("Radial vignette", MenuImageVignette), ("Flip horizontal", MenuImageFlipHorizontal), ("Flip vertical", MenuImageFlipVertical), ("Gaussian blur", MenuImageGaussianBlur), ("Emboss", MenuImageEmboss), ("Pixelate", MenuImagePixelate), ("Retro", MenuImageCRT), ("Exit", None)])
	storage.activeMenu = newMenu
	return True # I do not want to null the menu!

class CollageImageTransformation(dataobject):
	scaleLeftOffset : int = 0
	scaleRightOffset : int = 0
	scaleTopOffset : int = 0
	scaleBottomOffset : int = 0
	cropLeftOffset : int = 0
	cropRightOffset : int = 0
	cropTopOffset : int = 0
	cropBottomOffset : int = 0

class CollageImage:

	def __init__(self, image, left, top, scale=False):
		self.image = image # reference to the pillow image object for this collage image
		self.width = image.width # the width of the pillow image object
		self.height = image.height # the height of the pillow image object
		self.filterImage = image.copy() # the running clone of the pillow image object that has all the filters applied to it
		self.left = left # the x-coordinate of the top-left corner of the transformed image
		self.top = top # the y-coordinate of the top-left corner of the transformed image
		self.transformationSets = [CollageImageTransformation()] # the set of transformations to apply to self.image 
		self.lastTransformationType = TRANSFORMATION_CROP # the last transformation that was applied to this CollageImage
	
	# returns the top most transformation
	def TransformPeek(self):
		return self.transformationSets[-1] 
	
	# returns the 4-tupled box corresponding to the boundingBox of the image after the set of transformations have been applied to it
	def Vertices(self):

		left = self.left
		top = self.top
		right = self.left + self.image.width
		bottom = self.top + self.image.height

		for transformation in self.transformationSets:
			left += transformation.cropLeftOffset - transformation.scaleLeftOffset
			top += transformation.cropTopOffset - transformation.scaleTopOffset
			bottom += transformation.scaleBottomOffset - transformation.cropBottomOffset
			right += transformation.scaleRightOffset - transformation.cropRightOffset

		return (left, top, right, bottom)
	
	# returns the function corresponding to the current mouse position and the bounding box of the image after the set of transformations have been applied to it
	def BoundingBoxGetFunction(self, mouseX, mouseY):
		left, top, right, bottom = self.Vertices()
		
		leftDelta = abs(mouseX - left) <= 10
		rightDelta = abs(mouseX - right) <= 10
		topDelta = abs(mouseY - top) <= 10
		bottomDelta = abs(mouseY - bottom) <= 10
		boundX = left <= mouseX <= right
		boundY = top <= mouseY <= bottom
			
		if leftDelta and topDelta:
			return FUNCTION_TOP_LEFT_VERTEX
		elif leftDelta and bottomDelta:
			return FUNCTION_BOTTOM_LEFT_VERTEX
		elif rightDelta and topDelta:
			return FUNCTION_TOP_RIGHT_VERTEX
		elif rightDelta and bottomDelta:
			return FUNCTION_BOTTOM_RIGHT_VERTEX
		elif topDelta and boundX:
			return FUNCTION_TOP_EDGE
		elif bottomDelta and boundX:
			return FUNCTION_BOTTOM_EDGE
		elif leftDelta and boundY:
			return FUNCTION_LEFT_EDGE
		elif rightDelta and boundY:
			return FUNCTION_RIGHT_EDGE		
		elif boundX and boundY:
			return FUNCTION_WHOLE
		
		return FUNCTION_NULL
	
	# draws the image onto the dest
	def Blit(self, dest):

		renderImage = self.filterImage
		left = self.left
		top = self.top

		# transform the image
		for transformation in self.transformationSets:

			cropLeft = int(transformation.cropLeftOffset)
			cropTop = int(transformation.cropTopOffset)
			cropRight = int(renderImage.width - transformation.cropRightOffset)
			cropBottom = int(renderImage.height - transformation.cropBottomOffset)

			# NOTE(Noah): crop is also lazy, so changes in the source will affect 
			# the cropped image. This is no concern, because the cropped image is merely a temporary copy
			croppedImage = renderImage.crop((cropLeft, cropTop, cropRight, cropBottom))

			newLeft = left - transformation.scaleLeftOffset + transformation.cropLeftOffset
			newTop = top - transformation.scaleTopOffset + transformation.cropTopOffset
			newRight = left + renderImage.width + transformation.scaleRightOffset - transformation.cropRightOffset
			newBottom = top + renderImage.height  + transformation.scaleBottomOffset - transformation.cropBottomOffset

			# Scale the image
			width = max(1, int(newRight - newLeft))
			height = max(1, int(newBottom - newTop))
			renderImage = croppedImage.resize((width, height), resample=Image.BILINEAR)

			# commit the position change
			left = newLeft
			top = newTop

		dest.paste(renderImage, (int(left), int(top)))
	
	# crops the image according to the ativeFunction and the deltaX and deltaY
	def TransformationCrop(self, activeFunction, deltaX, deltaY):
		transform = self.TransformPeek()
		
		if self.lastTransformationType == TRANSFORMATION_SCALE:
			self.transformationSets.append(CollageImageTransformation())
			
		self.lastTransformationType = TRANSFORMATION_CROP
			
		def ClampLeft():
			#transform.cropLeftOffset = Clamp(transform.cropLeftOffset, 0, transform.cropLeftOffset)
			transform.cropLeftOffset = max(0, transform.cropLeftOffset)
		def ClampRight():
			#transform.cropRightOffset = Clamp(transform.cropRightOffset, 0, transform.cropRightOffset)
			transform.cropRightOffset = max(0, transform.cropRightOffset)
		def ClampTop():
			#transform.cropTopOffset = Clamp(transform.cropTopOffset, 0, transform.cropTopOffset)
			transform.cropTopOffset = max(0, transform.cropTopOffset)
		def ClampBottom():
			#transform.cropBottomOffset = Clamp(transform.cropBottomOffset, 0, transform.cropBottomOffset)
			transform.cropBottomOffset = max(0, transform.cropBottomOffset)
		
		if activeFunction == FUNCTION_BOTTOM_EDGE:
			transform.cropBottomOffset += -deltaY
			ClampBottom()
		elif activeFunction == FUNCTION_TOP_EDGE:
			transform.cropTopOffset += deltaY
			ClampTop()
		elif activeFunction == FUNCTION_LEFT_EDGE:
			transform.cropLeftOffset += deltaX
			ClampLeft()
		elif activeFunction == FUNCTION_RIGHT_EDGE:
			transform.cropRightOffset += -deltaX
			ClampRight()
		elif activeFunction == FUNCTION_TOP_LEFT_VERTEX:
			transform.cropLeftOffset += deltaX
			transform.cropTopOffset += deltaY
			ClampLeft()
			ClampTop()
		elif activeFunction == FUNCTION_TOP_RIGHT_VERTEX:
			transform.cropTopOffset += deltaY
			transform.cropRightOffset += -deltaX
			ClampRight()
			ClampTop()
		elif activeFunction == FUNCTION_BOTTOM_LEFT_VERTEX:
			transform.cropLeftOffset += deltaX
			transform.cropBottomOffset += -deltaY
			ClampLeft()
			ClampBottom()
		elif activeFunction == FUNCTION_BOTTOM_RIGHT_VERTEX:
			transform.cropBottomOffset += -deltaY
			transform.cropRightOffset += -deltaX
			ClampRight()
			ClampBottom()
	
	# scales the image according to the deltaX and the deltaY
	def TransformationScale(self, activeFunction, deltaX, deltaY):
		self.lastTransformationType = TRANSFORMATION_SCALE
		transform = self.TransformPeek()
		
		def ClampLeft():
			#transform.scaleLeftOffset = max(transform.scaleLeftOffset, transform.scaleRightOffset - image.width)
			pass
		def ClampRight():
			#transform.scaleRightOffset = max(transform.scaleRightOffset, transform.scaleLeftOffset - image.width)
			pass
		def ClampTop():
			#transform.scaleTopOffset = max(transform.scaleTopOffset, transform.scaleBottomOffset - image.height)
			pass
		def ClampBottom():
			#transform.scaleBottomOffset = max(transform.scaleBottomOffset, transform.scaleBottomOffset - image.height)
			pass
		
		if activeFunction == FUNCTION_BOTTOM_EDGE:
			transform.scaleBottomOffset += deltaY
			ClampBottom()
		elif activeFunction == FUNCTION_TOP_EDGE:
			transform.scaleTopOffset += -deltaY
			ClampTop()
		elif activeFunction == FUNCTION_LEFT_EDGE:
			transform.scaleLeftOffset += -deltaX
			ClampLeft()
		elif activeFunction == FUNCTION_RIGHT_EDGE:
			transform.scaleRightOffset += deltaX
			ClampRight()
		elif activeFunction == FUNCTION_TOP_LEFT_VERTEX:
			transform.scaleLeftOffset += -deltaX
			transform.scaleTopOffset += -deltaY
			ClampTop()
			ClampLeft()
		elif activeFunction == FUNCTION_TOP_RIGHT_VERTEX:
			transform.scaleTopOffset += -deltaY
			transform.scaleRightOffset += deltaX
			ClampTop()
			ClampRight()
		elif activeFunction == FUNCTION_BOTTOM_LEFT_VERTEX:
			transform.scaleLeftOffset += -deltaX
			transform.scaleBottomOffset += deltaY
			ClampBottom()
			ClampLeft()
		elif activeFunction == FUNCTION_BOTTOM_RIGHT_VERTEX:
			transform.scaleBottomOffset += deltaY
			transform.scaleRightOffset += deltaX
			ClampBottom()
			ClampRight()

# TODO(Noah): I sort of just thought of this. But what happens when we remove a thumbnail from the pool. Does this not require us to recalibrate the offsetY?
class Pool:
	
	def __init__(self, left, top, padding):
		self.offset = 0 # the offset at which to begin rendering the first thumbnail of the pool
		self.pool = [] # the set of pool tuples that make up this pool 
		self.offsetY = [] # set of coordinates corresponding to the top of each thumbnail in the pool. Used to resolve boundingBoxes.
		self.left = left # the x-coordinate of the top-left corner of the pool
		self.top = top # the y-coordinate of the top-left corner of the pool
		self.padding = padding # the amount of space between each consecutive thumbnail in the pool
	
	# NOTE(Noah): This function does not check if the fileName is correct
	# open the file from fileName and returns a pool objec tuple.
	@classmethod
	def PoolObjectFromFileName(self, fileName):
		newImage = ImageLoad(fileName)
		newWidth = 64
		newHeight = newWidth * newImage.height / newImage.width
		thumb = newImage.copy()
		thumb.thumbnail((newWidth, newHeight))
		return (newImage, thumb)
	
	# return the amount of thumbnails in the pool
	def __len__(self):
		return len(self.pool)
	
	# returns the corresponding pool obejct at index
	def __getitem__(self, index):
		return self.pool[index]
	
	# adds a new poolItem to self.pool
	# updates the offsetY
	def Append(self, poolItem):
		iamge, thumb = poolItem 
		self.pool.append(poolItem)
		
		if len(self.offsetY) == 0:
			self.offsetY.append(thumb.height + self.top)
		else:
			self.offsetY.append(self.offsetY[-1] + self.padding + thumb.height)
			
	# This function expects that the index is in range, and it does not checking
	# returns the bounding box of the thumbnail in the pool at index
	def ThumbnailBoundingBox(self, index):
		posX = self.left
		image, thumb = self.pool[index]
		image2, thumb2 = self.pool[self.offset] 
		bottom = self.offsetY[index] - (self.offsetY[self.offset] - self.top - thumb2.height)
		return (posX, bottom - thumb.height, posX + thumb.width, bottom)		

############### APPLICATION CALLBACKS ############################

# NOTE(Noah): This function does not care if the fileName is correct
def AppImport(platform, storage, imageName):
	storage.pool.Append(Pool.PoolObjectFromFileName(imageName))

# NOTE(Noah): This function does not care if the fileName is correct
def AppExport(platform, storage, backBuffer, imageName):
	canvas = Image.new("RGBA", (backBuffer.width, backBuffer.height), CANVAS_COLOUR)

	for image in storage.images:
		image.Blit(canvas)

	croppedCanvas = canvas.crop((PANEL_WIDTH, 0, backBuffer.width, backBuffer.height))
	# TODO(Noah): Implement image format filters in the C layer so 
	# that I can omit the fact that we only output png images
	croppedCanvas.save(imageName, "PNG")

	newMenu = Menu(None, backBuffer.width // 2, 20, (storage.renderer, storage.font), backBuffer.width, backBuffer.height, [("{} wrote successfully.".format(imageName), None)], timeout=2.0)
	newMenu.left -= newMenu.width // 2 # put it in the middle
	storage.activeMenu = newMenu

def AppPreInit(platform, storage):
	platform.SetWindowName("Collage Maker")

def AppInit(platform, storage, backBuffer):	
	storage.activeImage = None
	storage.activeMenu = None
	storage.goBannanas = False
	storage.images = []
	
	storage.pool = Pool(20, 75, 10)
	storage.pool.Append( Pool.PoolObjectFromFileName("dog.jpg") )
	storage.pool.Append( Pool.PoolObjectFromFileName("laptop.png") )
	storage.pool.Append( Pool.PoolObjectFromFileName("bouldering.jpg") )
	
	storage.lastMouseX = 0
	storage.lastMouseY = 0
		
	storage.font = ImageFont.truetype("arial.ttf", 20)
	storage.renderer = ImageDraw.Draw(backBuffer)
	
	storage.upArrow = ImageLoad("arrow.png")
	storage.downArrow = storage.upArrow.transpose(Image.FLIP_TOP_BOTTOM)
	
	storage.upArrowHover = ImageLoad("arrowHover.png")
	storage.downArrowHover = storage.upArrowHover.transpose(Image.FLIP_TOP_BOTTOM)
	
	# TODO(Noah): Below is debug code, please remove this until we are sure that we 
	# have given up on compiling the Pillow library ourselves but modified to how we like it.
	data = bytearray("Hello, World!	  ", "utf-8")
	
	dataImage = Image.frombuffer("RGBA", (2, 2), data, "raw", "RGBA", 0, 1)
	red, green, blue, alpha = dataImage.getpixel((0,0))
	platform.LogError("red: {}, green: {}, blue: {}, alpha: {}".format(red, green, blue, alpha))
	dataImage.putpixel((0,0), (34, 56, 43, 39))
	platform.LogError("after mod: {}".format(data))	
	 
def AppUpdateAndRender(platform, storage, backBuffer):		
	# If the backBuffer size changes, I need to make sure to capture it
	storage.backBufferWidth = backBuffer.width
	storage.backBufferHeight = backBuffer.height
	
	def UpArrowBoundingBox(upArrow, backBufferHeight):
		return (storage.pool.left, PANEL_ARROW_PEEK, storage.pool.left + upArrow.width, PANEL_ARROW_PEEK + upArrow.height)
	
	def DownArrowBoundingBox(downArrow, backBufferHeight):
		return (storage.pool.left, backBufferHeight - PANEL_ARROW_PEEK - downArrow.height, storage.pool.left + downArrow.width, backBufferHeight - PANEL_ARROW_PEEK)
	
	def PanelMaxThumbnailY():
		return backBuffer.height - storage.pool.top
	
	######### STATE UPDATING ROUTINES #########
	
	if storage.goBannanas:
		# this is a very funny meme indeed
		storage.activeMenu = Menu(None, int(random.random() * backBuffer.width), int(random.random() * backBuffer.height), (storage.renderer, storage.font), backBuffer.width, backBuffer.height, [("I am the bannana man.", None)], timeout=2.0)
	
	# A selection does not necessarily mean we have found an active image, 
	# it merely means that it is the top-most item that the user has hovered the mouse over.
	selection = None
	
	if storage.activeMenu:
		for i in range(len(storage.activeMenu.actions)):
			if BoundingBoxPrimitiveCollision(storage.activeMenu.ActionGetBoundingBox(i), platform.mouseX, platform.mouseY):
				selection = (2, i, FUNCTION_WHOLE)
				break

		if storage.activeMenu.timeout:
			# NOTE(Noah): This is a major cheese, but I love it. (it should never take a second to render a frame)
			if platform.deltaTime < 1:
				storage.activeMenu.elapsed += platform.deltaTime
			
			if storage.activeMenu.elapsed >= storage.activeMenu.timeout:
				storage.activeMenu = None
				
	elif storage.activeImage:
		image, activeFunction = storage.activeImage
		selection = (0, None, activeFunction)
		deltaX = platform.mouseX - storage.lastMouseX
		deltaY = platform.mouseY - storage.lastMouseY	
			
		if activeFunction == FUNCTION_WHOLE:
			image.left += deltaX
			image.top += deltaY
		
		elif platform.keys[platform.KEY_S].isDown:
			image.TransformationScale(activeFunction, deltaX, deltaY)
			
		else:
			image.TransformationCrop(activeFunction, deltaX, deltaY)		
	
			
		# if the user has let go of the mouse, the image is no longer active
		if not platform.keys[platform.KEY_MOUSE_LEFT].isDown:
			storage.activeImage = None

	else:
		
		maxY = PanelMaxThumbnailY() # maxY is the maximum pixel height that the end of the last thumbnail should extend
		for y in range(storage.pool.offset, len(storage.pool)):
			boundingBox = storage.pool.ThumbnailBoundingBox(y)
			if boundingBox[3] > maxY: 
				break
			if BoundingBoxPrimitiveCollision(boundingBox, platform.mouseX, platform.mouseY): 
				selection = (1, y, FUNCTION_WHOLE)
				break

		# Are we selecting one of the arrows?
		if selection == None:
			if BoundingBoxPrimitiveCollision(UpArrowBoundingBox(storage.upArrow, backBuffer.height), platform.mouseX, platform.mouseY):
				selection = (3, None, FUNCTION_WHOLE)
			elif BoundingBoxPrimitiveCollision(DownArrowBoundingBox(storage.downArrow, backBuffer.height), platform.mouseX, platform.mouseY):
				selection = (4, None, FUNCTION_WHOLE)

		# Are we selecting an image?
		if selection == None:
			for i in range(len(storage.images) -1, -1, -1):
				image = storage.images[i]
				boundingBoxFunc = image.BoundingBoxGetFunction(platform.mouseX, platform.mouseY)
				if boundingBoxFunc != FUNCTION_NULL:
					selection = (0, i, boundingBoxFunc)
					break				
	
	# Update the app based on the selection
	if selection != None:
		sType, sID, sFunc = selection
		
		# Check if this selection should generate a new activeImage
		if KeyHot(platform, platform.KEY_MOUSE_LEFT):
			if sType == 0: # regular image
				storage.activeImage = (storage.images[sID], sFunc)
			elif sType == 1: # thumbnail
				image, thumb = storage.pool[sID]
				newImage = CollageImage(image.copy(), platform.mouseX - image.width / 2, platform.mouseY - image.height / 2)
				storage.images.append(newImage)
				storage.activeImage = (newImage, FUNCTION_WHOLE)
			elif sType == 2: # menu button
				actionName, actionTask = storage.activeMenu.actions[sID]
				noNullMenu = False	
				if callable(actionTask):
					noNullMenu = actionTask(platform, storage, storage.activeMenu)
				if not noNullMenu:
					storage.activeMenu = None
			elif sType == 3: # up arrow on panel
				storage.pool.offset = max(0, storage.pool.offset - 1)
			elif sType == 4: # down arrow on panel
				storage.pool.offset = min(len(storage.pool) - 1, storage.pool.offset + 1)
		
		# Check if this selection should generate a new image menu
		elif KeyHot(platform, platform.KEY_MOUSE_RIGHT):
			platform.Log("generated new menu")
			if sType == 0: # regular image
				newMenu = Menu(sID, platform.mouseX, platform.mouseY, (storage.renderer, storage.font), backBuffer.width, backBuffer.height, [("Bring to top", MenuImageMoveUp), ("Bring to bottom", MenuImageMoveDown), ("Step up", MenuImageStepUp), ("Step down", MenuImageStepDown), ("Filter", MenuImageFilter), ("Reset transform", MenuImageResetTransform), ("Reset filters", MenuImageResetFilter), ("Remove", MenuImageRemove), ("Exit", None)])
				storage.activeMenu = newMenu
			elif sType == 1: # thumbnail
				newMenu = Menu(sID, platform.mouseX, platform.mouseY, (storage.renderer, storage.font), backBuffer.width, backBuffer.height, [("Remove", MenuThumbRemove), ("Exit", None)])
				storage.activeMenu = newMenu
		
		# Update the cursor based on the selection
		if sFunc == FUNCTION_WHOLE:
			platform.SetCursor(1)
		elif sFunc == FUNCTION_TOP_EDGE:
			platform.SetCursor(2)
		elif sFunc == FUNCTION_BOTTOM_EDGE:
			platform.SetCursor(2)
		elif sFunc == FUNCTION_LEFT_EDGE:
			platform.SetCursor(3)
		elif sFunc == FUNCTION_RIGHT_EDGE:
			platform.SetCursor(3)
		elif sFunc == FUNCTION_TOP_LEFT_VERTEX:
			platform.SetCursor(5)
		elif sFunc == FUNCTION_TOP_RIGHT_VERTEX:
			platform.SetCursor(4)
		elif sFunc == FUNCTION_BOTTOM_LEFT_VERTEX:
			platform.SetCursor(4)
		elif sFunc == FUNCTION_BOTTOM_RIGHT_VERTEX:
			platform.SetCursor(5)
	
	# If there was no selection, they may invoke the main menu for the program	
	else:
		if KeyHot(platform, platform.KEY_MOUSE_RIGHT):
			storage.activeMenu = Menu(None, platform.mouseX, platform.mouseY, (storage.renderer, storage.font), backBuffer.width, backBuffer.height, [("Go bannanas", MenuCollageGoBannanas), ("Generate collage", MenuCollageGenerator), ("Exit", None)])
		
		platform.SetCursor(0)

	######### DRAW ROUTINES #########
	
	# Clear the canvas to its default color
	DrawRect(backBuffer, (PANEL_WIDTH, 0, backBuffer.width, backBuffer.height), CANVAS_COLOUR)
	
	# Draw the images
	for image in storage.images:
		image.Blit(backBuffer)
	
	############## DRAW PANEL ############
	# Draw the panel background
	DrawRect(backBuffer, (0, 0, PANEL_WIDTH, backBuffer.height), (53, 50, 76))

	# Draw the arrow bits
	sType = None
	if selection != None:
		sType = selection[0]
	
	upArrowBounding = UpArrowBoundingBox(storage.upArrow, backBuffer.height)
	downArrowBounding = DownArrowBoundingBox(storage.downArrow, backBuffer.height)
	
	if sType == 3:
		backBuffer.paste(storage.upArrowHover, upArrowBounding, storage.upArrowHover)
	else:
		backBuffer.paste(storage.upArrow, upArrowBounding, storage.upArrow)

	if sType == 4:
		backBuffer.paste(storage.downArrowHover, downArrowBounding, storage.downArrowHover)
	else:
		backBuffer.paste(storage.downArrow, downArrowBounding, storage.downArrow)
	
	# Draw the thumbnails
	# TODO(Noah): Once again, there is a lot of repetiton here!
	maxY = PanelMaxThumbnailY()
	lastY = storage.pool.offset
	for y in range(storage.pool.offset, len(storage.pool)):
		image, thumb = storage.pool[y]
		sType, sID, sFunc = None, None, None
		left, top, right, bottom = storage.pool.ThumbnailBoundingBox(y)	
		
		if bottom > maxY:
			break

		lastY = y

		if selection != None:
			sType, sID, sFunc= selection
		
		if sType == 1 and sID == y:
			backBuffer.paste(thumb, (left + 10, top))
		else:
			backBuffer.paste(thumb, (left, top))

	
	# Draw the numbers who are friends with the arrows
	if storage.pool.offset:
		storage.renderer.text((upArrowBounding[0] - 7, upArrowBounding[1]), "+{}".format(storage.pool.offset), font=storage.font, fill=(255, 255, 255, 255))

	if lastY < len(storage.pool) - 1:
		renderString = "+{}".format(len(storage.pool) - 1 - lastY)
		textX, textY = storage.renderer.textsize(renderString, storage.font)
		storage.renderer.text((downArrowBounding[0] - 7, downArrowBounding[1] + storage.downArrow.height - textY), renderString, font=storage.font, fill=(255, 255, 255, 255))
	
	# Draw the menu if there is one
	if storage.activeMenu:	
		sType, sID, sFunc = None, None, None
		
		if selection != None:
			sType, sID, sFunc = selection
			
		storage.activeMenu.Blit(backBuffer, sType, sID)	
		
	storage.lastMouseX = platform.mouseX
	storage.lastMouseY = platform.mouseY

	#platform.Log("deltaTime: {}s".format(platform.deltaTime))
	#platform.Log("fps: {}".format(1 / platform.deltaTime))

def AppClose(platform, storage, backBuffer):
	platform.Log("App is closing!")

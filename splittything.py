#!/usr/bin/env python

import pygame
from pygame.locals import *
import os
import copy
import levels

import os
DVORAK = False
if os.name == 'posix':    
	from subprocess import check_output
	if "dvorak" in check_output(["setxkbmap", "-print"]):
		DVORAK = True

#TODO:
# Design levels
# Level editor?
# grabbing on to walls?

# move level loading from metalayer to level
# add a walljump timer

#Obstacles:
# Moving Obstacles
# Buttons and doors
# Slowness area
# Trampoline
# Stuff that interacts between the split people
# checkpoints

# Note: turn off cheat mode
# Do some Bug Testing

#Bugs
# ...

#Stuff we can do with more time
# Animations
# Story
# Angles
# Options (Such as resolution, keymap)
# timer bars
# Better graphics

#Done:
# Walljump
# Death from sides obstacle (or just put it together)
# Let pictures go outside their rectangles ( margins)
# Loading levels from files
# 3d animation
# background



#Constants

COORDS_HEIGHT = 1000.0

SCREEN_SIZE = [1600, 1000]

CHEATY_MODE = False

defaultscale = COORDS_HEIGHT / SCREEN_SIZE[1]

dt = 1.0/60.0

SLIDINGRECOVERYTIME = 0.5
SLIDINGTIME = 2
SPLITRECOVERYTIME = 1
GRAVITY = 0.5
RUNNINGSPEED = 10
JUMP = 17
WALLJUMP = 17
WALLMAXVELOCITY = 2
WALLTIME = 0.1
WALLACCEL = 3
STANDINGHEIGHT = 175
SLIDINGHEIGHT = 75
LEFTBORDER = 300
FOG=50
DISPLACEMENT = [150, 200]

WALLEFFECT = "WALL"

if DVORAK:
	KEYSPLIT = [K_SPACE]
	KEYJUMP = [[K_UP, K_COMMA], [K_c]]
	KEYSLIDE = [[K_DOWN, K_o], [K_t]]
	KEYLEFT = [[K_LEFT, K_a], [K_h]]
	KEYRIGHT = [[K_RIGHT, K_e], [K_n]]
	EDITORLEFT = [[K_LEFT, K_a]]
	EDITORRIGHT = [[K_RIGHT, K_e]]
else:
	KEYSPLIT = [K_SPACE]
	KEYJUMP = [[K_UP, K_w], [K_i]]
	KEYSLIDE = [[K_DOWN, K_s], [K_k]]
	KEYLEFT = [[K_LEFT, K_a], [K_j]]
	KEYRIGHT = [[K_RIGHT, K_d], [K_l]]
	EDITORLEFT = [[K_LEFT, K_a]]
	EDITORRIGHT = [[K_RIGHT, K_d]]

# Loads image from filename
def load_image(name):
	try:
		image = pygame.image.load(name)
	except pygame.error, message:
		print 'Cannot load image:', name
		raise SystemExit, message
	image = image.convert_alpha()
	return image

# Truncates each element in a list to an integer
def roundlist(l):
	return [int(e) for e in l]

# Stores top, left, right, and bottom positions of a rectangle
class rect():
	def __init__(self):
		self.left = 0
		self.right = 0
		self.bottom = 0
		self.top = 0
	
	def setrect(self, left, right, bottom, top):
		self.left = left
		self.right = right
		self.bottom = bottom
		self.top = top
	
	def copy(self):
		copy = rect()
		copy.left = self.left
		copy.right = self.right
		copy.bottom = self.bottom
		copy.top = self.top
		return copy
	
	def collides(self, otherrect): # Do 2 rectangles overlap?
		return not (otherrect.left > self.right \
			or otherrect.right < self.left \
			or otherrect.top < self.bottom \
			or otherrect.bottom > self.top)
	
	def __str__(self): # Ignore this
		return str(self.left) + " " + str(self.right) + " " + str(self.bottom) + " " + str(self.top)

class possprite(pygame.sprite.Sprite): # A sprite with a relative positioning system
	def __init__(self, lyr, pos):
		pygame.sprite.Sprite.__init__(self)
		
		self.pos = pos
		self.layer = lyr
		self.coordsrect = rect()
		
		self.margins = [0,0,0,0] #left, right, bottom, top
		
		self.image = None
		self.actualimg = None
		self.scale = None
		
	def setmargins(self, left, right, bottom, top):
		self.margins = [left, right, bottom, top]
		
	def setimage(self, image, scale=None, size=None): # Set the sprites image
		if scale == None: # Scale down the image if its too big
			scale = 1
		self.actualimg = image
		imgrect = self.actualimg.get_rect()
		
		if size != None: # Using size is the same as scale, but it sizes it so it will fit in a certain height
			if size[1] != None: # Use size=[None, myheight] in the arguments
				scale = float(size[1]) / imgrect.height # not including margins
			else:
				scale = float(size[0]) / imgrect.width
		
		self.scale = scale
		
		self.image = pygame.transform.scale(self.actualimg, roundlist([x*scale for x in self.layer.scaletoscreen(imgrect.size)]))
		
		self.rect = self.image.get_rect()
		
	def refreshimage(self):
		if self.actualimg != None:
			self.setimage(self.actualimg, scale=self.scale)
		
	def setinvisible(self, size): # Use invisible image instead of setimage
		self.rect = pygame.Rect((0,0), size)
		img = pygame.Surface((0,0))
		img.fill([0,0,0])
		self.image = img
		
	def move(self, direction):
		self.pos = [self.pos[0]+direction[0], self.pos[1]+direction[1]]
		
	def getrect(self): # Gets rectangle
#		left, top = self.layer.screentocoords(self.rect.topleft)
#		right, bottom = self.layer.screentocoords(self.rect.bottomright)
		
		width, height = self.layer.scaletocoords(self.rect.size)
		left, right = self.pos[0] - width/2.0, self.pos[0] + width/2.0
		bottom, top = self.pos[1] - height/2.0, self.pos[1] + height/2.0
		
		left += self.margins[0]
		right -= self.margins[1]
		bottom += self.margins[2]
		top -= self.margins[3]
		
		self.coordsrect.setrect(left, right, bottom, top)
		return self.coordsrect
		
	def collides(self, othersprite):
		return self.getrect().collides(othersprite.getrect())
		
	def update(self): # Update actual Rect to match self.pos
		self.rect.center = self.layer.coordstoscreen(self.pos)
		
	def draw(self, screen):
		pygame.sprite.Sprite.draw(self, screen)

class layer(): # Each split person has a layer. A layer contains person+obstacles
	def __init__(self, lvl, additionalscale = [1,1], hasperson=True):
		self.level = lvl
		
		self.offset = [0,0]
		self.layeroffset = [0,0]
		
		self.setadditionalscale(additionalscale)
		
		self.persongroup = pygame.sprite.Group()
		self.obstacles = pygame.sprite.Group()
		
		self.animating = False
		self.animatingbackwards = False
		self.animationtimer = 0
		self.animationbetween = None
		
		if hasperson:
			self.person = person(self, [0,0])
			
			self.persongroup.add(self.person)
			
	def setadditionalscale(self, additionalscale = [1,1]):
		self.additionalscale = additionalscale
		self.scale = [defaultscale * additionalscale[0], defaultscale * additionalscale[1]]
		
	def setpersonpos(self, pos):
		self.person.pos = pos
		
	def addobstacle(self, pos, size, **kwargs):
		self.obstacles.add(squareobstacle(self, pos, size, **kwargs))
		
	def addwall(self, pos, size, **kwargs):
		self.obstacles.add(sidewall(self, pos, size, **kwargs))
	
	def adddeathobstacle(self, pos, size, **kwargs):
		self.obstacles.add(deathobstacle(self, pos, size, **kwargs))
	
	def addwinobstacle(self, pos, size, **kwargs):
		self.obstacles.add(winobstacle(self, pos, size, **kwargs))
	
	def addsidedeathobstacle(self, pos, size, invisible=False, **kwargs):
		self.obstacles.add(squareobstacle(self, pos, size, invisible=invisible))
		halfsize = int(size[0] * 1.0/2.0)
#		newheight = size[1] - 20
#		if newheight < 0:
#			newheight = 0
		newheight = 0
		self.obstacles.add(deathobstacle(self, [pos[0] - halfsize, pos[1]], [0, newheight], invisible=True))
		self.obstacles.add(deathobstacle(self, [pos[0] + halfsize, pos[1]], [0, newheight], invisible=True))
		self.obstacles.add(decoration(self, [pos[0] - halfsize - 4, pos[1]], [10, size[1]], img="spikes.png"))
		self.obstacles.add(decoration(self, [pos[0] + halfsize + 4, pos[1]], [10, size[1]], img="reversedspikes.png"))
	
	def addbackground(self, imgname):
		self.obstacles.add(backgroundobstacle(self, imgname, 0))
		self.obstacles.add(backgroundobstacle(self, imgname, 1))
		
	def scaletocoords(self, scale):
		return [scale[0] * self.scale[0], scale[1] * self.scale[1]]
		
	def scaletoscreen(self, scale):
		return [scale[0] / self.scale[0], scale[1] / self.scale[1]]
		
	def coordstoscreen(self, coords):
		coords = self.scaletoscreen(coords)
		coords = [coords[0] + self.offset[0], -(coords[1] + self.offset[1])]
		return coords
		
	def screentocoords(self, screen):
		screen = [screen[0] - self.offset[0], -screen[1] - self.offset[1]]
		screen = self.scaletocoords(screen)
		return screen
		
	def animate(self, fromlayeroffset, fromadditionalscale, tolayeroffset, toadditionalscale, backwards = False):
		self.animating = True
		self.animatingbackwards = backwards
		self.animationtimer = 0
		self.animationbetween = [fromlayeroffset, fromadditionalscale, tolayeroffset, toadditionalscale]
	
	def between(self, t, l1, l2):
		return [l1[i] * (1-t) + l2[i] * (t) for i in range(len(l1))]
	
	def update(self):
		if self.animating:
			self.animationtimer += 0.1
			fromlayeroffset, fromadditionalscale, tolayeroffset, toadditionalscale = self.animationbetween
			if self.animationtimer >= 1:
				self.animating = False
				if self.animatingbackwards:
					layeroffset = fromlayeroffset
					additionalscale = fromadditionalscale
				else:
					layeroffset = tolayeroffset
					additionalscale = toadditionalscale
			else:
				layeroffset = self.between(self.animationtimer, fromlayeroffset, tolayeroffset)
				additionalscale = self.between(self.animationtimer, fromadditionalscale, toadditionalscale)
			self.layeroffset = layeroffset
			self.setadditionalscale(additionalscale)
			
			for obstacle in self.obstacles:
				obstacle.refreshimage()
			for person in self.persongroup:
				person.refreshimage()
		
		self.offset[1] = -SCREEN_SIZE[1]
		self.offset[0] = -self.scaletoscreen([self.level.minpersonpos() - LEFTBORDER, 0])[0]
		layeroffset = self.scaletoscreen(self.layeroffset)
		self.offset[0] += layeroffset[0]
		self.offset[1] += layeroffset[1]
		
		self.obstacles.update()
		self.persongroup.update()
		
	def draw(self, screen):
		self.obstacles.draw(screen)
		self.persongroup.draw(screen)
		
	def gameover(self):
		self.level.reset()
		
	def win(self):
		self.level.reset()
		nextlevel()

class metalayer(layer): # The layer when person is not split
	def __init__(self, lvl):
		layer.__init__(self, lvl)
		
		self.loadlevel()
		
	def loadlevel(self):
		self.level.levelmethod(self)
#		self.sample()
#		self.makemetalayer()
		
#	def makemetalayer(self):
#		for lyr in self.level.layers:
#			for obstcl in lyr.obstacles:
#				self.obstacles.add(obstcl)
	
	def makelayers(self, number):
		for i in range(number):
			newscale = 1 + 0.2 * (number - i - 1)
			newlayer = layer(self.level, additionalscale=[newscale, newscale])
			newlayer.actualadditionalscale = [newscale, newscale]
			offsetdist = (number - i) - 1 # Subtract 1 here?
			newlayer.layeroffset = [offsetdist * DISPLACEMENT[0], offsetdist * DISPLACEMENT[1]]
			newlayer.actuallayeroffset = newlayer.layeroffset
			self.level.layers.append(newlayer)
		
		newscale = 1 + 0.2 * (number)
		offsetdist = number
		self.level.background3dadditionalscale = [newscale, newscale]
		self.level.background3ddisplacement = [offsetdist * DISPLACEMENT[0], offsetdist * DISPLACEMENT[1]]
	
	def setbackground(self, imgname):
		self.level.setbackground(imgname)
	
	def getlayer(self, i):
		if i == None:
			return self.level.layers
		else:
			return [self.level.layers[i]]
		
	def addobstacle(self, l, *args, **kwargs):
		for lyr in self.getlayer(l):
			lyr.addobstacle(*args, **kwargs)
		layer.addobstacle(self, *args, **kwargs)
		
	def addwall(self, l, *args, **kwargs):
		for lyr in self.getlayer(l):
			lyr.addwall(*args, **kwargs)
		layer.addwall(self, *args, **kwargs)
	
	def adddeathobstacle(self, l, *args, **kwargs):
		for lyr in self.getlayer(l):
			lyr.adddeathobstacle(*args, **kwargs)
		layer.adddeathobstacle(self, *args, **kwargs)
	
	def addsidedeathobstacle(self, l, *args, **kwargs):
		for lyr in self.getlayer(l):
			lyr.addsidedeathobstacle(*args, **kwargs)
		layer.addsidedeathobstacle(self, *args, **kwargs)
	
	def addwinobstacle(self, l, *args, **kwargs):
		for lyr in self.getlayer(l):
			lyr.addwinobstacle(*args, **kwargs)
		layer.addwinobstacle(self, *args, **kwargs)

class level(): # Contains level information
	def __init__(self, levelmethod):
		self.meta = True
		
		self.levelmethod = levelmethod
		
		self.fog = pygame.Surface(SCREEN_SIZE)
		self.fog.fill((255,255,255))
		self.fog.set_alpha(FOG)
		
		self.backgroundlayer2d = None
		self.backgroundlayer3d = None
		
		self.reset()
		
	def setbackground(self, imgname):
		self.backgroundlayer2d = layer(self, hasperson=False)
		self.backgroundlayer3d = layer(self, hasperson=False, additionalscale=self.background3dadditionalscale)
		self.backgroundlayer3d.layeroffset = self.background3ddisplacement
		self.backgroundlayer2d.addbackground(imgname)
		self.backgroundlayer3d.addbackground(imgname)
		
	def reset(self):
		self.layers = []
		
		self.metalayer = metalayer(self)
		
#		layer1 = layer(self)
#		self.layers.append(layer1)

	def getperson(self, i=0):
		if self.meta:
			if i == 0:
				return self.metalayer.person
		else:
			return self.layers[i].person
			
	def getppl(self):
		if self.meta:
			return [self.getperson()]
		else:
			return [lyr.person for lyr in self.layers]
	
	def minperson(self):
		if self.meta:
			return self.metalayer.person
		else:
			return min([lyr.person for lyr in self.layers], key=lambda p : (p.pos[0]))# + p.layer.layeroffset[0]))
			
	def minpersonpos(self):
		return self.minperson().pos[0]# + self.minperson().layer.layeroffset[0]
		
	def hasperson(self, number):
		if self.meta:
			return number == 1
		else:
			return number < len(self.layers)
		
	def update(self):
		if self.meta:
			self.splitrecoverytimer = 0
		if not self.meta:
			self.splitrecoverytimer += dt
		
		if self.meta:
			self.metalayer.update()
			if self.backgroundlayer2d != None:
				self.backgroundlayer2d.update()
		else:
			for lyr in self.layers:
				lyr.update()
			if self.backgroundlayer3d != None:
				self.backgroundlayer3d.update()
	
	def split(self):
		if self.meta or self.splitrecoverytimer > SPLITRECOVERYTIME:
			if not self.meta:
				personpos = self.minperson().pos
				runningdir = self.minperson().runningdir
				velocity = self.minperson().velocity
				self.metalayer.setpersonpos(personpos)
				self.metalayer.person.runningdir = runningdir
				self.metalayer.person.velocity = copy.copy(velocity)
				for lyr in self.layers:
					lyr.animate(lyr.actuallayeroffset, lyr.actualadditionalscale, [0,0], [1,1], backwards=True)
				if self.backgroundlayer3d != None:
					self.backgroundlayer3d.animate([0, 0], [1, 1], self.background3ddisplacement, self.background3dadditionalscale)
			else:
				personpos = self.metalayer.person.pos
				runningdir = self.metalayer.person.runningdir
				velocity = self.metalayer.person.velocity
				for lyr in self.layers:
					lyr.setpersonpos(personpos)
					lyr.person.runningdir = runningdir
					lyr.person.velocity = copy.copy(velocity)
					lyr.animate([0,0], [1,1], lyr.actuallayeroffset, lyr.actualadditionalscale)
				if self.backgroundlayer2d != None:
					self.backgroundlayer2d.animate(self.background3ddisplacement, self.background3dadditionalscale, [0, 0], [1, 1])
			
			self.meta = not self.meta
		
	
	def draw(self, screen):
		if self.meta:
			if self.backgroundlayer2d != None:
				self.backgroundlayer2d.draw(screen)
			for lyr in self.layers:
				if lyr.animating:
#					screen.blit(self.fog, (0, 0))
					lyr.update()
					lyr.draw(screen)
			screen.blit(self.fog, (0, 0))
			self.metalayer.draw(screen)
		else:
			if self.backgroundlayer3d != None:
				self.backgroundlayer3d.draw(screen)
			for lyr in self.layers:
				screen.blit(self.fog, (0, 0))
				lyr.draw(screen)
#		screen.blit(self.fog, (0, 0))
		

class person(possprite):
	def __init__(self, lyr, pos):
		possprite.__init__(self, lyr, pos)
		self.uprightimage = load_image('person.png')
		self.uprightimages = [load_image('person2-1.png'), load_image('person2-2.png'), load_image('person2-3.png')]
		self.fallingimage = load_image('person2-falling.png')#, load_image('person2-falling2.png'), load_image('person2-falling3.png')]
		self.slidingimage = load_image('sliding_person2.png')
		self.wallimage = load_image('person2-wall.png')
		self.divingimage = load_image('diving_person.png')
		self.setimage(self.uprightimage, size=[None, STANDINGHEIGHT])
		
		self.margins = [10, 10, 10, 10]
		
		self.animindex = 0
		
		self.velocity = [0, 0] # variables
		self.walltimer = 0
		self.slidingtimer = 0
		self.slidingrecoverytimer = 0
		self.issliding = False
#		self.doslide = False
#		self.movingright = True
		self.runningdir = 1
		self.onwall = False
		self.onground = False
		self.doimageupdate = False
		self.effects = []
		
		self.update()
		
	def updateimage(self):
		self.doimageupdate = True
		
	def update(self):
#		if self.movingright: # Running right
#			self.velocity[0] = RUNNINGSPEED
#		else:
#			if self.velocity[0] > 0:
#				self.velocity[0] = 0
		self.velocity[0] = RUNNINGSPEED * self.runningdir
		
		self.velocity[1] -= GRAVITY
		oldrect = self.getrect().copy() # Get rect before being moved
		
		if self.issliding: # sliding timers
			self.slidingtimer += dt
			self.slidingrecoverytimer = 0
			if psn.slidingtimer >= SLIDINGTIME:
				self.issliding = False
				self.updateimage()
		else:
			self.slidingtimer = 0
			if self.slidingrecoverytimer < SLIDINGRECOVERYTIME:
				self.slidingrecoverytimer += dt
		
#		if self.issliding != self.doslide: # sliding
#		if self.doimageupdate:
#			self.doimageupdate = False
		if True:
			
			self.animindex = (self.animindex + 0.1) % 3
			
			height = None
			image = None
			
			if self.issliding:
				if self.onground:
					image = self.slidingimage
					height = SLIDINGHEIGHT
				else:
					image = self.divingimage
					height = SLIDINGHEIGHT
			elif self.onwall:
				image = self.wallimage
				height = STANDINGHEIGHT
			elif self.onground or WALLEFFECT in self.effects:
				image = self.uprightimages[int(self.animindex)]
				height = STANDINGHEIGHT
			else:
				image = self.fallingimage
				height = STANDINGHEIGHT
			
			if self.runningdir == -1:
				image = pygame.transform.flip(image, True, False)
			
			self.setimage(image, size=[None, height])
			
			self.move([0, oldrect.bottom - self.getrect().bottom])
		
		self.move(self.velocity)
		
		possprite.update(self)
		
		newrect = self.getrect()
		
		self.onground = False # reset variables (they are set below)
		self.effects = []
		self.onwall = False
		
		for obstacle in self.layer.obstacles: # check collisions with obstacles
			collrect = obstacle.getrect()
			if newrect.collides(collrect):
				obstacle.collidewithperson(self)
				
				if obstacle.physical: # .physical means can stand on top of
					
					distanceright =  newrect.right - collrect.left
					distanceleft = collrect.right - newrect.left
					distancedown = collrect.top - newrect.bottom
					distanceup = newrect.top - collrect.bottom
					
					distances = [distanceright, distanceleft, distancedown, distanceup]
					distances = [distance for distance in distances if distance >= 0]
					mindistance = min(distances)
					
					if mindistance == distanceright:
						#collision right
						self.move([collrect.left - newrect.right, 0])
						self.velocity[0] = 0
						self.onwall = True
					elif mindistance == distanceleft:
						#collision left
						self.move([collrect.right - newrect.left, 0])
						self.velocity[0] = 0
						self.onwall = True
					elif mindistance == distancedown:
						#collision is a floor
						self.move([0, collrect.top - newrect.bottom])
						self.velocity[1] = 0
						self.onground = True
					elif mindistance == distanceup:
						#collision is a ceiling
						self.move([0, collrect.bottom - newrect.top])
						if self.velocity[1] > 0:
							self.velocity[1] = 0
				
				if obstacle.effect != None: # Check for effects like walls available for running
					if not obstacle.effect in self.effects:
						self.effects.append(obstacle.effect)
		
		if self.onground:
			self.walltimer = 0
		
		possprite.update(self)
	
	def die(self):
		pause("You died\n\nPress Enter to try again")
		self.layer.gameover()
		
	def win(self):
		self.layer.win()

class obstacle(): # something other that a person
	def __init__(self, physical=True):
		self.physical = physical
		self.effect = None
		
	def collidewithperson(self, person):
		pass

class squareobstacle(possprite, obstacle): # square actually means rectangle. these are floors/walls
	def __init__(self, lyr, pos, size, color=None, invisible=False, margins=None, img=None):
		if color == None: color = [0, 0, 0]
		
		possprite.__init__(self, lyr, pos)
		obstacle.__init__(self)
		
		if margins != None:
			self.setmargins(*margins)
		
		if img != None:
			img = load_image(img)
			self.setimage(img, size=size)
		elif invisible:
			self.setinvisible(size)
		else:
			img = pygame.Surface(size)
			img.fill(color)
			self.setimage(img)
		
		self.update()
		
	def update(self):
		possprite.update(self)
		
class decoration(squareobstacle):
	def __init__(self, *args, **kargs):
		squareobstacle.__init__(self, *args, **kargs)
		self.physical = False

class backgroundobstacle(squareobstacle):
	def __init__(self, lyr, imgname, index):
		self.index = index
		
		squareobstacle.__init__(self, lyr, roundlist([COORDS_HEIGHT, (COORDS_HEIGHT-500)/2.0]), [None, COORDS_HEIGHT + 500], img=imgname)
		
	def update(self):
		squareobstacle.update(self)
		
		myrect = self.getrect()
		width = myrect.right - myrect.left
		center = self.layer.screentocoords([SCREEN_SIZE[0]/2, SCREEN_SIZE[1]/2])[0]
		value = int(center / width) + self.index
		self.pos = [value * width, self.pos[1]]

class sidewall(squareobstacle): # for wallrunning
	def __init__(self, lyr, pos, size, color=None, **kwargs):
		if color == None: color = [80, 80, 80]
		
		squareobstacle.__init__(self, lyr, pos, size, color, **kwargs)
		self.physical = False
		self.effect = WALLEFFECT
	
class deathobstacle(squareobstacle): # die if touched
	def __init__(self, lyr, pos, size, color=None, **kwargs):
		if color == None: color = [255, 0, 0]
		
		squareobstacle.__init__(self, lyr, pos, size, **kwargs)

	def collidewithperson(self, person):
		person.die()

class winobstacle(squareobstacle): # win (level) if touched
	def __init__(self, lyr, pos, size, color=None, **kwargs):
		if color == None: color = [255, 255, 0]
		
		squareobstacle.__init__(self, lyr, pos, size, color, **kwargs)
		self.physical = False

	def collidewithperson(self, person):
		person.win()

	
def pause(message):
	global paused, pausedmessage
	
	pausedmessage = message
#	paused = True
	lvl.meta = True
	pausedmessages = pausedmessage.split("\n")
	numbermessages = len(pausedmessages)
	for index, line in enumerate(pausedmessages):
		pausedtext = font.render(line, 1, (10, 10, 10))
		pausedtextpos = pausedtext.get_rect(centerx=background.get_width()/2, centery=(background.get_height()/2 + (index - numbermessages/2.0)*FONT_SIZE))
		screen.blit(pausedtext, pausedtextpos)

	pygame.display.flip()
	
	while True:
		clock.tick(1.0/dt)
		#Handle Input Events
		for event in pygame.event.get():
			if event.type == QUIT:
				exit()
			if event.type == KEYDOWN:
				if event.key == K_RETURN:
					return
				elif event.key == K_ESCAPE:
					exit()

pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)

background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((250, 250, 250))

screen.blit(background, (0, 0))
pygame.display.flip()

clock = pygame.time.Clock()

paused = False
pausedmessage = None

FONT_SIZE = 50
font = pygame.font.Font(None, FONT_SIZE)

def nextlevel():
	global levelnumber, lvl
	levelnumber += 1
	if (levelnumber < len(levels.levels)):
		lvl = level(levels.levels[levelnumber])
		if levelnumber != 0:
			pause("You won!\n\nPress Enter to continue to the next level")
	else:
		pause("There are no more levels left\n\nYou have beaten the game!")
		exit()

levelnumber = -1
nextlevel()

def keypressed(keys, validkeys):
	for key in validkeys:
		if keys[key]:
			return True
	return False

while True:
	clock.tick(1.0/dt)
    #Handle Input Events
	for event in pygame.event.get():
		if event.type == QUIT:
			exit()
		if event.type == KEYDOWN:
			if event.key == K_RETURN:
				if paused:
					paused = False
			elif event.key == K_ESCAPE:
				if paused:
#					paused = False
					exit()
				else:
					pause("Paused\n\nPress Enter to continue")
			elif event.key in KEYSPLIT: # Split
				lvl.split()
			for index, psn in enumerate(lvl.getppl()):
				playernum = numplayers - index - 1
				if playernum >= numctrls:
					playernum = 0
				
				if event.key in KEYJUMP[playernum]:
					if psn.onground:
						psn.velocity[1] = JUMP
					elif psn.onwall:
						psn.velocity[1] = WALLJUMP
						psn.runningdir = -psn.runningdir

	
	keys = pygame.key.get_pressed()  #checking pressed keys
	
	if not paused:
		numplayers = len(lvl.getppl())
		numctrls = len(KEYRIGHT)
		for index, psn in enumerate(lvl.getppl()):
			playernum = numplayers - index - 1
			if playernum >= numctrls:
				playernum = 0
			if CHEATY_MODE:
				psn.runningdir = 0
				if keypressed(keys, KEYRIGHT[playernum]):
					psn.runningdir = 1
				if keypressed(keys, KEYLEFT[playernum]):
					psn.runningdir = -1
			if keypressed(keys, KEYSLIDE[playernum]):
				if psn.slidingrecoverytimer >= SLIDINGRECOVERYTIME:
					psn.issliding = True
					psn.updateimage()
			else:
				psn.issliding = False
				psn.updateimage()
			if keypressed(keys, KEYJUMP[playernum]):
				if WALLEFFECT in psn.effects and psn.walltimer < WALLTIME and psn.velocity[1] < WALLMAXVELOCITY:
					psn.velocity[1] += WALLACCEL
					psn.walltimer += dt
		
		
		#update
		lvl.update()
	
	#Draw Everything
	screen.blit(background, (0, 0))
	
	lvl.draw(screen)
	
	if paused: # draw paused message
		pausedmessages = pausedmessage.split("\n")
		numbermessages = len(pausedmessages)
		for index, line in enumerate(pausedmessages):
			pausedtext = font.render(line, 1, (10, 10, 10))
			pausedtextpos = pausedtext.get_rect(centerx=background.get_width()/2, centery=(background.get_height()/2 + (index - numbermessages/2.0)*FONT_SIZE))
			screen.blit(pausedtext, pausedtextpos)

	pygame.display.flip()

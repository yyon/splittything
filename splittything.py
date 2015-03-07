#!/usr/bin/env python

import pygame
from pygame.locals import *
import os
import copy

#TODO:
# Splitting
# Design levels
# Loading levels from files
# Level editor
# Better graphics
# Let pictures go outside their rectangles

# Buttons and doors
# Slowness area
# Trampoline
# Stuff that interacts between the split people

#Stuff we can do with more time
# Animations
# Story
# Angles

SCREEN_SIZE = [1200, 800]

CHEATY_MODE = False

defaultoffset = [0, -SCREEN_SIZE[1]]
defaultscale = 1000.0 / SCREEN_SIZE[1]

dt = 1.0/60.0

SLIDINGRECOVERYTIME = 0.5
SLIDINGTIME = 1
GRAVITY = 0.5
RUNNINGSPEED = 10
JUMP = 17
WALLMAXVELOCITY = 2
WALLTIME = 0.1
WALLACCEL = 3

WALLEFFECT = "WALL"

def load_image(name):
	try:
		image = pygame.image.load(name)
	except pygame.error, message:
		print 'Cannot load image:', name
		raise SystemExit, message
	image = image.convert_alpha()
	return image

def roundlist(l):
	return [int(e) for e in l]

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
	
	def collides(self, otherrect):
		return not (otherrect.left > self.right \
			or otherrect.right < self.left \
			or otherrect.top < self.bottom \
			or otherrect.bottom > self.top)
	
	def __str__(self):
		return str(self.left) + " " + str(self.right) + " " + str(self.bottom) + " " + str(self.top)

class possprite(pygame.sprite.Sprite):
	def __init__(self, lyr, pos):
		pygame.sprite.Sprite.__init__(self)
		
		self.pos = pos
		self.layer = lyr
		self.coordsrect = rect()
		
		self.image = None
		
	def setimage(self, image, scale=1):
		self.img = image
		imgrect = self.img.get_rect()
		self.image = pygame.transform.scale(self.img, roundlist([x*scale for x in self.layer.scaletoscreen(imgrect.size)]))
		self.rect = self.image.get_rect()
		
	def setinvisible(self, size):
		self.rect = pygame.Rect((0,0), size)
		img = pygame.Surface((0,0))
		img.fill([0,0,0])
		self.image = img
		
	def move(self, direction):
		self.pos = [self.pos[0]+direction[0], self.pos[1]+direction[1]]
		
	def getrect(self):
#		left, top = self.layer.screentocoords(self.rect.topleft)
#		right, bottom = self.layer.screentocoords(self.rect.bottomright)
		
		width, height = self.layer.scaletocoords(self.rect.size)
		left, right = self.pos[0] - width/2.0, self.pos[0] + width/2.0
		bottom, top = self.pos[1] - height/2.0, self.pos[1] + height/2.0
		
		self.coordsrect.setrect(left, right, bottom, top)
		return self.coordsrect
		
	def collides(self, othersprite):
		return self.getrect().collides(othersprite.getrect())
		
	def update(self):
		self.rect.center = self.layer.coordstoscreen(self.pos)
		
	def draw(self, screen):
		pygame.sprite.Sprite.draw(self, screen)

class layer():
	def __init__(self, lvl):
		self.level = lvl
		
		self.offset = defaultoffset
		self.scale = [defaultscale,defaultscale]
		
		self.persongroup = pygame.sprite.Group()
		self.obstacles = pygame.sprite.Group()
		
		self.person = person(self, [0,300])
		
		self.persongroup.add(self.person)
		
		self.addobstacle([200, 100], [500,100])
#		self.addobstacle([250, 200], [100,100])
		self.addwall([800, 400], [400, 300])
		self.addobstacle([3300, 100], [4000,100])
		self.addobstacle([1800, 400], [100,300])
		self.addobstacle([2300, 200], [100,100])
		self.addobstacle([3100, 550], [100,100])
		self.addobstacle([3100, 250], [100,200])
		self.addobstacle([4500, 350], [800,25])
		self.adddeathobstacle([0,0], [90000, 0], True)
		self.adddeathobstacle([4500,700], [500, 100])
		self.addwinobstacle([5250,700], [25, 1400], False)
		
	def addobstacle(self, pos, size):
		self.obstacles.add(squareobstacle(self, pos, size))
		
	def addwall(self, pos, size):
		self.obstacles.add(sidewall(self, pos, size))
	
	def adddeathobstacle(self, pos, size, invisible=False):
		self.obstacles.add(deathobstacle(self, pos, size, invisible=invisible))
	
	def addwinobstacle(self, pos, size, invisible=True):
		self.obstacles.add(winobstacle(self, pos, size, invisible=invisible))
	
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
		
	def update(self):
		self.obstacles.update()
		self.persongroup.update()
#		self.offset[0] -= 1
		self.offset[0] = -self.scaletoscreen([self.person.pos[0] - 200, 0])[0]
		
	def draw(self, screen):
		self.obstacles.draw(screen)
		self.persongroup.draw(screen)
		
	def gameover(self):
		self.level.reset()
		
	def win(self):
		self.level.reset()

class person(possprite):
	def __init__(self, lyr, pos):
		possprite.__init__(self, lyr, pos)
		self.uprightimage = load_image('person.png')
		self.slidingimage = load_image('sliding_person.png')
		self.setimage(self.uprightimage)
		
		self.velocity = [0, 0]
		self.walltimer = 0
		self.slidingtimer = 0
		self.slidingrecoverytimer = 0
		self.issliding = False
		self.doslide = False
		self.movingright = True
		
		self.effects = []
		
		self.update()

	def update(self):
		if self.movingright:
			self.velocity[0] = RUNNINGSPEED
		else:
			if self.velocity[0] > 0:
				self.velocity[0] = 0
		
		self.velocity[1] -= GRAVITY
		oldrect = self.getrect().copy()
		
		if self.issliding:
			self.slidingtimer += dt
			self.slidingrecoverytimer = 0
			if self.slidingtimer >= SLIDINGTIME:
				self.doslide = False
		else:
			self.slidingtimer = 0
			if self.slidingrecoverytimer < SLIDINGRECOVERYTIME:
				self.slidingrecoverytimer += dt
		
		if self.issliding != self.doslide:
			self.issliding = self.doslide
			
			if self.issliding:
				self.setimage(self.slidingimage)
			else:
				self.setimage(self.uprightimage)
			
			self.move([0, oldrect.bottom - self.getrect().bottom])
			
		self.move(self.velocity)
		
		possprite.update(self)
		
		newrect = self.getrect()
		
		self.onground = False
		
		self.effects = []
		
		for obstacle in self.layer.obstacles:
			collrect = obstacle.getrect()
			if newrect.collides(collrect):
				obstacle.collidewithperson(self)
				
				if obstacle.physical:
					
					distanceright =  newrect.right - collrect.left
					distanceleft = collrect.right - newrect.left
					distancedown = collrect.top - newrect.bottom
					distanceup = newrect.top - collrect.bottom
					
					distances = [distanceright, distanceleft, distancedown, distanceup]
					distances = [distance for distance in distances if distance >= 0]
					mindistance = min(distances)
					
					if mindistance == distanceright:# self.velocity[0] > 0 and #collrect.left >= oldrect.right:
						#collision right
						if CHEATY_MODE:
							self.move([collrect.left - newrect.right, 0])
							self.velocity[0] = 0
						else:
							self.die()
					elif mindistance == distanceleft:# self.velocity[0] < 0 and #collrect.right <= oldrect.left:
						#collision left
						# This probably won't happen
						if CHEATY_MODE:
							self.move([collrect.right - newrect.left, 0])
							self.velocity[0] = 0
						else:
							if distanceleft > 5:
								self.die()
					elif mindistance == distancedown:# self.velocity[1] < 0 and #collrect.top <= oldrect.bottom:
						#collision is a floor
						self.move([0, collrect.top - newrect.bottom])
						self.velocity[1] = 0
						self.onground = True
					elif mindistance == distanceup:# self.velocity[1] > 0 and #collrect.bottom >= oldrect.top:
						#collision is a ceiling
						self.move([0, collrect.bottom - newrect.top])
						if self.velocity[1] > 0:
							self.velocity[1] = 0
				if obstacle.effect != None:
					if not obstacle.effect in self.effects:
						self.effects.append(obstacle.effect)
		
		if self.onground:
			self.walltimer = 0
		
		possprite.update(self)
	
	def die(self):
		pause("You died\n\nPress Enter to try again")
		self.layer.gameover()
		
	def win(self):
		pause("You won!\n\nPress Enter to continue to the next level")
		self.layer.win()

class obstacle():
	def __init__(self, physical=True):
		self.physical = physical
		self.effect = None
		
	def collidewithperson(self, person):
		pass

class squareobstacle(possprite, obstacle):
	def __init__(self, lyr, pos, size, color=[0, 0, 255], invisible=False):
		possprite.__init__(self, lyr, pos)
		obstacle.__init__(self)
		
		if invisible:
			self.setinvisible(size)
		else:
			img = pygame.Surface(size)
			img.fill(color)
			self.setimage(img)
		
		self.update()
		
	def update(self):
		possprite.update(self)

class sidewall(squareobstacle):
	def __init__(self, lyr, pos, size, color=[0, 255, 0]):
		squareobstacle.__init__(self, lyr, pos, size, color)
		self.physical = False
		self.effect = WALLEFFECT
	
class deathobstacle(squareobstacle):
	def __init__(self, lyr, pos, size, color=[255, 0, 0], invisible=False):
		squareobstacle.__init__(self, lyr, pos, size, color, invisible)

	def collidewithperson(self, person):
		person.die()

class winobstacle(squareobstacle):
	def __init__(self, lyr, pos, size, color=[255, 255, 0], invisible=True):
		squareobstacle.__init__(self, lyr, pos, size, color, invisible)
		self.physical = False

	def collidewithperson(self, person):
		person.win()

class level():
	def __init__(self):
		self.reset()
		
	def reset(self):
		self.layers = []
		layer1 = layer(self)
		self.layers.append(layer1)
		
	def update(self):
		for lyr in self.layers:
			lyr.update()
	
	def draw(self, screen):
		for lyr in self.layers:
			lyr.draw(screen)
		
	
def pause(message):
	global paused, pausedmessage
	paused = True
	pausedmessage = message


pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE)

background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((250, 250, 250))

screen.blit(background, (0, 0))
pygame.display.flip()

lvl = level()

clock = pygame.time.Clock()

paused = False
pausedmessage = None

FONT_SIZE = 50
font = pygame.font.Font(None, FONT_SIZE)


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

	
	keys = pygame.key.get_pressed()  #checking pressed keys
	
	
	if not paused:
		if CHEATY_MODE:
			lvl.layers[0].person.velocity[0] = 0
			if keys[K_RIGHT]:
				lvl.layers[0].person.movingright = True
			else:
				lvl.layers[0].person.movingright = False
			if keys[K_LEFT]:
				lvl.layers[0].person.velocity[0] = -RUNNINGSPEED
		if keys[K_DOWN]:
			if lvl.layers[0].person.slidingrecoverytimer >= SLIDINGRECOVERYTIME:
				lvl.layers[0].person.doslide = True
		else:
			lvl.layers[0].person.doslide = False
		if keys[K_SPACE]:
			if lvl.layers[0].person.onground:
				lvl.layers[0].person.velocity[1] = JUMP
			if WALLEFFECT in lvl.layers[0].person.effects and lvl.layers[0].person.walltimer < WALLTIME and lvl.layers[0].person.velocity[1] < WALLMAXVELOCITY:
				lvl.layers[0].person.velocity[1] += WALLACCEL
				lvl.layers[0].person.walltimer += dt
		
		
		#update
		lvl.update()
	
	#Draw Everything
	screen.blit(background, (0, 0))
	
	lvl.draw(screen)
	
	if paused:
		pausedmessages = pausedmessage.split("\n")
		numbermessages = len(pausedmessages)
		for index, line in enumerate(pausedmessages):
			pausedtext = font.render(line, 1, (10, 10, 10))
			pausedtextpos = pausedtext.get_rect(centerx=background.get_width()/2, centery=(background.get_height()/2 + (index - numbermessages/2.0)*FONT_SIZE))
			screen.blit(pausedtext, pausedtextpos)

	pygame.display.flip()

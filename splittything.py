#!/usr/bin/env python

import pygame
from pygame.locals import *
import os

def load_image(name):
	try:
		image = pygame.image.load(name)
	except pygame.error, message:
		print 'Cannot load image:', name
		raise SystemExit, message
	image = image.convert()
	return image, image.get_rect()

class Person(pygame.sprite.Sprite):
	def __init__(self):
		pygame.sprite.Sprite.__init__(self) #call Sprite initializer
		self.image, self.rect = load_image('person.png')


pygame.init()
screen = pygame.display.set_mode((800, 600))

background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((250, 250, 250))


screen.blit(background, (0, 0))
pygame.display.flip()

person1 = Person()

allsprites = pygame.sprite.RenderPlain((person1))

clock = pygame.time.Clock()

while True:
	clock.tick(60)
    #Handle Input Events
	for event in pygame.event.get():
		if event.type == QUIT:
			break

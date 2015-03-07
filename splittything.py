#!/usr/bin/env python

class Person(pygame.sprite.Sprite):
	def __init__(self):
		pygame.sprite.Sprite.__init__(self) #call Sprite initializer
		self.image, self.rect = load_image('fist.bmp', -1)


pygame.init()
screen = pygame.display.set_mode((800, 600))

background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((250, 250, 250))


screen.blit(background, (0, 0))
pygame.display.flip()

person1 = Person()

allsprites = pygame.sprite.RenderPlain((person1))

while True:
	clock.tick(60)


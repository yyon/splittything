#!/usr/bin/env python

def intro(ml):
	



def sample(ml):
	ml.makelayers(2)
	ml.setpersonpos([0, 300])
	
	ml.setbackground("sample_background.png")
	
	ml.addobstacle(None, [200, 50], [2200,200])
	ml.addobstacle(None, [500, 400], [100,500])#, margins=[20, 20, 20, 20])
	ml.addobstacle(None, [100, 800], [100,500])
	ml.addwall(None, [1800, 400], [400, 300], img="sidewall.png")
	ml.addobstacle(None, [4300, 0], [4000,300])
	ml.addsidedeathobstacle(None, [2800, 400], [100,200])
	ml.addsidedeathobstacle(None, [3300, 200], [100,100])
	ml.addsidedeathobstacle(None, [4100, 550], [100,100])
	ml.addsidedeathobstacle(None, [4100, 250], [100,200])
	
	ml.addsidedeathobstacle(0, [5000, 250], [100,200])
	ml.addsidedeathobstacle(1, [5000, 455], [100,200])
	
	ml.addobstacle(None, [5500, 350], [800,25])
	ml.adddeathobstacle(None, [0,0], [90000, 0], invisible=True)
	ml.adddeathobstacle(None, [5500,700], [500, 100])
	ml.addobstacle(0, [7000, 50], [1200,200])
	ml.addwinobstacle(None, [8000,700], [25, 1400], invisible=False)

levels = [sample]


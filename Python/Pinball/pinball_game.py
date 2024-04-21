# -*- coding: utf-8 -*-

import threading, sys, os
import queue

from tkinter import *
import random as random
#from math import copysign
import math
import numpy as np
from abc import ABC, abstractmethod
import time

# For console input, TKInter has its own keyboard handler
#from keyboardmod import read_key

WIDTH = 800
HEIGHT = 800

# Could differentiate collision and wall friction from general friction
# See PinballMachine for these constants
# FRICTION = 0.99 # .99 # 0.95
# GRAVITY = 0.1 # 0.1
# BUMPER_MULTIPLIER = 2.0
# MAX_SPEED = 10


# Goals for next week
# - Need fixed obstacles and collision detection
# - Need gravity pulling down and bumper at bottom
# - Need to refactor (change the structure) of the code to handle multiple objects
# ... Need a central animation core that manages multiple objects 
    # ... Main animation loop has to animate all objects at once
# ... Need a wrapper class for pinball machine
# - Need to separate rectangular wall objects from balls (boundaries become wall)
# - Need to add scoring
# - Need to add bumper controls
# - Need to add oblique angles as well as a proper handling of 
#   (directional angles) reflections for oblique objects
# - Collision modeling, physics computation and rendering

# - Multiple levels with ramps
# - Funnels at the top
# - Catch and timed random release bumpers 
# - Electromagnets
# - Multiple lower bumpers but also catch when hold up
# - Fix glitches
# - Hitting certain bumpers release balls
# - Real spring action

class PinballObject(ABC):
     
    id_counter = 0

    def __init__(self, canvas, initx, inity, sizex, sizey, color, 
                 velx, vely, fixed, bumper):
        self.canvas = canvas
        self.init = np.array([initx,inity]).astype('float64')
        self.size = np.array([sizex,sizey]).astype('float64')
        self.speed = np.array([velx,vely]).astype('float64')
        self.color = color

        self.fixed = fixed
        self.bumper = bumper

        if (fixed):
            self.mass = 10e100 # don't want numerical issues with positive infinity!
        else:
            # simple mass approximation assuming all rectangular objects
            self.mass = abs(sizex*sizey)
            
        self.id = PinballObject.id_counter
        self.active = None

        PinballObject.id_counter += 1
        print((type(self),self.id))
    
class PinballLine(PinballObject):    

    def __init__(self, canvas, initx, inity, sizex, sizey, color, 
                 fixed = True, bumper = 1):   
        super().__init__(canvas, initx, inity, sizex, sizey, color, 0, 0, fixed, bumper)
        self.shape = canvas.create_line(initx, inity, initx+sizex, inity+sizey, fill=color)
        self.active = False
        self.min = np.array([min(initx, initx + sizex), min(inity, inity + sizey)])
        self.max = np.array([max(initx, initx + sizex), max(inity, inity + sizey)])

class PinballActuator(PinballLine):
    
    def __init__(self, canvas, 
                 initx, inity, sizex, sizey, 
                 initx2, inity2, sizex2, sizey2, 
                 color, 
                 fixed = True, bumper = 1, keypress = None, duration = 5):   
        super().__init__(canvas, initx, inity, sizex, sizey, color, fixed, bumper)

        self.countdown_to_orig = 0
        self.duration = duration
        
        self.orig_initx = initx
        self.orig_inity = inity
        self.orig_sizex = sizex
        self.orig_sizey = sizey 
        self.orig_bumper = bumper

        self.action_initx = initx2
        self.action_inity = inity2
        self.action_sizex = sizex2
        self.action_sizey = sizey2
        self.action_bumper = 2.5*bumper
        
        self.keypress = keypress
        
        self.active = False
        self.min = np.array([min(initx, initx + sizex), min(inity, inity + sizey)])
        self.max = np.array([max(initx, initx + sizex), max(inity, inity + sizey)])
    
    def handleActuation(self, keyboard_event):
        
        # Set countdown timer as appropriate
        if (keyboard_event == self.keypress):
            #print("Handling: ", keyboard_event)
            self.countdown_to_orig = self.duration
        elif (self.countdown_to_orig > 0):
            self.countdown_to_orig -= 1
            
        # Set image based on whether actuated or not
        old_init = self.init.copy()
        old_size = self.size.copy()
        if (self.countdown_to_orig > 0):
            self.init = np.array([self.action_initx,self.action_inity]).astype('float64')
            self.size = np.array([self.action_sizex,self.action_sizey]).astype('float64')
            self.bumper = self.action_bumper
        else:
            self.init = np.array([self.orig_initx,self.orig_inity]).astype('float64')
            self.size = np.array([self.orig_sizex,self.orig_sizey]).astype('float64')
            self.bumper = self.orig_bumper

        # Redraw
        if (not np.array_equal(self.init, old_init) or not np.array_equal(self.size, old_size)):
            self.canvas.delete(self.shape)
            self.shape = self.canvas.create_line(self.init[0], self.init[1], self.init[0]+self.size[0], self.init[1]+self.size[1], fill=self.color)    
    
        # print("Count: ", self.countdown_to_orig)
        # print("Init: ", self.init)
        # print("Size: ", self.size)
    
class PinballCircle(PinballObject):
    
    RANDOM_LINE_PERTURB = 0.5
    
    def __init__(self, canvas, initx, inity, sizex, sizey, color, 
                 velx = 0, vely = 0, fixed = False, bumper = 1, score = 0):
        super().__init__(canvas, initx, inity, sizex, sizey, color, velx, vely, fixed, bumper)
        self.shape = canvas.create_oval(initx, inity, initx+sizex, inity+sizey, fill=color)
        # Replace mass with default sizex*sizey if specified
        self.score = score
        self.active = True
        self.radius = sizex / 2.0
        self.contact_wall = np.array([False, False])
        assert sizex == sizey, "circles are not symmetric in x,y dims"

    def get_center(self):
        pos = self.canvas.coords(self.shape)
        return np.array([(pos[0] + pos[2])/2.0, (pos[1] + pos[3])/2.0])

    # https://www.mathsisfun.com/physics/momentum-animation.html
    def is_collision(self, objs):
        for obj in objs:
            if (self == obj):
                continue
 
            if (isinstance(obj,PinballLine)):
                # We're projecting the center of a circle onto a line to see nearest point
                # of possible overlap.
                #
                # Do math to project to obtain (xc,yc), for now, just draw collision point
                # Line has slope (sizey/sizex)
                # Let points P & Q be on the line
                # ... N . (P-Q) = (-sizey, sizex) . (sizex, sizey)
                # normal_vector N = (-sizey, sizex) (can see that gradients )
                # ... N must be normalized unit vector
                # 
                # Let P be a point (center of self) and x = (obj.initx, obj.inity) be on the line
                # Proj = P - (P-x . N) elementwise* N
                #            \---v---/
                #                C
                P = self.get_center()
                x = obj.init
                N = np.array([-obj.size[1],obj.size[0]])/np.linalg.norm(obj.size)
                
                C = (P-x).dot(N)
                
                # Get the final projected point
                Proj = P - C*N
                
                dist = np.linalg.norm(P - Proj)
                #print("LINE DISTANCE: ", dist, "RADIUS: ", self.radius)

                # Also check within endpoints!
                if (dist < self.radius and Proj[0] >= obj.min[0] and Proj[0] <= obj.max[0]
                    and Proj[1] >= obj.min[1] and Proj[1] <= obj.max[1]):
                    #self.canvas.create_oval(Proj[0]-1, Proj[1]-1, Proj[0]+1, Proj[1]+1, fill="red")
                    # print("")
                    # print("COLLISION")
                    return obj
            
            elif (isinstance(obj, PinballCircle)):
                
                dist = np.linalg.norm(self.get_center() - obj.get_center())                
                gap = dist - (self.size[0] + obj.size[0])/2.0; # symmetrical objects
                
                if (gap <= 0):
                    return obj     
        return None

    def ball_update(self, objs, regions):
        
        ret_score = 0
        
        # See if ball disappears
        for region in regions:
            if (region.disappears and region.in_region(self)):
                objs.remove(self)
                self.canvas.delete(self.shape) 
                return ret_score
        
        # Check for boundary hit
        #old_pos = self.canvas.coords(self.shape)
        speedx = self.speed[0]
        speedy = self.speed[1]
        # if (old_pos[0] + speedx < 0):
        #     speedx = 0
        # elif (old_pos[2] + speedx > WIDTH):
        #     speedx = 0
        # elif (old_pos[1] + speedy < 0):
        #     speedy = 0
        # elif (old_pos[3] + speedy > HEIGHT):
        #     speedy = 0
            
        # Update position
        self.canvas.move(self.shape, speedx/2.0, speedy/2.0)
        
        # Remember the old position so that the wall hitting effects can take place
        #pos = old_pos
        pos = self.canvas.coords(self.shape)
        
        #(x=pos[0],y=pos[1])  
        #          +----+
        #          |    |
        #          +----+
        #               (x=pos[2],y=pos[3])
        #if (pos[2] >= WIDTH or pos[0] <= 0) and abs(self.speedx) != 0:
        #    self.speedx = (self.speedx - copysign(1,self.speedx)) * -1
        #if (pos[3] >= HEIGHT or pos[1] <= 0) and abs(self.speedy) != 0:
        #    self.speedy = (self.speedy - copysign(1,self.speedy)) * -1
        
        if (not self.fixed):
            #print("Speed: ",self.speed, " FRICTION: ", PinballMachine.FRICTION)
            
            # Check for unusual friction regions (assuming no overlap)
            modified_friction = self.get_friction(regions)
            self.speed *= math.sqrt(PinballMachine.FRICTION if modified_friction == None else modified_friction)
            
            # Check for unusual gravity regions (assuming no overlap)
            modified_gravity = self.get_gravity(regions)
            self.speed[1] += (PinballMachine.GRAVITY if modified_gravity == None else modified_gravity)/2.0
            
            self.speed = np.minimum(self.speed,  PinballMachine.MAX_SPEED)
            self.speed = np.maximum(self.speed, -PinballMachine.MAX_SPEED)
        
        # Eventually should handle multiple collisions, but requires refactoring
        # such that we return a set of all collisions and the velocity changes of impacts
        # are additive
        cobj = self.is_collision(objs)
        if (cobj != None and isinstance(cobj,PinballLine)):
            
            # Use Wiki article but final x difference should be a unit vector
            # https://en.wikipedia.org/wiki/Elastic_collision#Two-dimensional_collision_with_two_moving_objects
            # v_1' = v_1 - 2*m_2/(m_1+m_2) * <v_1 - v_2, x_1 - x_2> (x_1 - x_2)
            # v_2' = v_2 - 2*m_1/(m_1+m_2) * <v_2 - v_1, x_2 - x_1> (x_2 - x_1)
            # (x1 - x2) and (x2 - x1) both need to be unit vectors
            # self = x_1,v_1, cobj = x_2,v_2 (is fixed line = infinite mass = no update)
            
            # We're using collision point with line as x_2... see Proj above in collision with line
            P = self.get_center()
            x = cobj.init
            N = np.array([-cobj.size[1],cobj.size[0]])/np.linalg.norm(cobj.size)
            C = (P-x).dot(N)
                
            # Get the final projected point
            Proj = P - C*N
            
            diff_v1 = self.speed # object 2 is not moving
            diff_x1 = self.get_center() - Proj
            diff_x1 /= np.linalg.norm(diff_x1)
            
            # print("Collision speed before: ",(self.speed))
            
            if (not self.fixed):
                bumper_mult = cobj.bumper # (PinballMachine.BUMPER_MULTIPLIER if cobj.bumper else 1.0) # see if other obj is bumper
                # Mass coefficient 2*m_2/(m_1+m_2) = 2.0 since m_2 is infinite
                self.speed = self.speed - 2.0 * diff_v1.dot(diff_x1) * diff_x1 * bumper_mult
                self.speed[0] += np.random.uniform(-PinballCircle.RANDOM_LINE_PERTURB, PinballCircle.RANDOM_LINE_PERTURB)
                self.speed[1] += np.random.uniform(-PinballCircle.RANDOM_LINE_PERTURB, PinballCircle.RANDOM_LINE_PERTURB)
            
        elif (cobj != None and isinstance(cobj,PinballCircle) and self.id > cobj.id):
            
            ret_score = cobj.score + self.score 

            # Use Wiki article but final x difference should be a unit vector
            # https://en.wikipedia.org/wiki/Elastic_collision#Two-dimensional_collision_with_two_moving_objects
            # v_1' = v_1 - 2*m_2/(m_1+m_2) * <v_1 - v_2, x_1 - x_2> (x_1 - x_2)
            # v_2' = v_2 - 2*m_1/(m_1+m_2) * <v_2 - v_1, x_2 - x_1> (x_2 - x_1)
            # (x1 - x2) and (x2 - x1) both need to be unit vectors
            # self = x_1,v_1, cobj = x_2,v_2 (is fixed line = infinite mass = no update)
            mass_coef1 = (2.0*cobj.mass)/(self.mass + cobj.mass)
            mass_coef2 = (2.0*self.mass)/(self.mass + cobj.mass)
            
            diff_v1 = self.speed - cobj.speed
            diff_x1 = self.get_center() - cobj.get_center()
            diff_x1 /= np.linalg.norm(diff_x1)
            
            diff_v2 = cobj.speed - self.speed
            diff_x2 = cobj.get_center() - self.get_center()
            diff_x2 /= np.linalg.norm(diff_x2)

            if (not self.fixed):
                bumper_mult1 = cobj.bumper # (PinballMachine.BUMPER_MULTIPLIER if cobj.bumper else 1.0) # see if other obj is bumper
                self.speed = self.speed - (mass_coef1 * diff_v1.dot(diff_x1) * diff_x1 * bumper_mult1)

            if (not cobj.fixed):
                bumper_mult2 = self.bumper # (PinballMachine.BUMPER_MULTIPLIER if self.bumper else 1.0) # see if other obj is bumper
                cobj.speed = cobj.speed - (mass_coef2 * diff_v2.dot(diff_x2) * diff_x2 * bumper_mult2)

        else:
            # Handle wall collision (just reverses velocity for wall that is hit)
            # Note: wall variable prevents constantly reversing course
            if (pos[2] >= WIDTH or pos[0] <= 0) and not self.contact_wall[0]:
                self.speed[0] *= -1
                self.contact_wall[0] = True
            else:
                self.contact_wall[0] = False
                
            if (pos[3] >= HEIGHT or pos[1] <= 0) and not self.contact_wall[1]:
                self.speed[1] *= -1
                self.contact_wall[1] = True
            else:
                self.contact_wall[1] = False
    
        return ret_score
    
    def get_gravity(self, regions):
        for region in regions:
            if (region.gravity != None and region.in_region(self)):
                return region.gravity
        return None
        
    def get_friction(self, regions):
        for region in regions:
            if (region.friction != None and region.in_region(self)):
                return region.friction
        return None
        

class PinballRegion(ABC):
    def __init__(self, initx, inity, sizex, sizey, disappears = False, friction = None, gravity = None):  
        self.initx = initx
        self.inity = inity
        self.sizex = sizex
        self.sizey = sizey
        self.disappears = disappears
        self.friction = friction
        self.gravity = gravity

    def in_region(self, pinball_object):
        pos = pinball_object.get_center()
        return (self.initx < pos[0] and pos[0] < self.initx + self.sizex 
                and self.inity < pos[1] and pos[1] < self.inity + self.sizey)

class PinballMachine:
    
    TK = Tk()
    CANVAS = Canvas(TK, width=WIDTH, height=HEIGHT, bg="gray")
    CANVAS.pack()

    # # Frictionless balls in space
    # FRICTION = 1.00 # .99 # 0.95
    # GRAVITY = 0.0 # 0.1
    # BUMPER_MULTIPLIER = 1.0
    # MAX_SPEED = 50.0
    # LAYOUT = [
    #                   PinballCircle(CANVAS,0,0,50,50,"red", 3, 3), 
    #                   PinballCircle(CANVAS,100,100,50,50,"blue", 3, 3),
    #                   PinballCircle(CANVAS,200,200,100,100,"black", 6, 3),
    #                   PinballCircle(CANVAS,350,350,100,100,"green", 3, 6),
    #                 # PinballCircle(CANVAS,0,200,100,100,"black", 6, 3),
    #                 # PinballCircle(CANVAS,0,350,100,100,"green", 3, 6),
    #                 # PinballCircle(CANVAS,200,0,100,100,"black", 6, 3),
    #                 # PinballCircle(CANVAS,350,0,100,100,"green", 3, 6),
    #                 # PinballCircle(CANVAS,100,200,100,100,"red", 6, 3),
    #                 # PinballCircle(CANVAS,100,350,100,100,"blue", 3, 6),
    #                 # PinballCircle(CANVAS,200,100,100,100,"purple", 6, 3),
    #                 # PinballCircle(CANVAS,350,100,100,100,"yellow", 3, 6),
    #                   PinballCircle(CANVAS,50,50,20,20,"purple", 3, 3),
    #                   PinballCircle(CANVAS,150,150,20,20,"yellow", 9, 9)]
 
    # # Balls dropping
    # FRICTION = 0.995 # .99 # 0.95
    # GRAVITY = 0.1 # 0.1
    # BUMPER_MULTIPLIER = 1.0
    # MAX_SPEED = 50.0
    # LAYOUT = [
    #                   PinballCircle(CANVAS,10,10,50,50,"red"), #, 3, 3), 
    #                   PinballCircle(CANVAS,100,100,50,50,"blue"), #, 3, 3),
    #                   PinballCircle(CANVAS,200,200,100,100,"black"), #, 6, 3),
    #                   PinballCircle(CANVAS,350,350,100,100,"green"), #, 3, 6),
    #                 # PinballCircle(CANVAS,0,200,50,50,"black"),
    #                 # PinballCircle(CANVAS,0,350,50,50,"green"),
    #                 # PinballCircle(CANVAS,200,0,100,100,"black", 6, 3),
    #                 # PinballCircle(CANVAS,350,0,100,100,"green", 3, 6),
    #                 # PinballCircle(CANVAS,100,200,100,100,"red", 6, 3),
    #                 # PinballCircle(CANVAS,100,350,100,100,"blue", 3, 6),
    #                 # PinballCircle(CANVAS,200,100,100,100,"purple", 6, 3),
    #                 # PinballCircle(CANVAS,350,100,100,100,"yellow", 3, 6),
    #                   PinballCircle(CANVAS,50,50,20,20,"purple"), #, -3, -3),
    #                   PinballCircle(CANVAS,150,150,20,20,"yellow", -9, -9)]

    # # Balls dropping on lines
    # FRICTION = 0.99 # .99 # 0.95
    # GRAVITY = 0.1 # 0.1
    # BUMPER_MULTIPLIER = 1.0
    # MAX_SPEED = 50.0
    # LAYOUT = [
    #                   PinballCircle(CANVAS,0,0,50,50,"red", 3, 3), 
    #                   PinballCircle(CANVAS,100,100,50,50,"blue", 3, 3),
    #                   PinballCircle(CANVAS,200,200,35,35,"black", 6, 3),
    #                   PinballCircle(CANVAS,350,350,35,35,"green", 3, 6),
    #  k                # PinballCircle(CANVAS,350,100,100,100,"yellow", 3, 6),
    #                   PinballCircle(CANVAS,50,50,20,20,"purple", 3, 3),
    #                   PinballCircle(CANVAS,150,150,20,20,"yellow", 9, 9),
    #                   PinballLine(CANVAS,200,400,500,50,"black"),
    #                   PinballLine(CANVAS,100,200,500,-50,"black")]
    
    # Pinball!
    FRICTION = 0.99 # .99 # 0.95
    GRAVITY = 0.1 # 0.1 # 0.1
    BUMPER_MULTIPLIER = 2.0 # 2.0
    MAX_SPEED = 15.0
    BALL_LIMIT = 10
    LAYOUT = [       # beyond color: velx, vely, fixed?, bumper?
                      PinballCircle(CANVAS,WIDTH-75,HEIGHT-550,50,50,"lightblue",0,-14.0,False,2.0,10),
                      PinballCircle(CANVAS,WIDTH-75,HEIGHT-450,50,50,"blue",0,-12.0,False,2.0,10),
                      #khPinballCircle(CANVAS,WIDTH-75,HEIGHT-350,20,20,"darkblue",0,-14.0),
                      PinballCircle(CANVAS,(WIDTH-100)/2-50,-25,100,100,"red",0,0,True,BUMPER_MULTIPLIER,10),
                      PinballCircle(CANVAS,(WIDTH-100)/2-200,150,50,50,"orange",0,0,True,BUMPER_MULTIPLIER,5),
                      PinballCircle(CANVAS,(WIDTH-100)/2+150,150,50,50,"orange",0,0,True,BUMPER_MULTIPLIER,5),
                      PinballCircle(CANVAS,(WIDTH-100)/2-25,300,50,50,"green",0,0,True,BUMPER_MULTIPLIER,5),
                      # Left and right top slanted lines
                      PinballLine(CANVAS,0,100,100,-100,"red",True,BUMPER_MULTIPLIER),
                      PinballLine(CANVAS,WIDTH-100,0,100,100,"red",True,BUMPER_MULTIPLIER),
                      # Middle line
                      #PinballLine(CANVAS,(WIDTH-100)/2-100,500,200,0,"green",True,BUMPER_MULTIPLIER),
                      #PinballCircle(CANVAS,(WIDTH-100)/2-200,500,100,100,"green",0,0,True,1.5,5),
                      #PinballCircle(CANVAS,(WIDTH-100)/2+100,500,100,100,"green",0,0,True,1.5,5),
                      
                      # Bumpers
                      PinballActuator(CANVAS,
                                      0,HEIGHT-150,-50 + (WIDTH-100)/2.0,50,
                                      0,HEIGHT-150,-50 + (WIDTH-100)/2.0,25,
                                      "red",True, BUMPER_MULTIPLIER, 'h', 10),
                      #PinballActuator(CANVAS,
                      #                0,HEIGHT-150,-50 + (WIDTH-100)/2.0,50,
                      #                0,HEIGHT-125,WIDTH,0,
                      #                "red",True, BUMPER_MULTIPLIER, 'u', 10),
                      PinballActuator(CANVAS,
                                      50 + (WIDTH-100)/2.0,HEIGHT-100,
                                      WIDTH-100 - 50 - (WIDTH-100)/2.0,-50,
                                      50 + (WIDTH-100)/2.0,HEIGHT-125,
                                      WIDTH-100 - 50 - (WIDTH-100)/2.0,-25,
                                      "red",True, BUMPER_MULTIPLIER, 'k', 10),
                      # LHS vertical line
                      PinballLine(CANVAS,98,150,2,0,"black", True),
                      PinballLine(CANVAS,100,150,0,HEIGHT-400,"black", True, 1),
                      PinballLine(CANVAS,98,150,0,HEIGHT-400,"blue", True, BUMPER_MULTIPLIER*2),
                      # RHS vertical line
                      PinballLine(CANVAS,WIDTH-100,150,2,0,"black", True),
                      PinballLine(CANVAS,WIDTH-100,150,0,HEIGHT-150,"black", True),
                      PinballLine(CANVAS,WIDTH-98,150,0,HEIGHT-150,"black", True)]
    
    REGIONS = [       # The region at bottom where balls disappear
                      PinballRegion(0,HEIGHT-30,WIDTH,30, True, None, None),
                      PinballRegion(0,150,98,HEIGHT-400, False, 1.1, -2.0),
                      PinballRegion((WIDTH-100)/2-220,130,90,90, False, None, -1.0),
                      PinballRegion((WIDTH-100)/2+130,130,90,90, False, None, -1.0)
                      ]
    
    # Pinball!
    # FRICTION = 0.995 # .99 # 0.95
    # GRAVITY = 0.1 # 0.1 # 0.1
    # BUMPER_MULTIPLIER = 2.0 # 2.0
    # MAX_SPEED = 25.0
    # BALL_LIMIT = 5
    # LAYOUT = [       # beyond color: velx, vely, fixed?, bumper?
    #                   PinballCircle(CANVAS,WIDTH-75,HEIGHT-550,50,50,"lightblue",0,-14.0,False,2.0,10),
    #                   PinballCircle(CANVAS,WIDTH-75,HEIGHT-450,50,50,"blue",0,-12.0,False,2.0,10),
    #                   #PinballCircle(CANVAS,WIDTH-75,HEIGHT-350,20,20,"darkblue",0,-14.0),
                      
    #                   # Bumpers
    #                   PinballCircle(CANVAS,190,65,20,20,"orange",0,0,True,BUMPER_MULTIPLIER,10),
    #                   PinballCircle(CANVAS,290,65,20,20,"red",0,0,True,BUMPER_MULTIPLIER,10),
    #                   PinballCircle(CANVAS,390,65,20,20,"red",0,0,True,BUMPER_MULTIPLIER,10),
    #                   PinballCircle(CANVAS,490,65,20,20,"orange",0,0,True,BUMPER_MULTIPLIER,10),
    #                   PinballCircle(CANVAS,150,350,50,50,"green",0,0,True,BUMPER_MULTIPLIER,20),
    #                   PinballCircle(CANVAS,500,350,50,50,"green",0,0,True,BUMPER_MULTIPLIER,20),
    #                   #PinballCircle(CANVAS,(WIDTH-100)/2-200,150,50,50,"orange",0,0,True,BUMPER_MULTIPLIER,5),
    #                   ##PinballCircle(CANVAS,(WIDTH-100)/2+150,150,50,50,"orange",0,0,True,BUMPER_MULTIPLIER,5),
    #                   #PinballCircle(CANVAS,(WIDTH-100)/2-25,300,50,50,"green",0,0,True,BUMPER_MULTIPLIER,5),
    #                  # Left and right top slanted lines
    #                   PinballLine(CANVAS,0,100,100,-100,"red",True,BUMPER_MULTIPLIER),
    #                   PinballLine(CANVAS,WIDTH-100,0,100,100,"red",True,BUMPER_MULTIPLIER),
    #                   # Middle line
    #                   #PinballLine(CANVAS,(WIDTH-100)/2-100,500,200,0,"green",True,BUMPER_MULTIPLIER),
    #                   #PinballCircle(CANVAS,(WIDTH-100)/2-200,500,100,100,"green",0,0,True,1.5,5),
    #                   #PinballCircle(CANVAS,(WIDTH-100)/2+100,500,100,100,"green",0,0,True,1.5,5),
                      
    #                   # Bumpers
    #                   PinballActuator(CANVAS,
    #                                   0,HEIGHT-150,-50 + (WIDTH-100)/2.0,50,
    #                                   0,HEIGHT-150,-50 + (WIDTH-100)/2.0,25,
    #                                   "red",True, BUMPER_MULTIPLIER, 'h', 10),
    #                   #PinballActuator(CANVAS,
    #                   #                0,HEIGHT-150,-50 + (WIDTH-100)/2.0,50,
    #                   #                0,HEIGHT-125,WIDTH,0,
    #                   #                "red",True, BUMPER_MULTIPLIER, 'u', 10),
    #                   PinballActuator(CANVAS,
    #                                   50 + (WIDTH-100)/2.0,HEIGHT-100,
    #                                   WIDTH-100 - 50 - (WIDTH-100)/2.0,-50,
    #                                   50 + (WIDTH-100)/2.0,HEIGHT-125,
    #                                   WIDTH-100 - 50 - (WIDTH-100)/2.0,-25,
    #                                   "red",True, BUMPER_MULTIPLIER, 'k', 10),
    #                   # Top lines
    #                   PinballLine(CANVAS,120,250,80,-100,"black",True),
    #                   PinballLine(CANVAS,200,150,100,0,"black",True),
    #                   PinballLine(CANVAS,400,150,100,0,"black",True),
    #                   PinballLine(CANVAS,500,150,80,100,"black",True),
    #                   PinballLine(CANVAS,200,275,300,0,"red",True,3.0),
    #                   # Triangle
    #                   PinballLine(CANVAS,300,450,100,0,"blue",True,BUMPER_MULTIPLIER),
    #                   PinballLine(CANVAS,300,450,50,100,"blue",True,BUMPER_MULTIPLIER),
    #                   PinballLine(CANVAS,350,550,50,-100,"blue",True,BUMPER_MULTIPLIER),
    #                   PinballLine(CANVAS,310,455,80,0,"blue",True,BUMPER_MULTIPLIER),
    #                   PinballLine(CANVAS,310,455,40,80,"blue",True,BUMPER_MULTIPLIER),
    #                   PinballLine(CANVAS,350,535,40,-80,"blue",True,BUMPER_MULTIPLIER),
    #                   PinballCircle(CANVAS,325,455,50,50,"blue",0,0,True,BUMPER_MULTIPLIER,10),
    #                   # LHS vertical line
    #                   #PinballLine(CANVAS,98,150,2,0,"black", True),
    #                   #PinballLine(CANVAS,100,150,0,HEIGHT-400,"black", True, 1),
    #                   #PinballLine(CANVAS,98,150,0,HEIGHT-400,"blue", True, BUMPER_MULTIPLIER*2),
    #                   # RHS vertical line
    #                   PinballLine(CANVAS,WIDTH-100,150,2,0,"black", True),
    #                   PinballLine(CANVAS,WIDTH-100,150,0,HEIGHT-150,"black", True),
    #                   PinballLine(CANVAS,WIDTH-98,150,0,HEIGHT-150,"black", True)]
    
    # REGIONS = [       # The region at bottom where balls disappear
    #                   PinballRegion(0,HEIGHT-30,WIDTH,30, True, None, None),
    #                   #PinballRegion(0,150,98,HEIGHT-400, False, 1.1, -2.0),
    #                   PinballRegion(700,150,100,650, False, 1.1, -2.0)
    #                   #PinballRegion((WIDTH-100)/2-220,130,90,90, False, None, -1.0),
    #                   #PinballRegion((WIDTH-100)/2+130,130,90,90, False, None, -1.0)
    #                   ]
    
    def __init__(self):
        self.tk = PinballMachine.TK
        self.canvas = PinballMachine.CANVAS
        self.objs = PinballMachine.LAYOUT
        self.regions = PinballMachine.REGIONS
        self.balls_left = PinballMachine.BALL_LIMIT
        self.keyQueue = queue.Queue() 
        #self.start_keyboard_thread()
        self.tk.bind('<Key>', self.key_pressed)
        self.score = 0
        self.score_text = self.canvas.create_text(45,30,fill="blue",font="Times 20 italic bold",
                        text=str(self.score))
        self.ball_text = self.canvas.create_text(WIDTH-45,30,fill="blue",font="Times 20 italic bold",
                        text=str(self.balls_left))
        self.move_active()
        
        # Give window main focus and start
        self.tk.lift()
        self.tk.attributes('-topmost',True)
        self.tk.after_idle(self.tk.attributes,'-topmost',False)
        self.tk.mainloop()
        
    # Main processing loop
    def move_active(self):
                
        # Handle keypress   
        input_str = None        
        if (self.keyQueue.qsize() > 0):
            input_str = self.keyQueue.get()
            #print("You pressed: ", input_str)
            if (input_str == 'q'):
                sys.exit()
                #os._exit(1)
            elif (input_str == 'z' and self.balls_left > 0):
                self.balls_left -= 1
                mult = np.random.uniform(0.5,1.5)
                self.objs.append(PinballCircle(self.canvas,WIDTH-75,HEIGHT-450,mult*40,mult*40,"black",0,-12.0))
           
        # Hall ball update and actuation
        for obj in self.objs:
            if obj.active:
                self.score += obj.ball_update(self.objs, self.regions)
            if (isinstance(obj,PinballActuator)):
                obj.handleActuation(input_str)
        self.canvas.itemconfig(self.score_text, text=str(self.score))
        self.canvas.itemconfig(self.ball_text, text=str(self.balls_left))
           
        # Queue next call to move_active
        self.tk.after(5, self.move_active) # 40, changed from 10ms to 30ms        

    def key_pressed(self, event):
        c = event.char
        #print("You pressed <<%s>>" % c)
        self.keyQueue.put(c)
        
    # # This works for console input, TKInter has its own key capture
    # def read_kbd_input(self, keyQueue):
    #     print('Ready for keyboard input:')
    #     while (True):
    #         #input_str = input()
    #         c = read_key()
    #         print("You pressed <<%s>>" % c)
    #         if (c == "q"):
    #             # Windows only
    #             os._exit(1)
    #         keyQueue.put(c)
    #
    # def start_keyboard_thread(self):
    #     inputThread = threading.Thread(target=self.read_kbd_input, args=(self.keyQueue,), daemon=True)
    #     inputThread.start()

game = PinballMachine()
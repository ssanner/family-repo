# -*- coding: utf-8 -*-

from tkinter import *
#from math import copysign
import math
import numpy as np
from abc import ABC, abstractmethod
import time

WIDTH = 800
HEIGHT = 500

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

class PinballObject(ABC):
     
    id_counter = 0

    def __init__(self, canvas, initx, inity, sizex, sizey, color, 
                 velx, vely, fixed, bumper):
        self.canvas = canvas
        self.init = np.array([initx,inity]).astype('float64')
        self.size = np.array([sizex,sizey]).astype('float64')
        self.speed = np.array([velx,vely]).astype('float64')

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
                 fixed = True, bumper = False):   
        super().__init__(canvas, initx, inity, sizex, sizey, color, 0, 0, fixed, bumper)
        self.shape = canvas.create_line(initx, inity, initx+sizex, inity+sizey, fill=color)
        self.active = False
        self.min = np.array([min(initx, initx + sizex), min(inity, inity + sizey)])
        self.max = np.array([max(initx, initx + sizex), max(inity, inity + sizey)])

class PinballCircle(PinballObject):
    
    def __init__(self, canvas, initx, inity, sizex, sizey, color, 
                 velx = 0, vely = 0, fixed = False, bumper = False):
        super().__init__(canvas, initx, inity, sizex, sizey, color, velx, vely, fixed, bumper)
        self.shape = canvas.create_oval(initx, inity, initx+sizex, inity+sizey, fill=color)
        # Replace mass with default sizex*sizey if specified
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
                    print("")
                    print("COLLISION")
                    return obj
            
            elif (isinstance(obj, PinballCircle)):
                
                dist = np.linalg.norm(self.get_center() - obj.get_center())                
                gap = dist - (self.size[0] + obj.size[0])/2.0; # symmetrical objects
                
                if (gap <= 0):
                    return obj     
        return None

    def ball_update(self, objs):
        self.canvas.move(self.shape, self.speed[0], self.speed[1])
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
            self.speed *= PinballMachine.FRICTION
            self.speed[1] += PinballMachine.GRAVITY
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
            
            print("Collision speed before: ",(self.speed))
            
            if (not self.fixed):
                bumper_mult = (PinballMachine.BUMPER_MULTIPLIER if cobj.bumper else 1.0) # see if other obj is bumper
                # Mass coefficient 2*m_2/(m_1+m_2) = 2.0 since m_2 is infinite
                self.speed = self.speed - 2.0 * diff_v1.dot(diff_x1) * diff_x1 * bumper_mult
            
        elif (cobj != None and isinstance(cobj,PinballCircle) and self.id > cobj.id):
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
                bumper_mult1 = (PinballMachine.BUMPER_MULTIPLIER if cobj.bumper else 1.0) # see if other obj is bumper
                self.speed = self.speed - (mass_coef1 * diff_v1.dot(diff_x1) * diff_x1 * bumper_mult1)

            if (not cobj.fixed):
                bumper_mult2 = (PinballMachine.BUMPER_MULTIPLIER if self.bumper else 1.0) # see if other obj is bumper
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
    #                   PinballCircle(CANVAS,0,200,25,25,"black", 6, 3),
    #                   PinballCircle(CANVAS,0,350,25,25,"green", 3, 6),
    #                 # PinballCircle(CANVAS,200,0,100,100,"black", 6, 3),
    #                 # PinballCircle(CANVAS,350,0,100,100,"green", 3, 6),
    #                 # PinballCircle(CANVAS,100,200,100,100,"red", 6, 3),
    #                 # PinballCircle(CANVAS,100,350,100,100,"blue", 3, 6),
    #                 # PinballCircle(CANVAS,200,100,100,100,"purple", 6, 3),
    #                 # PinballCircle(CANVAS,350,100,100,100,"yellow", 3, 6),
    #                   PinballCircle(CANVAS,50,50,20,20,"purple", 3, 3),
    #                   PinballCircle(CANVAS,150,150,20,20,"yellow", 9, 9),
    #                   PinballLine(CANVAS,200,400,500,50,"black"),
    #                   PinballLine(CANVAS,100,200,500,-50,"black")]
    
    # Pinball!
    FRICTION = 0.99 # .99 # 0.95
    GRAVITY = 0.1 # 0.1 # 0.1
    BUMPER_MULTIPLIER = 2.0 # 2.0
    MAX_SPEED = 10.0
    LAYOUT = [       # beyond color: velx, vely, fixed?, bumper?
                      PinballCircle(CANVAS,WIDTH-75,HEIGHT-200,50,50,"blue",0,-9.0),
                      PinballCircle(CANVAS,(WIDTH-100)/2-50,-25,100,100,"red",0,0,True,True),
                      PinballCircle(CANVAS,(WIDTH-100)/2-200,150,50,50,"orange",0,0,True,True),
                      PinballCircle(CANVAS,(WIDTH-100)/2+150,150,50,50,"orange",0,0,True,True),
                      PinballCircle(CANVAS,(WIDTH-100)/2-25,300,50,50,"green",0,0,True,True),
                      PinballLine(CANVAS,WIDTH-100,150,0,HEIGHT-150,"black", True, False),
                      PinballLine(CANVAS,0,100,100,-100,"red",True,True),
                      PinballLine(CANVAS,WIDTH-100,0,100,100,"red",True,True),
                      PinballLine(CANVAS,0,HEIGHT-150,-50 + (WIDTH-100)/2.0,50,"red",True,True),
                      PinballLine(CANVAS,50 + (WIDTH-100)/2.0,HEIGHT-100,
                                  WIDTH-100 - 50 - (WIDTH-100)/2.0,-50,"red",True,True)]
    
    def __init__(self):
        self.tk = PinballMachine.TK
        self.canvas = PinballMachine.CANVAS
        self.objs = PinballMachine.LAYOUT
        self.move_active()
        self.tk.mainloop()
        
    def move_active(self):
        for obj in self.objs:
            if obj.active:
                obj.ball_update(self.objs)
        self.tk.after(10, self.move_active) # 40, changed from 10ms to 30ms        


game = PinballMachine()
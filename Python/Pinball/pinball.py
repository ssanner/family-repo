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
        self.initx = initx
        self.inity = inity
        self.sizex = sizex
        self.sizey = sizey
        self.speedx = velx 
        self.speedy = vely 

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
        self.minx = min(initx, initx + sizex)
        self.maxx = max(initx, initx + sizex)
        self.miny = min(inity, inity + sizey)
        self.maxy = max(inity, inity + sizey)

class PinballCircle(PinballObject):
    
    def __init__(self, canvas, initx, inity, sizex, sizey, color, 
                 velx = 0, vely = 0, fixed = False, bumper = False):
        super().__init__(canvas, initx, inity, sizex, sizey, color, velx, vely, fixed, bumper)
        self.shape = canvas.create_oval(initx, inity, initx+sizex, inity+sizey, fill=color)
        # Replace mass with default sizex*sizey if specified
        self.active = True
        self.radius = self.sizex / 2.0
        self.contact_x_wall = False
        self.contact_y_wall = False
        assert self.sizex == self.sizey, "circles are not symmetric in x,y dims"

    def get_center(self):
        pos = self.canvas.coords(self.shape)
        return [(pos[0] + pos[2])/2.0, (pos[1] + pos[3])/2.0]

    # https://www.mathsisfun.com/physics/momentum-animation.html
    def is_collision(self, objs):
        for obj in objs:
            if (self == obj):
                continue
 
            if (isinstance(obj,PinballLine)):
                # Do math to project to obtain (xc,yc), for now, just draw collision point
                # Line has slope (sizey/sizex)
                # Let points P & Q be on the line
                # ... N . (P-Q) = (-sizey, sizex) . (sizex, sizey)
                # normal_vector N = (-sizey, sizex) (can see that gradients )
                # 
                # Let P be a point and x = (initx, inity) be on the line
                # ... P - (P-x . N) elementwise* N
                #         ---------
                #             C
                #
                # But need to normalize N into (nx,ny)
                Z = math.sqrt(obj.sizey*obj.sizey + obj.sizex*obj.sizex)
                nx = 1.0/Z * -obj.sizey
                ny = 1.0/Z * obj.sizex
                pos = self.get_center()
                # Note: projection is linear if plane is fixed
                Pmx_x = pos[0] - obj.initx
                Pmx_y = pos[1] - obj.inity
                C = Pmx_x * nx + Pmx_y * ny
                projx = pos[0] - C*nx
                projy = pos[1] - C*ny
                #print("NORM: (",ny,",",nx,"), C=",C)
                
                xdiff = abs(pos[0] - projx);
                ydiff = abs(pos[1] - projy);
                dist = math.sqrt(xdiff*xdiff + ydiff*ydiff);
                #print("DISTANCE: ", dist)

                # Also check within endpoints!  Requires that lines were defined
                # with positive slopes, otherwise bounds reverse!
                #print((projx,projy)," in ",(obj.minx,obj.maxx,obj.miny,obj.maxy))
                if (dist < self.radius and projx >= obj.minx and projx <= obj.maxx
                    and projy >= obj.miny and projy <= obj.maxy):
                    #self.canvas.create_oval(projx-1, projy-1, projx+1, projy+1, fill="red")
                    print("")
                    print("COLLISION")
                    return obj
            
            elif (isinstance(obj, PinballCircle)):
                pos1 = self.get_center()
                pos2 = obj.get_center()
                
                xdiff = abs(pos1[0] - pos2[0]);
                ydiff = abs(pos1[1] - pos2[1]);
                dist = math.sqrt(xdiff*xdiff + ydiff*ydiff);
                            
                radius1 = self.sizex / 2.0;
                radius2 = obj.sizex / 2.0;
                
                gap = dist - (radius1 + radius2);
                
                if (gap <= 0):
                    return obj     
    #            widthx = (self.sizex + obj.sizex)/2.0
    #            widthy = (self.sizey + obj.sizey)/2.0 
    #            if (abs(pos1[0] - pos2[0]) < widthx and abs(pos1[1] - pos2[1]) < widthy):
    #                return True
        return None

    def ball_update(self, objs):
        self.canvas.move(self.shape, self.speedx, self.speedy)
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
            self.speedx *= PinballMachine.FRICTION
            self.speedy *= PinballMachine.FRICTION
            self.speedy += PinballMachine.GRAVITY
            self.speedx = min(self.speedx, PinballMachine.MAX_SPEED)
            self.speedy = min(self.speedy, PinballMachine.MAX_SPEED)
            self.speedx = max(self.speedx, -PinballMachine.MAX_SPEED)
            self.speedy = max(self.speedy, -PinballMachine.MAX_SPEED)
        
        # Eventually should handle multiple collisions, but requires refactoring
        # such that we return a set of all collisions and the velocity changes of impacts
        # are additive
        cobj = self.is_collision(objs)
        if (cobj != None and isinstance(cobj,PinballLine)):
            # Use Wiki article but final x difference should be a unit vector
            # https://en.wikipedia.org/wiki/Elastic_collision#Two-dimensional_collision_with_two_moving_objects
            # Compute velocity update to self = 1, cobj = 2
            
            # First, find point of collision
            Z = math.sqrt(cobj.sizey*cobj.sizey + cobj.sizex*cobj.sizex)
            nx = 1.0/Z * -cobj.sizey
            ny = 1.0/Z * cobj.sizex
            pos = self.get_center()
            # Note: projection is linear if plane is fixed
            Pmx_x = pos[0] - cobj.initx
            Pmx_y = pos[1] - cobj.inity
            C = Pmx_x * nx + Pmx_y * ny
            projx = pos[0] - C*nx
            projy = pos[1] - C*ny
            print("NORM: (",ny,",",nx,"), C=",C)
            
            # Now compute impact of two circles at the collision point where
            # one circle (the wall) has infinite mass
            mass_coef1 = 2 #cobj is infinite: (2*cobj.mass)/(self.mass + cobj.mass)
            #mass_coef2 = 0 #cobj is infinite: (2*self.mass)/(self.mass + cobj.mass)
            # cobj not moving: delta_vx = self.speedx - cobj.speedx
            # cobj not moving: delta_vy = self.speedy - cobj.speedy

            pos_self = self.get_center()
            #pos_cobj = cobj.get_center()

            delta_x  = pos_self[0] - projx
            delta_y  = pos_self[1] - projy
            norm_xdiff = math.sqrt(delta_x*delta_x + delta_y*delta_y)
            delta_x_unit = delta_x / norm_xdiff
            delta_y_unit = delta_y / norm_xdiff
            second_coef = ((self.speedx * delta_x_unit) + (self.speedy * delta_y_unit)) 
            
            # print("Norm ({},{})".format(delta_x_unit,delta_y_unit))
            # print(pos_self)
            # print((self.speedx, self.speedy))
            # print(pos_cobj)
            # print((cobj.speedx, cobj.speedy))
            # print((delta_x,delta_y))
            # print((delta_vx,delta_vy))
            # print((self.speedx,mass_coef1,second_coef,delta_x))
            # print((self.speedy,mass_coef1,second_coef,delta_y))
            
            print("Collision speed before: ",(self.speedx,self.speedy))
            
            if (not self.fixed):
                bumper_mult1 = (PinballMachine.BUMPER_MULTIPLIER if cobj.bumper else 1.0) # see if other obj is bumper
                print("Bumper multiplier: ",bumper_mult1)
                self.speedx = self.speedx - (mass_coef1 * second_coef * delta_x_unit * bumper_mult1)
                self.speedy = self.speedy - (mass_coef1 * second_coef * delta_y_unit * bumper_mult1)

            #cobj.speedx = cobj.speedx + (mass_coef2 * second_coef * delta_x_unit)
            #cobj.speedy = cobj.speedy + (mass_coef2 * second_coef * delta_y_unit)
            
            print("Collision speed update: ",(self.speedx,self.speedy))
            # print((cobj.speedx,cobj.speedy))
            # print()
            #exit()
        elif (cobj != None and isinstance(cobj,PinballCircle) and self.id > cobj.id):
            # Use Wiki article but final x difference should be a unit vector
            # https://en.wikipedia.org/wiki/Elastic_collision#Two-dimensional_collision_with_two_moving_objects
            # Compute velocity update to self = 1, cobj = 2
            mass_coef1 = (2*cobj.mass)/(self.mass + cobj.mass)
            mass_coef2 = (2*self.mass)/(self.mass + cobj.mass)
            delta_vx = self.speedx - cobj.speedx
            delta_vy = self.speedy - cobj.speedy

            pos_self = self.get_center()
            pos_cobj = cobj.get_center()

            delta_x  = pos_self[0] - pos_cobj[0]
            delta_y  = pos_self[1] - pos_cobj[1]
            norm_xdiff = math.sqrt(delta_x*delta_x + delta_y*delta_y)
            delta_x_unit = delta_x / norm_xdiff
            delta_y_unit = delta_y / norm_xdiff
            second_coef = ((delta_vx * delta_x_unit) + (delta_vy * delta_y_unit)) 
            
            # print("Norm ({},{})".format(delta_x_unit,delta_y_unit))
            # print(pos_self)
            # print((self.speedx, self.speedy))
            # print(pos_cobj)
            # print((cobj.speedx, cobj.speedy))
            # print((delta_x,delta_y))
            # print((delta_vx,delta_vy))
            # print((self.speedx,mass_coef1,second_coef,delta_x))
            # print((self.speedy,mass_coef1,second_coef,delta_y))
                        
            if (not self.fixed):
                bumper_mult1 = (PinballMachine.BUMPER_MULTIPLIER if cobj.bumper else 1.0) # see if other obj is bumper
                self.speedx = self.speedx - (mass_coef1 * second_coef * delta_x_unit * bumper_mult1)
                self.speedy = self.speedy - (mass_coef1 * second_coef * delta_y_unit * bumper_mult1)

            if (not cobj.fixed):
                bumper_mult2 = (PinballMachine.BUMPER_MULTIPLIER if self.bumper else 1.0) # see if other obj is bumper
                cobj.speedx = cobj.speedx + (mass_coef2 * second_coef * delta_x_unit * bumper_mult2)
                cobj.speedy = cobj.speedy + (mass_coef2 * second_coef * delta_y_unit * bumper_mult2)
            
            # print((self.speedx,self.speedy))
            # print((cobj.speedx,cobj.speedy))
            # print()
            #exit()
        else:
            # Note: wall variable prevents constantly reversing course
            if (pos[2] >= WIDTH or pos[0] <= 0) and not self.contact_x_wall:
                self.speedx *= -1
                self.contact_x_wall = True
            else:
                self.contact_x_wall = False
                
            if (pos[3] >= HEIGHT or pos[1] <= 0) and not self.contact_y_wall:
                self.speedy *= -1
                self.contact_y_wall = True
            else:
                self.contact_y_wall = False
    

class PinballMachine:
    
    TK = Tk()
    CANVAS = Canvas(TK, width=WIDTH, height=HEIGHT, bg="gray")
    CANVAS.pack()

    # Frictionless balls in space
    FRICTION = 1.00 # .99 # 0.95
    GRAVITY = 0.0 # 0.1
    BUMPER_MULTIPLIER = 1.0
    MAX_SPEED = 50
    LAYOUT = [
                      PinballCircle(CANVAS,0,0,50,50,"red", 3, 3), 
                      PinballCircle(CANVAS,100,100,50,50,"blue", 3, 3),
                      PinballCircle(CANVAS,200,200,100,100,"black", 6, 3),
                      PinballCircle(CANVAS,350,350,100,100,"green", 3, 6),
                    # PinballCircle(CANVAS,0,200,100,100,"black", 6, 3),
                    # PinballCircle(CANVAS,0,350,100,100,"green", 3, 6),
                    # PinballCircle(CANVAS,200,0,100,100,"black", 6, 3),
                    # PinballCircle(CANVAS,350,0,100,100,"green", 3, 6),
                    # PinballCircle(CANVAS,100,200,100,100,"red", 6, 3),
                    # PinballCircle(CANVAS,100,350,100,100,"blue", 3, 6),
                    # PinballCircle(CANVAS,200,100,100,100,"purple", 6, 3),
                    # PinballCircle(CANVAS,350,100,100,100,"yellow", 3, 6),
                      PinballCircle(CANVAS,50,50,20,20,"purple", 3, 3),
                      PinballCircle(CANVAS,150,150,20,20,"yellow", 9, 9)]
 
    # # Balls dropping
    # FRICTION = 0.995 # .99 # 0.95
    # GRAVITY = 0.1 # 0.1
    # BUMPER_MULTIPLIER = 1.0
    # MAX_SPEED = 50
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
    # MAX_SPEED = 50
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
    
    # # Pinball!
    # FRICTION = 0.99 # .99 # 0.95
    # GRAVITY = 0.1 # 0.1
    # BUMPER_MULTIPLIER = 2.0 # 2.0
    # MAX_SPEED = 10
    # LAYOUT = [       # beyond color: velx, vely, fixed?, bumper?
    #                   PinballCircle(CANVAS,WIDTH-75,HEIGHT-200,50,50,"blue",0,-9.25),
    #                   PinballCircle(CANVAS,(WIDTH-100)/2-50,-25,100,100,"red",0,0,True,True),
    #                   PinballCircle(CANVAS,(WIDTH-100)/2-200,150,50,50,"orange",0,0,True,True),
    #                   PinballCircle(CANVAS,(WIDTH-100)/2+150,150,50,50,"orange",0,0,True,True),
    #                   PinballCircle(CANVAS,(WIDTH-100)/2-25,300,50,50,"green",0,0,True,True),
    #                   PinballLine(CANVAS,WIDTH-100,150,0,HEIGHT-150,"black", True, False),
    #                   PinballLine(CANVAS,0,100,100,-100,"red",True,True),
    #                   PinballLine(CANVAS,WIDTH-100,0,100,100,"red",True,True),
    #                   PinballLine(CANVAS,0,HEIGHT-150,-50 + (WIDTH-100)/2.0,50,"red",True,True),
    #                   PinballLine(CANVAS,50 + (WIDTH-100)/2.0,HEIGHT-100,
    #                               WIDTH-100 - 50 - (WIDTH-100)/2.0,-50,"red",True,True)]
    
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
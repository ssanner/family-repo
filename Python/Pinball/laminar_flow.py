# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 15:25:38 2020

@author: ssann
"""

from tkinter import *

size = 15
gap = 5
columns = 25
rows = 7

downspace = 40  # space for the buttons below the animation
screenwidth = columns*size + (columns-2)*gap
screenheight = rows*size + rows*gap + downspace

color = "sky blue"
xspeed = [2, 3, 4, 5, 4, 3, 2]  # list for the speeds of the particle rows


class Animation:
    """Class for the animation and buttons"""

    def __init__(self):
        """
        Creates the canvas, lines, buttons and runs the mainloop of the tkinter window
        self.particlelist is a list for the rows of particles
        """

        self.root = Tk()
        self.canvas = Canvas(self.root, width=screenwidth, height=screenheight)
        self.canvas.pack()

        self.root.title("Laminar flow in a pipe")
        self.canvas.create_line(0, gap, screenwidth, gap, width=2)
        self.canvas.create_line(0, rows*size + (rows+2)*gap, screenwidth, rows*size + (rows+2)*gap, width=2)

        self.particlelist = []

        self.stop_animation = False
        self.start = Button(self.root, text="Start animation", command=self.start_anim)
        self.start.pack()
        self.stop = Button(self.root, text="Stop animation", command=self.stop_anim)
        self.stop.pack()

        self.init()
        self.root.mainloop()


    def start_anim(self):
        """Starts the animation"""

        self.stop_animation = False
        self.start.configure(state=DISABLED)
        self.stop.configure(state=NORMAL)
        self.update()


    def stop_anim(self):
        """
        Stops the animation and deletes the particles
        Runs the function init to draw new particles to the beginning positions
        """

        self.stop_animation = True
        self.start.configure(state=NORMAL)
        self.stop.configure(state=DISABLED)
        self.update()

        for i in range(len(self.particlelist)):
            xlist = self.particlelist[i]
            for particle in xlist:
                particle.delete()
            self.particlelist[i] = []

        self.init()


    def init(self):
        """
        Creates lists of particle rows and appends them to self.particlelist

            * ypos: vertical postition of the particle
            * xpos: horizontal position of the particle
        """

        ypos = 10
        for i in range(rows):
            xpos = 0
            xlist = []

            for t in range(columns):
                xlist.append(Particle(self.canvas, xpos, ypos, color, xspeed[i]))
                xpos += size + gap

            self.particlelist.append(xlist)
            ypos += size + gap


    def update(self):
        """
        Updates the screen
            * t: update interval in milliseconds
        """

        t = 20

        if self.stop_animation == False:
            for i in range(len(self.particlelist)):
                xlist = self.particlelist[i]
                for particle in xlist:
                    particle.move()

            self.canvas.after(t, self.update)



class Particle():
    """
    Class for particles

    Parameters:
        * canvas: canvas from the class "Animation"
        * xpos: x coordinate for creation of the shape
        * ypos: y coordinate for creation of the shape
        * color: fill color of the shape
        * xspeed: speed of the shape to the horizontal direction
    """


    def __init__(self, canvas, xpos, ypos, color, xspeed):
        self.canvas = canvas
        self.shape = self.canvas.create_oval(xpos, ypos, xpos+size, ypos+size, fill=color)
        self.xspeed = xspeed


    def move(self):
        """
        Function for moving the shape.

            * "pos" gives a vector of position [x0, y0, x1, y1] where 0 is the left upper corner
              and 1 is the right down corner of the shape
        """

        self.canvas.move(self.shape, self.xspeed, 0)
        pos = self.canvas.coords(self.shape)

        if pos[0] >= screenwidth:     # returning the shape to the left side of the screen
            overlap = (pos[0] - screenwidth)
            self.canvas.coords(self.shape, gap-size+overlap, pos[1], gap+overlap, pos[3])


    def delete(self):
        """Function for deleting the shape"""

        self.canvas.delete(self.shape)

Animation()
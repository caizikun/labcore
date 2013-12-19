# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 16:47:33 2013

@author: zah
"""

import heapq
import numpy as np

from pqdict import PQDict
atan2 = np.arctan2
pi = np.pi
class AdaptiveSampler(object):
    def __init__(self, f, a ,b, sample_over = None, 
                 min_angle =  0.07, init_points = 7, 
                 epsilon = 0, max_points = 300):
        
        self.f = f
        self.a = a
        self.b = b
        self.sample_over = sample_over
        self.init_points = init_points
        self.min_angle = min_angle
        self.epsilon = epsilon
        self.max_points = max_points
        
        
    
    def get_y(self,yret):
         if self.sample_over is not None:
            return yret[self.sample_over]
         else:
            return yret
    
    def get_prior(self, x, y ,xp, yp, xn, yn):
        a1 = atan2(y-yp,x-xp + self.epsilon)
        a2 = atan2(yn-y,xn-x + self.epsilon)
        prior = -(min(np.abs(a1-a2), 2*pi-np.abs((a1-a2))))
        return prior
        
    def eval_point(self, x, xp, yp, xn, yn ,yret = None):
        del self.data[x]
        if yret is None:    
            yret = self.f(x)
        y = self.get_y(yret)
            
       
        prior = self.get_prior(x, y ,xp, yp, xn, yn)
        
        if -prior > self.min_angle: 
            #d1 = ((x-xp)/2. , xp, yp, x, y, depth+1)
            #d2 = ((xn-x)/2., x, y, xn, yn, depth +1)
            lx = (x+xp)/2.
            rx = (xn+x)/2.
            self.heapdict.additem(lx, prior)
            self.heapdict.additem(rx, prior)
            self.data[lx] = [xp, yp, x, y]
            self.data[rx] =  [x, y, xn, yn]
            try:
                xpd = self.data[xp]
            except KeyError:
                pass
            else:
                xpd[2] = x
                xpd[3] = y
                xpp = self.get_prior(xp,yp,*xpd)
                self.heapdict.updateitem(xp, xpp)
            try:
                xnd = self.data[xn]
            except KeyError:
                pass
            else:
                xnd[0] = x
                xnd[1] = y
                xnp = self.get_prior(xn,yn,*xnd)
                self.heapdict.updateitem(xn, xnp)
            #heapq.heappush(self.heap, (prior, d1))
            #heapq.heappush(self.heap, (prior, d2))
            
        return x,yret
    
    def run(self):
        self.heapdict = PQDict()
        self.data = {}
        initx = np.linspace(self.a, self.b, self.init_points)
        initdelta = (initx[1] - initx[0])/2.
        inity = []
        for x in initx:
            yret = self.f(x)
            yield (x, yret)
            inity.append(yret)
        for (i,xp) in enumerate(initx[0:-1]):
            d = [initx[i], self.get_y(inity[i]),
                 initx[i+1], self.get_y(inity[i+1]),
                ]
            newx = xp + initdelta
            
            prior = self.get_prior(newx, self.get_y(inity[i]), *d)
            if -prior > self.min_angle:
                self.data[newx] = d
                self.heapdict.additem(newx, prior)
                            
       
        n_points = self.init_points
        print self.heapdict
        while n_points < self.max_points:
            try:
                x , _ = self.heapdict.popitem()
                print self.heapdict
            except KeyError:
                return
            else:
                d = self.data[x]
                yield self.eval_point(x, *d)
                n_points += 1
                
    def __call__(self):
        return self.run()
        
        
def test():
    global s, it, x, y
    from scipy import stats
    import matplotlib.pyplot as plt
    from matplotlib import animation
    
    yscale = 1

    f = lambda x : yscale * stats.cauchy.pdf(x,0.73,.3)
    fig = plt.figure()
    ax = plt.axes(xlim=(-6, 6), ylim=(-0, yscale * 1.1))
    x = []
    y = []
    line, = ax.plot(x, y, 'o',lw=2)
    
    
    def init():
        global s, it, x, y
        s = AdaptiveSampler(f, -4, 5.1, max_points = 90, epsilon = 0, min_angle = 0)
        it = s.run()
        x = []
        y = []
        line.set_data([], [])
        return line,
    
    def animate(i):
        point = next(it)
        x.append(point[0])
        y.append(point[1])
        line.set_data(x,y)
        return line,
    anim = animation.FuncAnimation(fig, animate, init_func = init,
                                   frames=80, interval=0, blit=True, 
                                   )
    plt.show()
    plt.plot(x,y, marker = 'o', drawstyle = 'steps')
    plt.show()

#test()
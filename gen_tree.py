from matplotlib import pyplot
from shapely.geometry import Polygon 
from descartes import PolygonPatch
from numpy import linspace,sqrt,log,exp,arange
from scipy import pi,sin,cos
from collections import namedtuple
from itertools import izip


BLUE = '#6699cc'
GRAY = '#999999'
LIGHT_DEC_FACTOR = -1
INIT_LIGHT_STRENGTH = 1
class Tree(object):
    def __init__(self):
        self.leaves = []
    def addLeaf(self,leaf):
        self.leaves.append(leaf)
    def show(self):
        pyplot.xlim([-10,10])
        pyplot.ylim([-10,10])
        fig = pyplot.figure(1)
        ax = fig.add_subplot(111)
        for leaf in self.leaves:
            patch = PolygonPatch(leaf.surface, fc=BLUE, ec=BLUE, alpha=0.5, zorder=2)
            ax.add_patch(patch)

        pyplot.show()

    def getAboveLeaves(self,leaf):
        leaf_index = self.leaves.index(leaf)
        for i in xrange(0,leaf_index):
            yield self.leaves[i]
    
    def getAbsorbedEnergy(self):
        energy_arr = [l.getAbsorbedEnergy() for l in self.leaves]
        #print energy_arr
        return sum(energy_arr)
def ellipse(ra,rb,ang,x0,y0,Nb=50):
    '''ra - major axis length
    rb - minor axis length
    ang - angle
    x0,y0 - position of centre of ellipse
    Nb - No. of points that make an ellipse
    '''
    xpos,ypos=x0,y0
    radm,radn=ra,rb
    an=ang

    co,si=cos(an),sin(an)
    the=linspace(0,2*pi,Nb)
    X=radm*cos(the)*co-si*radn*sin(the)+xpos
    Y=radm*cos(the)*si+co*radn*sin(the)+ypos
    return zip(X,Y)

def get_decreased_light_strength(light_strength):
    return light_strength * exp(LIGHT_DEC_FACTOR) 

class Leaf(object):
    def __init__(self,**kwargs):
        """ """
        self.angle = kwargs['angle']
        self.ra= kwargs['a_mag']
        self.rb= kwargs['b_mag']
        self.x0 = kwargs['x0']
        self.y0 = kwargs['y0']
        self.Nb= kwargs['Nb']
        self.surface = Polygon(ellipse(self.ra,self.rb,self.angle,self.x0,self.y0,Nb = 100))

        self.sunlit_areas = []


    def addSunlitArea(self,surface):
        self.sunlit_areas.append(surface)

    def getSunlitAreas(self):
        return self.sunlit_areas

    def getSunlitAreasAbove(self,area):
        return [a for a in self.sunlit_areas if area.light_strength < a.light_strength]

    def intersects(self,another_surface):
        return self.surface.intersects(another_surface)

    def getAbsorbedEnergy(self):
        energy = 0
        for a in self.sunlit_areas:
            energy += a.polygon.area * a.light_strength * (1 - exp(LIGHT_DEC_FACTOR))
        return energy

class TreeGenerator(object):
    def __init__(self,ba_ratio = 0.6):
        self.tree = Tree()
        self.leaf_level_index = 2
        self.leaf_area = 1
        self.ba_ratio = ba_ratio
        #self.leaf_ra = leaf_a_mag_fact
        #self.leaf_rb = leaf_b_mag_fact
        self.cur_angle = 0

        self.leaf_area_inc_rate = 1.1
        self.petiole_len_inc_rate= 1.05
        self.petiole_len = 1
    def gen_leaf(self):
        _param = {}
        _param['angle'] = self.cur_angle
        leaf_area_factor = self.get_leaf_area_multiplier()
        #_param['a_mag'] = self.leaf_ra * leaf_area_factor 
        #_param['b_mag'] = self.leaf_rb * leaf_area_factor 
        leaf_area = self.get_leaf_area()
        _param['a_mag'] = sqrt(leaf_area / pi / self.ba_ratio)
        _param['b_mag'] = leaf_area / _param['a_mag'] / pi
        self.leaf_ra = _param['a_mag']
        self.leaf_rb = _param['b_mag']
        _param['x0'] , _param['y0'] = self.get_grow_point_cord(self.leaf_ra)
        _param['Nb'] = 50
        return Leaf(**_param)
    
    def gen_tree(self,leaf_cnt):
        SunlitArea = namedtuple('SunlitArea','polygon light_strength')
        for i in xrange(leaf_cnt):
            leaf = self.gen_leaf()
            self.tree.addLeaf(leaf)

            for lf in self.tree.getAboveLeaves(leaf):
                for area in lf.getSunlitAreas():
                    if leaf.intersects(area.polygon):#if the below leaf is not blocked by this area
                        #print area
                        #print area.polygon
                        #print leaf.surface.intersection(area.polygon)
                        sunlit_area = leaf.surface.intersection(area.polygon)
                        leaf.addSunlitArea(SunlitArea(\
                                          polygon= sunlit_area,\
                                          light_strength = get_decreased_light_strength(area.light_strength)))
            unblkd_area = leaf.surface
            for area in leaf.getSunlitAreas():#subtract the blocked part
                unblkd_area = unblkd_area.difference(area.polygon)
            #add the area that is not blocked by any leaf
            leaf.addSunlitArea(SunlitArea(\
                                          polygon= unblkd_area,\
                                          light_strength = INIT_LIGHT_STRENGTH))
            #print 'total area',leaf.surface.area,[(area.polygon.area,area.light_strength) for area in leaf.getSunlitAreas()]
            total = 0
            for area in leaf.getSunlitAreas():
                for above_area in leaf.getSunlitAreasAbove(area):
                    #print 'area',area.polygon.area,area.light_strength
                    #print 'above areas:',[(a.polygon.area,a.light_strength) for a in leaf.getSunlitAreasAbove(area)]
                    if above_area.polygon.intersects(area.polygon):
                        index = leaf.sunlit_areas.index(above_area)
                        leaf.sunlit_areas.pop(index)
                        #print 'above old',above_area.polygon.area,above_area.light_strength
                        leaf.sunlit_areas.insert(index, SunlitArea(\
                                          polygon= above_area.polygon.difference(area.polygon),\
                                          light_strength = above_area.light_strength))
                        #print 'above new',leaf.sunlit_areas[index].polygon.area,above_area.light_strength

                        #print 
            for area in leaf.getSunlitAreas():
                    total += area.polygon.area
                    #print 'sunlit area',area.polygon.area,
            #print total
            #print '*'*100
            angle = self.next_angle()
        return self.tree

    def next_angle(self):   
        self.cur_angle += 137.5/360 * 2 * pi
        return self.cur_angle

    def get_petiole_len(self):
        petiole_len = self.petiole_len
        self.petiole_len *= self.petiole_len_inc_rate
        return log(petiole_len)

    def get_leaf_area_multiplier(self):
        area_factor = sqrt(self.leaf_level_index)
        self.leaf_level_index *= self.leaf_area_inc_rate
        return area_factor
    
    def get_leaf_area(self):
        area = self.leaf_area
        self.leaf_area *= self.leaf_area_inc_rate
        return area

    def get_grow_point_cord(self,ra):
        p_len = self.get_petiole_len()
        midrib_len = p_len + ra
        return  midrib_len * cos(self.cur_angle) , midrib_len * sin(self.cur_angle)

if __name__ == "__main__":
    #tg = TreeGenerator(ba_ratio = 0.5)
    #tree = tg.gen_tree(10)
    #tree.show()
    result = []
    for ba_ratio in arange(0.01,2,0.01):
        tg = TreeGenerator(ba_ratio = ba_ratio)
        try:
            tree = tg.gen_tree(10)
        except:
            print ba_ratio
        result.append((ba_ratio,tree.getAbsorbedEnergy()))

    x,y = izip(*result)
    pyplot.plot(x,y)
    pyplot.ylabel('SAI of the tree')
    pyplot.xlabel('The value of b/a ')
    pyplot.show()


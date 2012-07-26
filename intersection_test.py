from matplotlib import pyplot
from shapely.geometry import Polygon
from descartes import PolygonPatch
p1 = Polygon([(0,0),(0,1),(1,0)])
p2 = Polygon([(0.3,0.3),(0.3,1.3),(1.3,0.3)])
print p1.intersection(p2).area



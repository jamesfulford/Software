from collections import namedtuple

import duckietown_utils as dtu
from duckietown_utils.exception_utils import check_isinstance
from duckietown_utils.matplotlib_utils import CreateImageFromPylab
import numpy as np


SegMapPoint = namedtuple('SegMapPoint', 'id_frame coords') 
SegMapSegment = namedtuple('SegMapSegment', 'points color')
SegMapFace = namedtuple('SegMapFace', 'points color')

FRAME_AXLE = 'axle'
FRAME_TILE = 'tile'

class SegmentsMap(object):
    
    @dtu.contract(points=dict, segments=list, faces=list)
    def __init__(self, points, segments, faces):
        self.points = points
        self.segments = segments
        self.faces = faces
        self.validate()
        
    def validate(self):
        for k, p in self.points.items():
            check_isinstance(p, SegMapPoint)
            
        for S in self.segments:
            check_isinstance(S, SegMapSegment)
            for p in S.points:
                if not p in self.points:
                    msg = 'Invalid point %r' % p
                    raise ValueError(msg)
                
        for F in self.faces:
            check_isinstance(F, SegMapFace)
            for p in F.points:
                if not p in self.points:
                    msg = 'Invalid point %r' % p
                    raise ValueError(msg)

    @staticmethod
    def from_yaml(data):

        points = data['points']
        faces = data['faces']
        segments = data['segments']
        
#         if faces is None: faces = []
        
        points2 = {}
        for k, p in points.items():
            points2[k] = SegMapPoint(id_frame=p[0], coords=np.array(p[1]))
        
        segments2 = []
        for S in segments:
            if not isinstance(S, SegMapSegment):
                S = SegMapSegment(points=S['points'], color=S['color'])
            segments2.append(S)
        
        faces2 = []
        for f in faces:
            F = SegMapFace(points=f['points'], color=f['color'])
            faces2.append(F)

        return SegmentsMap(points=points2, faces=faces2, segments=segments2)


@dtu.contract(sm=SegmentsMap)
def plot_map_and_segments(sm, tinfo, segments, dpi=120):
    """ Returns a BGR image """  
    a = CreateImageFromPylab(dpi=dpi)

    with a as pylab:
        _plot_map_segments(sm, pylab)
        _plot_detected_segments(tinfo, segments, pylab)
        
        # draw arrow
        L = 0.1
        w1 = tinfo.transform_point(np.array([0,0,0]), frame1=FRAME_AXLE, frame2=FRAME_TILE)
        w2 = tinfo.transform_point(np.array([L,0,0]), frame1=FRAME_AXLE, frame2=FRAME_TILE)
        
        pylab.plot([w1[0], w2[0]], [w1[1], w2[1]], 'm-')
        pylab.plot(w1[0], w1[1], 'mo', markersize=6)
        
        pylab.axis('equal')
        
    return a.get_bgr()

def _plot_detected_segments(tinfo, segments, pylab):
    
    for segment in segments:
        p1 = segment.points[0]
        p2 = segment.points[1]
        
        f = lambda _: np.array([_.x, _.y, _.z])
        
        w1 = tinfo.transform_point(f(p1), frame1=FRAME_AXLE, frame2=FRAME_TILE)
        w2 = tinfo.transform_point(f(p2), frame1=FRAME_AXLE, frame2=FRAME_TILE)
        
#         dtu.logger.debug('Plotting w1 %s w2 %s' % (w1, w2))
        pylab.plot([w1[0], w2[0]], [w1[1], w2[1]], 'm-')

        
@dtu.contract(sm=SegmentsMap)
def _plot_map_segments(sm, pylab):

    for face in sm.faces:
        xs = []
        ys = []
        for p in face.points:
            if sm.points[p].id_frame != FRAME_TILE:
                msg = "Cannot deal with points not in frame FRAME_AXLE"
                raise NotImplementedError(msg)
            
            coords = sm.points[p].coords
            xs.append(coords[0])
            ys.append(coords[1])
            
        xs.append(xs[0])
        ys.append(ys[0])
        pylab.fill(xs, ys, facecolor=face.color, edgecolor='black')

    for segment in sm.segments:
        p1 = segment.points[0]
        p2 = segment.points[1]

        # If we are both in FRAME_AXLE
        if ( not (sm.points[p1].id_frame == FRAME_TILE) and 
             (sm.points[p2].id_frame == FRAME_TILE)):
            msg = "Cannot deal with points not in frame FRAME_TILE"
            raise NotImplementedError(msg)
    
        w1 = sm.points[p1].coords
        w2 = sm.points[p2].coords
        
        color = 'k-'
        pylab.plot([w1[0], w2[0]], [w1[1], w2[1]], color)
    
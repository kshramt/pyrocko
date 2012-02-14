import sys
from newmodel_base import Object, String, Int, Float, Bool, List, Tuple, Timestamp, load, dump, load_all, dump_all

class Response(Object):
    pass

class Gain(Response):
    gain = Float.T()

class PolesAndZeros(Response):
    constant = Float.T(default=1.0)
    poles = List.T(Float.T())
    zeros = List.T(Float.T())

class Channel(Object):
    channel = String.T(default='')
    azimuth = Float.T(optional=True)
    dip = Float.T(optional=True)
    response = Response.T(optional=True)

class Station(Object):
    network = String.T(default='')
    station = String.T(default='')
    location = String.T(default='')
    lat = Float.T(default=0.0)
    lon = Float.T(default=0.0)
    elevation = Float.T(default=0.0)
    depth = Float.T(default=0.0)
    channels = List.T(Channel.T())

class MomentTensor(Object):
    m = Tuple.T(6,Float.T(default=0.0))

class Event(Object):
    lat = Float.T(default=0.0)
    lon = Float.T(default=0.0)
    time = Timestamp.T(default=0.0)
    depth = Float.T(optional=True)
    magnitude = Float.T(optional=True)
    duration = Float.T(optional=True)
    moment_tensor = MomentTensor.T(optional=True)
    name = String.T(optional=True)
    region = String.T(optional=True)
    catalog = String.T(optional=True)

class PhasePick(Object):
    tmin = Timestamp.T(default=0.0)
    tmax = Timestamp.T(default=0.0)
    nslc_pattern = Tuple.T(4, String.T(''))
    phasename = String.T(default='?')
    automatic = Bool.T(default=False)
    polarity = Int.T(optional=True)
    weight = Float.T(default=1.0)
    amplitude = Float.T(optional=True)
    terror = Float.T(optional=True) 
    
class MarkerBase(Object):
    kind = Int.T(default=0)

class Marker(MarkerBase):
    nslc_patterns = List.T(Tuple.T(4, String.T('')))
    tmin = Timestamp.T(default=0.0)
    tmax = Timestamp.T(default=0.0)

class EventMarker(MarkerBase):
    event = Event.T()

class PhaseMarker(MarkerBase):
    event = Event.T()
    pick = PhasePick.T()

mt = MomentTensor(m=(1.,0.,0.,0.,0.,0.))
mt.validate()

print mt
for x in load_all(open('event.truf')):
    print x
    print dump_all([x,x])


s = Station()
c = Channel(channel='Z')
c.validate()
s.channels.append(c)

paz = PolesAndZeros()
c.response = paz
paz.constant = 10.
s.validate()

m = Marker(nslc_patterns=[ ('', 'STA', '*', 'BH?'), ('', 'STA2', '*', 'BH?') ])
print m

print dump_all([s, s, c])
print dump(s)

#for x in load_all(open('test.truf')):
    #print x


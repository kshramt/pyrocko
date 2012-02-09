from newmodel_base import Object, String, Float, List, load, dump, load_all, dump_all

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

s = Station()
c = Channel(channel='Z')
c.validate()
s.channels.append(c)

paz = PolesAndZeros()
c.response = paz
paz.constant = 10.
s.validate()


#print dump_all([s, s, c])
#print dump(s)

for x in load_all(open('test.yaml')):
    print x


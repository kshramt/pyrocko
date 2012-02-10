import info
import yaml
import datetime, calendar
from itertools import izip
from cStringIO import StringIO

g_iprop = 0

g_yaml_version = (1,1)
g_truf_version = (1,0)
g_prefix = 'Truf.'
g_banner = '''
# YAML %i.%i
# Truf data model %i.%i
# Written by Pyrocko %s
''' % (g_yaml_version + g_truf_version + (info.version,))

def set_properties(cls):
    props = []
    for k in dir(cls):
        prop = getattr(cls, k)
        if isinstance(prop, Tbase):
            prop.name = k
            props.append(prop)

    props.sort(key=lambda x: x.iprop)
    cls.properties = props
    cls.property_names = [ t.name for t in cls.properties ]

class Tbase(object):
    def __init__(self, default=None, optional=False):
        global g_iprop
        self.iprop = g_iprop
        g_iprop += 1
        self._default = default
        self.optional = optional
        self.name = None
        self.parent = None

    def default(self):
        return self._default

    def xname(self):
        if self.name is not None:
            return self.name
        elif self.parent is not None:
            return 'element of %s' % self.parent.xname()

    def _validate(self, val, shallow, regularize):
        if self.optional and val is None:
            return None

        return self.validate(val, shallow, regularize)

    def validate(self, val, shallow, regularize):
        raise ValidationError('%s: no validation method available' % self.xname())

    def validate_simple(self, val, typ, regularize):
        if regularize:
            try:
                val = typ(val)
            except:
                raise ValidationError('%s: could not convert "%s" to type %s' % (self.xname(), val, type.__name__))
            
        if not isinstance(val, typ):
            raise ValidationError('%s: "%s" is not of type %s' % (self.xname(), val, typ.__name__))
        
        return val

yaml_tagname_to_class = {}
class_to_yaml_tagname = {}

class MetaClass(type):
    def __new__(meta, classname, bases, class_dict):
        cls = type.__new__(meta, classname, bases, class_dict)
        if classname != 'Object':
            set_properties(cls)
            if not hasattr(cls, 'T'):
                class T(Tbase):
                    def validate(self, val, shallow, regularize):
                        if not isinstance(val, cls):
                            raise ValidationError('%s: object is not of required type' % (self.xname()))
                        if not shallow:
                            return val.validate(regularize)

                cls.T = T
            
            tagname = g_prefix + classname
            yaml_tagname_to_class[tagname] = cls
            class_to_yaml_tagname[cls] = tagname

        return cls

class ValidationError(Exception):
    pass

class ArgumentError(Exception):
    pass

class Object(object):
    __metaclass__ = MetaClass

    def __init__(self, **kwargs):
        for prop in self.properties:
            k = prop.name
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))
            else:
                if not prop.optional and prop.default() is None:
                    raise ArgumentError('Missing argument to %s: %s' % (self.classname(), prop.name()))
                else:
                    setattr(self, k, prop.default())
        
        if kwargs:
            raise ArgumentError('Invalid argument to %s: %s' % (self.classname(), ', '.join(kwargs.keys())))

    def ipropvals(self):
        for prop in self.properties:
            yield prop, getattr(self, prop.name)

    def inamevals(self, omit_unset=False):
        for prop in self.properties:
            v = getattr(self, prop.name)
            if not (prop.optional and v is None):
                yield prop.name, v

    def inamevals_to_save(self, omit_unset=False):
        for prop in self.properties:
            v = getattr(self, prop.name)
            if not (prop.optional and v is None):
                if isinstance(prop, Timestamp.T):
                    v = datetime.datetime.utcfromtimestamp(v)

                yield prop.name, v

    def validate(self, shallow=False, regularize=False):
        for prop, val in self.ipropvals():
            newval = prop._validate(val, shallow, regularize)
            if regularize and newval is not val:
                setattr(self, prop.name, newval)

    def values(self):
        return [ getattr(self, k) for k in self.property_names ]

    def classname(self):
        return self.__class__.__name__

    def dump(self, stream=None, header=False):
        return dump(self, stream=stream, header=header)

    @classmethod
    def load(cls, stream):
        return load(stream)

    def __str__(self):
        return self.dump()

def dump(object, stream=None, header=False, _dump_function=yaml.safe_dump):
    if stream is None:
        stream_ = StringIO()
    else:
        stream_ = stream

    if header:
        if isinstance(header, str):
            banner = header
        else:
            banner = g_banner

        stream_.write(banner)

    _dump_function(object, stream=stream_, explicit_start=True)
    if stream is None:
        return stream_.getvalue()

def dump_all(object, stream=None, header=True):
    return dump(object, stream=stream, header=header, _dump_function=yaml.safe_dump_all)

def load(stream):
    return yaml.safe_load(stream)

def load_all(stream):
    return yaml.safe_load_all(stream)

def multi_representer(dumper, data):
    data.validate(shallow=True)
    node = dumper.represent_mapping('!'+class_to_yaml_tagname[data.__class__], 
            data.inamevals_to_save(omit_unset=True), flow_style=False)

    return node

def multi_constructor(loader, tag_suffix, node):
    tagname = g_prefix+str(tag_suffix)
    cls = yaml_tagname_to_class[tagname]
    kwargs = dict(loader.construct_mapping(node).iteritems())
    o = cls(**kwargs)
    o.validate(shallow=True, regularize=True)
    return o

yaml.add_multi_representer(Object, multi_representer, Dumper=yaml.SafeDumper)
yaml.add_multi_constructor('!'+g_prefix, multi_constructor, Loader=yaml.SafeLoader)

class Int(Object):
    class T(Tbase):
        def validate(self, val, shallow, regularize):
            return self.validate_simple(val, int, regularize)

class Float(Object):
    class T(Tbase):
        def validate(self, val, shallow, regularize):
            return self.validate_simple(val, float, regularize)

class Bool(Object):
    class T(Tbase):
        def validate(self, val, shallow, regularize):
            return self.validate_simple(val, bool, regularize)

class String(Object):
    class T(Tbase):
        def validate(self, val, shallow, regularize):
            return self.validate_simple(val, str, regularize)

class List(Object):
    class T(Tbase):
        def __init__(self, content, *args, **kwargs):
            Tbase.__init__(self, *args, **kwargs)
            self.content_t = content
            self.content_t.parent = self

        def default(self):
            return []

        def validate(self, val, shallow, regularize):
            if not isinstance(val, list):
                raise ValidationError('%s is not a list' % self.xname())
            
            for i, ele in enumerate(val):
                newele = self.content_t.validate(ele, shallow, regularize)
                if regularize and newele is not ele:
                    val[i] = newele
                
            return val

class Tuple(Object):
    class T(Tbase):
        def __init__(self, n, content, *args, **kwargs):
            Tbase.__init__(self, *args, **kwargs)
            self.content_t = content
            self.content_t.parent = self
            self.n = n

        def default(self):
            return tuple( self.content_t.default() for x in xrange(self.n) )

        def validate(self, val, shallow, regularize):
            if not isinstance(val, tuple):
                raise ValidationError('%s is not a tuple' % self.xname())

            if not len(val) == self.n:
                raise ValidationError('%s should have length %i' % (self.xname(), self.n))

            if not regularize:
                for ele in val:
                    self.content_t.validate(ele, shallow, regularize)

                return val
            else:
                newval = []
                isnew = False
                for ele in val:
                    newele = self.content_t.validate(ele, shallow, regularize)
                    newval.append(newele)
                    if newele is not ele:
                        isnew = True
                
                if isnew:
                    return tuple(newval)
                else:
                    return val

class Timestamp(Object):
    class T(Tbase):
        def validate(self, val, shallow, regularize):
            if regularize:
                if isinstance(val, datetime.datetime):
                    tt = val.utctimetuple()
                    newval = calendar.timegm(tt) + val.microsecond * 1e-6  

                elif isinstance(val, str):
                    newval = util.str_to_time(val)
                
                elif isinstance(val, int):
                    newval = float(val)

                val = newval

            if not isinstance(val, float):
                raise ValidationError('%s: "%s" is not a timestamp' % (self.xname(), val))
            
            return val


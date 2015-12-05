from __future__ import print_function, unicode_literals
import regex as re
from urllib import unquote
import datetime
import json
import bz2file

# n-triples
parser = re.compile(r'<(.+)>\s<(.+)>\s(.+)\s\.+')

# values
value_patterns = [
    re.compile(r'"(.+)"@[A-Za-z]+'),
    re.compile(r'"(.+)"\^\^<(.+)>'),
    re.compile(r'<(.+)>'),
]

def to_unicode_or_bust(obj, encoding='utf-8'):
    """
    From http://farmdev.com/talks/unicode/
    """
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def iter_entities_from(filename):
    """
    bz2 wikipedia n-triples import.
    for each entity returns a set of values for each defined attribute in the filename.
    """
    print('reading', filename)

    with bz2file.open(filename, 'r') as dump:
        prev_resource = None
        values = None

        for l in dump:
            if l.startswith('#'):
                continue 

            l = to_unicode_or_bust(l).strip()

            parts = get_parts(l)
            if not parts:
                continue 

            resource = parts['resource']

            if prev_resource != resource:
                if prev_resource != None:
                    yield values

                values = {'resource': resource}
                prev_resource = resource


            value = parts['object']
            if not value:
                continue

            key = parts['predicate']

            if not key in values:
                values[key] = set()
            
            values[key].add(value)

        if values is not None:
            yield values
    


def parse_attrib(uri):
    parts = uri.split('/')
    name = unquote(parts[-1])
    name = name.replace('_', ' ')
    return to_unicode_or_bust(name)

def get_parts(line):
    parts = parser.match(line)
    if not parts:
        return None 

    parts = parts.group(1, 2, 3)
    resource = parts[0]
    subject = parse_attrib(parts[0])
    predicate = parse_attrib(parts[1])
    obj = None 

    for pattern in value_patterns:
        match_string = pattern.match(parts[2])
        if match_string != None:
            obj = match_string.group(1)
            break
        
    if obj:
        obj = unicode(obj.decode('unicode-escape', errors='ignore'))
    
    return {'resource': resource, 'subject': subject, 'predicate': predicate, 'object': obj}


def get_attr(values, attr, default=None):
    try:
        return values[attr][0]
    except KeyError:
        return default


def get_date(values, attr):
    try:
        d = values[attr].pop()
        parts = d.split('-')
    
        try:
            if len(parts) == 3:
                dt = datetime.datetime.strptime(d, "%Y-%m-%d")
            elif len(parts) == 2:
                dt = datetime.datetime.strptime(d, "%Y-%m")
            elif len(parts) == 1:
                dt = datetime.datetime.strptime(d, "%Y")
            else:
                return None
        except ValueError:
            return None
    
        return dt
    except KeyError:
        return None
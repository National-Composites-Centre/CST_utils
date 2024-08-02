from stl import mesh
import CompositeStandard as cs
from pydantic import BaseModel
from jsonic import serialize, deserialize

#Only leave python related utilities in this module - rest to dedicated "utils"

def method_reverse_lookup(a, b, c=None):
    #Check if [a] is in list [b] and return index c (currently only last index returned)
    reverse_lookup = {x:i for i, x in enumerate(b)}
    for i, x in enumerate(a):
        i = reverse_lookup.get(x, -1)
    return i




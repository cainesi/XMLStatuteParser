import itertools

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)

def triples(iterable):
    "s -> (None,s0,s1), (s0,s1,s2), (s1,s2,s3), ... (sn-1,sn,None)"
    a,b,c = itertools.tee(iterable,3)
    a = itertools.chain([None], a)
    next(c,None)
    c = itertools.chain(c,[None])
    return itertools.izip(a,b,c)
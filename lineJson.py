class lineJson(object):
    lineID = ""
    text = ""


def as_lineJson(d):
    lj = lineJson()
    lj.__dict__.update(d)
    return lj
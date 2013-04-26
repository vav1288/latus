
import json
import pprint

JSON_STYLE = "JSON"

def lprint(obj_param, style = None):
    if style == JSON_STYLE:
        print (json.dumps(obj_param))
    else:
        pprint.pprint(obj_param)
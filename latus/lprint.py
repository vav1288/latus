
import json
import sys

JSON_STYLE = "JSON"

def lprint(obj_param, style = None):
    if style == JSON_STYLE:
        print (json.dumps(obj_param))
    else:
        # assumed to be a string
        # http://stackoverflow.com/questions/5419/python-unicode-and-the-windows-console
        # (see entry by Giampaolo Rodolà)
        try:
            print (obj_param)
        except UnicodeEncodeError:
            # handles printing to windows console
            print (obj_param.encode('utf-8').decode(sys.stdout.encoding))

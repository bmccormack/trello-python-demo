import json

def jprint(obj):
  print json.dumps(obj, sort_keys=True,
                    indent=4, separators=(',', ': '))
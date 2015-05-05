"""
script to show how betfair_api.py can be used
"""

import betfair_api as bf

import yaml

@bf.authorise
def get_sports(token, *args, **kwargs):
    req={"method": "SportsAPING/v1.0/listEventTypes",
         "params": {"filter": {}}}
    return bf.api_post([req], token)

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("Please enter username, password")
        username, password = sys.argv[1:3]
        kwargs={"username": username,
                "password": password}
        print yaml.safe_dump(get_sports(**kwargs), default_flow_style=False)
    except RuntimeError, error:
        print "Error: %s" % str(error)

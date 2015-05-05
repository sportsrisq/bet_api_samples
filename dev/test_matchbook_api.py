"""
script to show how matchbook_api.py can be used
"""

import matchbook_api as mb

import yaml

@mb.authorise
def get_events(token, *args, **kwargs):
    params={"include-markets": "true",
            # "include-runners": "true",
            # "include-prices": "true",
            "sport-ids": mb.FootballId,
            "per-page": mb.MaxResults,
            "market-per-page": mb.MaxResults,
            "tag-ids": kwargs["league_id"]}
    return mb.api_get("/bpapi/rest/events", params, token)

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("Please enter username, password")
        username, password = sys.argv[1:3]
        kwargs={"username": username,
                "password": password}
        print yaml.safe_dump(get_events(league_id=32, **kwargs),
                             default_flow_style=False)
    except RuntimeError, error:
        print "Error: %s" % str(error)

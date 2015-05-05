import base64, httplib, json

from lxml import etree

import datetime, yaml

Endpoint="54.76.246.112:443"

ProxyPath="/secure_proxy"

ApiPath="/api.pinnaclesports.com"

DateTimeFormat="%Y-%m-%dT%H:%M:%SZ"

PinnacleTrue, PinnacleFalse = "TRUE", "FALSE"

MatchOdds, AsianHandicap, OverUnder = "MONEYLINE", "SPREAD", "TOTAL"

HomeWin, AwayWin, Draw = "Team1", "Team2", "Draw"

Decimal="DECIMAL"

Risk="RISK"

Running, Settled = "RUNNING", "SETTLED"

FootballSportId=29

Leagues=yaml.load("""
ENG.1: 1980
""")

DefaultPeriodNumber=0

# helpers

def filter_child_string(el, key):
    return el.xpath(key)[0].text

def filter_child_int(el, key):
    return int(filter_child_string(el, key))

def filter_child_float(el, key):
    return float(filter_child_string(el, key))

def filter_child_datetime(el, key):
    return datetime.datetime.strptime(filter_child_string(el, key),
                                      DateTimeFormat)

"""
- all methods support XML
- however some support XML and JSON
- if you don't specify 'Accept' header, you get JSON :-(
"""

def api_get(path, username, password, content_type, response_handler):
    http=httplib.HTTPSConnection(Endpoint)
    username_password=base64.b64encode("%s:%s" % (username, password))
    headers= {'Authorization': 'Basic %s' % username_password,
              'Accept': content_type}
    path=ProxyPath+ApiPath+path
    http.request('GET', path, 
                 headers=headers)
    resp=http.getresponse()
    if resp.status/100==4:
        raise RuntimeError(resp.read())
    if resp.status!=200:
        raise RuntimeError("Server returned HTTP %i" % resp.status)
    return response_handler(resp.read())

def api_get_xml(path, username, password):
    return api_get(path, username, password, "application/xml", lambda x: etree.fromstring(x))

def api_get_json(path, username, password):
    return api_get(path, username, password, "application/json", lambda x: json.loads(x))

def api_post(path, payload, username, password, content_type, response_handler):
    http=httplib.HTTPSConnection(Endpoint)
    username_password=base64.b64encode("%s:%s" % (username, password))
    headers={'Authorization': 'Basic %s' % username_password,
             'Accept': content_type,
             'Content-Type': content_type,
             'Content-Length': str(len(payload))}
    path=ProxyPath+ApiPath+path
    http.request('POST', path, 
                 body=payload, 
                 headers=headers)
    resp=http.getresponse()
    if resp.status/100==4:
        raise RuntimeError(resp.read())
    if resp.status!=200:
        raise RuntimeError("Server returned HTTP %i" % resp.status)
    return response_handler(resp.read())

def api_post_json(path, struct, username, password):
    return api_post(path, json.dumps(struct), username, password, "application/json", lambda x: json.loads(x))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("Please enter username, password")
        username, password = sys.argv[1:3]
        kwargs={"username": username,
                "password": password}
        doc=api_get_xml("/v1/sports", **kwargs)
        print etree.tostring(doc, pretty_print=True)
    except RuntimeError, error:
        print "Error: %s" % str(error)

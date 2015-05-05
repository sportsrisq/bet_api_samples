"""
http://trac.matchbook.com/
sportsrisq/sportsrisq$1
http://trac.matchbook.com/bpad.pdf
"""

import datetime, httplib, json, os, yaml

Endpoint="matchbook.com"

AuthPath="/bpapi/rest/security/session"

FootballId=15

MatchOdds="Match Odds"

Decimal="DECIMAL"

ExchangeType="back-lay"

Back, Lay = "back", "lay"

Draw = "Draw"

MaxResults=500

Leagues=yaml.load("""
ENG.1: 32
""")

def api_authenticate(username, password):
    http=httplib.HTTPSConnection(Endpoint)
    payload=json.dumps({"username": username,
                        "password": password})
    headers={"Content-Type": "application/json"}
    http.request('POST', AuthPath, headers=headers, body=payload)
    resp=http.getresponse()
    if resp.status==400:
        raise RuntimeError(resp.read())
    if resp.status!=200:
        raise RuntimeError("Server returned HTTP %i" % resp.status)
    struct=json.loads(resp.read())
    return struct["session-token"]

def authorise(fn, window=datetime.timedelta(minutes=30)):
    def wrapped_fn(*args, **kwargs):
        username, password = kwargs["username"], kwargs["password"]
        filename="tmp/Matchbook~%s.yaml" % username
        now=datetime.datetime.now()                
        def shall_authenticate(username):
            if os.path.exists(filename):
                credentials=yaml.load(file(filename).read())
                return now-credentials["timestamp"] > window
            else:
                return True
        def authenticate(username, password):
            token=api_authenticate(username, password)
            credentials={"token": token,
                         "timestamp": now}
            dest=file(filename, 'w')
            dest.write(yaml.safe_dump(credentials,
                                      default_flow_style=False))
            dest.close()
            return token
        if shall_authenticate(username):            
            # print "Authenticating %s" % username
            token=authenticate(username, password)
        else:
            # print "Loading %s credentials" % username
            credentials=yaml.load(file(filename).read())
            token=credentials["token"]
        return fn(token, *args, **kwargs)
    return wrapped_fn

def querystring(args):
    return "&".join(["%s=%s" % (k, v) for k, v in args.items()])

def api_get(path, params, token):
    http=httplib.HTTPSConnection(Endpoint)
    headers={"Cookie": "session-token=%s;" % token}
    http.request('GET', path+"?"+querystring(params), 
                 headers=headers)
    resp=http.getresponse()
    if resp.status==400:
        raise RuntimeError(resp.read())
    if resp.status!=200:
        raise RuntimeError("Server returned HTTP %i" % resp.status)
    return json.loads(resp.read())

def api_post(path, struct, token):
    http=httplib.HTTPSConnection(Endpoint)
    headers={"Cookie": "session-token=%s;" % token,
             "Content-Type": "application/json"}
    http.request('POST', path, 
                 body=json.dumps(struct), 
                 headers=headers)
    resp=http.getresponse()
    if resp.status==400:
        raise RuntimeError(resp.read())
    if resp.status!=200:
        # START TEMP CODE
        print resp.read()
        # END TEMP CODE
        raise RuntimeError("Server returned HTTP %i" % resp.status)
    return json.loads(resp.read())

def api_delete(path, params, token):
    http=httplib.HTTPSConnection(Endpoint)
    headers={"Cookie": "session-token=%s;" % token}
    http.request('DELETE', path+"?"+querystring(params), 
                 headers=headers)
    resp=http.getresponse()
    if resp.status==400:
        raise RuntimeError(resp.read())
    if resp.status!=200:
        raise RuntimeError("Server returned HTTP %i" % resp.status)
    return json.loads(resp.read())


@authorise
def get_events(token, *args, **kwargs):
    params={"sport-ids": FootballId,
            "tag-ids": kwargs["league_id"],
            "per-page": MaxResults}
    return api_get("/bpapi/rest/events", params, token)

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

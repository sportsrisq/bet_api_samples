"""
script requires you to add your Betfair cert file in the 'cert' directory, with the same name as your Betfair username (eg '/cert/sportsrisq.pem')
also requires you to enter your app key below
"""

import datetime, httplib, json, os, yaml


AppKey=None # ENTER YOUR APP KEY HERE

AuthEndpoint="identitysso.betfair.com:443"

AuthPath="/api/certlogin"

APIEndpoint="api.betfair.com"

APIPath="/exchange/betting/json-rpc/v1"

UserAgent="Python2.7"

FormURLEncoded="application/x-www-form-urlencoded"

JSONContentType="application/json"

CertFile, KeyFile = "cert/%s.crt", "cert/%s.key"

DateTimeFormat="%Y-%m-%dT%H:%M:%S.000Z"

MarketProjection=yaml.load("""
- COMPETITION
- EVENT
- EVENT_TYPE
- MARKET_START_TIME
- RUNNER_DESCRIPTION
""")

MarketTypes=yaml.load("""
- ASIAN_HANDICAP
- CORRECT_SCORE
- MATCH_ODDS 
- OVER_UNDER_25
""")

MatchOdds="MATCH_ODDS"

Back, Lay = "BACK", "LAY"

LimitOrder="LIMIT"

Lapse="LAPSE"

Success="SUCCESS"

MaxResults=1000

MinBetSize=2

Leagues=yaml.load("""
ENG.1: 31
""")

def parse_date(datestr):
    return datetime.datetime.strptime(datestr, DateTimeFormat)

def api_authenticate(username, password):
    http=httplib.HTTPSConnection(AuthEndpoint,
                                 cert_file=CertFile % username,
                                 key_file=KeyFile % username)
    body="username=%s&password=%s" % (username, password)
    headers={"Content-Type": FormURLEncoded,
             "Content-Length": str(len(body)),
             "User-Agent": UserAgent,
             "X-Application": AppKey}
    http.request('POST', AuthPath, 
                 body=body,
                 headers=headers)
    resp=http.getresponse()
    if resp.status/100==4:
        raise RuntimeError(resp.read())
    if resp.status!=200:
        raise RuntimeError("Server returned HTTP %i" % resp.status)
    body=json.loads(resp.read())
    if body["loginStatus"]!=Success:
        raise RuntimeError("Authentication returned '%s'" % body["loginStatus"])
    return body["sessionToken"]
    
def authorise(fn, window=datetime.timedelta(minutes=30)):
    def wrapped_fn(*args, **kwargs):
        username, password = kwargs["username"], kwargs["password"]
        filename="tmp/Betfair~%s.yaml" % username
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

def api_post(struct, token):
    http=httplib.HTTPSConnection(APIEndpoint)
    body=json.dumps(struct)
    headers={"Content-Type": JSONContentType,
             "Content-Length": str(len(body)),
             "User-Agent": UserAgent,
             "X-Application": AppKey,
             "X-Authentication": token}
    http.request('POST', APIPath, 
                 body=body,
                 headers=headers)
    resp=http.getresponse()
    if resp.status==400:
        raise RuntimeError(resp.read())
    if resp.status!=200:
        raise RuntimeError("Server returned HTTP %i" % resp.status)
    return json.loads(resp.read())

@authorise
def get_sports(token, *args, **kwargs):
    req={"method": "SportsAPING/v1.0/listEventTypes",
         "params": {"filter": {}}}
    return api_post([req], token)

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

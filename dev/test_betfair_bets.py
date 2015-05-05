"""
script to test Betfair bet placement
"""

import betfair_api as bf

@bf.authorise
def get_events(token, league_id, *args, **kwargs):
    req={"method": "SportsAPING/v1.0/listEvents",
         "params": {"filter": {"competitionIds": [league_id]}}}
    resp=bf.api_post([req], token)
    return [item["event"] for item in resp[0]["result"]]

# get markets

@bf.authorise
def get_1x2_markets(token, event_ids, *args, **kwargs):
    req={"method": "SportsAPING/v1.0/listMarketCatalogue",
         "params": {"filter": {"eventIds": event_ids,
                               "marketTypeCodes": [bf.MatchOdds]},
                    "maxResults": bf.MaxResults,
                    "marketProjection": bf.MarketProjection}}
    resp=bf.api_post([req], token)
    return resp[0]["result"]

def init_limit_order_bet(market, selectionname, size, price):
    selections=dict([(runner["runnerName"], runner["selectionId"]) 
                    for runner in market["runners"]])
    side=bf.Back if size > 0 else bf.Lay
    return {"selectionId": selections[selectionname],
            "handicap": 0,
            "side": side,
            "orderType": bf.LimitOrder,
            "limitOrder": {"size": abs(size),
                           "price": price,
                           "persistenceType": bf.Lapse}}

@bf.authorise
def place_bets(token, market, bets, *args, **kwargs):
    req={"method": "SportsAPING/v1.0/placeOrders",
         "params": {"marketId": market["marketId"],
                    "instructions": bets}}
    resp=bf.api_post([req], token)
    return resp[0]["result"]

@bf.authorise
def get_bets(token, market, *args, **kwargs):
    req={"method": "SportsAPING/v1.0/listCurrentOrders",
         "params": {"marketIds": [market["marketId"]]}}
    resp=bf.api_post([req], token)
    return resp[0]["result"]

@bf.authorise
def cancel_bets(token, bet_ids, *args, **kwargs):
    req={"method": "SportsAPING/v1.0/cancelOrders",
         "params": {"betIds": bet_ids}}
    resp=bf.api_post([req], token)
    return resp[0]["result"]

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 5:
            raise RuntimeError("Please enter username, password, leaguename, teamname")
        username, password, leaguename, teamname = sys.argv[1:5]
        if leaguename not in bf.Leagues:
            raise RuntimeError("League not found")
        kwargs={"username": username,
                "password": password}
        # get events
        events=get_events(league_id=bf.Leagues[leaguename],
                          **kwargs)
        print "%i events" % len(events)
        # get markets
        event_ids=[event["id"] for event in events]        
        markets=get_1x2_markets(event_ids=event_ids, **kwargs)
        print "%i markets" % len(markets)
        # get market
        markets=[market for market in markets
                 if teamname in market["event"]["name"]]
        if markets==[]:
            raise RuntimeError("No markets containing team found")
        market=markets[0]
        print market["event"]["name"]
        # retrieve bets
        bets=get_bets(market, **kwargs)
        print "%i bets" % len(bets["currentOrders"])
        # initialise bet
        bet=init_limit_order_bet(market, teamname,
                                 size=bf.MinBetSize, 
                                 price=1000)
        print "Bet: %s" % bet
        # place bet
        resp=place_bets(market, [bet], **kwargs)
        betids=[item["betId"] for item in resp["instructionReports"]]
        print "Bet ids: %s" % betids
        # retrieve bets
        bets=get_bets(market, **kwargs)
        print "%i bets" % len(bets["currentOrders"])
        # cancel bet
        resp=cancel_bets(betids, **kwargs)
        print resp
        # wait a bit
        import time
        print "Waiting 5 secs .."
        time.sleep(5)
        # retrieve bets
        bets=get_bets(market, **kwargs)
        print "%i bets" % len(bets["currentOrders"])
    except RuntimeError, error:
        print "Error: %s" % str(error)

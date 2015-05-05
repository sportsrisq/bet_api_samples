"""
script to test placement of Matchbook bets
"""

import matchbook_api as mb

@mb.authorise
def get_1x2_markets(token, league_id, *args, **kwargs):
    params={"include-markets": "true",
            "include-runners": "true",
            # "include-prices": "true",
            "sport-ids": mb.FootballId,
            "per-page": mb.MaxResults,
            "market-per-page": mb.MaxResults,
            "tag-ids": league_id}
    resp=mb.api_get("/bpapi/rest/events", params, token)
    def filter_1x2_market(event):
        markets=[market for market in event["markets"]
                 if market["name"]==mb.MatchOdds]
        if markets!=[]:
            market=markets[0]
            market["event-name"]=event["name"]
            return market
        return None
    return [market for market in [filter_1x2_market(event) 
                                  for event in resp["events"]]
            if market]

"""
/reports/bets doesn't support filtering by tag-ids :-(
"""

@mb.authorise
def get_matched_bets(token, market, *args, **kwargs):
    params={"sport-ids": mb.FootballId,
            "per-page": mb.MaxResults,
            "matched": "true"}
    resp=mb.api_get("/bpapi/rest/reports/bets", params, token)
    bets=[bet for bet in resp["bets"]
          if bet["event-id"]==market["event-id"]]
    return bets

@mb.authorise
def get_unmatched_bets(token, market, *args, **kwargs):
    params={"sport-ids": mb.FootballId,
            "per-page": mb.MaxResults,
            "matched": "false"}
    resp=mb.api_get("/bpapi/rest/reports/bets", params, token)
    bets=[bet for bet in resp["bets"]
          if bet["event-id"]==market["event-id"]]
    return bets


def init_bet(market, selectionname, size, price):
    selectionids=dict([(runner["name"], runner["id"])
                       for runner in market["runners"]])
    side=mb.Back if size > 0 else mb.Lay
    return {"odds": price,
            "stake": abs(size),
            "side": side,
            "runner-id": selectionids[selectionname],
            "temp-id": 1}
    
@mb.authorise
def place_bets(token, market, bets, *args, **kwargs):
    struct={"odds-type": mb.Decimal,
            "exchange-type": mb.ExchangeType,
            "offers": bets}
    return mb.api_post("/bpapi/rest/offers", struct, token)

@mb.authorise
def cancel_bets(token, bet_ids, *args, **kwargs):
    params={"offer-ids": ",".join([str(id) for id in bet_ids])}
    return mb.api_delete("/bpapi/rest/offers", params, token)

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 5:
            raise RuntimeError("Please enter username, password, leaguename, teamname")
        username, password, leaguename, teamname = sys.argv[1:5]
        if leaguename not in mb.Leagues:
            raise RuntimeError("League not found")
        kwargs={"username": username,
                "password": password}
        # get markets
        markets=get_1x2_markets(league_id=mb.Leagues[leaguename], 
                                **kwargs)
        print "%i markets" % len(markets)
        # get market
        markets=[market for market in markets
                 if teamname in market["event-name"]]
        if markets==[]:
            raise RuntimeError("No markets containing team found")
        market=markets[0]
        print market
        # retrieve bets
        bets=get_unmatched_bets(market, **kwargs)
        print "%i bets" % len(bets)
        # initialise bet
        bet=init_bet(market, teamname,
                     size=2, 
                     price=1000)
        print "Bet: %s" % bet
        # place bet
        resp=place_bets(market, [bet], **kwargs)
        betids=[offer["id"] for offer in resp["offers"]]
        print betids
        # retrieve bets
        bets=get_unmatched_bets(market, **kwargs)
        print "%i bets" % len(bets)
        # cancel bet
        resp=cancel_bets(betids, **kwargs)
        print resp
        # retrieve bets
        bets=get_unmatched_bets(market, **kwargs)
        print "%i bets" % len(bets)
    except RuntimeError, error:
        print "Error: %s" % str(error)

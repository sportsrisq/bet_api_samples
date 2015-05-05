"""
script to test placement of Pinnacle bets
"""

import pinnacle_api as pn

import datetime

"""
Parameter,Type,Required
uniqueRequestId,GUID,Yes
acceptBetterLine,BOOLEAN,Yes
oddsFormat,ODDS_FORMAT,Yes # [AMERICAN, DECIMAL, [Other]]
stake,Decimal,Yes,
winRiskStake,WIN_RISK_TYPE,Yes # [WIN, RISK]
sportId,Int,Yes
eventId,Int,Yes
periodNumber,Int,Yes
betType,BET_TYPE,Yes # [SPREAD, MONEYLINE, TOTAL_POINTS, TEAM_TOTAL_POINTS]
team,TEAM_TYPE,No # [Team1, Team2, Draw] [required for SPREAD, MONEYLINE, TEAM_TOTAL_POINTS only]
side,SIDE_TYPE,No # [OVER, UNDER] [required for TOTAL_POINTS, TEAM_TOTAL_POINTS only]
lineId,Int,Yes,Line,
altLineId,Int,No,
pitcher1MustStart,BOOLEAN,No
pitcher2MustStart,BOOLEAN,No
"""

DefaultStake=50

DateFormat="%Y-%m-%d"

def get_1x2_markets(sport_id, league_id, username, password):
    path="/v1/feed?sportid=%i&leagueid=%i" % (sport_id, league_id)
    doc=pn.api_get_xml(path, username, password)    
    events=doc.xpath("//events/event")
    def has_zero_period(event):
        periods=[period for period in event.xpath("periods/period")
                 if pn.filter_child_int(period, "number")==0]
        return len(periods) > 0
    def filter_1x2_market(event):
        kickoff=pn.filter_child_datetime(event, "startDateTime")
        event_name="%s vs %s" % tuple([pn.filter_child_string(event, "%sTeam/name" % attr) for attr in ["home", "away"]])
        event_id=pn.filter_child_int(event, "id")
        periods=[period for period in event.xpath("periods/period")
                 if pn.filter_child_int(period, "number")==0]
        line_id=int(periods[0].attrib["lineId"])
        return {"kickoff": kickoff,
                "event_name": event_name,
                "event_id": event_id,
                "line_id": line_id}
    return [filter_1x2_market(event)
            for event in events
            if has_zero_period(event)]

"""
no price specification; you get whatever price is on offer
no support for multiple bets
mininum bet size specified on per- market basis; see API
"""

def init_bet(market, selectionname, stake):
    teamnames=market["event_name"].split(" vs ")
    import uuid
    return {"uniqueRequestId": str(uuid.uuid1()),
            "acceptBetterLine": pn.PinnacleFalse,
            "oddsFormat": pn.Decimal,
            "stake": stake,
            "winRiskStake": pn.Risk,
            "sportId": pn.FootballSportId,
            "eventId": market["event_id"],
            "periodNumber": pn.DefaultPeriodNumber, 
            "betType": pn.MatchOdds,
            "team": pn.HomeWin if selectionname==teamnames[0] else pn.AwayWin, 
            "lineId": market["line_id"]}
     
def place_bet(bet, username, password):
    return pn.api_post_json("/v1/bets/place", bet, username, password)

def get_bets(startdate, enddate, username, password, bet_type):
    path="/v1/bets?betlist=%s&fromDate=%s&toDate=%s" % (bet_type, startdate.strftime(DateFormat), enddate.strftime(DateFormat))
    doc=pn.api_get_xml(path, username, password)
    def parse_bet(el):
        return {"placed_at": pn.filter_child_string(el, "placedAt"),
                "sport_id": pn.filter_child_int(el, "sportId"),
                "league_id": pn.filter_child_int(el, "leagueId"),
                "event_id": pn.filter_child_int(el, "eventId"),
                "bet_id": pn.filter_child_int(el, "betId"),
                "bet_type": pn.filter_child_string(el, "betType"),
                "team_name": pn.filter_child_string(el, "teamName"),
                "price": pn.filter_child_float(el, "price"),
                "stake": pn.filter_child_float(el, "risk")}
    return [parse_bet(el) for el in doc.xpath("//straightBet")]

def get_unsettled_bets(startdate, enddate, username, password):
    return get_bets(startdate, enddate, username, password, pn.Running)

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 5:
            raise RuntimeError("Please enter username, password, leaguename, teamname")
        username, password, leaguename, teamname = sys.argv[1:5]
        if leaguename not in pn.Leagues:
            raise RuntimeError("League not found")
        kwargs={"username": username,
                "password": password}
        markets=get_1x2_markets(sport_id=pn.FootballSportId, 
                                league_id=pn.Leagues[leaguename], 
                                **kwargs)
        print "%i markets found" % len(markets)
        markets=[market for market in markets
                 if teamname in market["event_name"]]
        if markets==[]:
            raise RuntimeError("No markets for containing team found")
        market=markets[0]
        teamnames=market["event_name"].split(" vs ")
        selectionnames=[name for name in teamnames 
                       if name!=teamname]
        if selectionnames==[]:
            raise RuntimeError("Selection for team name not found")
        bet=init_bet(market, selectionnames[0], DefaultStake)
        print "Bet:  %s" % bet
        print "Bet confirm: %s" % place_bet(bet, **kwargs)
        enddate=datetime.date.today()+datetime.timedelta(days=1)
        startdate=enddate-datetime.timedelta(days=7)
        bets=get_unsettled_bets(startdate, enddate, **kwargs)
        print "%i bets" % len(bets)
    except RuntimeError, error:
        print "Error: %s" % str(error)

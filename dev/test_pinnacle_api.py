"""
script to show how pinnacle_api.py can be used
"""

import pinnacle_api as pn

from lxml import etree

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("Please enter username, password")
        username, password = sys.argv[1:3]
        kwargs={"username": username,
                "password": password}
        doc=pn.api_get_xml("/v1/sports", **kwargs)
        print etree.tostring(doc, pretty_print=True)
    except RuntimeError, error:
        print "Error: %s" % str(error)

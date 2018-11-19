import json
from random import randrange
import requests
from openreports.locations import Locations

class OpenReports:
    api_urls = {'stackoverflow.com': 'http://logs.sobotics.org/napi/api/reports/all',
                'stackexchange.com': 'http://logs.sobotics.org/napi/api/reports/all/au',
                'copypastor' : 'http://copypastor.sobotics.org/posts/pending?reasons=true'}

    def __init__(self, user, utils, amount, back, host, location = Locations.Natty):
        self.user = user
        self.utils = utils
        self.amount = amount
        self.from_back = back
        self.host = host
        self.location = location
        self.reports = None
        self.which_ignore_list = None


    def fetch_posts(self):
        is_pleb = self.user.reputation < 10000 # Plebs = People who can't view deleted posts since they have less than 10k rep

        ignorefile_name = f"{self.user.id}{self.host}.ignorelist"
        whichIL = "gutty" if self.location is Locations.Guttenberg else ""
        source = "copypastor" if self.location == Locations.Guttenberg else self.host # Set the API from which the reports should be fetched

        reports = self.get_reports(source)
        self.reports = [r["name"] for r in reports] if self.location != Locations.Guttenberg else [r["post_id"] for r in reports]

        if self.location == Locations.Sentinel:
            for r in reports:
                r["link"] = f"https://sentinel.erwaysoftware.com/posts/aid/{r['name']}" #Change post links (from Natty) to Sentinel links

        #TODO: Port legacy code to new architecture

    def get_reports(self, source):
        """
        Get all reports from the chosen API
        :param source: Valid site API endpoint defined in "api_urls"
        :return: Reports returned by the API
        """

        #Call API and load reports into JSON
        response = requests.get(self.api_urls[source])
        response.raise_for_status()
        data = json.loads(response.text)

        #CopyPastor returns the reports in the "posts" property and NAPI in the "items" property
        return data['posts'] if source is "copypastor" else data['items']



    @staticmethod
    def _pleb_or_plop(self):
        num = randrange(100)
        return "plop" if num == 0 else "pleb"
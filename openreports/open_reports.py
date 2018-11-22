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
        self.is_pleb = self.user.reputation < 10000 # Plebs = People who can't view deleted posts since they have less than 10k rep
        self.utils = utils
        self.amount = amount
        self.from_back = back
        self.host = host
        self.location = location
        self.reports = None
        self.which_ignore_list = None

        #TODO: Port legacy code to new architecture

    def fetch_amount(self):
        reports = self.get_reports(self._get_source())
        report_count = len(reports)

        if report_count == 0:
            return "All reports have been tended to."
        else:
            pleb_str = ""
            if self.is_pleb:
                pleb_str = f"Ignored {0} deleted posts (<10k {self._pleb_or_plop()}). "
            return f"{pleb_str}There {self.pluralize('is', report_count)} {report_count} unhandled {self.pluralize('report', report_count)}, {0} of which {self.pluralize('is', 0)} on your ignore list."

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

    def _get_source(self):
        """
        Set the API from which the reports should be fetched
        :return: Which API
        """
        return "copypastor" if self.location == Locations.Guttenberg else self.host

    @staticmethod
    def pluralize(word, amount):
        plurarized = word + 's'
        if word == "is":
            return "is" if amount == 1 else "are"
        return word if amount == 1 else plurarized

    @staticmethod
    def _pleb_or_plop():
        num = randrange(100)
        return "plop" if num == 0 else "pleb"
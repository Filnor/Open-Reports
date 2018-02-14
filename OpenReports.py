# Creates a socvr report with all unhandled Natty reports and maintains an ignore list

import requests
import json as js
import webbrowser
from random import randrange
from datetime import datetime
from argparse import ArgumentParser
from math import ceil
import shelve

apiUrls = {'stackoverflow.com' : 'http://logs.sobotics.org/napi/api/reports/all',
        'stackexchange.com' : 'http://logs.sobotics.org/napi/api/reports/all/au',
        'copypastor' : 'http://copypastor.sobotics.org/posts/pending?reasons=true'}
socvrAPI = 'http://reports.sobotics.org/api/v2/report/create'
seApiUrl = 'https://api.stackexchange.com/2.2/posts/'
siteNames = {'stackoverflow.com' : 'stackoverflow', 'stackexchange.com' : 'askubuntu'}

def _pluralize(word, amount):
    return word if amount == 1 else word + 's'

def _getData(api):
    remote = requests.get(apiUrls[api])
    remote.raise_for_status()

    data = js.loads(remote.text)
    return data['posts'] if api == 'copypastor' else data['items']

def _buildReport(reports):
    ret = {'appName' : 'OpenReports', 'appURL' : 'https://github.com/SOBotics/Open-Reports'}
    posts = []
    for v in reports:
        reasons = ', '.join(r['reasonName'] for r in v['reasons'])
        # Timestamp is in ms for some reason
        d = datetime.utcfromtimestamp(v['timestamp'] / 1000)
        date = d.isoformat()

        posts.append([{'id':'title', 'name':v['name'], 'value':v['link'], 'type':'link'},
            {'id':'score', 'name':'NAA Score', 'value':v['naaValue']},
            {'id':'reasons', 'name':'Reasons', 'value':reasons},
            {'id':'date', 'name':'Date', 'value':date, 'type':'date'}])
    ret['fields'] = posts
    return ret

def _openGutty(reports):
    if len(reports) == 0:
        return None

    baseURL = 'http://copypastor.sobotics.org/posts/'

    report = {'appName' : 'OpenReports', 'appURL' : 'https://github.com/SOBotics/Open-Reports'}
    items = []
    for r in reports:
        idStr = str(r['post_id'])
        items.append([
            {'id':'title', 'name': 'Report #' + idStr,
                'value':baseURL + idStr, 'type':'link'},
            {'id':'postOne', 'name':r['title_one'],
                'value':r['url_one'] + ' by ' + r['username_one']},
            {'id':'postTwo', 'name':r['title_two'],
                'value':r['url_two'] + ' by ' + r['username_two']}])
    report['fields'] = items
    r = requests.post(socvrAPI, json=report)
    r.raise_for_status()
    res = r.json()
    return res['reportURL']

def _openLinks(reports):
    if len(reports) == 0:
        return None
    report = _buildReport(reports)
    
    r = requests.post(socvrAPI, json=report)
    r.raise_for_status()
    res = r.json()
    return res['reportURL']

def _plebString(curr, client):
    nonDeleted = []
    for i in range(ceil(len(curr) / 100)):
        r = requests.get(seApiUrl + ';'.join(curr[i*100:(i+1)*100]) + '?site=' \
                + siteNames[client.host] + '&key=Vhtdwbqa)4HYdpgQlVMqTw((')
        r.raise_for_status()
        data = js.loads(r.text)
        nonDeleted += [str(v['post_id']) for v in data['items']]
    numDel = len(curr) - len(nonDeleted)
    if numDel:
        plopper = randrange(100)
        plopStr = 'plop' if plopper == 0 else 'pleb'
        return 'Ignored %s deleted %s (<10k '%(numDel, _pluralize('post', numDel)) \
                + plopStr + '). ', nonDeleted
    return '', nonDeleted

def _openSentinel(reports):
    return _openLinks(reports)

def OpenReports(mode, user, client, amount, back, where):
    userID = user.id
    lowRep = user.reputation < 10000

    filename = str(userID) + client.host + '.ignorelist'
    whichIL = 'gutty' if where is 'gutty' else ''
    source = 'copypastor' if where == 'gutty' else client.host
    reports = _getData(source)
    curr = [v['name'] for v in reports] if where != 'gutty' \
            else [v['post_id'] for v in reports]

    if where == 'sentinel':
        for v in reports:
            v['link'] = 'https://sentinel.erwaysoftware.com/posts/aid/' + v['name']

    with shelve.open(filename) as db:

        try:
            ignored = db['ignored' + whichIL]
            last = db['last' + whichIL]
        except:
            ignored = []
            last = []

        if mode == 'ignore_rest':
            newIgnored = [v for v in last if v in curr]
            db['ignored' + whichIL] = newIgnored
            db['last' + whichIL] = last
            msg = str(len(newIgnored)) + ' %s in ignore list.'%_pluralize('report', len(newIgnored))
            return msg
        else:
            msg = ''
            if (where is None) and lowRep:
                msg, curr = _plebString(curr, client)
                reports = [v for v in reports if v['name'] in curr]
            if where == 'gutty':
                good = [v for v in reports if not v in ignored]
            else:
                good = [v for v in reports if not v['name'] in ignored]
            numIgnored = len(curr) - len(good)
            if mode == 'fetch_amount':
                if len(curr) == 0:
                    msg += 'All reports have been tended to.'
                else:
                    msg += 'There ' + ('is ' if len(curr) == 1 else 'are ') + str(len(curr)) \
                            + ' unhandled ' + ('report' if len(curr) == 1 else 'reports') \
                            + ', %s of which '%numIgnored \
                            + ('is' if numIgnored == 1 else 'are') + ' on your ignore list.'
                return msg
            else:
                if amount:
                    if not back:
                        good = good[:amount]
                    elif amount < len(good):
                        good = good[len(good) - amount:]
                goodIds = [v['name'] for v in good] if where != 'gutty' else good
                last = [v for v in curr if (v in goodIds) or (v in ignored)]

                db['last' + whichIL] = last
                db['ignored' + whichIL] = ignored
                if numIgnored:
                    msg += 'Skipped %s ignored %s. '%(numIgnored, _pluralize('report', numIgnored))
                report = _openLinks(good) if where != 'gutty' else _openGutty(good)
                if not good:
                    msg += 'All reports have been tended to.'
                else:
                    msg += 'Opened %s [report%s](%s).'%(len(good),'' if len(good) == 1 else 's', report)
                return msg


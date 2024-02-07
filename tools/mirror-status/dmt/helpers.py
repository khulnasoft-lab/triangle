#!/usr/bin/python3

import urllib
import psycopg2.extras
import errno
import json
import os
import re

if __name__ == '__main__' and __package__ is None:

    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
    import dmt.helpers
    __package__ = 'dmt.helpers'

import dmt.db as db

#FTPMASTER = "ftp-master.debian.org"
FTPMASTER = "repo.kali.org"

class BTSInfo:
    STATE_FILE = ".bugs-state.json"
    state = None

    @classmethod
    def _load_bts_state(cls):
        if cls.state is not None: return
        try:
            with open(cls.STATE_FILE) as data_file:
                cls.state = json.load(data_file)
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise
    @classmethod
    def bugs_for_mirror(cls, hostname):
        cls._load_bts_state()
        if cls.state is None: return []

        hn = re.escape(hostname)
        regex = '(^|\s|[:,;\[])%(hn)s(\s|$|[:,;\]])' % { 'hn': hn}
        p = re.compile(regex)

        yield from filter(lambda bug: p.search(bug['subject']), cls.state)

def get_baseurl(site):
    hn = site['name']
    if not site['http_override_host'] is None:
        hn = site['http_override_host']
    if not site['http_override_port'] is None:
        hn += ':%d'%(site['http_override_port'],)

    baseurl = urllib.parse.urljoin("http://" + hn, site['http_path'])
    if not baseurl.endswith('/'): baseurl += '/'
    return baseurl

def get_tracedir(site):
    baseurl = get_baseurl(site)
    tracedir = urllib.parse.urljoin(baseurl, 'project/trace/')
    return tracedir

def get_ftpmaster_trace(cur):
    """Get the most current trace file timestamp from ftpmaster
    """
    assert(isinstance(cur, psycopg2.extras.RealDictCursor))
    cur.execute("""
        SELECT trace_timestamp
        FROM mastertrace JOIN
            site ON site.id = mastertrace.site_id JOIN
            checkrun ON checkrun.id = mastertrace.checkrun_id
        WHERE
            site.name = %(site_name)s AND
            trace_timestamp IS NOT NULL
        ORDER BY
            timestamp DESC
        LIMIT 1
        """, {
            'site_name': FTPMASTER,
        })
    res = cur.fetchone()
    if res is None: return None
    return res['trace_timestamp']

def get_latest_checkrun(cur):
    """Get the most current checkrun
    """
    assert(isinstance(cur, psycopg2.extras.RealDictCursor))
    cur.execute("""
        SELECT id, timestamp
        FROM checkrun
        ORDER BY timestamp DESC
        LIMIT 1
        """)
    checkrun = cur.fetchone()
    return checkrun

def get_ftpmaster_traces_lastseen(cur):
    """For each trace timestamp from ftp-master, report when it was last seen on ftp-master
    """
    assert(isinstance(cur, psycopg2.extras.RealDictCursor))
    cur.execute("""
        SELECT
            checkrun.timestamp,
            mastertrace.trace_timestamp
        FROM checkrun JOIN
            mastertrace ON mastertrace.checkrun_id = checkrun.id JOIN
            site ON mastertrace.site_id = site.id
        WHERE
            site.name = %(ftpmastername)s AND
            mastertrace.trace_timestamp IS NOT NULL
        ORDER BY
            timestamp
        """, {
            'ftpmastername': FTPMASTER,
        })
    trace_timestamp_lastseen = {}
    for row in cur.fetchall():
        trace_timestamp_lastseen[row['trace_timestamp']] = row['timestamp']
    return trace_timestamp_lastseen

def hostname_comparator(hostname):
    return '.'.join(reversed(hostname.split('.')))

def get_bugs_for_mirror(hostname):
    yield from BTSInfo.bugs_for_mirror(hostname)

#!/usr/bin/python3

import argparse
import datetime
import json
import sys

import dmt.db as db
import dmt.helpers as helpers


OUTFILE = 'mirror-trace.html'


class Generator():
    def __init__(self, outfile, **kwargs):
        self.outfile = outfile
        self.template_name = 'mirror-trace.html'

    def get_pages(self, dbh):
        return [self]

    def prepare(self, dbh):
        cur = dbh.cursor()

        now = datetime.datetime.now(datetime.timezone.utc)
        checkrun = helpers.get_latest_checkrun(cur)
        if checkrun is None: return

        cur.execute("""
            SELECT DISTINCT ON (site.id)
                site.name,
                site.http_override_host,
                site.http_override_port,
                site.http_path,

                sitetrace.content->'upstream-mirror'->>'text' AS upstream,
                coalesce(sitetrace.content->'creator'->>'text', sitetrace.content->'used ftpsync version'->>'text') AS creator,
                sitetrace.content->'trigger'->>'text' AS trigger,
                sitetrace.content->'total time spent in rsync'->>'text' AS time_total,
                sitetrace.content->'architectures-configuration'->>'text' AS arches

            FROM
                sitetrace
                INNER JOIN site ON site.id = sitetrace.site_id
                INNER JOIN checkrun ON checkrun.id = sitetrace.checkrun_id
            WHERE
                checkrun.timestamp > CURRENT_TIMESTAMP - INTERVAL '1 day'
                AND sitetrace.content IS NOT NULL
            ORDER BY site.id, checkrun.timestamp DESC
            """)

        mirrors = []
        for row in cur.fetchall():
            row['trace_url'] = helpers.get_tracedir(row)
            mirrors.append(row)

        mirrors.sort(key=lambda m: helpers.hostname_comparator(m['name']))
        context = {
            'baseurl': '.',
            'mirrors': mirrors,
            'last_run': checkrun['timestamp'],
            'now': now,
        }
        self.context = context

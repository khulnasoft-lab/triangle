#!/usr/bin/python3

import argparse
import datetime
import itertools
import json
import sys
import os

if __name__ == '__main__' and __package__ is None:
    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
    import dmt.HierarchyGenerator
    __package__ = 'dmt.HierarchyGenerator'

import dmt.db as db
import dmt.helpers as helpers

class MirrorProcessor():
    def __init__(self, site, mastertraces_lastseen):
        self.site = site
        self.mastertraces_lastseen = mastertraces_lastseen

    def process(self, dbh):
        cur = dbh.cursor()
        cur2 = dbh.cursor()

        # Get all Checkruns for $site which have not been analyzed yet,
        # i.e., that don't have a corresponding entry in checkoverview yet.
        # Associated with each checkrun is the mastertrace and sitetrace
        # information, provided it's available.

        # This is not very efficient when there are a large number of unprocessed
        # checkruns per site.  But usually there will be exactly one.
        cur.execute("""
            SELECT
                checkrun.id as checkrun_id,
                checkrun.timestamp as checkrun_timestamp,

                mastertrace.id AS mastertrace_id,
                mastertrace.error AS mastertrace_error,
                mastertrace.trace_timestamp AS mastertrace_trace_timestamp,

                sitetrace.id AS sitetrace_id,
                sitetrace.error AS sitetrace_error,
                sitetrace.trace_timestamp AS sitetrace_trace_timestamp

            FROM checkrun LEFT OUTER JOIN
                (SELECT * FROM mastertrace WHERE site_id = %(site_id)s) AS mastertrace ON checkrun.id = mastertrace.checkrun_id LEFT OUTER JOIN
                (SELECT * FROM sitetrace   WHERE site_id = %(site_id)s) AS sitetrace   ON checkrun.id = sitetrace.checkrun_id
            WHERE
              -- Select check runs that have not been processed yet
                checkrun.id NOT in (SELECT checkrun_id FROM checkoverview WHERE site_id = %(site_id)s)
              AND
              -- assuming they are either newer than previously processed ones
                (checkrun.timestamp > (
                  SELECT max(checkrun.timestamp)
                  FROM checkrun
                    JOIN checkoverview
                    ON checkrun.id = checkoverview.checkrun_id
                  WHERE site_id = %(site_id)s
                  )
              -- or there is data.  This way new mirrors that don't have any data yet will not
              -- get a bunch of negative checkoverview entries.
                OR
                 mastertrace.id IS NOT NULL
                OR
                 sitetrace.id IS NOT NULL
                )
            ORDER BY
                checkrun.timestamp
            """, {
                'site_id': self.site['id'],
            })
#                traceset.id AS traceset_id,
#                traceset.error AS traceset_error,
#                traceset.traceset AS traceset_traceset

#                (SELECT * FROM mastertrace WHERE site_id = %(site_id)s) AS mastertrace ON checkrun.id = mastertrace.checkrun_id LEFT OUTER JOIN
#                (SELECT * FROM sitetrace   WHERE site_id = %(site_id)s) AS sitetrace   ON checkrun.id = sitetrace.checkrun_id LEFT OUTER JOIN
#                (SELECT * FROM traceset    WHERE site_id = %(site_id)s) AS traceset    ON checkrun.id = traceset.checkrun_id

#                (SELECT trace_timestamp
#                 FROM checkrun AS prev_checkrun LEFT OUTER JOIN
#                      sitetrace ON prev_checkrun.id = sitetrace.checkrun_id
#                 WHERE site_id = %(site_id)s AND prev_checkrun.timestamp < checkrun.timestamp
#                 ORDER BY prev_checkrun.timestamp DESC
#                 LIMIT 1) AS prev_sitetrace_trace_timestamp,
#                (SELECT trace_timestamp
#                 FROM checkrun AS prev_checkrun LEFT OUTER JOIN
#                      mastertrace ON prev_checkrun.id = mastertrace.checkrun_id
#                 WHERE site_id = %(site_id)s AND prev_checkrun.timestamp < checkrun.timestamp
#                 ORDER BY prev_checkrun.timestamp DESC
#                 LIMIT 1) AS prev_mastertrace_trace_timestamp

#            WHERE
#                checkrun.id NOT in (SELECT checkrun_id FROM checkoverview WHERE site_id = %(site_id)s)

        cache = {}
        for row in cur.fetchall():
            cur2.execute("""
                SELECT
                    sitealias.name as sitealias_name,

                    sitealiasmastertrace.id AS sitealiasmastertrace_id,
                    sitealiasmastertrace.error AS sitealiasmastertrace_error,
                    sitealiasmastertrace.trace_timestamp AS sitealiasmastertrace_trace_timestamp

                FROM sitealias LEFT OUTER JOIN
                    sitealiasmastertrace ON sitealias.id = sitealiasmastertrace.sitealias_id
                WHERE
                    site_id = %(site_id)s AND
                    checkrun_id = %(checkrun_id)s
                ORDER BY
                    sitealias.name
                """, {
                    'site_id': self.site['id'],
                    'checkrun_id': row['checkrun_id'],
                })
            aliases = {}
            for row2 in cur2.fetchall():
                if row2['sitealiasmastertrace_id'] is None:
                    continue
                d = {}
                if row2['sitealiasmastertrace_error'] is not None:
                    d['error'] = row2['sitealiasmastertrace_error']
                    d['ok'] = False
                elif row2['sitealiasmastertrace_trace_timestamp'] == row['mastertrace_trace_timestamp']:
                    d['ok'] = True
                else:
                    d['ok'] = True
                aliases[row2['sitealias_name']] = d
            aliases = json.dumps(aliases, separators=(',', ':'))

            errors = []
            for kind in ('master', 'site'):
                if row[kind+'trace_error'] is not None:
                    errors.append(kind+"trace: "+row[kind+'trace_error'])
                elif row[kind+'trace_trace_timestamp'] is None:
                    errors.append(kind+"trace unavailable")

            data = {}
            data['site_id'] = self.site['id']
            data['checkrun_id'] = row['checkrun_id']
            data['error'] = None
            data['version'] = None
            data['age'] = None
            data['aliases'] = aliases
            if len(errors) > 0:
                data['error'] = '; '.join(errors)
            else:
                if row['sitetrace_trace_timestamp'] in cache:
                    res = cache[row['sitetrace_trace_timestamp']]
                else:
                    # compute version and age
                    ##
                    # The version we think this mirror is at is the contents of the master tracefile
                    # the last time the site tracefile got updated, i.e., the earliest time the
                    # sitetrace existed.
                    #
                    # Only consider checkruns where we got both, a mastertrace and a sitetrace.
                    cur2.execute("""
                        SELECT
                            mastertrace.trace_timestamp AS mastertrace_trace_timestamp
                        FROM checkrun JOIN
                            (SELECT * FROM mastertrace WHERE site_id = %(site_id)s) AS mastertrace ON checkrun.id = mastertrace.checkrun_id JOIN
                            (SELECT * FROM sitetrace   WHERE site_id = %(site_id)s) AS sitetrace   ON checkrun.id = sitetrace.checkrun_id
                        WHERE
                            sitetrace.trace_timestamp = %(sitetrace_trace_timestamp)s AND
                            mastertrace.trace_timestamp IS NOT NULL
                        ORDER BY
                            checkrun.timestamp ASC
                        LIMIT 1
                        """, {
                            'site_id': self.site['id'],
                            'sitetrace_trace_timestamp': row['sitetrace_trace_timestamp']
                        })
                    res = cur2.fetchone()
                    cache[row['sitetrace_trace_timestamp']] = res
                if res is None:
                    data['error'] = 'mastertrace validity uncertain'
                else:
                    data['version'] = res['mastertrace_trace_timestamp']

                    if data['version'] in self.mastertraces_lastseen:
                        if self.mastertraces_lastseen[data['version']] > row['checkrun_timestamp']:
                            data['age'] = datetime.timedelta(0)
                        else:
                            data['age'] = row['checkrun_timestamp'] - self.mastertraces_lastseen[data['version']]
                    else:
                        data['error'] = 'unexpected mirror version: ' + str(data['version'])
            cur2.execute("""INSERT INTO checkoverview (site_id, checkrun_id, error, version, age, aliases)
                            VALUES (%(site_id)s, %(checkrun_id)s, %(error)s, %(version)s, %(age)s, %(aliases)s)""",
                         data)
        dbh.commit()

class Processor():
    @staticmethod
    def process(dbh):
        cur = dbh.cursor()
        mastertraces_lastseen = helpers.get_ftpmaster_traces_lastseen(cur)

        cur.execute("""
            SELECT
                site.id,
                site.name
            FROM site
            """)
        for site in cur.fetchall():
            yield MirrorProcessor(site = site, mastertraces_lastseen = mastertraces_lastseen)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dburl', help='database', default=db.MirrorDB.DBURL)
    args = parser.parse_args()

    dbh = db.RawDB(args.dburl)
    for x in Processor.process(dbh):
        x.process(dbh)

if __name__ == "__main__":
    main()

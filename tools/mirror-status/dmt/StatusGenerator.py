#!/usr/bin/python3

import argparse
import datetime
import sys

if __name__ == '__main__' and __package__ is None:
    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
    import dmt.StatusGenerator
    __package__ = 'dmt.StatusGenerator'

import dmt.db as db
import dmt.helpers as helpers

class Generator():
    def __init__(self, outfile, **kwargs):
        self.outfile = outfile
        self.template_name = 'mirror-status.html'

    def get_pages(self, dbh):
        return [self]

    def prepare(self, dbh):
        cur = dbh.cursor()

        now = datetime.datetime.now(datetime.timezone.utc)
        ftpmastertrace = helpers.get_ftpmaster_trace(cur)
        if ftpmastertrace is None: ftpmastertrace = now
        checkrun = helpers.get_latest_checkrun(cur)
        if checkrun is None: return

        cur.execute("""
            SELECT
                site.name,
                site.http_override_host,
                site.http_override_port,
                site.http_path,

                checkoverview.error AS checkoverview_error,
                checkoverview.age AS checkoverview_age,
                checkoverview.score AS checkoverview_score,
                checkoverview.aliases AS checkoverview_aliases,

                mastertrace.error AS mastertrace_error,
                mastertrace.trace_timestamp AS mastertrace_trace_timestamp,

                sitetrace.error AS sitetrace_error,
                sitetrace.trace_timestamp AS sitetrace_trace_timestamp,
                sitetrace.content AS sitetrace_content,

                traceset.id AS traceset_id,
                traceset.error AS traceset_error,
                traceset.traceset AS traceset_traceset,

                runs_per_day.runs_per_day,

                max_age.avg    AS max_age_avg,
                max_age.stddev AS max_age_stddev

            FROM site JOIN
                checkoverview ON site.id = checkoverview.site_id LEFT OUTER JOIN
                mastertrace ON site.id = mastertrace.site_id LEFT OUTER JOIN
                sitetrace     ON site.id = sitetrace.site_id LEFT OUTER JOIN
                traceset      ON site.id = traceset.site_id LEFT OUTER JOIN
                (
                 SELECT num_runs / days AS runs_per_day,
                        site_id
                 FROM (
                  SELECT COUNT(distinct trace_timestamp) AS num_runs,
                         EXTRACT(epoch from CURRENT_TIMESTAMP - MIN(checkrun.timestamp))/24/3600 AS days,
                         sitetrace.site_id
                  FROM sitetrace JOIN
                       checkrun ON sitetrace.checkrun_id = checkrun.id
                  WHERE sitetrace.trace_timestamp IS NOT NULL AND
                        checkrun.timestamp > CURRENT_TIMESTAMP - INTERVAL '2 week'
                  GROUP BY sitetrace.site_id) AS sub
                ) AS runs_per_day ON site.id = runs_per_day.site_id  LEFT OUTER JOIN
                (
                 SELECT
                        site_id,
                        AVG(max_age) AS avg,
                        STDDEV_SAMP(extract('epoch' from max_age)) as stddev
                  FROM
                        (SELECT
                                site_id,
                                CASE WHEN age > lead(age) OVER (PARTITION BY site_id ORDER BY checkrun.timestamp)
                                     THEN age END AS max_age
                                FROM checkrun LEFT OUTER JOIN
                                     checkoverview ON checkrun.id = checkoverview.checkrun_id
                                WHERE checkrun.timestamp > CURRENT_TIMESTAMP - INTERVAL '2 week'
                        ) AS SUB
                          GROUP BY site_id
                 ) as max_age ON site.id = max_age.site_id
            WHERE
                (checkoverview.checkrun_id = %(checkrun_id)s) AND
                (mastertrace  .checkrun_id = %(checkrun_id)s OR mastertrace.checkrun_id IS NULL) AND
                (sitetrace    .checkrun_id = %(checkrun_id)s OR sitetrace.checkrun_id IS NULL) AND
                (traceset     .checkrun_id = %(checkrun_id)s OR traceset.checkrun_id IS NULL)
            """, {
                'checkrun_id': checkrun['id']
            })

        mirrors = []
        traceset_elem_ctr = {}
        for row in cur.fetchall():
            row['trace_url'] = helpers.get_tracedir(row)

            mastertrace_trace_timestamp = row['mastertrace_trace_timestamp']
            if mastertrace_trace_timestamp is not None:
                row['mastertrace_trace_age'] = ftpmastertrace - mastertrace_trace_timestamp
            else:
                row['mastertrace_trace_age'] = None
            sitetrace_trace_timestamp = row['sitetrace_trace_timestamp']
            if sitetrace_trace_timestamp is not None:
                row['sitetrace_trace_age'] = now - sitetrace_trace_timestamp
            else:
                row['sitetrace_trace_age'] = None

            if row['traceset_traceset'] is not None:
                if not isinstance(row['traceset_traceset'], list):
                    raise Exception("Hmm.  traceset_traceset for site %s(%s) is not a list"%(row['id'], row['name']))
                for traceset_elem in row['traceset_traceset']:
                    traceset_elem_ctr[traceset_elem] = traceset_elem_ctr.get(traceset_elem, 0) + 1

            row['aliases' ] = row['checkoverview_aliases']
            row['bugs'] = helpers.get_bugs_for_mirror(row['name'])

            if row['sitetrace_content'] is not None:
                row['sitetrace_content'] = dict(
                  (key
                      .replace(" ", "_")
                      .replace("-", "_")
                  , value) for (key, value) in row['sitetrace_content'].items())

            mirrors.append(row)

        for m in mirrors:
            if m['traceset_traceset'] is not None:
                assert(isinstance(m['traceset_traceset'], list))
                if 'master' in m['traceset_traceset']:
                    m['traceset_traceset'].remove('master')
                m['traceset_traceset'].sort(key=lambda traceset_elem: -traceset_elem_ctr.get(traceset_elem, 0))
                m['traceset_traceset_sorter'] = ':'.join([helpers.hostname_comparator(h) for h in m['traceset_traceset']])
            else:
                m['traceset_traceset_sorter'] = '??:'+helpers.hostname_comparator(m['name'])

        mirrors.sort(key=lambda m: helpers.hostname_comparator(m['name']))
        context = {
            'baseurl': '.',
            'mirrors': mirrors,
            'last_run': checkrun['timestamp'],
            'ftpmastertrace': ftpmastertrace,
            'allsitenames': set([row['name'] for row in mirrors]),
            'now': now,
        }
        self.context = context

OUTFILE='mirror-status.html'

if __name__ == "__main__":
    from dmt.BasePageRenderer import BasePageRenderer

    parser = argparse.ArgumentParser()
    parser.add_argument('--dburl', help='database', default=db.RawDB.DBURL)
    parser.add_argument('--templatedir', help='template directory', default='templates')
    parser.add_argument('--outfile', help='output-file', default=OUTFILE, type=argparse.FileType('w'))
    args = parser.parse_args()

    base = BasePageRenderer(**args.__dict__)
    dbh = db.RawDB(args.dburl)
    g = Generator(**args.__dict__)
    for x in g.get_pages(dbh):
        x.prepare(dbh)
        base.render(x)

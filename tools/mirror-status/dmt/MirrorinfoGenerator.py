#!/usr/bin/python3

import argparse
import datetime
import itertools
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

OUTFILE='mirror-info'
HISTORY_HOURS=24*7


class MirrorReport():
    def __init__(self,
            site, allsitenames,
            mastertraces_lastseen,
            traceset_elem_ctr,
            history_hours=HISTORY_HOURS, outfile=OUTFILE, **kwargs):
        self.outfile = outfile
        self.site = site
        self.allsitenames = allsitenames
        self.history_hours = history_hours
        self.mastertraces_lastseen = mastertraces_lastseen
        self.traceset_elem_ctr = traceset_elem_ctr
        self.template_name = 'mirror-report.html'

    def prepare(self, dbh):
        cur = dbh.cursor()
        cur2 = dbh.cursor()

        now = datetime.datetime.now()
        checkrun = helpers.get_latest_checkrun(cur)
        check_age_cutoff = now - datetime.timedelta(hours=self.history_hours)

        cur.execute("""
            SELECT
                checkrun.timestamp as checkrun_timestamp,

                mastertrace.id AS mastertrace_id,
                mastertrace.error AS mastertrace_error,
                mastertrace.trace_timestamp AS mastertrace_trace_timestamp,

                sitetrace.id AS sitetrace_id,
                sitetrace.error AS sitetrace_error,
                sitetrace.trace_timestamp AS sitetrace_trace_timestamp,
                encode(digest(sitetrace.full, 'sha256'), 'hex') as sitetrace_trace_digest,
                sitetrace.archive_update_in_progress AS sitetrace_archive_update_in_progress,
                sitetrace.archive_update_required AS sitetrace_archive_update_required,

                traceset.id AS traceset_id,
                traceset.error AS traceset_error,
                traceset.traceset AS traceset_traceset,

                checkoverview.id AS checkoverview_id,
                checkoverview.error AS checkoverview_error,
                checkoverview.version AS checkoverview_version,
                checkoverview.age AS checkoverview_age,
                checkoverview.aliases AS checkoverview_aliases,
                checkoverview.score AS checkoverview_score

            FROM checkrun LEFT OUTER JOIN
                (SELECT * FROM mastertrace   WHERE site_id = %(site_id)s) AS mastertrace   ON checkrun.id = mastertrace.checkrun_id LEFT OUTER JOIN
                (SELECT * FROM sitetrace     WHERE site_id = %(site_id)s) AS sitetrace     ON checkrun.id = sitetrace.checkrun_id LEFT OUTER JOIN
                (SELECT * FROM traceset      WHERE site_id = %(site_id)s) AS traceset      ON checkrun.id = traceset.checkrun_id LEFT OUTER JOIN
                (SELECT * FROM checkoverview WHERE site_id = %(site_id)s) AS checkoverview ON checkrun.id = checkoverview.checkrun_id
            WHERE
                checkrun.timestamp >= %(check_age_cutoff)s
              AND
                (
                mastertrace.id IS NOT NULL
                OR
                sitetrace.id IS NOT NULL
                OR
                traceset.id IS NOT NULL
                OR
                checkoverview.id IS NOT NULL
                )
            ORDER BY
                checkrun.timestamp
            """, {
                'check_age_cutoff': check_age_cutoff,
                'site_id': self.site['id'],
            })

        track_items = ['mastertrace_trace_timestamp', 'sitetrace_trace_timestamp', 'checkoverview_version']
        prev = {x: None for x in track_items}
        checks = []
        for row in cur.fetchall():
            for x in track_items:
                if row[x] is not None:
                    if prev[x] is not None and prev[x] != row[x]:
                        row[x+'_changed'] = True
                    prev[x] = row[x]
            if row['traceset_traceset'] is not None:
                if not isinstance(row['traceset_traceset'], list):
                    raise Exception("Hmm.  traceset_traceset for traceset_id %s is not a list"%(row['traceset_id'], ))
                if 'master' in row['traceset_traceset']:
                    row['traceset_traceset'].remove('master')
                row['traceset_traceset'].sort(key=lambda traceset_elem: -self.traceset_elem_ctr.get(traceset_elem, 0))
            row['aliases' ] = row['checkoverview_aliases']
            checks.append(row)

        context = {
            'baseurl': '..',
            'now': now,
            'last_run': checkrun['timestamp'],
            'checks': reversed(checks),
            'allsitenames': self.allsitenames,
        }
        context['site'] = {
            'name'     : self.site['name'],
            'base_url' : helpers.get_baseurl(self.site),
            'trace_url': helpers.get_tracedir(self.site),
            'bugs'     : helpers.get_bugs_for_mirror(self.site['name']),
        }

        self.context = context



class Generator():
    def __init__(self, outfile = OUTFILE, **kwargs):
        self.outfile = outfile

    def get_pages(self, dbh):
        outdir = self.outfile
        if not os.path.isdir(outdir):
            os.mkdir(outdir)

        cur = dbh.cursor()
        mastertraces_lastseen = helpers.get_ftpmaster_traces_lastseen(cur)

        sites = {}
        cur.execute("""
            SELECT
                site.id,
                site.name,
                site.http_override_host,
                site.http_override_port,
                site.http_path,

                traceset.traceset::jsonb AS traceset_traceset
            FROM site LEFT JOIN
                (
                 SELECT *
                   FROM traceset
                   WHERE checkrun_id = (SELECT id FROM checkrun ORDER BY checkrun.timestamp LIMIT 1)
                ) AS traceset ON site.id = traceset.site_id
            """)

        traceset_elem_ctr = {}
        for row in cur.fetchall():
            sites[row['name']] = row
            if row['traceset_traceset'] is not None:
                if not isinstance(row['traceset_traceset'], list):
                    raise Exception("Hmm.  traceset_traceset for site %s(%s) is not a list"%(row['id'], row['name']))
                for traceset_elem in row['traceset_traceset']:
                    traceset_elem_ctr[traceset_elem] = traceset_elem_ctr.get(traceset_elem, 0) + 1

        for site in sites.values():
            of = os.path.join(outdir, site['name'] + '.html')
            i = MirrorReport(
                    base=self,
                    outfile=of,
                    site=site,
                    allsitenames=list(sites.keys()),
                    mastertraces_lastseen=mastertraces_lastseen,
                    traceset_elem_ctr=traceset_elem_ctr)
            yield i


if __name__ == "__main__":
    from dmt.BasePageRenderer import BasePageRenderer

    parser = argparse.ArgumentParser()
    parser.add_argument('--dburl', help='database', default=db.MirrorDB.DBURL)
    parser.add_argument('--templatedir', help='template directory', default='templates')
    parser.add_argument('--outfile', help='output-dir', default=OUTFILE)
    args = parser.parse_args()

    base = BasePageRenderer(**args.__dict__)
    dbh = db.RawDB(args.dburl)
    g = Generator(**args.__dict__)
    for x in g.get_pages(dbh):
        x.prepare(dbh)
        base.render(x)

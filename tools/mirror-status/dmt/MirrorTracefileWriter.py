#!/usr/bin/python3

import argparse
import os
import hashlib
import sys
import errno

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

    def get_pages(self, dbh):
        outdir = self.outfile
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        return [self]

    def prepare(self, dbh):
        cur = dbh.cursor()

        cur.execute("""
            SELECT sitetrace.full,  extract('epoch' from max(trace_timestamp)) AS ts FROM sitetrace WHERE sitetrace.full IS NOT NULL GROUP BY sitetrace.full

            """, {
            })

        for row in cur.fetchall():
            full = row['full']
            digest = hashlib.sha256(full.encode('utf-8')).hexdigest()
            dstdir = self.outfile+'/'+digest[:2]
            try:
                os.mkdir(dstdir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            dstfile = dstdir + '/' + digest + '.txt'
            with open(dstfile, "w", encoding='utf-8') as f:
                f.write(full)
            if row['ts'] is not None:
                os.utime(dstfile, (row['ts'], row['ts']))

    # nop, we did everything during prepare
    def render(self):
        pass

OUTFILE='mirror-traces'

if __name__ == "__main__":
    from dmt.BasePageRenderer import BasePageRenderer

    parser = argparse.ArgumentParser()
    parser.add_argument('--dburl', help='database', default=db.RawDB.DBURL)
    parser.add_argument('--templatedir', help='template directory', default='templates')
    parser.add_argument('--outfile', help='output-dir', default=OUTFILE)
    args = parser.parse_args()

    base = BasePageRenderer(**args.__dict__)
    dbh = db.RawDB(args.dburl)
    g = Generator(**args.__dict__)
    for x in g.get_pages(dbh):
        x.prepare(dbh)
        base.render(x)

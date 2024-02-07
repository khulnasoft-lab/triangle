#!/usr/bin/python3

import argparse
import datetime
import itertools
import json
import sys
import os

# ignore checkrun for scoring purposes if more than this fraction
# of checks resulted in errors
IGNORE_RUN_THRESHOLD = 0.7

if __name__ == '__main__' and __package__ is None:
    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
    import dmt.HierarchyGenerator
    __package__ = 'dmt.HierarchyGenerator'

import dmt.db as db
import dmt.helpers as helpers

class CheckrunScorer():
    def __init__(self, checkrun):
        self.checkrun = checkrun

    def process(self, dbh):
        cur = dbh.cursor()
        cur2 = dbh.cursor()

        cur.execute("""
            SELECT
                count(*) AS total,
                count(error) AS errors
            FROM checkoverview
            WHERE
                checkoverview.checkrun_id = %(checkrun_id)s
            """, {
                'checkrun_id': self.checkrun['id'],
            })
        counts = cur.fetchone()
        ignore_this_run = counts['total'] > 0 and float(counts['errors'])/counts['total'] > IGNORE_RUN_THRESHOLD
        #if ignore_this_run:
        #    print("IGNORING THIS RUN for scoring purposes:", counts['errors'], "out of", counts['total'], "failed.")

        cur.execute("""
            SELECT
                checkoverview.site_id AS site_id,
                checkoverview.id      AS checkoverview_id,
                checkoverview.error   AS checkoverview_error,
                checkoverview.age     AS checkoverview_age

            FROM checkoverview
            WHERE
                checkoverview.checkrun_id = %(checkrun_id)s AND
                checkoverview.score IS NULL
            """, {
                'checkrun_id': self.checkrun['id'],
            })

        #print(self.checkrun['timestamp'])
        for row in cur.fetchall():
            # Get the previous score for this mirror
            cur2.execute("""
                SELECT
                    checkrun.id         AS checkrun_id,
                    checkrun.timestamp  AS checkrun_timestamp,

                    checkoverview.score AS checkoverview_score
                FROM checkrun JOIN
                    checkoverview ON checkrun.id = checkoverview.checkrun_id
                WHERE
                    checkoverview.site_id = %(site_id)s AND
                    checkrun.timestamp < %(this_checkrun_timestamp)s
                ORDER BY
                    checkrun.timestamp DESC
                LIMIT 1
                """, {
                    'site_id': row['site_id'],
                    'this_checkrun_timestamp': self.checkrun['timestamp']
                })
            prev = cur2.fetchone()

            if prev is None:
                score = 0.0
                delta = 300 # pick some arbitrary time delta for the first weight
            else:
                score = prev['checkoverview_score']
                if score is None:
                    raise Exception("Previous score is NULL; that makes no sense")
                delta = (self.checkrun['timestamp'] - prev['checkrun_timestamp']).total_seconds()
            weight = float(delta)/(3600*24)

            if ignore_this_run:
                adj = 0
            elif row['checkoverview_error'] is not None:
                adj = -30
            elif row['checkoverview_age'] <= datetime.timedelta(hours = 4):
                adj = +5
            elif row['checkoverview_age'] <= datetime.timedelta(hours = 12):
                adj = +1
            elif row['checkoverview_age'] <= datetime.timedelta(hours = 24):
                adj = 0
            elif row['checkoverview_age'] <= datetime.timedelta(hours = 48):
                adj = -5
            else:
                adj = -30

            score += float(adj) * weight
            if   score >  100: score = 100
            elif score < -100: score = -100
            #print(self.checkrun['timestamp'], "Mirror is ", row['checkoverview_age'], "old.  Adjusting score by", adj, "; weighted:", float(adj) * weight, "; new score is", score)

            cur2.execute("""UPDATE checkoverview SET score = %(score)s WHERE id=%(checkoverview_id)s""",
                         {'checkoverview_id': row['checkoverview_id'],
                          'score': score}
                        )
        dbh.commit()

class Scorer():
    @staticmethod
    def process(dbh):
        cur = dbh.cursor()
        cur.execute("""
            SELECT
                id,
                timestamp
            FROM checkrun
            WHERE EXISTS
              (SELECT * FROM checkoverview WHERE checkoverview.checkrun_id=checkrun.id AND score IS NULL)
            ORDER BY
                timestamp ASC
            """)
        for checkrun in cur.fetchall():
            yield CheckrunScorer(checkrun = checkrun)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dburl', help='database', default=db.MirrorDB.DBURL)
    args = parser.parse_args()

    dbh = db.RawDB(args.dburl)
    for x in Scorer.process(dbh):
        x.process(dbh)

if __name__ == "__main__":
    main()

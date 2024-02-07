#!/usr/bin/python3

import argparse
import datetime
import itertools
import sys

if __name__ == '__main__' and __package__ is None:
    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
    import dmt.HierarchyGenerator
    __package__ = 'dmt.HierarchyGenerator'

import dmt.db as db
import dmt.helpers as helpers


OUTFILE='mirror-hierarchy.html'
RECENTCHANGE_HOURS=24*2

def powersetish(iterable):
    """return the powerset of iterable, from longest subset to smallest
    """
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s), -1, -1))

def iter_endcheck(iterable):
    """iterate over an iterable, and for each element i yield a tuples of (i, whether i is the last element)
    """
    it = iter(iterable)
    prev = next(it)
    for val in it:
        yield prev, False
        prev = val
    yield prev, True


class HierarchyNode:
    def __init__(self, labels, parent):
        assert(isinstance(labels, tuple))
        self.names = []
        self.labels = labels
        self.parent = parent
        self.children = []
        if parent is not None:
            parent.children.append(self)
            self.labelsdiff = set(labels) - set(parent.labels)
            #print("Parent is ", parent.labels, "and has children", (', '.join(str(x.labelsdiff) for x in parent.children)))
        else:
            self.labelsdiff = set(labels)

class HierarchyTree:
    def __init__(self):
        self.nodes_by_labels = {}

        root = HierarchyNode((), None)
        self.root = root
        root.parent = root
        self.nodes_by_labels[root.labels] = root

    def _find_position(self, labels):
        for s in powersetish(labels):
            if s in self.nodes_by_labels:
                return self.nodes_by_labels[s]
        raise Exception("We should have found at least the root by now.  (Was looking for "+str(labels)+")")

    def _add_node(self, name, labels):
        #print("Adding node", name)
        if labels in self.nodes_by_labels:
            node = self.nodes_by_labels[labels]
        else:
            parent = self._find_position(labels)
            assert(parent is not None)
            assert(parent.labels != labels)

            node = HierarchyNode(labels, parent)
            self.nodes_by_labels[labels] = node

        node.names.append(name)
        return node

    def add_nodes(self, tuples):
        #for name, labels in sorted(tuples, key=lambda t: [len(t[1])] + list(reversed(t[0].split('.')))):
        for name, labels in sorted(tuples, key=lambda t: len(t[1])):
            #print("Calling add_node for", name, "with lables", labels)
            n = self._add_node(name, labels)

    @staticmethod
    def _str_subtree(prefix, last, node):
        yield prefix+('+','\\')[last]+'-- '+str(node.labelsdiff)
        prefix = prefix+('|',' ')[last]+'  '

        for name in node.names:
            yield prefix+(' ','|')[len(node.children)>0] +'    + '+name
        for c, last in iter_endcheck(node.children):
            yield from HierarchyTree._str_subtree(prefix, last, c)

    def __str__(self):
        return "\n".join(self._str_subtree("", True, self.root))


    @staticmethod
    def nodelabeldomain_comparator(x):
        if len(x.labelsdiff) == 0: return None
        hostname = sorted(x.labelsdiff)[0]
        return helpers.hostname_comparator(hostname)

    @staticmethod
    def _table_subtree(node):
        #print(node.labels, "has children", (', '.join(str(x.labelsdiff) for x in node.children)))
        child_cells = list(itertools.chain.from_iterable(HierarchyTree._table_subtree(c) for c in sorted(node.children, key=HierarchyTree.nodelabeldomain_comparator)))
        number_terminals = sum(c['celltype'] == 'terminal' for c in child_cells)

        cell = { 'celltype': 'middle',
                 'entrytype': 'labels-only',
                 'labels': sorted(node.labelsdiff, key=helpers.hostname_comparator),
                 'width' : len(node.labelsdiff)
               }

        names = sorted(node.names)
        if len(node.labelsdiff) == 1:
            nodename = next(iter(node.labelsdiff)) # get the only element from the set
            if nodename in names:
                names.remove(nodename)
                cell['entrytype'] = 'site'
                cell['name'] = nodename
                cell['main'] = True
                cell['celltype'] = ['middle', 'terminal'][len(names) == 0 and number_terminals == 0]
        cell['height'] = max(len(names) + number_terminals, 1)
        yield cell

        for name in names:
            cell = { 'celltype': 'terminal',
                     'entrytype': 'site',
                     'name': name,
                     'main': False,
                     'height': 1,
                     'width' : 1,
                   }
            yield cell
        yield from child_cells

    def table(self):
        yield from self._table_subtree(self.root)


class MirrorHierarchy:
    def __init__(self, mirrors):
        self.mirrors = mirrors

        sitelabels = [(site, tuple(mirrors[site]['traces'])) for site in mirrors]

        self.tree = HierarchyTree()
        self.tree.add_nodes(sitelabels)
        #print(t)
        #for x in t.table():
        #    print(x)
    def get_cells(self):
        for c in self.tree.table():
            if c['entrytype'] == 'site':
                c['mirror'] = self.mirrors[c['name']]
            yield c

def get_traceset_changes(cur, site_id, traces_last_change_cutoff):
    cur.execute("""
        SELECT
            traceset.traceset,
            checkrun.timestamp
        FROM traceset JOIN
            checkrun  ON traceset.checkrun_id = checkrun.id
        WHERE
            traceset.site_id = %(site_id)s AND
            traceset.traceset IS NOT NULL AND
            checkrun.timestamp >= %(traces_last_change_cutoff)s
        ORDER BY
            checkrun.timestamp
        """, {
            'site_id': site_id,
            'traces_last_change_cutoff': traces_last_change_cutoff,
        })

    it = iter(cur.fetchall())
    last_ts = None
    try:
        last_ts = next(it)
    except StopIteration:
        pass
    cnt = 0
    last_change = None
    for i in it:
        if last_ts['traceset'] != i['traceset']:
            last_change = i['timestamp']
            cnt += 1
        last_ts = i

    res = { 'cnt': cnt,
            'last_change': last_change,
            'most_recent': last_ts['traceset'] if last_ts is not None else None,
          }
    return res

class Generator():
    def __init__(self, outfile = OUTFILE, textonly = False, recent_hours = RECENTCHANGE_HOURS, **kwargs):
        self.outfile = outfile
        self.recent_hours = recent_hours
        self.textonly = textonly
        self.template_name = 'mirror-hierarchy.html'

    def get_pages(self, dbh):
        if self.textonly:
            self.prepare(dbh)
            return []
        else:
            return [self]

    def prepare(self, dbh):
        cur = dbh.cursor()
        cur2 = dbh.cursor()

        now = datetime.datetime.now()
        checkrun = helpers.get_latest_checkrun(cur)
        if checkrun is None: return
        traces_last_change_cutoff = now - datetime.timedelta(hours=self.recent_hours)

        cur.execute("""
            SELECT DISTINCT ON (site.id)
                site.id AS site_id,
                site.name,
                site.http_override_host,
                site.http_override_port,
                site.http_path,

                checkoverview.error AS checkoverview_error,
                checkoverview.age AS checkoverview_age,
                checkoverview.aliases AS checkoverview_aliases,

                traceset.id AS traceset_id,
                traceset.error AS traceset_error,
                traceset.traceset AS traces

            FROM
                site
                LEFT OUTER JOIN traceset ON site.id = traceset.site_id
                LEFT OUTER JOIN checkoverview ON site.id = checkoverview.site_id
                INNER JOIN checkrun ON checkrun.id = traceset.checkrun_id AND checkrun.id = checkoverview.checkrun_id
            WHERE
                checkrun.timestamp > CURRENT_TIMESTAMP - INTERVAL '%(recent_hours)s hours'
            ORDER BY
                site.id,
                traceset.traceset IS NULL ASC,
                checkrun.timestamp DESC
            """ % {
                'recent_hours': self.recent_hours,
            })

        mirrors = {}
        for row in cur.fetchall():
            row['site_trace_url'] = helpers.get_tracedir(row)
            error = []

            error.append(row['traceset_error'])
            if row['traceset_id'] is None: error.append("No traceset information")
            error.append(row['checkoverview_error'])
            row['error'] = "; ".join(filter(lambda x: x is not None, error))
            if row['error'] == "": row['error'] = None

            row['traceset_changes'] = get_traceset_changes(cur2, row['site_id'], traces_last_change_cutoff)

            if row['traces'] is not None:
                try:
                    row['traces'].remove('master')
                except ValueError:
                    msg = 'Traceset missing master item'
                    if row['error']:
                        row['error'] = row['error'] + "; " + msg
                    else:
                        row['error'] = msg
            else:
                row['traces'] = []

            row['aliases' ] = row['checkoverview_aliases']

            mirrors[row['name']] = row
        hierarchy =  MirrorHierarchy(mirrors)

        if self.textonly:
            print(hierarchy.tree)
            #for x in hierarchy.get_cells():
            #    print(x)
        else:
            cells = list(hierarchy.get_cells())
            del cells[0]
            cells[-1]['last'] = True

            self.context = {
                'baseurl': '.',
                'now': now,
                'last_run': checkrun['timestamp'],
                'hierarchy_table': cells,
                'recent_hours': self.recent_hours,
            }


if __name__ == "__main__":
    from dmt.BasePageRenderer import BasePageRenderer

    parser = argparse.ArgumentParser()
    parser.add_argument('--dburl', help='database', default=db.MirrorDB.DBURL)
    parser.add_argument('--templatedir', help='template directory', default='templates')
    parser.add_argument('--textonly', help='only write text to stdout', default=False, action='store_true')
    parser.add_argument('--recent-hours', help='flag mirrors that changed hierarchy within the last <x> hours', type=float, default=RECENTCHANGE_HOURS)
    parser.add_argument('--outfile', help='output-file', default=OUTFILE)
    args = parser.parse_args()

    base = BasePageRenderer(**args.__dict__)
    dbh = db.RawDB(args.dburl)
    g = Generator(**args.__dict__)
    for x in g.get_pages(dbh):
        x.prepare(dbh)
        base.render(x)

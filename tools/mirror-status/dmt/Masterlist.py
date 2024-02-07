#!/usr/bin/python3

# Copyright 2016, 2017 Peter Palfrader
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Load a debian Mirrors.masterlist

from collections import OrderedDict
import email
import sys

class MasterlistEntry:
    MULTI_VALUE_FIELDS = ('Alias', 'Candidate', 'Sponsor', 'Provides')

    def __init__(self, lines):
        self.data = email.message_from_string('\n'.join(lines))
        self._clean()
    def __str__(self):
        return self.data.__str__()
    def __getitem__(self, key):
        if key in self.MULTI_VALUE_FIELDS:
            return self.data.get_all(key)
        else:
            return self.data[key]
    def __setitem__(self, key, data):
        del self.data[key]
        self.data[key] = data
    def __contains__(self, key):
        return key in self.data
    def _clean(self):
        if not 'Site' in self.data:
            print("Missing sitename for mirror.", file=sys.stderr)
        for key in self.data:
            v = self.data.get_all(key)
            if len(v) > 1 and not key in self.MULTI_VALUE_FIELDS:
                print("Warning:", self.data['Site'], "multiple values for", key, file=sys.stderr)
        for key in self.MULTI_VALUE_FIELDS:
            if key in self.data:
                s = set(self[key])
                if len(s) != len(self[key]):
                    print("Warning:", self.data['Site'], "duplicate values in", key, file=sys.stderr)

    def _add_included_by(self, alias):
        self.data['Provides'] = alias # This *adds* an alias; it does not overwrite existing ones

    @staticmethod
    def from_fh(fh):
        m = []
        for line in fh:
            line = line.strip()
            if line == "":
                if len(m) > 0: break
            else:
                m.append(line)

        if len(m) > 0: return MasterlistEntry(m)
        return None

class Masterlist:
    def __init__(self, fn, ignore_geodns=True):
        self._load_entries(fn, ignore_geodns)

    def _load_entries(self, fn, ignore_geodns):
        seen = {}
        includes = OrderedDict()
        entries = OrderedDict()
        with open(fn, encoding='utf-8') as masterlist:
            while True:
                e = MasterlistEntry.from_fh(masterlist)
                if e is None: break
                if not 'Site' in e:
                    print("Mirror is lacking sitename: skipping", file=sys.stderr)
                    continue

                if e['Site'] in seen:
                    print("Duplicate site", e['Site'], "- dropping.", file=sys.stderr)
                    continue

                seen[e['Site']] = True
                if e['Type'] in ('GeoDNS', ) and ignore_geodns:
                    pass
                elif 'Includes' in e:
                    includes[e['Site']] = e
                else:
                    entries[e['Site']] = e

        for alias in includes:
            for site in includes[alias]['Includes'].split():
                if not site in entries:
                    print("Site", alias, "is allegedly provided by", site,"but we do not know about that.", file=sys.stderr)
                    continue
                entries[site]._add_included_by(alias)

        self.entries = entries
        self.includes = includes

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('masterlist', help='Mirrors.masterlist.in file')
    args = parser.parse_args()

    masterlist = Masterlist(args.masterlist)
    for site in masterlist.entries:
        print('Site:', site)
        #e.fetch_traces()

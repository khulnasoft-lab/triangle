#!/usr/bin/python3

import dateutil.relativedelta
import datetime
import jinja2

if __name__ == '__main__' and __package__ is None:
    from pathlib import Path
    top = Path(__file__).resolve().parents[1]
    sys.path.append(str(top))
    import dmt.BasePageRenderer
    __package__ = 'dmt.BasePageRenderer'

import dmt.db as db
from dmt import helpers

#CONTACT_EMAIL = 'mirrors@d.o'
#DISTRO = 'Debian'
CONTACT_EMAIL = 'devel@k.o'
DISTRO = 'Kali Linux'

def get_human_readable_age(ts, base):
    assert(ts is not None)
    assert(base is not None)

    if base < ts:
        rounding_skew = datetime.timedelta(seconds = 30)
    elif base > ts:
        rounding_skew = datetime.timedelta(seconds = -30)
    else:
        rounding_skew = datetime.timedelta(0)
    rd = dateutil.relativedelta.relativedelta(base, ts + rounding_skew)
    attrs = [('years', 'y'), ('months', 'm'), ('days', 'd'), ('hours', 'h'), ('minutes', 'min')]
    elems = ['%d %s' % (getattr(rd, attr), text) for attr, text in attrs if getattr(rd, attr)]

    hr = ', '.join(elems[0:2])
    if hr == "": hr = "seconds"
    #hr += ' (%s)'%(rd,)
    formattedts = ts.strftime('%Y-%m-%d %H:%M:%S')

    return (formattedts, hr)

# this shows relativedelta, i.e. months and days correctly done starting from a fixed timestamp.
def timedeltaagefilter(delta, base):
    if delta.total_seconds() == 0:
        res = 'current'
    else:
        formattedts, hr = get_human_readable_age(base-delta, base)
        res = '<abbr title="%s">%s</abbr>'%(formattedts, hr)
    return jinja2.Markup(res)

# this shows relativedelta, i.e. months and days correctly done starting from a fixed timestamp.
def timedeltaagenoabbrfilter(delta, base):
    formattedts, hr = get_human_readable_age(base-delta, base)
    res = '%s - %s'%(hr, formattedts)
    return res

# return hrs:mins
def timedelta_hrs_mins_filter(delta):
    if isinstance(delta, datetime.timedelta):
        secs = delta.total_seconds()
    else:
        secs = delta

    mins = secs / 60
    hrs, mins = divmod(mins, 60)
    return "%d:%02d"%(hrs,mins)

def datetimeagefilter(ts, base):
    if ts == base:
        res = 'current'
    else:
        formattedts, hr = get_human_readable_age(ts, base)
        res = '<abbr title="%s">%s</abbr>'%(formattedts, hr)
    return jinja2.Markup(res)

def datetimeagenoabbrfilter(ts, base):
    formattedts, hr = get_human_readable_age(ts, base)
    res = '%s - %s'%(hr, formattedts)
    return res

def timedelta_total_seconds_filter(delta):
    assert(isinstance(delta, datetime.timedelta))
    return delta.total_seconds()


def agegroupclassfilter(delta):
    # our template defines 8 agegroups from OK(0) to okish(2) to warn(3) and Warn(4-5) to Error(6-7)
    if delta < datetime.timedelta(hours=6):
        return 'age0'
    elif delta < datetime.timedelta(hours=11):
        return 'age1'
    elif delta < datetime.timedelta(hours=16):
        return 'age2'
    elif delta < datetime.timedelta(hours=24):
        return 'age3'
    elif delta < datetime.timedelta(hours=48):
        return 'age4'
    elif delta < datetime.timedelta(days=3):
        return 'age5'
    elif delta < datetime.timedelta(days=4):
        return 'age6'
    elif delta < datetime.timedelta(days=8):
        return 'age7'
    elif delta < datetime.timedelta(days=14):
        return 'age8'
    elif delta < datetime.timedelta(days=30):
        return 'age9'
    else:
        return 'age10'

def agegroupdeltaclassfilter(ts, base):
    delta = base - ts
    return agegroupclassfilter(delta)

def formaterrorfilter(error):
    if len(error) > 20:
        return '{}...'.format(error[:16])
    return error

def raise_helper(msg):
    raise Exception(msg)

class BasePageRenderer:
    def __init__(self, **kwargs):
        self.tmplenv = self.setup_template_env(kwargs['templatedir'])

    @staticmethod
    def setup_template_env(templatedir):
        tmplenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(templatedir),
            autoescape = True,
            undefined = jinja2.StrictUndefined
        )
        tmplenv.filters['datetimeage'] = datetimeagefilter
        tmplenv.filters['datetimeagenoabbr'] = datetimeagenoabbrfilter
        tmplenv.filters['timedeltaage'] = timedeltaagefilter
        tmplenv.filters['timedeltaagenoabbr'] = timedeltaagenoabbrfilter
        tmplenv.filters['agegroupdeltaclass'] = agegroupdeltaclassfilter
        tmplenv.filters['agegroupclass'] = agegroupclassfilter
        tmplenv.filters['timedelta_total_seconds'] = timedelta_total_seconds_filter
        tmplenv.filters['timedelta_hrs_mins'] = timedelta_hrs_mins_filter
        tmplenv.filters['mirrorsortkey'] = helpers.hostname_comparator
        tmplenv.filters['formaterror'] = formaterrorfilter
        tmplenv.globals['raise'] = raise_helper
        tmplenv.globals['contact_email'] = CONTACT_EMAIL
        tmplenv.globals['distro'] = DISTRO
        return tmplenv

    def render(self, page):
        try: # Maybe this page brings its own rendering stuff
            page.render()
        except AttributeError:
            self.template = self.tmplenv.get_template(page.template_name)
            self.template.stream(page.context).dump(page.outfile, errors='strict')

#!/usr/bin/python3

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Interval, Float
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy
from sqlalchemy.orm import relationship, backref
import sqlalchemy.ext.declarative
import psycopg2
import psycopg2.extras

Base = sqlalchemy.ext.declarative.declarative_base()

class Origin(Base):
    """Origin of site information, i.e. the place from which we learned that
       a site exists.  E.g. "Mirrors.masterlist.in"
       """
    __tablename__           = 'origin'
    id                      = Column(Integer, primary_key=True)

    label                   = Column(String, nullable=False, unique=True)

class Site(Base):
    """Site offering the debian archive.
    """
    __tablename__           = 'site'
    id                      = Column(Integer, primary_key=True)

    origin_id               = Column(Integer, ForeignKey('origin.id', ondelete='CASCADE'), nullable=False, index=True)
    origin                  = relationship("Origin", backref=backref("sites", passive_deletes=True))

    name                    = Column(String, nullable=False, unique=True)
    http_path               = Column(String, nullable=False)
    http_override_host      = Column(String)
    http_override_port      = Column(Integer)

class SiteAlias(Base):
    """Alias name for a site offering the debian archive.
    """
    __tablename__           = 'sitealias'
    id                      = Column(Integer, primary_key=True)

    site_id                 = Column(Integer, ForeignKey('site.id', ondelete='CASCADE'), nullable=False, index=True)
    site                    = relationship("Site", backref=backref("sitealiases", passive_deletes=True))

    name                    = Column(String, nullable=False)
    priority                = Column(Integer)

class Checkrun(Base):
    """Instance of a mirror check run
    """
    __tablename__           = 'checkrun'
    id                      = Column(Integer, primary_key=True)

    timestamp               = Column(DateTime(timezone=True), index=True)


class Mastertrace(Base):
    """Age of the master tracefile
    """
    __tablename__           = 'mastertrace'
    __plural__              = __tablename__ + 's'
    id                      = Column(Integer, primary_key=True)

    site_id                 = Column(Integer, ForeignKey("site.id", ondelete='CASCADE'), nullable=False, index=True)
    checkrun_id             = Column(Integer, ForeignKey("checkrun.id", ondelete='CASCADE'), nullable=False, index=True)
    site                    = relationship("Site", backref=backref(__plural__, passive_deletes=True))
    checkrun                = relationship("Checkrun", backref=backref(__plural__, passive_deletes=True))

    full                    = Column(String, index=True)
    trace_timestamp         = Column(DateTime(timezone=True))
    error                   = Column(String)
    content                 = Column(JSONB(none_as_null=True))


class Sitetrace(Base):
    """site tracefile
    """
    __tablename__           = 'sitetrace'
    __plural__              = __tablename__ + 's'
    id                      = Column(Integer, primary_key=True)

    site_id                 = Column(Integer, ForeignKey("site.id", ondelete='CASCADE'), nullable=False, index=True)
    checkrun_id             = Column(Integer, ForeignKey("checkrun.id", ondelete='CASCADE'), nullable=False, index=True)
    site                    = relationship("Site", backref=backref(__plural__, passive_deletes=True))
    checkrun                = relationship("Checkrun", backref=backref(__plural__, passive_deletes=True))

    archive_update_in_progress = Column(DateTime(timezone=True))
    archive_update_required    = Column(DateTime(timezone=True))

    full                    = Column(String, index=True)
    trace_timestamp         = Column(DateTime(timezone=True), index=True)
    error                   = Column(String)
    content                 = Column(JSONB(none_as_null=True))


class Traceset(Base):
    """List of tracefiles found in project/traces
    """
    __tablename__           = 'traceset'
    __plural__              = __tablename__ + 's'
    id                      = Column(Integer, primary_key=True)

    site_id                 = Column(Integer, ForeignKey("site.id", ondelete='CASCADE'), nullable=False, index=True)
    checkrun_id             = Column(Integer, ForeignKey("checkrun.id", ondelete='CASCADE'), nullable=False, index=True)
    site                    = relationship("Site", backref=backref(__plural__, passive_deletes=True))
    checkrun                = relationship("Checkrun", backref=backref(__plural__, passive_deletes=True))

    traceset                = Column(JSONB(none_as_null=True))
    error                   = Column(String)

class SiteAliasMastertrace(Base):
    """Age of the master tracefile
    """
    __tablename__           = 'sitealiasmastertrace'
    __plural__              = __tablename__ + 's'
    id                      = Column(Integer, primary_key=True)

    sitealias_id            = Column(Integer, ForeignKey("sitealias.id", ondelete='CASCADE'), nullable=False, index=True)
    checkrun_id             = Column(Integer, ForeignKey("checkrun.id", ondelete='CASCADE'), nullable=False, index=True)
    sitealias               = relationship("SiteAlias", backref=backref(__plural__, passive_deletes=True))
    checkrun                = relationship("Checkrun", backref=backref(__plural__, passive_deletes=True))

    full                    = Column(String)
    trace_timestamp         = Column(DateTime(timezone=True))
    error                   = Column(String)
    content                 = Column(JSONB(none_as_null=True))

class Checkoverview(Base):
    """For a mirror and a check, summarize all we learned from a test-run.

    Data in this table will be populated after the rest runs, and is used
    to generate the report and compute scores.
    """
    __tablename__           = 'checkoverview'
    __plural__              = __tablename__ + 's'
    id                      = Column(Integer, primary_key=True)

    site_id                 = Column(Integer, ForeignKey("site.id", ondelete='CASCADE'), nullable=False, index=True)
    checkrun_id             = Column(Integer, ForeignKey("checkrun.id", ondelete='CASCADE'), nullable=False, index=True)
    site                    = relationship("Site", backref=backref(__plural__, passive_deletes=True))
    checkrun                = relationship("Checkrun", backref=backref(__plural__, passive_deletes=True))

    error                   = Column(String)
    version                 = Column(DateTime(timezone=True))
    age                     = Column(Interval)
    score                   = Column(Float)
    aliases                 = Column(JSONB(none_as_null=True))

class MirrorDB():
    DBURL = 'postgresql:///mirror-status'
    def __init__(self, dburl=DBURL):
        self.engine = sqlalchemy.create_engine(dburl)
        Base.metadata.bind = self.engine
        self.sessionMaker = sqlalchemy.orm.sessionmaker(bind=self.engine)

    def session(self):
        return self.sessionMaker()

class RawDB():
    DBURL = MirrorDB.DBURL
    def __init__(self, dburl=DBURL):
        self.conn = psycopg2.connect(dburl)

    def cursor(self):
        c = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return c

    def commit(self):
       self.conn.commit()

def update_or_create(session, model, updates, **kwargs):
    r = session.query(model).filter_by(**kwargs)
    if len(updates) == 0:
        need_insert = r.first() is None
    else:
        need_insert = r.update(updates) == 0
    if need_insert:
        attributes = dict((k, v) for k, v in kwargs.items())
        attributes.update(updates)
        instance = model(**attributes)
        session.add(instance)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from datetime import datetime

from pybamboo.connection import Connection
from pybamboo.exceptions import BambooError, ErrorParsingBambooData

from microsite.bamboo import get_bamboo_dataset_id, get_bamboo_url, CachedDataset

AN_HOUR = 60 * 60
A_DAY = AN_HOUR * 24
A_MONTH = A_DAY * 30
A_YEAR = A_DAY * 365


class ESTSPlot(dict):

    def ident(self):
        return (self.iquadrant, self.icluster, self.iplot)

    @property
    def iquadrant(self):
        try:
            return int(self['quadrant'])
        except:
            return self['quadrant']

    @property
    def icluster(self):
        try:
            return int(self['cluster'])
        except:
            return self['cluster']

    @property
    def iplot(self):
        try:
            return int(self['plot'])
        except:
            return self['plot']

    @property
    def gps(self):
        # use only GPS1 for now
        gpd = {}
        for key, value in self.items():
            if not key.startswith('_gps1'):
                continue
            gpd.update({key.replace('_gps1_', ''): value})
        return gpd


class ESTSSample(object):

    STATUS_COLLECTED = 0
    STATUS_SENT_TO_PC = 1
    STATUS_ARRIVED_AT_PC = 2
    STATUS_SENT_TO_NSTC = 3
    STATUS_ARRIVED_AT_NSTC = 4
    STATUS_SENT_TO_ARCHIVE = 5
    STATUS_ARRIVED_AT_ARCHIVE = 6

    STATUSES = {STATUS_COLLECTED: u"Collected",
                STATUS_SENT_TO_PC: u"Sent to PC",
                STATUS_ARRIVED_AT_PC: u"Arrived at PC",
                STATUS_SENT_TO_NSTC: u"Sent to NSTC",
                STATUS_ARRIVED_AT_NSTC: u"Arrived at NSTC",
                STATUS_SENT_TO_ARCHIVE: u"Sent to Archive",
                STATUS_ARRIVED_AT_ARCHIVE: u"Arrived at Archive"}

    TOP_QR = 'top_qr'
    SUB_QR = 'sub_qr'
    QR_20_40 = 'qr_20_40'
    QR_40_60 = 'qr_40_60'
    QR_60_80 = 'qr_60_80'
    QR_80_100 = 'qr_80_100'

    POSITIONS = {
        TOP_QR: u"top",
        SUB_QR: u"0-20",
        QR_20_40: u"20-40",
        QR_40_60: u"40-60",
        QR_60_80: u"60-80",
        QR_80_100: u"80-100"
    }

    def __init__(self, sample_id):

        self.sample_id = sample_id
        self._position = None
        self._status = None
        self._events = {}

        self.retrieve_datasets()

        self.query_status()

    def __str__(self):
        return self.sample_id

    def retrieve_datasets(self):
        connection = Connection()

        self.plot_dataset = CachedDataset(u'ddc7943d6d284b7dadc1b02de39f33eb',
                                          connection=connection)
        self.datasets = {self.STATUS_SENT_TO_PC:
                            CachedDataset(u'1a889141be2d4264b4b4bb77b33d330d',
                                          connection=connection),
                         self.STATUS_ARRIVED_AT_PC:
                             CachedDataset(u'bf56cd8eb1054df287dc0a1350677231',
                                           connection=connection),
                         self.STATUS_SENT_TO_NSTC:
                             CachedDataset(u'33a6530d513242d9af9683146e69a5a3',
                                           connection=connection),
                         self.STATUS_ARRIVED_AT_NSTC:
                             CachedDataset(u'd32110b1706945e7ab276f6e7e23b194',
                                           connection=connection),
                         self.STATUS_SENT_TO_ARCHIVE:
                             CachedDataset(u'',
                                           connection=connection),
                         self.STATUS_ARRIVED_AT_ARCHIVE:
                             CachedDataset(u'3021738ddad04a8d9195db5bd119a5c8',
                                           connection=connection)}

    def query_status(self):

        # find out plot to make sure we have a valid sample_id
        for position in self.POSITIONS.keys():
            matching_plots = self.plot_dataset \
                                 .get_data(query={u'found_%s' % position:
                                                    self.sample_id},
                                           order_by='-end',
                                           limit=1,
                                           cache=True,
                                           cache_expiry=A_MONTH)
            if matching_plots and len(matching_plots):
                self._position = position
                self._plot = ESTSPlot(matching_plots[0])
                break
        if not self.position:
            raise ValueError(u"Invalid Sample ID: no matching plot.")

        # find out status of the sample
        for status in sorted(self.STATUSES.keys(), reverse=True)[:-1]:
            try:
                matching_events = self.datasets[status] \
                                      .get_data(query={'scan_soil_id':
                                                            self.sample_id},
                                                order_by="-end_time",
                                                limit=1,
                                                cache=True,
                                                cache_expiry=A_DAY)
            except ErrorParsingBambooData:
                continue
            if matching_events and len(matching_events):
                self._events[status] = matching_events[0]
                self._events[status].update({'status': status})
                if isinstance(self._events[status]['end_time'], (int, basestring)):
                    # temp fix for fixture
                    try:
                        self._events[status].update({'end_time': datetime.fromtimestamp(int(self._events[status]['end_time']))})
                    except:
                        pass
                if not self.status:
                    self._status = status
            else:
                self._events[status] = None
        # mark as collected if none found
        if not self.status:
            self._status = self.STATUS_COLLECTED

    @property
    def is_valid(self):
        return self._status is not None and self.plot is not None

    @property
    def status(self):
        return self._status

    @property
    def verbose_status(self):
        return self.STATUSES.get(self.status)

    @classmethod
    def get_verbose_status(cls, status):
        return cls.STATUSES.get(status)

    @property
    def position(self):
        return self._position

    @property
    def depth(self):
        return self.POSITIONS.get(self.position, u"n/a")

    def events(self):
        return self._events

    def data(self):
        if self.status is None:
            return {}
        if self.status == self.STATUS_COLLECTED:
            return self.plot()
        return self.events()[self.status]

    @property
    def plot(self):
        return self._plot

    def plot_ident(self):
        return self.plot.ident()

    def ident(self):
        return u'%s.%s.%s' % self.plot_ident() + '.' + self.depth

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from pybamboo.connection import Connection
from pybamboo.exceptions import ErrorParsingBambooData

from microsite.bamboo import (get_bamboo_url, CachedDataset)
from microsite.utils import get_option

AN_HOUR = 60 * 60
A_DAY = AN_HOUR * 24
A_MONTH = A_DAY * 30
A_YEAR = A_DAY * 365


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

    def __init__(self, sample_id, project):

        self.sample_id = sample_id
        self._position = None
        self._status = None
        self._status_date = None
        self._events = {}
        self.project = project

        self.retrieve_dataset()

        self.query_status()

    def __str__(self):
        return self.sample_id

    def retrieve_dataset(self):
        connection = Connection(get_bamboo_url(self.project))
        self.dataset = CachedDataset(get_option(self.project, 'ests_dataset'),
                                     connection=connection)
        self.data = self.dataset.get_data(query={u'barcode': self.sample_id},
                                          cache=True)[0]

        self.siblings = {}
        for position in self.POSITIONS:
            if position == self.position:
                self.siblings[position] = self.sample_id
                continue
            try:
                data = self.dataset.get_data(query={u'position': position,
                                                u'block': self.data['block'],
                                                u'quadrant': self.data['quadrant'],
                                                u'cluster': self.data['cluster'],
                                                u'plot': self.data['plot'],
                                                },
                                         select=['barcode'],
                                         cache=True)[-1]
                if isinstance(data, dict):
                    data = data.get(u'barcode', u'')
            except:
                # raise
                data = None
            self.siblings[position] = data

    def query_status(self):

        for astatus in self.STATUSES.keys():
            end = self.data.get('step%d_end_time' % astatus)
            name = self.data.get('step%d_name' % astatus)
            try:
                if astatus > 1:
                    prev_end = self.data.get('step%d_end_time' % (astatus - 1))
                else:
                    prev_end = self.data.get('end')
                delay = (end - prev_end)
            except:
                delay = None
            processing_center = self.data.get('step%d_processing_center' % astatus)
            pc_destination = self.data.get('step%s_pc_destination' % astatus)
            pc_name = processing_center if processing_center else pc_destination

            if end is not None and end != u'null':

                # create Event
                self._events[astatus] = {'date': end,
                                         'delay': delay,
                                         'survey_day': end,
                                         'pc_name': pc_name,
                                         'name': name,
                                         'status': astatus}
                # Update Status
                self._status = astatus
                self._status_date = end

        # mark as collected if none found
        if not self.status:
            self._status = self.STATUS_COLLECTED
            self._status_date = self.data.get('end')

    @property
    def is_valid(self):
        return self._status is not None

    @property
    def status(self):
        return self._status

    @property
    def status_date(self):
        return self._status_date

    @property
    def verbose_status(self):
        return self.STATUSES.get(self.status)

    @classmethod
    def get_verbose_status(cls, status):
        return cls.STATUSES.get(status)

    @property
    def position(self):
        return self.data.get(u'position', u"n/a")

    @property
    def depth(self):
        return self.position

    def events(self):
        return self._events

    def ident(self):
        return u'%s.%s.%s.%s' % self.plot_ident_data() + '.' + self.depth

    def plot_ident_data(self):
        return (self.iblock, self.iquadrant, self.icluster, self.iplot)

    def plot_ident(self):
        return u".".join([str(e) for e in self.plot_ident_data()])

    @property
    def iblock(self):
        block = self.data.get(u'block', u'')
        try:
            return int(block)
        except:
            return block

    @property
    def iquadrant(self):
        quadrant = self.data.get(u'quadrant', u'')
        try:
            return int(quadrant)
        except:
            return quadrant

    @property
    def icluster(self):
        cluster = self.data.get(u'cluster', u'')
        try:
            return int(cluster)
        except:
            return cluster

    @property
    def iplot(self):
        plot = self.data.get(u'plot', u'')
        try:
            return int(plot)
        except:
            return plot

    @property
    def gps(self):
        # use only GPS1 for now
        gpd = {}
        for key, value in self.data.items():
            if not key.startswith('_gps1'):
                continue
            gpd.update({key.replace('_gps1_', ''): value})
        return gpd

    @property
    def sibling_top_qr(self):
        return self.siblings.get('top_qr')

    @property
    def sibling_sub_qr(self):
        return self.siblings.get('sub_qr')

    @property
    def sibling_qr_20_40(self):
        return self.siblings.get('qr_20_40')

    @property
    def sibling_qr_40_60(self):
        return self.siblings.get('qr_40_60')

    @property
    def sibling_qr_60_80(self):
        return self.siblings.get('qr_60_80')

    @property
    def sibling_qr_80_100(self):
        return self.siblings.get('qr_80_100')

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2013 OpenERP s.a. (<http://openerp.com>).
#    Copyright (C) 2013-2014 initOS GmbH & Co. KG (<http://www.initos.com>).
#    Copyright (C) 2014 Intero Technologies GmbH
#                                        (<http://intero-technologies.de>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm, fields
from openerp.addons.base_icalendar.property import icalendar_property
from datetime import datetime
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as _DSDF


class CrmMeeting(orm.Model):
    _inherit = ['crm.meeting', 'icalendar.component.model']
    _name = 'crm.meeting'

    def _get_icalendar_component_mapping(self):
        return super(CrmMeeting, self)._get_icalendar_component_mapping() + \
            [icalendar_property('uid', column_name='component_uid'),
             icalendar_property('dtstart', column_name='date',
                                set_transformation=(
                                    lambda x: datetime.fromtimestamp(time.mktime(time.strptime(x, _DSDF)))),
                                get_transformation=(lambda x: datetime.strftime(x, _DSDF))),
             icalendar_property('dtend', column_name='date_deadline',
                                set_transformation=(
                                    lambda x: datetime.fromtimestamp(time.mktime(time.strptime(x, _DSDF)))),
                                get_transformation=(lambda x: datetime.strftime(x, _DSDF))),
             ]

    def get_required_fields(self):
        """Called to get model specific required fields, filled with
        temporary values."""
        return {
            'date': fields.datetime.now(),
            'date_deadline': fields.datetime.now()
        }

    def _fill_get_icalendar_component(self, cr, uid, ids, icalendar):
        """Called if an iCalendar has to be generated from a model.
        This method can be used to extend the mapping mechanism
        provided by _get_icalendar_mapping"""
        # TODO: what about models with translatable fields
        meeting = self.browse(cr, uid, ids)[0]
        event = icalendar.vevent

        if meeting.name:
            summary = event.add('summary')
            summary.value = meeting.name
        if meeting['class']:
            privacy = event.add('class')
            privacy.value = meeting['class']
        if meeting.description:
            desc = event.add('description')
            desc.value = meeting.description
        if meeting.location:
            loc = event.add('location')
            loc.value = meeting.location
        if meeting.organizer:
            organizer = event.add('organizer')
            organizer.value = meeting.organizer
        if meeting.base_calendar_url:
            url = event.add('url')
            url.value = meeting.base_calendar_url

    def _fill_set_icalendar_component(self, cr, uid, ids, icalendar, update_values):
        """Called if an iCalendar has to be generated from a model.
        This method can be used to extend the mapping mechanism
        provided by _get_icalendar_mapping"""
        if 'summary' in icalendar and icalendar['summary']:
            update_values['name'] = icalendar['summary'][0].value
        if 'class' in icalendar and icalendar['class']:
            update_values['class'] = icalendar['class'][0].value.lower()
        if 'description' in icalendar and icalendar['description']:
            update_values['description'] = icalendar['description'][0].value
        if 'location' in icalendar and icalendar['location']:
            update_values['location'] = icalendar['location'][0].value
        if 'organizer' in icalendar and icalendar['organizer']:
            update_values['organizer'] = icalendar['organizer'][0].value
        if 'url' in icalendar and icalendar['url']:
            update_values['url'] = icalendar['url'][0].value

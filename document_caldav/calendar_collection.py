# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
from caldav_node import node_model_calendar_collection


class CalendarCollection(orm.Model):
    _inherit = 'document.directory'

    _columns = {
        'calendar_collection': fields.boolean('Calendar Collection'),
    }

    _default = {
        'calendar_collection': False,
    }

    def get_node_class(self, cr, uid, ids, dbro=None, dynamic=False,
                       context=None):
        if dbro is None:
            dbro = self.browse(cr, uid, ids, context=context)

        if dbro.calendar_collection:
            return node_model_calendar_collection
        else:
            return super(CalendarCollection, self) \
                .get_node_class(cr, uid, ids, dbro=dbro, dynamic=dynamic,
                                context=context)

    def get_description(self, cr, uid, ids, context=None):
        # TODO: return description of all calendars
        return False

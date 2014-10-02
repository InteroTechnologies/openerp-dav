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


class icalendar_property(object):
    "Handles the connection between a icalendar property and an OpenERP record"
    def __init__(self, icalendar_name, column_name=None, set_transformation=None,
                 get_transformation=None):
        self._icalendar_name = icalendar_name
        self._column_name = column_name
        self._set_transformation = set_transformation
        self._get_transformation = get_transformation

    def icalendar_name(self):
        "Returns iCalendar name"
        return self._icalendar_name

    def set_icalendar(self, icalendar, record):
        "Sets a icalendar property from a browse object"
        if not self._column_name:
            return False
        record_val = getattr(record, self._column_name, None)
        if record_val and self._set_transformation:
            record_val = self._set_transformation(record_val)
        if record_val:
            icalendar_prop = icalendar.add(self._icalendar_name)
            icalendar_prop.value = record_val
            return True
        return False

    def get_icalendar(self, update_values, icalendar):
        """Reads a icalendar property and puts in into a dictionary
           suitable for .write(.)"""
        if not self._column_name:
            return False
        value = icalendar.contents[self._icalendar_name][0].value
        if self._get_transformation:
            value = self._get_transformation(value)
        if self._icalendar_name in icalendar.contents:
            update_values[self._column_name] = value
            return True
        return False


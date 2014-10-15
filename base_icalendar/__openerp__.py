# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2013 OpenERP s.a. (<http://openerp.com>).
#    Copyright (C) 2013-14 initOS GmbH & Co. KG (<http://www.initos.com>).
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
{
    "name": "iCalendar support for models",
    "version": "0.1",
    "depends": ["base", "base_calendar"],
     'external_dependencies': {
        'python': ['vobject'],
     },
    'author': 'Intero Technologies GmbH',
    "category": "",
    "summary": "Basic iCalendar support (mapping for calendar.event)",
    'license': 'AGPL-3',
    "description": """
This module introduces a icalendar.component.model that helps to export
and import OpenERP records as iCalendars. It includes a basic mapping
for calendar.event.
    """,
    'data': [
        'base_calendar_data.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}

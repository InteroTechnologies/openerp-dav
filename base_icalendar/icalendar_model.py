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
import datetime
import uuid
import vobject
try:
    import cPickle as pickle
except ImportError:
    import pickle


class icalendar_component_model(orm.AbstractModel):

    """This class can be used as a mix-in to import and export
     existing models as iCalendars (with one component) and to
     make models available as a CalDav Calendar"""

    _name = 'icalendar.component.model'
    _description = 'iCalendar Component Model'

    _columns = {
        'create_date': fields.datetime('Creation date', readonly=True),
        'write_date': fields.datetime('Last Update', readonly=True),
        'component_uid': fields.char('UID for iCalendar', size=128, required=True,
                                     select=True),
        'component_filename': fields.char('Filename of iCalendar', size=128,
                                          required=True, select=True),
        'component_properties': fields.binary('Additional iCalendar '
                                              'component Properties '
                                              '(not managed by OpenERP)'),
        'dav_filter_id': fields.many2one('ir.filters',
                                         'Filter that the record '
                                         'was created under'),
    }

    _defaults = {
        'component_uid': lambda *x: uuid.uuid4(),
        'component_filename': lambda *x: str(uuid.uuid4()) + '.ics',
    }

    _sql_constraints = [
        ('icalendar_uid_uniq', 'unique(icalendar_uid)',
         'CalDAV UID must be unique in a database'),
        ('icalendar_filename_uniq', 'unique(icalendar_filename)',
         'CalDAV file name must be unique in a database'),
    ]

    def copy(self, cr, uid, _id, default=None, context=None):
        default = default or {}
        # - set a new uid on copy
        # - don't copy unmapped iCalendar properties
        default.update({
            'component_uid': str(uuid.uuid4()),
            'component_filename': str(uuid.uuid4()) + '.ics',
            'component_properties': False,
        })
        return super(icalendar_component_model, self).copy(cr, uid, _id, default,
                                                           context=context)

    def _get_icalendar_component_mapping(self):
        """Defines mapping between iCalendar component and model properties.
        There are no default required properties determined
        for _all_ components."""
        return []

    def _fill_get_icalendar_component(self, cr, uid, ids, icalendar):
        """Called if an iCalendar has to be generated from a model.
        This method can be used to extend the mapping mechanism provided by
        _get_icalendar_mapping"""
        pass

    def _fill_set_icalendar_component(self, cr, uid, ids, icalendar, update_values):
        """Called if a model is to be created/updated from an iCalendar.
        This method can be used to extend the mapping mechanism provided by
        _get_icalendar_mapping."""
        pass

    def get_icalendar(self, cr, uid, ids, component_type='vevent'):
        "Exports a model as an iCalendar"
        record = self.browse(cr, uid, ids)[0]

        icalendar = vobject.iCalendar()
        component = icalendar.add(component_type)
        dtstamp = component.add('dtstamp')
        dtstamp.value = datetime.datetime.now()
        mapped_properties = set()
        for prop in self._get_icalendar_component_mapping():
            prop.set_icalendar(component, record)
            mapped_properties.add(prop.icalendar_name())

        unmapped_properties = []
        if record.component_properties:
            unmapped_properties = pickle.loads(record.icalendar_properties)
        for prop in unmapped_properties:
            if prop.name.lower() not in mapped_properties:
                icalendar.add(prop)

        self._fill_get_icalendar_component(cr, uid, ids, icalendar)
        return icalendar

    def set_icalendar(self, cr, uid, ids, icalendar_string, component_type='vevent'):
        "Import a model from an iCalendar"
        component = eval('vobject.readOne(icalendar_string).' + component_type)

        mapped_properties = set(['version'])
        update_values = {}
        for prop in self._get_icalendar_component_mapping():
            prop.get_icalendar(update_values, component)
            mapped_properties.add(prop.icalendar_name())

        unmapped_properties = []
        for prop in component.getChildren():
            if prop.name.lower() not in mapped_properties:
                unmapped_properties.append(prop)
        update_values['icalendar_properties'] = \
            pickle.dumps(unmapped_properties)

        self._fill_set_icalendar_component(
            cr, uid, ids, component.contents, update_values)
        self.write(cr, uid, ids, update_values)

    def get_uid_by_icalendar(self, icalendar_string, component_type='vevent'):
        component = eval('vobject.readOne(icalendar_string).' + component_type)
        return component.uid.value

    def get_required_fields(self):
        """ called to get model specific required fields, filled with temporary
        values."""
        return {}

    def _migrate_icalendar_uid(self, cr, uid, ids=None, context=None):
        # We overwrite existing uids because of the following behavior
        #  of OpenERP: When a new column with default value is added,
        #  this default value is only computed once. Therefore
        #  all rows share the same icalendar_uid.
        cr.execute("""UPDATE %s
                         SET component_uid = 'internal-' || id,
                             component_filename = 'internal-' || id || '.ics'"""
                   % (self._table))
        # After we fixed the uids, we can add the unique constraint
        #  if it not already exists (if the database contained less than
        #  two users, the uid was unique before).
        for col_name in ["component_uid", "component_filename"]:
            constraint_name = "%s_%s_uniq" % (self._table, col_name)
            cr.execute("""SELECT conname,
                                 pg_catalog.pg_get_constraintdef(oid, true)
                                   AS condef
                            FROM pg_constraint
                           WHERE conname=%s""", (constraint_name,))
            if not cr.fetchone():
                cr.execute("""ALTER TABLE "%s" ADD CONSTRAINT "%s" %s"""
                           % (self._table, constraint_name,
                              "UNIQUE(%s)" % col_name))

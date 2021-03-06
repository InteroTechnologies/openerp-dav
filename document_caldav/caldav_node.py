# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.addons.document_webdav_fast import nodes
from openerp.addons.document_webdav_fast.dav_fs import dict_merge2
from openerp.addons.document.document import nodefd_static
from openerp.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)
from openerp.tools.translate import _


_NS_CALDAV = "urn:ietf:params:xml:ns:caldav"


class node_model_calendar_collection(nodes.node_res_obj):

    """The children of this node are all models that
    implement icalendar.component.model"""

    DAV_M_NS = {
        "DAV:": '_get_dav',
    }
    
    http_options = {'DAV': ['calendar-access']}

    def get_dav_resourcetype(self, cr):
        return [('collection', 'DAV:')]

    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        if name:
            elements = name.split("-")
            model = elements[1]
            filter_id = None
            if len(elements) > 2: 
                filter_id = elements[2]
            return self._get_nodes_by_name(cr, model, filter_id)
        else:
            return self._get_all_nodes(cr)
    

    def _get_nodes_by_name(self, cr, ir_model, ir_filter_id=None):
        model_obj = self.context._dirobj.pool.get('ir.model')
        model_ids = model_obj.search(cr, self.context.uid,
                                     [('model', '=', ir_model)])
        model_data = model_obj.read(cr, self.context.uid, model_ids,
                                    ['model', 'name'])
        nodes = []
        for _model in model_data:
            displayname = _model['name']
            model = _model['model']
            if ir_filter_id:
                filters_obj = self.context._dirobj.pool.get('ir.filters')
                filter = filters_obj.browse(cr, self.context.uid, ir_filter_id)
                nodes.append(node_calendar("filtered-%s-%s" % (model, filter.id), 
                                           self,
                                           self.context,
                                           model, 
                                           filter.domain, 
                                           filter.id,
                                           displayname = _("%s (filtered by %s)") 
                                           % (displayname, filter.name),))
            else:
                nodes.append(node_calendar("all-%s" % ir_model, 
                                           self,
                                           self.context, 
                                           model,
                                           displayname=displayname))
        return nodes


    def _get_all_nodes(self, cr):
        """find all models that implement icalendar.component.model"""
        fields_obj = self.context._dirobj.pool.get('ir.model.fields')
        fields_ids = fields_obj.search(cr, self.context.uid,
                                       [('name', '=', 'component_uid'),
                                        ('model_id.model', '!=', 'icalendar.component.model')])
        fields = fields_obj.browse(cr, self.context.uid, fields_ids)
        nodes = []
        for _field in fields:
            displayname = _field.model_id.name
            model = _field.model_id.model
            nodes.append(node_calendar("all-%s" % model,
                                       self,
                                       self.context,
                                       model, 
                                       displayname=displayname))
            # add filtered nodes
            filters_obj = self.context._dirobj.pool.get('ir.filters')
            filter_ids = filters_obj.search(cr, self.context.uid,
                                            [('model_id', '=', _field.model_id.id),
                                             ('user_id', 'in', [self.context.uid, False])])
            filters_obj = self.context._dirobj.pool.get('ir.filters')
            filter_data = filters_obj.read(cr, self.context.uid, filter_ids,
                                       ['context', 'domain', 'name'])
            for _filter in filter_data:
                nodes.append(node_calendar("filtered-%s-%s" % (model, _filter['id']), 
                                           self,
                                           self.context,
                                           model, 
                                           _filter['domain'], 
                                           _filter['id']),
                                           displayname = _("%s (filtered by %s)") 
                                           % (displayname, _filter['name']),
                             )
        return nodes


class node_calendar(nodes.node_class):

    """This node contains iCalendar for all records of a given model.
    If a filter is given, the node contains only those records
    that match the filter."""
    DAV_PROPS = dict_merge2(nodes.node_dir.DAV_PROPS,
                            {"DAV:": ('supported-report-set',),
                             _NS_CALDAV: (
                                'calendar-description',
                                'supported-calendar-component-set',
                            )})
    DAV_M_NS = {
        "DAV:": '_get_dav',
                _NS_CALDAV: '_get_caldav',
    }
    http_options = {'DAV': ['calendar-access']}

    def __init__(self, path, parent, context,
                 ir_model='calendar.event', filter_name=None,
                 filter_domain=None, filter_id=None, displayname=None):
        super(node_calendar, self).__init__(path, parent, context)
        self.mimetype = 'application/x-directory'
        self.create_date = parent.create_date
        self.ir_model = ir_model
        self.filter_id = filter_id
        if filter_domain and self.filter_id:
            self.filter_domain = ['|',
                                  ('dav_filter_id', '=', self.filter_id)] + \
                safe_eval(filter_domain)
        else:
            self.filter_domain = []
        if not displayname:
            if filter_name:
                self.displayname = "%s filtered by %s" % (ir_model, filter_name)
            else:
                self.displayname = "%s" % path
        else:
            self.displayname = displayname

    def children(self, cr, domain=None):
        if not domain:
            domain = []
        return self._child_get(cr, domain=(domain + self.filter_domain))

    def child(self, cr, name, domain=None):
        if not domain:
            domain = []
        res = self._child_get(cr, name, domain=(domain + self.filter_domain))
        if res:
            return res[0]
        return None

    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        children = []
        model_obj = self.context._dirobj.pool.get(self.ir_model)
        if not domain:
            domain = []

        if name:
            domain.append(('component_filename', '=', name))
        record_ids = model_obj.search(cr, self.context.uid, domain)

        for record in model_obj.browse(cr, self.context.uid,
                                       record_ids):
            children.append(
                res_node_calendar(record.component_filename,
                                  self, self.context, record,
                                  None, None, self.ir_model))
        return children

    def _get_ttag(self, cr):
        return 'calendar-%d-%s' % (self.context.uid, self.path)

    def get_dav_resourcetype(self, cr):
        return [('collection', 'DAV:'),
                ('calendar', _NS_CALDAV)]

    def _get_dav_supported_report_set(self, cr):
        return ('supported-report', 'DAV:',
                ('report', 'DAV:',
                 ('principal-match', 'DAV:')))

    def _get_caldav_calendar_description(self, cr):
        return self.displayname

    def _get_caldav_supported_calendar_data(self, cr):
        return ('calendar-data', _NS_CALDAV, None,
                {'content-type': "text/calendar", 'version': "2.0"})
        
    def _get_caldav_supported_calendar_component_set(self, cr):
        return ('comp', _NS_CALDAV, None, {'name': 'VEVENT'})

    def _get_caldav_max_resource_size(self, cr):
        return 65535

    def get_domain(self, cr, filter_node):
        """
        Return a domain for the caldav filter

        :param cr: database cursor
        :param filter_node: the DOM Element of filter
        :return: a list for domain
        """
        # FIXME support for VEVENT only
        return []
#         if not filter_node:
#             return []
#         if filter_node.localName != 'calendar-query':
#             return []

        raise ValueError("filtering is not implemented")

    def create_child(self, cr, path, data=None):
        if not data:
            raise ValueError("Cannot create a contact with no data")
        model_obj = self.context._dirobj.pool.get(self.ir_model)
        uid = model_obj.get_uid_by_icalendar(data)
        values = {'name': 'TEMPORARY_NAME',
                  'component_uid': uid,
                  'component_filename': path,
                  'dav_filter_id': self.filter_id}
        values.update(model_obj.get_required_fields())
        record_id = model_obj.create(cr, self.context.uid, values)
        model_obj.set_icalendar(cr, self.context.uid, [record_id], data)
        record = model_obj.browse(cr, self.context.uid, record_id)
        return res_node_calendar(record.component_filename, self, self.context,
                                 record, None, None, self.ir_model)


class res_node_calendar(nodes.node_class):

    """This node represents a single iCalendar"""
    our_type = 'file'
    DAV_PROPS = {_NS_CALDAV: (
        'calendar-description',
        'calendar-data',
    )}
    DAV_M_NS = {_NS_CALDAV: '_get_caldav'}

    http_options = {'DAV': ['calendar-access']}

    def __init__(self, path, parent, context, res_obj=None, res_model=None,
                 res_id=None, ir_model=None):
        super(res_node_calendar, self).__init__(path, parent, context)
        self.mimetype = 'text/calendar; charset=utf-8'
        self.create_date = parent.create_date
        self.write_date = parent.write_date or parent.create_date
        self.displayname = None
        self.ir_model = ir_model

        self.res_obj = res_obj
        if self.res_obj:
            if self.res_obj.create_date:
                self.create_date = self.res_obj.create_date
            if self.res_obj.write_date:
                self.write_date = self.res_obj.write_date

    def open_data(self, cr, mode):
        return nodefd_static(self, cr, mode)

    def get_data(self, cr, fil_obj=None):
        return self.res_obj.get_icalendar().serialize()

    def _get_caldav_calendar_data(self, cr):
        return self.get_data(cr)

    def get_dav_resourcetype(self, cr):
        return [('calendar', _NS_CALDAV)]

    def get_data_len(self, cr, fil_obj=None):
        data = self.get_data(cr, fil_obj)
        if data:
            return len(data)
        return 0

    def set_data(self, cr, data):
        self.res_obj.set_icalendar(data)

    def _get_ttag(self, cr):
        return 'calendar-%s-%s' % (self.res_obj._name,
                                   self.res_obj.id)

    def rm(self, cr):
        uid = self.context.uid
        record_obj = self.context._dirobj.pool.get(self.ir_model)
        return record_obj.unlink(cr, uid, [self.res_obj.id])

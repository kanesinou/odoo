# -*- coding: utf-8 -*-

from odoo import fields
from odoo.fields import determine


class DynamicSelection(fields.Selection):

    workflowable_id = None

    def _description_selection(self, env):
        selection = self.selection
        model = None
        id = None
        if self.workflowable_id:
            model = 'workflowable'
            id = self.workflowable_id
        if env.context.get('default_workflowable_id', False):
            model = 'workflowable'
            id = env.context.get('default_workflowable_id')
        elif env.context.get('active_model', False) and env.context.get('active_id', False):
            model = env.context.get('active_model')
            id = env.context.get('active_id')
        elif env.context.get('params', False):
            if env.context.get('params').get('model', False) and env.context.get('params').get('id', False):
                model = env.context.get('params').get('model')
                id = env.context.get('params').get('id')
        if model and id:
            if env.context.get('workflow_process_id', False):
                if model == 'workflowable':
                    workflowable_position = env['workflowable.position'].search([
                        '&', ('workflowable_id', '=', id),
                        ('workflow_process_id', '=', env.context.get('workflow_process_id'))
                    ])
                    if workflowable_position.exists():
                        return determine(selection, workflowable_position)
                else:
                    workflowable = env['workflowable'].search([
                        ('workflowable_type_id.model_id.model', '=', model)
                    ])
                    if workflowable.exists():
                        workflowable_position = env['workflowable.position'].search([
                            '&', ('workflowable_id', '=', workflowable.id),
                            ('workflow_process_id', '=', env.context.get('workflow_process_id'))
                        ])
                        if workflowable_position.exists():
                            return determine(selection, workflowable_position)
            else:
                if model == 'workflowable':
                    workflowable_positions = env['workflowable.position'].search([
                        ('workflowable_id', '=', id)
                    ])
                    return determine(selection, workflowable_positions.exists())
                else:
                    workflowable = env['workflowable'].search([
                        ('workflowable_type_id.model_id.model', '=', model)
                    ])
                    if workflowable.exists():
                        workflowable_positions = env['workflowable.position'].search([
                            ('workflowable_id', '=', workflowable.id)
                        ])
                        return determine(selection, workflowable_positions.exists())

    def get_values(self, record):
        selection = self.selection
        if isinstance(selection, str) or callable(selection):
            selection = determine(selection, record)
        return [value for value, _ in selection]

    def convert_to_read(self, value, record, use_name_get=True):
        for val in self.get_values(record):
            if val == value:
                return value
        return False

    def convert_to_column(self, value, record, values=None, validate=True):
        if validate and self.validate:
            value = self.convert_to_cache(value, record)
        values = self.get_values(record)
        return super(DynamicSelection, self).convert_to_column(value, record, values, validate)

    def convert_to_cache(self, value, record, validate=True):
        if not validate:
            return value or None
        if value and self.column_type[0] == 'int4':
            value = int(value)
        states = self.get_values(record)
        if value in states:
            return value
        elif not value:
            return None
        raise ValueError("Wrong value for %s: %r" % (self, value))

    def convert_to_export(self, value, record):
        for val in determine(self.selection, record):
            if val[0] == value:
                return val[1]
        return ''

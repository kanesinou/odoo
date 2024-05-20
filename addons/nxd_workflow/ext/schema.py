# -*- coding: utf-8 -*-

from odoo import fields
from odoo.fields import determine


def compute_state_selection(records):
    states_selection_list = []
    states_list = []
    for record in records:
        if record.workflow_process_stage_id:
            procedure_stage = record.workflow_process_stage_id.workflow_procedure_stage_id
            if procedure_stage.exists():
                states_list += procedure_stage.inbound_workflow_procedure_stage_transition_ids.mapped(
                    'from_workflow_procedure_stage_id.workflow_state_id'
                )
                states_list.append(procedure_stage.workflow_state_id)
                states_list += procedure_stage.outbound_workflow_procedure_stage_transition_ids.mapped(
                    'to_workflow_procedure_stage_id.workflow_state_id'
                )
                if procedure_stage.can_be_breaked and procedure_stage.break_workflow_state_id:
                    states_list.append(procedure_stage.break_workflow_state_id)
                if procedure_stage.can_be_resumed and procedure_stage.resume_workflow_state_id:
                    states_list.append(procedure_stage.resume_workflow_state_id)
                if procedure_stage.can_be_cancelled and procedure_stage.cancel_workflow_state_id:
                    states_list.append(procedure_stage.cancel_workflow_state_id)
                for state in states_list:
                    state_selection = (state.codename, state.name)
                    if state_selection not in states_selection_list:
                        states_selection_list.append(state_selection)
    return states_selection_list


class DynamicSelection(fields.Selection):

    workflowable_id = None

    def _description_selection(self, env):
        selection = self.selection
        model = None
        record_id = None
        if self.workflowable_id:
            model = env.context.get('model')
            record_id = self.workflowable_id
        if env.context.get('default_workflowable_id', False):
            model = env.context.get('model')
            record_id = env.context.get('default_workflowable_id')
        elif env.context.get('active_model', False) and env.context.get('active_id', False):
            model = env.context.get('active_model')
            record_id = env.context.get('active_id')
        elif env.context.get('params', False):
            if env.context.get('params').get('model', False) and env.context.get('params').get('id', False):
                model = env.context.get('params').get('model')
                record_id = env.context.get('params').get('id')
            elif env.context.get('params').get('model', False):
                model_name = env.context.get('params').get('model')
                if model_name in ['workflowable', 'workflowable.position']:
                    workflowable_positions = env['workflowable.position'].search([])
                else:
                    workflowable_positions = env['workflowable.position'].search([
                        ('workflowable_id.workflowable_type_id.model_id.model', '=', model_name)
                    ])
                return determine(selection, workflowable_positions.exists())
        elif env.context.get('model', False):
            model = env.context.get('model')
            if env.context.get('id', False):
                record_id = env.context.get('id')
        if model and record_id:
            if env.context.get('workflow_process_id', False):
                if model in ['workflowable', 'workflowable.position']:
                    workflowable_position = env['workflowable.position'].search([
                        '&', ('workflowable_id', '=', record_id),
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
                        return determine(selection, workflowable_position.exists())
            else:
                if model == 'workflowable':
                    workflowable_positions = env['workflowable.position'].search([
                        ('workflowable_id', '=', record_id)
                    ])
                    return determine(selection, workflowable_positions.exists())
                elif model == 'workflowable.position':
                    workflowable_position = env['workflowable.position'].search([
                        ('workflowable_id', '=', record_id)
                    ])
                    if not workflowable_position.exists():
                        workflowable_position = env['workflowable.position'].search([
                            ('id', '=', record_id)
                        ])
                    return determine(selection, workflowable_position.exists())
                else:
                    workflowable = env['workflowable'].search([
                        ('workflowable_type_id.model_id.model', '=', model)
                    ])
                    if workflowable.exists():
                        workflowable_positions = env['workflowable.position'].search([
                            ('workflowable_id', '=', workflowable.id)
                        ])
                        return determine(selection, workflowable_positions.exists())
        else:
            if model in ['workflowable', 'workflowable.position']:
                workflowable_positions = env['workflowable.position'].search([])
                return determine(selection, workflowable_positions.exists())
            else:
                workflowables = env['workflowable'].search([
                    ('workflowable_type_id.model_id.model', '=', model)
                ])
                if workflowables.exists():
                    workflowable_positions = env['workflowable.position'].search([
                        ('workflowable_id', 'in', workflowables.mapped('id'))
                    ])
                    return determine(selection, workflowable_positions.exists())
                return determine(selection, env['workflowable.position'].browse())

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

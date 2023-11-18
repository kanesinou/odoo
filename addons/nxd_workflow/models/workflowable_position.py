# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command
from ..ext import schema


def compute_state_selection(workflowable_position_records):
    states_selection_list = []
    for workflowable_position_record in workflowable_position_records:
        if workflowable_position_record.workflow_process_id:
            states_list = workflowable_position_record.env['workflow.procedure.stage'].search([
                (
                    'root_workflow_procedure_id',
                    '=',
                    workflowable_position_record.workflow_process_id.workflow_procedure_id.id
                )
            ]).mapped('workflow_state_id')
            for state in states_list:
                state_selection = (state.codename, state.name)
                if state_selection not in states_selection_list:
                    states_selection_list.append(state_selection)
    return states_selection_list


def get_current_state(workflowable_position_records):
    states = compute_state_selection(workflowable_position_records)
    for workflowable_position_record in workflowable_position_records:
        for state in states:
            if state[0] == workflowable_position_record.workflow_process_stage_id.workflow_state_id.codename:
                workflowable_position_record.state = state[0]
                break


class WorkflowablePosition(models.Model):
    _name = "workflowable.position"
    _description = "Workflowable Position"
    _sql_constraints = [
        ('position_company_uniq', 'unique (workflowable_id,workflow_process_id,company_id)', 'The workflowable must '
                                                                                             'be unique per workflow '
                                                                                             'process and per company '
                                                                                             '!')
    ]

    @api.onchange('workflow_process_id', 'workflowable_id')
    def _onchange_workflow_process_id(self):
        if self.workflow_process_id.exists() and self.workflowable_id.exists():
            get_current_state(self)

    @api.onchange('workflow_process_stage_id')
    def _onchange_workflow_process_stage(self):
        if self.workflow_process_stage_id.exists():
            self._compute_current_state()

    @api.depends('workflow_process_stage_id', 'state')
    def _compute_current_state(self):
        for position in self:
            states = compute_state_selection(position)
            for state in states:
                if state[0] == position.workflow_process_stage_id.workflow_state_id.codename:
                    position.state = state[0]
                    break

    workflowable_id = fields.Many2one('workflowable', required=True, readonly=True,
                                      string="Workflowable")
    workflow_process_id = fields.Many2one('workflow.process', required=True,
                                          readonly=True, string="Process")
    workflow_process_stage_id = fields.Many2one('workflow.process.stage',
                                                string="Current Stage", required=False)
    state = schema.DynamicSelection(selection=compute_state_selection, string="State", store=True,
                                    required=False, compute="_compute_current_state")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 required=True, default=lambda self: self.env.company)
    active = (fields.Boolean(default=True))

    def read(self, fields=None, load='_classic_read'):
        dynamic_selection_fields = []
        for name in fields:
            field = self._fields.get(name)
            if isinstance(field, schema.DynamicSelection):
                dynamic_selection_fields.append(name)
        for position in self:
            for field_name in dynamic_selection_fields:
                position._fields.get(field_name).workflowable_id = position.workflowable_id.id
        res = super(WorkflowablePosition, self).read(fields, load)
        return res

    def _get_states_list(self):
        states_selection_list = []
        if self.workflow_process_id:
            states_list = self.env['workflow.procedure.stage'].search([
                ('root_workflow_procedure_id', '=', self.workflow_process_id.workflow_procedure_id.id)
            ]).mapped('workflow_state_id')
            for state in states_list:
                states_selection_list.append((state.codename, state.name))
        return states_selection_list

    def _set_state_selection(self):
        if self.workflow_process_id:
            model = self.workflow_process_id.workflowable_id.workflowable_type_id.model_id
            if model:
                state_field = self.env['ir.model.fields'].search([
                    '&', ('model_id', '=', model.id), ('name', '=', 'state')
                ], limit=1)
                if state_field:
                    state_field_selection_commands = []
                    seq = 0
                    for state_selection in self._get_states_list():
                        data = {
                            'sequence': seq, 'value': state_selection[0], 'name': state_selection[1]
                        }
                        seq += 1
                        state_field_selection_commands.append(Command.create(data))
                    if len(state_field_selection_commands) > 0:
                        state_field.write({'selection_ids': state_field_selection_commands})

    def _compute_selection(self):
        return self._get_states_list()

    def compute_current_state(self):
        get_current_state(self)

    def get_next_workflow_states(self):
        procedure_stage = self.workflow_process_stage_id.workflow_procedure_stage_id
        states_list = []
        next_procedure_states = procedure_stage.outbound_workflow_procedure_stage_transition_ids.mapped('to_workflow_procedure_stage_id.workflow_state_id')
        for next_procedure_state in next_procedure_states:
            states_list.append((next_procedure_state.codename, next_procedure_state.name))
        return states_list

    def get_next_stages_data(self):
        procedure_stage = self.workflow_process_stage_id.workflow_procedure_stage_id
        stages_data = []
        next_procedure_stage_transitions = procedure_stage.outbound_workflow_procedure_stage_transition_ids
        for next_procedure_stage_transition in next_procedure_stage_transitions:
            state = next_procedure_stage_transition.to_workflow_procedure_stage_id.workflow_state_id
            action = next_procedure_stage_transition.workflow_stage_transition_id.workflow_state_transition_id.workflow_action_id
            if (action, state) not in stages_data:
                stages_data.append((action, state))
        return stages_data

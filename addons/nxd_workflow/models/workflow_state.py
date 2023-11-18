# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowState(models.Model):
    _name = "workflow.state"
    _description = "Workflow State"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow state must be unique '
                                                                  'per company !')
    ]

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    workflow_stage_ids = fields.One2many('workflow.stage',
                                         'workflow_state_id', string="Workflow Stages")
    workflow_procedure_stage_ids = fields.One2many('workflow.procedure.stage',
                                                   'workflow_state_id',
                                                   string="Procedure Stages")
    workflow_process_stage_ids = fields.One2many('workflow.process.stage',
                                                 'workflow_state_id',
                                                 string="Process Stages")
    inbound_workflow_state_transition_ids = fields.One2many('workflow.state.transition',
                                                            'from_workflow_state_id')
    outbound_workflow_state_transition_ids = fields.One2many('workflow.state.transition',
                                                             'to_workflow_state_id')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

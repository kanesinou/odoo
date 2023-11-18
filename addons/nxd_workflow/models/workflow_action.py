# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowAction(models.Model):
    _name = "workflow.action"
    _description = "Workflow Action"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow action must be unique '
                                                                  'per company !')
    ]

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_action_id',
                                                     string="Process executions")
    workflow_state_transition_ids = fields.One2many('workflow.state.transition',
                                                    'workflow_action_id',
                                                    string="State Transitions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

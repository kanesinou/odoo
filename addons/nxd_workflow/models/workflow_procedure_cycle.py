# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcedureCycle(models.Model):
    _name = "workflow.procedure.cycle"
    _description = "Workflow Procedure Cycle"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow procedure cycle must '
                                                                  'be unique per company !')
    ]

    @api.onchange('workflow_procedure_ids')
    def _onchange_procedures(self):
        if len(self.workflow_procedure_ids) >= 2:
            self.procedure_transitions_allowed = True
        else:
            self.procedure_transitions_allowed = False

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    workflow_process_cycle_ids = fields.One2many('workflow.process.cycle',
                                                 'workflow_procedure_cycle_id')
    workflow_procedure_cycle_duration_ids = fields.One2many('workflow.procedure.cycle.duration',
                                                            'workflow_procedure_cycle_id')
    workflow_procedure_ids = fields.Many2many('workflow.procedure',
                                              'workflow_procedure_cycle_procedure')
    workflow_procedure_transition_ids = fields.Many2many('workflow.procedure.transition',
                                                         'workflow_procedure_cycle_procedure_transition')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    procedure_transitions_allowed = fields.Boolean(readonly=True, default=True)

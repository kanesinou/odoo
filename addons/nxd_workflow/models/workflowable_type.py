# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowableType(models.Model):
    _name = 'workflowable.type'
    _description = "Workflowable Type"
    _sql_constraints = [
        ('model_company_uniq', 'unique (model_id,company_id)', 'The model of the workflowable type must be unique per '
                                                               'company !')
    ]

    @api.depends('workflowable_ids')
    def _compute_has_workflowables(self):
        for workflowable in self:
            workflowable.has_workflowables = len(workflowable.workflowable_ids) > 0

    @api.depends('workflowable_ids')
    def _compute_workflowables_count(self):
        for workflowable in self:
            workflowable.workflowables_count = len(workflowable.workflowable_ids)

    @api.depends('workflow_procedure_ids')
    def _compute_has_procedures(self):
        for workflowable in self:
            workflowable.has_procedures = len(workflowable.workflow_procedure_ids) > 0

    @api.depends('workflow_procedure_ids')
    def _compute_procedures_count(self):
        for workflowable in self:
            workflowable.procedures_count = len(workflowable.workflow_procedure_ids)

    name = fields.Char(string="Name", required=True, readonly=True, related="model_id.name")
    model_id = fields.Many2one('ir.model', required=True, string='Model',
                               auto_join=True, ondelete='cascade')
    workflowable_ids = fields.One2many('workflowable',
                                       'workflowable_type_id')
    workflow_procedure_ids = fields.One2many('workflow.procedure',
                                             'workflowable_type_id')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    has_workflowables = fields.Boolean(readonly=True, compute="_compute_has_workflowables")
    workflowables_count = fields.Integer(readonly=True, compute="_compute_workflowables_count")
    has_procedures = fields.Boolean(readonly=True, compute="_compute_has_procedures")
    procedures_count = fields.Integer(readonly=True, compute="_compute_procedures_count")

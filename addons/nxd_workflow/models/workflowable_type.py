# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowableType(models.Model):
    _name = 'workflowable.type'
    _description = "Workflowable Type"
    _sql_constraints = [
        ('model_company_uniq', 'unique (model_id,company_id)', 'The model of the workflowable type must be unique per '
                                                               'company !')
    ]

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

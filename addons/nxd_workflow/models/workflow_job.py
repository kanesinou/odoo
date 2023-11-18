# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowJob(models.Model):
    _name = "workflow.job"
    _description = "Workflow Job"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow job must be unique '
                                                                  'per company !')
    ]

    codename = fields.Char(string='Codename', required=True, size=64, copy=False)
    name = fields.Char(string='Name', required=True, translate=True)
    workflow_procedure_execution_ids = fields.One2many('workflow.procedure.execution',
                                                       'workflow_job_id')
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_job_id')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

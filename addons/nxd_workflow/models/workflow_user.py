# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowUser(models.Model):
    _name = "workflow.user"
    _description = "Workflow User"

    res_users_id = fields.Many2one('res.users', required=True, string='User',
                                   auto_join=True, ondelete='cascade')
    workflow_procedure_execution_ids = fields.One2many('workflow.procedure.execution',
                                                       'workflow_user_id',
                                                       string="Procedure Executions")
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_user_id',
                                                     string="Process Executions")
    workflow_procedure_collision_ids = fields.One2many('workflow.procedure.collision',
                                                       'workflow_user_id',
                                                       string="Procedure Collisions")
    name = fields.Char(related='res_users_id.name', inherited=True, readonly=False)
    email = fields.Char(related='res_users_id.email', inherited=True, readonly=False)
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

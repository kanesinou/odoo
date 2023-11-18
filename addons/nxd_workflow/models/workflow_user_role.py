# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowUserRole(models.Model):
    _name = "workflow.user.role"
    _description = "Workflow User Role"

    res_groups_id = fields.Many2one('res.groups', required=True, string='Groups',
                                    auto_join=True, ondelete='cascade')
    name = fields.Char(related='res_groups_id.name', inherited=True, readonly=False)
    workflow_procedure_execution_ids = fields.One2many('workflow.procedure.execution',
                                                       'workflow_user_role_id',
                                                       string="Procedure Executions")
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_user_role_id',
                                                     string="Process Executions")
    workflow_procedure_collision_ids = fields.One2many('workflow.procedure.collision',
                                                       'workflow_user_id',
                                                       string="Procedure Collisions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
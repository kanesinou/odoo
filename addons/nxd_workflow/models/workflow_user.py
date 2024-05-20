# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowUser(models.Model):
    _name = "workflow.user"
    _description = "Workflow User"

    @api.depends('workflow_procedure_execution_ids')
    def _compute_has_procedure_executions(self):
        for user in self:
            user.has_procedure_executions = len(user.workflow_procedure_execution_ids) > 0

    @api.depends('workflow_procedure_execution_ids')
    def _compute_procedure_executions_count(self):
        for user in self:
            user.procedure_executions_count = len(user.workflow_procedure_execution_ids)

    @api.depends('workflow_process_execution_ids')
    def _compute_has_process_executions(self):
        for user in self:
            user.has_process_executions = len(user.workflow_process_execution_ids) > 0

    @api.depends('workflow_process_execution_ids')
    def _compute_process_executions_count(self):
        for user in self:
            user.process_executions_count = len(user.workflow_process_execution_ids)

    @api.depends('workflow_procedure_collision_ids')
    def _compute_has_procedure_collisions(self):
        for user in self:
            user.has_procedure_collisions = len(user.workflow_procedure_collision_ids) > 0

    @api.depends('workflow_procedure_collision_ids')
    def _compute_procedure_collisions_count(self):
        for user in self:
            user.procedure_collisions_count = len(user.workflow_procedure_collision_ids)

    res_users_id = fields.Many2one('res.users', required=True, string='User',
                                   auto_join=True, ondelete='cascade')
    name = fields.Char(string="Name", related="res_users_id.name")
    email = fields.Char(string="Email", related="res_users_id.email")
    workflow_procedure_execution_ids = fields.One2many('workflow.procedure.execution',
                                                       'workflow_user_id',
                                                       string="Procedure Executions")
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_user_id',
                                                     string="Process Executions")
    workflow_procedure_collision_ids = fields.One2many('workflow.procedure.collision',
                                                       'workflow_user_id',
                                                       string="Procedure Collisions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    has_procedure_executions = fields.Boolean(readonly=True, compute="_compute_has_procedure_executions")
    procedure_executions_count = fields.Integer(readonly=True, compute="_compute_procedure_executions_count")
    has_process_executions = fields.Boolean(readonly=True, compute="_compute_has_process_executions")
    process_executions_count = fields.Integer(readonly=True, compute="_compute_process_executions_count")
    has_procedure_collisions = fields.Boolean(readonly=True, compute="_compute_has_procedure_collisions")
    procedure_collisions_count = fields.Integer(readonly=True, compute="_compute_procedure_collisions_count")

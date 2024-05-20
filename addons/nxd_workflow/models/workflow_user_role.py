# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowUserRole(models.Model):
    _name = "workflow.user.role"
    _description = "Workflow User Role"

    @api.depends('workflow_procedure_execution_ids')
    def _compute_has_procedure_executions(self):
        for role in self:
            role.has_procedure_executions = len(role.workflow_procedure_execution_ids) > 0

    @api.depends('workflow_procedure_execution_ids')
    def _compute_procedure_executions_count(self):
        for role in self:
            role.procedure_executions_count = len(role.workflow_procedure_execution_ids)

    @api.depends('workflow_process_execution_ids')
    def _compute_has_process_executions(self):
        for role in self:
            role.has_process_executions = len(role.workflow_process_execution_ids) > 0

    @api.depends('workflow_process_execution_ids')
    def _compute_process_executions_count(self):
        for role in self:
            role.process_executions_count = len(role.workflow_process_execution_ids)

    @api.depends('workflow_procedure_collision_ids')
    def _compute_has_procedure_collisions(self):
        for role in self:
            role.has_procedure_collisions = len(role.workflow_procedure_collision_ids) > 0

    @api.depends('workflow_procedure_collision_ids')
    def _compute_procedure_collisions_count(self):
        for role in self:
            role.procedure_collisions_count = len(role.workflow_procedure_collision_ids)

    res_groups_id = fields.Many2one('res.groups', required=True, string='Groups',
                                    auto_join=True, ondelete='cascade')
    name = fields.Char(related='res_groups_id.name', readonly=True, string="Name")
    full_name = fields.Char(string="Full Name", related="res_groups_id.full_name", readonly=True)
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
    has_procedure_executions = fields.Boolean(readonly=True, compute="_compute_has_procedure_executions")
    procedure_executions_count = fields.Integer(readonly=True, compute="_compute_procedure_executions_count")
    has_process_executions = fields.Boolean(readonly=True, compute="_compute_has_process_executions")
    process_executions_count = fields.Integer(readonly=True, compute="_compute_process_executions_count")
    has_procedure_collisions = fields.Boolean(readonly=True, compute="_compute_has_procedure_collisions")
    procedure_collisions_count = fields.Integer(readonly=True, compute="_compute_procedure_collisions_count")

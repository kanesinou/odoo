# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcedureCollision(models.Model):
    _name = "workflow.procedure.collision"
    _description = "Workflow Procedure Collision"

    @api.constrains('workflow_user_id', 'workflow_user_role_id')
    def _check_non_null_user_and_role(self):
        for collision in self:
            if not collision.workflow_user_id and not collision.workflow_user_role_id:
                raise ValidationError(_("Both the user and the role cannot be null. You must enter one of them"))

    @api.depends('workflow_user_id', 'workflow_user_role_id')
    def _compute_name(self):
        for collision in self:
            name_str = collision.workflow_procedure_id.name
            if collision.workflow_user_id:
                name_str += "[%s]" % collision.workflow_user_id.name
            elif collision.workflow_user_role_id:
                name_str += "[%s]" % collision.workflow_user_role_id.name
            collision.name = name_str

    @api.depends('workflow_procedure_id')
    def _compute_root_workflow_procedure(self):
        for collision in self:
            collision.root_workflow_procedure_id = collision.workflow_procedure_id.root_workflow_procedure_id.id

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    workflow_procedure_id = fields.Many2one('workflow.procedure',
                                            required=True, string="Procedure")
    workflow_user_id = fields.Many2one('workflow.user', required=False,
                                       string="User")
    workflow_user_role_id = fields.Many2one('workflow.user.role',
                                            required=False, string="User Role")
    workflow_procedure_stage_ids = fields.Many2many('workflow.procedure.stage',
                                                    'workflow_procedure_collision_stage',
                                                    string="Procedure Stages")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import safe_eval


class WorkflowProcessStageAcl(models.Model):
    _name = "workflow.process.stage.acl"
    _description = "Workflow Process Stage Access Control List"
    _sql_constraints = [
        ('process_stage_uniq', 'unique (workflow_process_stage_id)', 'The workflow process stage must be unique !')
    ]

    @api.onchange('access_workflow_user_ids')
    def _onchange_access_users(self):
        self._compute_is_user_protected()

    @api.onchange('access_workflow_role_ids')
    def _onchange_access_roles(self):
        self._compute_is_role_protected()

    @api.depends('workflow_process_stage_id')
    def _compute_name(self):
        for acl in self:
            acl.name = str(acl.id) + ' Access Control List'
            if acl.workflow_process_stage_id:
                acl.name = acl.workflow_process_stage_id.name + ' Access Control List'

    @api.depends('access_workflow_user_ids')
    def _compute_is_user_protected(self):
        for acl in self:
            acl.is_user_protected = len(acl.access_workflow_user_ids) > 0

    @api.depends('access_workflow_role_ids')
    def _compute_is_role_protected(self):
        for acl in self:
            acl.is_role_protected = len(acl.access_workflow_role_ids) > 0

    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Procedure", store=True,
                                               related="workflow_process_stage_id.root_workflow_process_id")
    workflow_process_stage_id = fields.Many2one('workflow.process.stage', required=False,
                                                string="Process Stage")
    workflow_procedure_stage_acl_id = fields.Many2one('workflow.procedure.stage.acl',
                                                      string="Procedure Stage ACL")
    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    model_name = fields.Char(string="Domain Model", readonly=True, required=False,
                             related="workflow_procedure_stage_acl_id.model_name")
    filter_domain = fields.Text(string="Domain", required=False, readonly=True,
                                related="workflow_procedure_stage_acl_id.filter_domain")
    access_workflow_user_ids = fields.Many2many('workflow.user', string="Granted Users",
                                                relation="workflow_process_stage_acl_access_users",
                                                related="workflow_procedure_stage_acl_id.access_workflow_user_ids")
    access_workflow_role_ids = fields.Many2many('workflow.user.role', string="Granted Roles",
                                                relation="workflow_process_stage_acl_access_roles",
                                                related="workflow_procedure_stage_acl_id.access_workflow_role_ids")
    cancel_workflow_user_ids = fields.Many2many('workflow.user', string="Cancel Granted Users",
                                                relation="workflow_process_stage_acl_cancel_users",
                                                related="workflow_procedure_stage_acl_id.cancel_workflow_user_ids")
    cancel_workflow_role_ids = fields.Many2many('workflow.user.role', string="Cancel Granted Roles",
                                                relation="workflow_process_stage_acl_cancel_roles",
                                                related="workflow_procedure_stage_acl_id.cancel_workflow_role_ids")
    break_workflow_user_ids = fields.Many2many('workflow.user', string="Break Granted Users",
                                               relation="workflow_process_stage_acl_break_users",
                                                related="workflow_procedure_stage_acl_id.break_workflow_user_ids")
    break_workflow_role_ids = fields.Many2many('workflow.user.role', string="Break Granted Roles",
                                               relation="workflow_process_stage_acl_break_roles",
                                                related="workflow_procedure_stage_acl_id.break_workflow_role_ids")
    resume_workflow_user_ids = fields.Many2many('workflow.user', string="Resume Granted Users",
                                                relation="workflow_process_stage_acl_resume_users",
                                                related="workflow_procedure_stage_acl_id.resume_workflow_user_ids")
    resume_workflow_role_ids = fields.Many2many('workflow.user.role', string="Resume Granted Roles",
                                                relation="workflow_process_stage_acl_resume_roles",
                                                related="workflow_procedure_stage_acl_id.resume_workflow_role_ids")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    is_user_protected = fields.Boolean(readonly=True, store=True, compute="_compute_is_user_protected")
    is_role_protected = fields.Boolean(readonly=True, store=True, compute="_compute_is_role_protected")

    def eval_filter_domain(self, context=False):
        self.ensure_one()
        if not context:
            context = self.env.context
        domain_filter = safe_eval.safe_eval(self.filter_domain, context)
        return self.env[self.model_name].search(domain_filter)

    def user_can_access(self, workflow_user):
        self.ensure_one()
        if self.env.is_superuser() or self.env.is_admin() or self.env.is_system():
            return True
        if workflow_user in self.access_workflow_user_ids:
            return True
        for access_role in self.access_workflow_role_ids:
            if workflow_user.res_users_id.has_group(access_role.name):
                return True
        return False

    def user_can_cancel(self, workflow_user):
        self.ensure_one()
        if self.env.is_superuser() or self.env.is_admin() or self.env.is_system():
            return True
        if not self.user_can_access(workflow_user):
            return False
        if workflow_user in self.cancel_workflow_user_ids:
            return True
        for cancel_role in self.cancel_workflow_role_ids:
            if workflow_user.res_users_id.has_group(cancel_role.name):
                return True
        return False

    def user_can_break(self, workflow_user):
        self.ensure_one()
        if self.env.is_superuser() or self.env.is_admin() or self.env.is_system():
            return True
        if not self.user_can_access(workflow_user):
            return False
        if workflow_user in self.break_workflow_user_ids:
            return True
        for break_role in self.break_workflow_role_ids:
            if workflow_user.res_users_id.has_group(break_role.name):
                return True
        return False

    def user_can_resume(self, workflow_user):
        self.ensure_one()
        if self.env.is_superuser() or self.env.is_admin() or self.env.is_system():
            return True
        if not self.user_can_access(workflow_user):
            return False
        if workflow_user in self.resume_workflow_user_ids:
            return True
        for resume_role in self.resume_workflow_role_ids:
            if workflow_user.res_users_id.has_group(resume_role.name):
                return True
        return False

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval


class WorkflowProcedureStageAcl(models.Model):
    _name = "workflow.procedure.stage.acl"
    _description = "Workflow Procedure Stage Access Control List"
    _sql_constraints = [
        ('procedure_stage_uniq', 'unique (workflow_procedure_stage_id)', 'The workflow procedure stage must be unique !')
    ]

    @api.constrains('workflow_procedure_stage_id', 'access_workflow_user_ids', 'access_workflow_role_ids')
    def _check_non_empty_acl(self):
        for acl in self:
            if acl.workflow_procedure_stage_id and len(acl.access_workflow_user_ids) == 0 and len(acl.access_workflow_role_ids) == 0:
                raise ValidationError(_("Access Control List must define at least user or role !"))

    @api.depends('workflow_procedure_stage_id')
    def _compute_name(self):
        for acl in self:
            acl.name = str(acl.id) + ' Access Control List'
            if acl.workflow_procedure_stage_id:
                acl.name = acl.workflow_procedure_stage_id.name + ' Access Control List'

    @api.depends('root_workflow_procedure_id')
    def _compute_model_name(self):
        for acl in self:
            acl.model_name = None
            if acl.root_workflow_procedure_id:
                acl.model_name = acl.root_workflow_procedure_id.model_name

    @api.depends('access_workflow_user_ids')
    def _compute_access_users_count(self):
        for acl in self:
            acl.access_users_count = len(acl.access_workflow_user_ids)

    @api.depends('access_workflow_role_ids')
    def _compute_access_roles_count(self):
        for acl in self:
            acl.access_roles_count = len(acl.access_workflow_role_ids)

    @api.depends('access_users_count')
    def _compute_is_user_protected(self):
        for acl in self:
            acl.is_user_protected = acl.access_users_count > 0

    @api.depends('access_roles_count')
    def _compute_is_role_protected(self):
        for acl in self:
            acl.is_role_protected = acl.access_roles_count > 0

    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 related="workflow_procedure_stage_id.root_workflow_procedure_id")
    workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage', required=False,
                                                string="Procedure Stage")
    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    model_name = fields.Char(string="Domain Model", readonly=True, required=False,
                             compute="_compute_model_name")
    filter_domain = fields.Text(string="Domain", required=False)
    workflow_process_stage_acl_ids = fields.One2many('workflow.process.stage.acl',
                                                     'workflow_procedure_stage_acl_id',
                                                     string="Process Stage ACLs")
    access_workflow_user_ids = fields.Many2many('workflow.user', string="Access Granted Users",
                                                relation="workflow_procedure_stage_acl_access_users")
    access_workflow_role_ids = fields.Many2many('workflow.user.role', string="Access Granted Roles",
                                                relation="workflow_procedure_stage_acl_access_roles")
    cancel_workflow_user_ids = fields.Many2many('workflow.user', string="Cancel Granted Users",
                                                relation="workflow_procedure_stage_acl_cancel_users")
    cancel_workflow_role_ids = fields.Many2many('workflow.user.role', string="Cancel Granted Roles",
                                                relation="workflow_procedure_stage_acl_cancel_roles")
    break_workflow_user_ids = fields.Many2many('workflow.user', string="Break Granted Users",
                                               relation="workflow_procedure_stage_acl_break_users")
    break_workflow_role_ids = fields.Many2many('workflow.user.role', string="Break Granted Roles",
                                               relation="workflow_procedure_stage_acl_break_roles")
    resume_workflow_user_ids = fields.Many2many('workflow.user', string="Resume Granted Users",
                                                relation="workflow_procedure_stage_acl_resume_users")
    resume_workflow_role_ids = fields.Many2many('workflow.user.role', string="Resume Granted Roles",
                                                relation="workflow_procedure_stage_acl_resume_roles")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    access_users_count = fields.Integer(readonly=True, compute="_compute_access_users_count")
    access_roles_count = fields.Integer(readonly=True, compute="_compute_access_roles_count")
    is_user_protected = fields.Boolean(readonly=True, store=True, compute="_compute_is_user_protected")
    is_role_protected = fields.Boolean(readonly=True, store=True, compute="_compute_is_role_protected")

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        records = super(WorkflowProcedureStageAcl, self).create(vals_list)
        for record in records:
            if len(record.access_workflow_user_ids) > 0:
                record.write({'is_user_protected': True})
            else:
                record.write({'is_user_protected': False})
            if len(record.access_workflow_role_ids) > 0:
                record.write({'is_role_protected': True})
            else:
                record.write({'is_role_protected': False})
        return records

    def eval_filter_domain(self, context=False):
        self.ensure_one()
        if not context:
            context = self.env.context
        domain_filter = safe_eval.safe_eval(self.filter_domain, context)
        return self.env[self.model_name].search(domain_filter)

    def get_corresponding_process_stage_acl_data(self):
        self.ensure_one()
        return {'workflow_procedure_stage_acl_id': self.id}

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

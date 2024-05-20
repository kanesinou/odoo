# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import safe_eval


class WorkflowProcessStageTransitionAcl(models.Model):
    _name = "workflow.process.stage.transition.acl"
    _description = "Workflow Process Stage Transition Access Control List"
    _sql_constraints = [
        ('process_stage_transition_uniq', 'unique (workflow_process_stage_transition_id)', 'The workflow process '
                                                                                           'stage transition must be '
                                                                                           'unique !')
    ]

    @api.depends('workflow_process_stage_transition_id')
    def _compute_name(self):
        for acl in self:
            acl.name = acl.workflow_process_stage_transition_id.name + ' Access Control List'

    @api.depends('root_workflow_process_id')
    def _compute_model_name(self):
        for acl in self:
            acl.model_name = None
            if acl.root_workflow_process_id:
                acl.model_name = acl.root_workflow_process_id.workflow_procedure_id.workflowable_type_id.model_id.model

    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Procedure", store=True,
                                               related="workflow_process_stage_transition_id.root_workflow_process_id")
    workflow_process_stage_transition_id = fields.Many2one('workflow.process.stage.transition',
                                                           required=False, string="Process Stage Transition")
    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    model_name = fields.Char(string="Domain Model", readonly=True, required=False,
                             related="workflow_procedure_stage_transition_acl_id.model_name")
    filter_domain = fields.Text(string="Domain", required=False, readonly=True,
                                related="workflow_procedure_stage_transition_acl_id.filter_domain")
    workflow_procedure_stage_transition_acl_id = fields.Many2one('workflow.procedure.stage.transition.acl',
                                                                 string="Procedure Stage Transition ACL")
    workflow_user_ids = fields.Many2many('workflow.user', string="Granted Users",
                                         relation="workflow_process_stage_transition_acl_users",
                                         related="workflow_procedure_stage_transition_acl_id.workflow_user_ids")
    workflow_role_ids = fields.Many2many('workflow.user.role', string="Granted Roles",
                                         relation="workflow_process_stage_transition_acl_roles",
                                         related="workflow_procedure_stage_transition_acl_id.workflow_role_ids")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    def eval_filter_domain(self, context=False):
        self.ensure_one()
        if not context:
            context = self.env.context
        domain_filter = safe_eval.safe_eval(self.filter_domain, context)
        return self.env[self.model_name].search(domain_filter)

    def user_can_execute(self, workflow_user):
        self.ensure_one()
        if self.env.is_superuser() or self.env.is_admin() or self.env.is_system():
            return True
        if workflow_user in self.workflow_user_ids:
            return True
        for access_role in self.workflow_role_ids:
            if workflow_user.res_users_id.has_group(access_role.name):
                return True
        return False

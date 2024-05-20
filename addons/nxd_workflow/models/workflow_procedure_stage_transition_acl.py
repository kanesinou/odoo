# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval


class WorkflowProcedureStageTransitionAcl(models.Model):
    _name = "workflow.procedure.stage.transition.acl"
    _description = "Workflow Procedure Stage Transition Access Control List"
    _sql_constraints = [
        ('procedure_stage_transition_uniq', 'unique (workflow_procedure_stage_transition_id)', 'The workflow '
                                                                                               'procedure stage '
                                                                                               'transition must be '
                                                                                               'unique !')
    ]

    @api.constrains('workflow_procedure_stage_transition_id', 'workflow_user_ids', 'workflow_role_ids')
    def _check_non_empty_acl(self):
        for acl in self:
            if acl.workflow_procedure_stage_transition_id and len(acl.workflow_user_ids) == 0 and len(acl.workflow_role_ids) == 0:
                raise ValidationError(_("Access Control List must define at least user or role !"))

    @api.depends('workflow_procedure_stage_transition_id')
    def _compute_name(self):
        for acl in self:
            acl.name = acl.workflow_procedure_stage_transition_id.name + ' Access Control List'

    @api.depends('root_workflow_procedure_id')
    def _compute_model_name(self):
        for acl in self:
            acl.model_name = None
            if acl.root_workflow_procedure_id:
                acl.model_name = acl.root_workflow_procedure_id.model_name

    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 related="workflow_procedure_stage_transition_id.root_workflow_procedure_id")
    workflow_procedure_stage_transition_id = fields.Many2one('workflow.procedure.stage.transition',
                                                             required=False, string="Procedure Stage Transition")
    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    model_name = fields.Char(string="Domain Model", readonly=True, required=False,
                             compute="_compute_model_name")
    filter_domain = fields.Text(string="Domain", required=False)
    workflow_process_stage_transition_acl_ids = fields.One2many('workflow.process.stage.transition.acl',
                                                                'workflow_procedure_stage_transition_acl_id',
                                                                string="Process Stage Transition ACLs")
    workflow_user_ids = fields.Many2many('workflow.user', string="Granted Users",
                                         relation="workflow_procedure_stage_transition_acl_users")
    workflow_role_ids = fields.Many2many('workflow.user.role', string="Granted Roles",
                                         relation="workflow_procedure_stage_transition_acl_roles")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    def eval_filter_domain(self, context=False):
        self.ensure_one()
        if not context:
            context = self.env.context
        domain_filter = safe_eval.safe_eval(self.filter_domain, context)
        return self.env[self.model_name].search(domain_filter)

    def get_corresponding_process_stage_transition_acl_data(self, workflowable_record):
        self.ensure_one()
        data = {
            'workflow_procedure_stage_transition_acl_id': self.id,
            'filter_domain': self.filter_domain,
            'workflow_user_ids': self.workflow_user_ids,
            'workflow_role_ids': self.workflow_role_ids
        }
        return data

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

# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcedureStageAclWizard(models.TransientModel):
    _name = "workflow.procedure.stage.acl.wizard"
    _description = "Configure Procedure Stage Access Control List"

    @api.depends('workflow_procedure_stage_id')
    def _compute_model_name(self):
        for acl in self:
            acl.model_name = None
            if acl.workflow_procedure_stage_id:
                acl.model_name = acl.workflow_procedure_stage_id.root_workflow_procedure_id.model_name

    workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage', required=True,
                                                  readonly=True)
    model_name = fields.Char(string="Domain Model", readonly=True, required=False,
                             compute="_compute_model_name")
    filter_domain = fields.Text(string="Domain", required=False)
    access_workflow_user_ids = fields.Many2many('workflow.user', string="Access Granted Users",
                                                relation="workflow_procedure_stage_acl_wizard_access_users")
    access_workflow_role_ids = fields.Many2many('workflow.user.role', string="Access Granted Roles",
                                                relation="workflow_procedure_stage_acl_wizard_access_roles")
    cancel_workflow_user_ids = fields.Many2many('workflow.user', string="Cancel Granted Users",
                                                relation="workflow_procedure_stage_acl_wizard_cancel_users")
    cancel_workflow_role_ids = fields.Many2many('workflow.user.role', string="Cancel Granted Roles",
                                                relation="workflow_procedure_stage_acl_wizard_cancel_roles")
    break_workflow_user_ids = fields.Many2many('workflow.user', string="Break Granted Users",
                                               relation="workflow_procedure_stage_acl_wizard_break_users")
    break_workflow_role_ids = fields.Many2many('workflow.user.role', string="Break Granted Roles",
                                               relation="workflow_procedure_stage_acl_wizard_break_roles")
    resume_workflow_user_ids = fields.Many2many('workflow.user', string="Resume Granted Users",
                                                relation="workflow_procedure_stage_acl_wizard_resume_users")
    resume_workflow_role_ids = fields.Many2many('workflow.user.role', string="Resume Granted Roles",
                                                relation="workflow_procedure_stage_acl_wizard_resume_roles")

    def create_procedure_stage_acl_from_wizard(self):
        if self.workflow_procedure_stage_id and (len(self.access_workflow_user_ids) > 0 or len(self.access_workflow_role_ids) > 0):
            data = {'workflow_procedure_stage_id': self.workflow_procedure_stage_id.id}
            if self.filter_domain:
                data['filter_domain'] = self.filter_domain
            if self.access_workflow_user_ids:
                data['access_workflow_user_ids'] = self.access_workflow_user_ids.mapped('id')
            if self.access_workflow_role_ids:
                data['access_workflow_role_ids'] = self.access_workflow_role_ids.mapped('id')
            if self.cancel_workflow_user_ids:
                data['cancel_workflow_user_ids'] = self.cancel_workflow_user_ids.mapped('id')
            if self.cancel_workflow_role_ids:
                data['cancel_workflow_role_ids'] = self.cancel_workflow_role_ids.mapped('id')
            if self.break_workflow_user_ids:
                data['break_workflow_user_ids'] = self.break_workflow_user_ids.mapped('id')
            if self.break_workflow_role_ids:
                data['break_workflow_role_ids'] = self.break_workflow_role_ids.mapped('id')
            if self.resume_workflow_user_ids:
                data['resume_workflow_user_ids'] = self.resume_workflow_user_ids.mapped('id')
            if self.resume_workflow_role_ids:
                data['resume_workflow_role_ids'] = self.resume_workflow_role_ids.mapped('id')
            self.env['workflow.procedure.stage.acl'].create(data)

# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcedureStageTransitionAclWizard(models.TransientModel):
    _name = "workflow.procedure.stage.transition.acl.wizard"
    _description = "Configure Procedure Stage Transition Access Control List"

    @api.depends('workflow_procedure_stage_transition_id')
    def _compute_model_name(self):
        for acl in self:
            acl.model_name = None
            if acl.workflow_procedure_stage_transition_id:
                acl.model_name = acl.workflow_procedure_stage_transition_id.root_workflow_procedure_id.model_name

    workflow_procedure_stage_transition_id = fields.Many2one('workflow.procedure.stage.transition',
                                                             required=True, readonly=True)
    model_name = fields.Char(string="Domain Model", readonly=True, required=False,
                             compute="_compute_model_name")
    filter_domain = fields.Text(string="Domain", required=False)
    workflow_user_ids = fields.Many2many('workflow.user', string="Granted Users",
                                         relation="workflow_procedure_stage_transition_wizard_acl_users")
    workflow_role_ids = fields.Many2many('workflow.user.role', string="Granted Roles",
                                         relation="workflow_procedure_stage_transition_wizard_acl_roles")

    def create_procedure_stage_transition_acl_from_wizard(self):
        if self.workflow_procedure_stage_transition_id and (len(self.workflow_user_ids) > 0 or len(self.workflow_role_ids) > 0):
            data = {
                'workflow_procedure_stage_transition_id': self.workflow_procedure_stage_transition_id.id
            }
            if self.filter_domain:
                data['filter_domain'] = self.filter_domain
            if len(self.workflow_user_ids) > 0:
                data['workflow_user_ids'] = self.workflow_user_ids.mapped('id')
            if len(self.workflow_role_ids) > 0:
                data['workflow_role_ids'] = self.workflow_role_ids.mapped('id')
            self.env['workflow.procedure.stage.transition.acl'].create(data)

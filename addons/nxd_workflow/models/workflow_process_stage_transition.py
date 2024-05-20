# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcessStageTransition(models.Model):
    _name = "workflow.process.stage.transition"
    _description = "Workflow Process Stage Transition"

    @api.constrains('workflow_process_id', 'workflow_process_transition_id')
    def _check_transition_context(self):
        for transition in self:
            if not transition.workflow_process_id and not transition.workflow_process_transition_id:
                raise ValidationError(_("A process stage transition must occur either in a workflow process or a "
                                        "process transition context !"))
            elif transition.workflow_process_id and transition.workflow_process_transition_id:
                raise ValidationError(_("The context of the transition must be unique. Set either a workflow "
                                        "process or workflow process transition, not both !"))

    @api.constrains('can_return', 'return_action_name')
    def _check_return_setting(self):
        for transition in self:
            if transition.can_return and not transition.return_action_name:
                raise ValidationError(_('If the transition can return, the return action name must be set !'))

    @api.onchange('workflow_process_id', 'workflow_process_transition_id')
    def _onchange_transition_context(self):
        if self.workflow_process_id and not self.workflow_process_transition_id:
            self.context_type = 'sibling'
        elif not self.workflow_process_id and self.workflow_process_transition_id:
            self.context_type = 'transition'

    @api.depends('from_workflow_process_stage_id', 'to_workflow_process_stage_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_process_stage_id:
                name_str = transition.from_workflow_process_stage_id.name
            name_str += ' ---> '
            if transition.to_workflow_process_stage_id:
                name_str += transition.to_workflow_process_stage_id.name
            transition.name = name_str

    @api.depends('from_workflow_process_stage_id', 'to_workflow_process_stage_id')
    def _compute_cross_border(self):
        for transition in self:
            if transition.from_workflow_process_stage_id.parent_id != transition.to_workflow_process_stage_id.parent_id:
                transition.cross_border = True
            else:
                transition.cross_border = False

    @api.depends('workflow_process_stage_transition_acl_ids')
    def _compute_is_protected(self):
        for stage in self:
            stage.is_protected = len(stage.workflow_process_stage_transition_acl_ids) > 0

    @api.depends('workflow_process_stage_transition_acl_ids')
    def _compute_is_execution_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_execution_protected = False
            else:
                acl = stage.workflow_process_stage_transition_acl_ids[0]
                stage.is_execution_protected = len(acl.workflow_user_ids) > 0 or len(acl.workflow_role_ids)

    @api.depends('from_workflow_process_stage_id')
    def _compute_has_executions(self):
        for transition in self:
            transition.has_executions = False
            if len(transition.get_process_stage_executions()) > 0:
                transition.has_executions = True

    @api.depends('from_workflow_process_stage_id')
    def _compute_has_mandatory_executions(self):
        for transition in self:
            transition.has_mandatory_executions = False
            if len(transition.get_mandatory_process_stage_executions()) > 0:
                transition.has_mandatory_executions = True

    @api.depends('from_workflow_process_stage_id')
    def _compute_has_optional_executions(self):
        for transition in self:
            transition.has_optional_executions = False
            if len(transition.get_optional_process_stage_executions()) > 0:
                transition.has_optional_executions = True

    @api.depends('from_workflow_process_stage_id', 'has_executions', 'has_mandatory_executions', 'has_optional_executions')
    def _compute_has_job_done(self):
        for transition in self:
            if not transition.has_executions:
                transition.has_job_done = True
            else:
                transition.has_job_done = True
                for execution in transition.get_mandatory_process_stage_executions():
                    if not execution.is_complete:
                        transition.has_job_done = False
                        return
                if len(transition.get_optional_process_stage_executions().filtered(
                    lambda e: e.is_complete
                )) == 0:
                    transition.has_job_done = False

    @api.depends('job_done_required', 'has_job_done')
    def _compute_can_be_executed(self):
        for transition in self:
            transition.can_be_executed = False
            if not transition.job_done_required:
                transition.can_be_executed = True
            elif transition.has_job_done:
                transition.can_be_executed = True

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=True,
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')])
    transition_datetime = fields.Datetime(string="Transition Datetime", copy=False,
                                          required=True)
    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               related="from_workflow_process_stage_id.root_workflow_process_id")
    from_workflow_process_stage_id = fields.Many2one('workflow.process.stage', required=True,
                                                     string="From Process Stage")
    to_workflow_process_stage_id = fields.Many2one('workflow.process.stage', required=True,
                                                   string="To Process Stage")
    workflow_procedure_stage_transition_id = fields.Many2one('workflow.procedure.stage.transition',
                                                             required=True,
                                                             string="To Procedure Stage Transition")
    workflow_process_id = fields.Many2one('workflow.process', required=False,
                                          string="Process")
    workflow_process_transition_id = fields.Many2one('workflow.process.transition',
                                                     required=False, string="Process Transition")
    job_done_required = fields.Boolean(string="Job Done Required",
                                       related="workflow_procedure_stage_transition_id.job_done_required")
    can_return = fields.Boolean(string="Can Return",
                                related="workflow_procedure_stage_transition_id.can_return")
    return_action_name = fields.Char(string="Return Action Name", required=False,
                                     related="workflow_procedure_stage_transition_id.return_action_name")
    return_action_title = fields.Char(string='Return Action Title',
                                      related="workflow_procedure_stage_transition_id.return_action_title")
    action_name = fields.Char(string="Action Name",
                              related="workflow_procedure_stage_transition_id.action_name")
    action_title = fields.Char(string='Action Title', required=False, translate=True,
                               related="workflow_procedure_stage_transition_id.action_title")
    button_type = fields.Selection(string="Button Type",
                                   related="workflow_procedure_stage_transition_id.button_type")
    workflow_user_id = fields.Many2one('workflow.user', readonly=True, required=False,
                                       string="User")
    workflow_process_stage_transition_acl_ids = fields.One2many('workflow.process.stage.transition.acl',
                                                                'workflow_process_stage_transition_id',
                                                                string="Process Stage Transition Access Control List")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cross_border = fields.Boolean(readonly=True, compute="_compute_cross_border")
    is_protected = fields.Boolean(readonly=True, compute="_compute_is_protected")
    is_execution_protected = fields.Boolean(readonly=True, compute="_compute_is_execution_protected")
    has_executions = fields.Boolean(readonly=True, compute="_compute_has_executions")
    has_mandatory_executions = fields.Boolean(readonly=True, compute="_compute_has_mandatory_executions")
    has_optional_executions = fields.Boolean(readonly=True, compute="_compute_has_optional_executions")
    has_job_done = fields.Boolean(readonly=True, compute="_compute_has_job_done")
    can_be_executed = fields.Boolean(readonly=True, compute="_compute_can_be_executed")

    def user_can_execute(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_execution_protected:
            return True
        else:
            return self.workflow_process_stage_transition_acl_ids[0].user_can_execute(workflow_user)

    def get_process_stage_executions(self):
        self.ensure_one()
        return self.from_workflow_process_stage_id.workflow_process_execution_ids

    def get_mandatory_process_stage_executions(self):
        self.ensure_one()
        return self.from_workflow_process_stage_id.workflow_process_execution_ids.filtered(
            lambda e: e.mandatory
        )

    def get_optional_process_stage_executions(self):
        self.ensure_one()
        return self.from_workflow_process_stage_id.workflow_process_execution_ids.filtered(
            lambda e: not e.mandatory
        )

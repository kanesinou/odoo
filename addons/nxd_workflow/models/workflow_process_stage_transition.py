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

    @api.depends('workflow_process_id', 'workflow_process_transition_id')
    def _compute_root_workflow_process(self):
        for transition in self:
            if transition.workflow_process_id:
                transition.root_workflow_process_id = transition.workflow_process_id.root_workflow_process_id.id
                if not self.workflow_process_transition_id:
                    self.context_type = 'sibling'
            else:
                transition.root_workflow_process_id = transition.workflow_process_transition_id.root_workflow_process_id.id
                if not self.workflow_process_id:
                    self.context_type = 'transition'

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=True,
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')])
    transition_datetime = fields.Datetime(string="Transition Datetime", copy=False,
                                          required=True)
    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               compute="_compute_root_workflow_process")
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
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cross_border = fields.Boolean(readonly=True, compute="_compute_cross_border")

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcessTransition(models.Model):
    _name = "workflow.process.transition"
    _description = "Workflow Process Transition"

    @api.constrains('workflow_process_id', 'workflow_process_transition_id')
    def _check_transition_context(self):
        for transition in self:
            if not transition.workflow_process_id and not transition.workflow_process_transition_id:
                raise ValidationError(_("A process transition must occur either in a workflow process or a process "
                                        "transition context !"))
            elif transition.workflow_process_id and transition.workflow_process_transition_id:
                raise ValidationError(_("The context of the transition must be unique. Set either a workflow process "
                                        "or workflow process transition, not both !"))

    @api.onchange('workflow_process_id', 'workflow_process_transition_id')
    def _onchange_transition_context(self):
        if self.workflow_process_id and not self.workflow_process_transition_id:
            self.context_type = 'sibling'
        elif not self.workflow_process_id and self.workflow_process_transition_id:
            self.context_type = 'transition'

    @api.depends('from_workflow_process_id', 'to_workflow_process_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_process_id:
                name_str = transition.from_workflow_process_id.name
            name_str += ' ---> '
            if transition.to_workflow_process_id:
                name_str += transition.to_workflow_process_id.name
            transition.name = name_str

    @api.depends('from_workflow_process_id', 'to_workflow_process_id')
    def _compute_cross_border(self):
        for transition in self:
            if transition.from_workflow_process_id.parent_id != transition.to_workflow_process_id.parent_id:
                transition.cross_border = True
            else:
                transition.cross_border = False

    @api.depends("workflow_process_stage_transition_ids", "has_stage_transitions")
    def _compute_has_stage_transitions(self):
        for transition in self:
            if len(transition.workflow_process_stage_transition_ids) > 0:
                transition.has_stage_transitions = True
            else:
                transition.has_stage_transitions = False

    @api.depends("workflow_process_transition_ids", "has_process_transitions")
    def _compute_has_process_transitions(self):
        for transition in self:
            if len(transition.workflow_process_transition_ids) > 0:
                transition.has_process_transitions = True
            else:
                transition.has_process_transitions = False

    @api.depends('workflow_process_id', 'workflow_process_transition_id')
    def _compute_root_workflow_process(self):
        for transition in self:
            if transition.workflow_process_id:
                transition.root_workflow_process_id = transition.workflow_process_id.root_workflow_process_id.id
                if not self.workflow_process_id:
                    self.context_type = 'sibling'
            else:
                transition.root_workflow_process_id = transition.workflow_process_transition_id.root_workflow_process_id.id
                if not self.workflow_process_transition_id:
                    self.context_type = 'transition'

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=True,
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')])
    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               compute="_compute_root_workflow_process")
    from_workflow_process_id = fields.Many2one('workflow.process', required=True,
                                               string="From Process")
    to_workflow_process_id = fields.Many2one('workflow.process', required=True,
                                             string="To Process")
    workflow_process_id = fields.Many2one('workflow.process', required=False,
                                          string="Process")
    workflow_process_transition_id = fields.Many2one('workflow.process.transition',
                                                     required=False,
                                                     string="Context Processes Transition")
    workflow_procedure_transition_id = fields.Many2one('workflow.procedure.transition',
                                                       required=True, string="Procedure Transition")
    workflow_process_stage_transition_ids = fields.One2many('workflow.process.stage.transition',
                                                            'workflow_process_transition_id',
                                                            string="Process Stage Transitions")
    workflow_process_transition_ids = fields.One2many('workflow.process.transition',
                                                      'workflow_process_transition_id',
                                                      string="Procedure Transitions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cross_border = fields.Boolean(default=False, readonly=True, compute="_compute_cross_border")
    has_stage_transitions = fields.Boolean(readonly=True, compute="_compute_has_stage_transitions")
    has_process_transitions = fields.Boolean(readonly=True, compute="_compute_has_process_transitions")

    def get_workflow_process_stage_transitions_by_id(self, workflow_process_transition_id):
        return self.workflow_process_stage_transition_ids.filtered(
            lambda t: t.id == workflow_process_transition_id
        )

    def get_workflow_process_stage_transition_by_id(self, workflow_process_transition_id):
        records = self.get_workflow_process_stage_transitions_by_id(
            workflow_process_transition_id
        )
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_stage_transitions_by_ids(self, workflow_process_transition_ids):
        return self.workflow_process_stage_transition_ids.filtered(
            lambda t: t.id in workflow_process_transition_ids
        )

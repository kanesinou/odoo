# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowStageTransition(models.Model):
    _name = "workflow.stage.transition"
    _description = "Workflow Stage Transition"

    @api.constrains('workflow_id', 'workflow_transition_id')
    def _check_transition_context(self):
        for transition in self:
            if not transition.workflow_id and not transition.workflow_transition_id:
                raise ValidationError(_("A workflow stage transition must occur either in a workflow or a workflow "
                                        "transition context !"))
            elif transition.workflow_id and transition.workflow_transition_id:
                raise ValidationError(_("The context of the transition must be unique. Set either a workflow or "
                                        "workflow transition, not both !"))
            elif transition.workflow_id and not transition.workflow_id.activity_workflow:
                raise ValidationError(_("The context of a workflow stage transition must be either an activity "
                                        "workflow or a transition between two activity workflows !"))
            elif transition.workflow_transition_id and not transition.workflow_transition_id.activity_workflow:
                raise ValidationError(_("The context of a workflow stage transition must be either an activity "
                                        "workflow or a transition between two activity workflows !"))

    @api.onchange('from_workflow_stage_id', 'to_workflow_stage_id', 'workflow_state_transition_id')
    def _onchange_from_and_to_stages(self):
        if self.from_workflow_stage_id and self.to_workflow_stage_id:
            return {
                'domain': {
                    'workflow_state_transition_id': [
                       '&',
                        ('from_workflow_state_id', '=', self.from_workflow_stage_id.workflow_state_id.id),
                        ('to_workflow_state_id', '=', self.to_workflow_stage_id.workflow_state_id.id)
                    ]
                }
            }
        elif self.workflow_state_transition_id:
            from_stage_id = self.env['workflow.stage'].search([
                ('workflow_state_id', '=', self.workflow_state_transition_id.from_workflow_state_id.id)
            ], limit=1)
            to_stage_id = self.env['workflow.stage'].search([
                ('workflow_state_id', '=', self.workflow_state_transition_id.to_workflow_state_id.id)
            ], limit=1)
            domain = {'domain': {}}
            if from_stage_id:
                self.from_workflow_stage_id = from_stage_id.id
                domain['domain']['from_workflow_stage_id'] = [
                    ('workflow_state_id', '=', self.workflow_state_transition_id.from_workflow_state_id.id)
                ]
            if to_stage_id:
                self.to_workflow_stage_id = to_stage_id.id
                domain['domain']['to_workflow_stage_id'] = [
                    ('workflow_state_id', '=', self.workflow_state_transition_id.to_workflow_state_id.id)
                ]
            if domain['domain']:
                return domain

    @api.onchange('from_workflow_stage_id')
    def _onchange_from_workflow_stage(self):
        if self.from_workflow_stage_id:
            if self.workflow_state_transition_id:
                domain = {
                    'from_workflow_stage_id': [
                        ('workflow_state_id', '=', self.workflow_state_transition_id.from_workflow_state_id.id)
                    ],
                    'to_workflow_stage_id': [
                        ('workflow_state_id', '=', self.workflow_state_transition_id.to_workflow_state_id.id)
                    ]
                }
            else:
                excluded_to_stages = []
                excluded_to_stage_ids = [self.from_workflow_stage_id.id]
                if self.workflow_id:
                    excluded_to_stages = self.env['workflow.stage.transition'].search([
                        '&', ('workflow_id', '=', self.workflow_id.id),
                        ('from_workflow_stage_id', '=', self.from_workflow_stage_id.id)
                    ]).mapped('to_workflow_stage_id')
                elif self.workflow_transition_id:
                    excluded_to_stages = self.env['workflow.stage.transition'].search([
                        '&', ('workflow_transition_id', '=', self.workflow_transition_id.id),
                        ('from_workflow_stage_id', '=', self.from_workflow_stage_id.id)
                    ]).mapped('to_workflow_stage_id')
                for stage in excluded_to_stages:
                    excluded_to_stage_ids.append(stage.id)
                domain = {
                    'to_workflow_stage_id': [
                        '!', ('id', 'in', excluded_to_stage_ids)
                    ]
                }
            return {'domain': domain}

    @api.onchange('to_workflow_stage_id')
    def _onchange_to_workflow_stage(self):
        if self.to_workflow_stage_id:
            if self.workflow_state_transition_id:
                domain = {
                    'from_workflow_stage_id': [
                        ('workflow_state_id', '=', self.workflow_state_transition_id.from_workflow_state_id.id)
                    ],
                    'to_workflow_stage_id': [
                        ('workflow_state_id', '=', self.workflow_state_transition_id.to_workflow_state_id.id)
                    ]
                }
            else:
                excluded_from_stages = []
                excluded_from_stage_ids = [self.to_workflow_stage_id.id]
                if self.workflow_id:
                    excluded_from_stages = self.env['workflow.stage.transition'].search([
                        '&', ('workflow_id', '=', self.workflow_id.id),
                        ('to_workflow_stage_id', '=', self.to_workflow_stage_id.id)
                    ]).mapped('from_workflow_stage_id')
                elif self.workflow_transition_id:
                    excluded_from_stages = self.env['workflow.stage.transition'].search([
                        '&', ('workflow_transition_id', '=', self.workflow_transition_id.id),
                        ('to_workflow_stage_id', '=', self.to_workflow_stage_id.id)
                    ]).mapped('from_workflow_stage_id')
                for stage in excluded_from_stages:
                    excluded_from_stage_ids.append(stage.id)
                domain = {
                    'from_workflow_stage_id': [
                        '!', ('id', 'in', excluded_from_stage_ids)
                    ]
                }
            return {'domain': domain}

    @api.onchange('workflow_id', 'workflow_allowed', 'workflow_transition_allowed')
    def _onchange_workflow(self):
        if self.workflow_id:
            self.workflow_allowed = True
            self.workflow_transition_allowed = False
        else:
            self.workflow_allowed = False
            self.workflow_transition_allowed = True

    @api.onchange('workflow_transition_id', 'workflow_allowed', 'workflow_transition_allowed')
    def _onchange_workflow_transition(self):
        if self.workflow_transition_id:
            self.workflow_allowed = False
            self.workflow_transition_allowed = True
        else:
            self.workflow_allowed = True
            self.workflow_transition_allowed = False

    @api.onchange('workflow_id')
    def _onchange_workflow_id(self):
        if self.workflow_id:
            if not self.workflow_transition_id:
                self.context_type = 'sibling'
            return {
                'domain': {'to_workflow_stage_id': [('workflow_id', '=', self.workflow_id.id)]}
            }

    @api.onchange('workflow_transition_id')
    def _onchange_workflow_transition_id(self):
        if self.workflow_transition_id:
            if not self.workflow_id:
                self.context_type = 'transition'
            return {
                'domain': {'from_workflow_stage_id': [('workflow_id', '=', self.workflow_id.id)]}
            }

    @api.depends('from_workflow_stage_id', 'to_workflow_stage_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_stage_id:
                name_str = transition.from_workflow_stage_id.name
            name_str += ' ---> '
            if transition.to_workflow_stage_id:
                name_str += transition.to_workflow_stage_id.name
            transition.name = name_str

    @api.depends('from_workflow_stage_id', 'to_workflow_stage_id')
    def _compute_cross_border(self):
        for transition in self:
            if transition.from_workflow_stage_id.parent_id != transition.to_workflow_stage_id.parent_id:
                transition.cross_border = True
            else:
                transition.cross_border = False

    @api.depends('workflow_id', 'workflow_transition_id')
    def _compute_root_workflow(self):
        for transition in self:
            if transition.workflow_id:
                transition.root_workflow_id = transition.workflow_id.root_workflow_id.id
                self.workflow_allowed = True
                self.workflow_transition_allowed = False
                if not self.workflow_transition_id:
                    self.context_type = 'sibling'
            else:
                transition.root_workflow_id = transition.workflow_transition_id.root_workflow_id.id
                self.workflow_allowed = False
                self.workflow_transition_allowed = True
                if not self.workflow_id:
                    self.context_type = 'transition'

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=True,
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')])
    root_workflow_id = fields.Many2one('workflow', required=False, string="Root Workflow",
                                       readonly=True, store=True, compute="_compute_root_workflow")
    from_workflow_stage_id = fields.Many2one('workflow.stage', required=True,
                                             string="From Workflow Stage")
    to_workflow_stage_id = fields.Many2one('workflow.stage', required=True,
                                           string="To Workflow Stage")
    workflow_state_transition_id = fields.Many2one('workflow.state.transition',
                                                   required=True, string="Workflow State Transition")
    workflow_id = fields.Many2one('workflow', required=False, string="Workflow")
    workflow_transition_id = fields.Many2one('workflow.transition', required=False,
                                             string="Workflow Transition")
    workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                              'workflow_stage_transition_id',
                                                              string="Procedure Stage Transitions")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cross_border = fields.Boolean(default=False, readonly=True, compute="_compute_cross_border")
    workflow_allowed = fields.Boolean(readonly=True, default=True)
    workflow_transition_allowed = fields.Boolean(readonly=True, default=True)

    def get_workflow_procedure_stage_transitions_by_id(self, workflow_stage_transition_id):
        return self.workflow_procedure_stage_transition_ids.filtered(
            lambda t: t.id == workflow_stage_transition_id
        )

    def get_workflow_procedure_stage_transition_by_id(self, workflow_stage_transition_id):
        records = self.get_workflow_procedure_stage_transitions_by_id(workflow_stage_transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_stage_transitions_by_ids(self, workflow_stage_transition_ids):
        return self.workflow_procedure_stage_transition_ids.filtered(
            lambda t: t.id in workflow_stage_transition_ids
        )

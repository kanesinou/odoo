# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowTransition(models.Model):
    _name = "workflow.transition"
    _description = "Workflow Transition"

    @api.constrains('workflow_id', 'workflow_transition_id')
    def _check_workflow_context(self):
        for transition in self:
            if not transition.workflow_id and not transition.workflow_transition_id:
                raise ValidationError(_("Either a workflow or workflow transition must be set as context !"))
            elif transition.workflow_id and transition.workflow_transition_id:
                raise ValidationError(_("The context of the transition must be unique. Set either a workflow or "
                                        "workflow transition, not both !"))

    @api.onchange('from_workflow_id')
    def _onchange_from_workflow(self):
        if self.from_workflow_id:
            if self.workflow_id:
                return {
                    'domain': {
                        'to_workflow_id': [
                            '&',
                            ('parent_id', '=', self.from_workflow_id.parent_id.id),
                            ('id', '!=', self.from_workflow_id.id)
                        ]
                    }
                }
            elif self.workflow_transition_id:
                return {
                    'domain': {
                        'to_workflow_id': [
                            '&',
                            ('parent_id', '=', self.workflow_transition_id.to_workflow_id.id),
                            ('id', '!=', self.from_workflow_id.id)
                        ]
                    }
                }

    @api.onchange('to_workflow_id')
    def _onchange_to_workflow(self):
        if self.to_workflow_id:
            if self.workflow_id:
                return {
                    'domain': {
                        'from_workflow_id': [
                            '&',
                            ('parent_id', '=', self.to_workflow_id.parent_id.id),
                            ('id', '!=', self.to_workflow_id.id)
                        ]
                    }
                }
            elif self.workflow_transition_id:
                return {
                    'domain': {
                        'from_workflow_id': [
                            '&',
                            ('parent_id', '=', self.workflow_transition_id.from_workflow_id.id),
                            ('id', '!=', self.to_workflow_id.id)
                        ]
                    }
                }

    @api.onchange('workflow_id', 'workflow_transition_id')
    def _on_change_transition_context(self):
        if self.workflow_id and not self.workflow_transition_id:
            self.context_type = 'sibling'
        elif not self.workflow_id and self.workflow_transition_id:
            self.context_type = 'transition'
            return {
                'domain': {
                    'from_workflow_id': [
                        ('id', 'in', self.workflow_transition_id.from_workflow_id.workflow_ids)
                    ],
                    'to_workflow_id': [
                        ('id', 'in', self.workflow_transition_id.to_workflow_id.workflow_ids)
                    ]
                }
            }

    @api.onchange('workflow_id', 'workflow_allowed', 'workflow_transition_allowed')
    def _onchange_workflow(self):
        if self.workflow_id:
            self.workflow_allowed = True
            self.workflow_transition_allowed = False
        else:
            self.workflow_allowed = False
            self.workflow_transition_allowed = True

    @api.onchange('workflow_transition_id', 'workflow_allowed', 'workflow_transition_allowed')
    def _onchange_workflow_transition_id(self):
        if self.workflow_transition_id:
            self.workflow_allowed = False
            self.workflow_transition_allowed = True
        else:
            self.workflow_allowed = True
            self.workflow_transition_allowed = False

    @api.depends('from_workflow_id', 'to_workflow_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_id:
                name_str = transition.from_workflow_id.name
            name_str += ' ---> '
            if transition.to_workflow_id:
                name_str += transition.to_workflow_id.name
            transition.name = name_str

    @api.depends('from_workflow_id', 'to_workflow_id')
    def _compute_cross_border(self):
        for transition in self:
            if transition.from_workflow_id.parent_id != transition.to_workflow_id.parent_id:
                transition.cross_border = True
            else:
                transition.cross_border = False

    @api.depends('workflow_id', 'workflow_transition_id')
    def _compute_root_workflow(self):
        for transition in self:
            if transition.workflow_id:
                transition.root_workflow_id = transition.workflow_id.root_workflow_id.id
            else:
                transition.root_workflow_id = transition.workflow_transition_id.root_workflow_id.id

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=True,
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')])
    root_workflow_id = fields.Many2one('workflow', required=False, string="Root Workflow",
                                       readonly=True, store=True, compute="_compute_root_workflow")
    from_workflow_id = fields.Many2one('workflow', required=True, string="From  workflow")
    to_workflow_id = fields.Many2one('workflow', required=True, string="To  workflow")
    workflow_id = fields.Many2one('workflow', required=True, string="Workflow")
    workflow_transition_id = fields.Many2one('workflow.transition', required=False,
                                             string="Workflow Transition")
    workflow_stage_transition_ids = fields.One2many('workflow.stage.transition',
                                                    'workflow_transition_id',
                                                    string="Workflow Stage Transitions")
    workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                        'workflow_transition_id',
                                                        string="Workflow Procedure Transitions")
    workflow_transition_ids = fields.One2many('workflow.transition',
                                              'workflow_transition_id',
                                              string="Workflow Transitions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cross_border = fields.Boolean(default=False, readonly=True, compute="_compute_cross_border")
    workflow_allowed = fields.Boolean(readonly=True, default=True)
    workflow_transition_allowed = fields.Boolean(readonly=True, default=True)

    def get_workflow_procedure_transitions_by_id(self, workflow_transition_id):
        return self.workflow_procedure_transition_ids.filtered(
            lambda t: t.id == workflow_transition_id
        )

    def get_workflow_procedure_transition_by_id(self, workflow_transition_id):
        records = self.get_workflow_procedure_transitions_by_id(workflow_transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_transitions_by_ids(self, workflow_transition_ids):
        return self.workflow_procedure_transition_ids.filtered(
            lambda t: t.id in workflow_transition_ids
        )

    def get_workflow_stage_transitions_by_id(self, workflow_transition_id):
        return self.workflow_stage_transition_ids.filtered(
            lambda t: t.id == workflow_transition_id
        )

    def get_workflow_stage_transition_by_id(self, workflow_transition_id):
        records = self.get_workflow_stage_transitions_by_id(workflow_transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_stage_transitions_by_ids(self, workflow_transition_ids):
        return self.workflow_stage_transition_ids.filtered(
            lambda t: t.id in workflow_transition_ids
        )

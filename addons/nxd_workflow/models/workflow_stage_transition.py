# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import json


class WorkflowStageTransition(models.Model):
    _name = "workflow.stage.transition"
    _description = "Workflow Stage Transition"
    _sql_constraints = [
        ('from_to_stages_uniq', 'unique (from_workflow_stage_id,to_workflow_stage_id)', 'This workflow stage '
                                                                                        'transition already exists !')
    ]

    @api.constrains('workflow_id', 'workflow_transition_id')
    def _check_transition_context(self):
        for transition in self:
            if not transition.workflow_id and not transition.workflow_transition_id:
                raise ValidationError(_("A workflow stage transition must occur either in a workflow or a workflow "
                                        "transition context !"))
            if transition.workflow_id and transition.workflow_transition_id:
                raise ValidationError(_("The context of the transition must be unique. Set either a workflow or "
                                        "workflow transition, not both !"))
            if transition.workflow_id and not transition.workflow_id.activity_workflow:
                raise ValidationError(_("The context of a workflow stage transition must be either an activity "
                                        "workflow or a transition between two activity workflows !"))
            if transition.workflow_transition_id and (not transition.workflow_transition_id.from_workflow_id.activity_workflow or not transition.workflow_transition_id.to_workflow_id.activity_workflow):
                raise ValidationError(_("The context of a workflow stage transition must be either an activity "
                                        "workflow or a transition between two activity workflows !"))
            if transition.cross_border and transition.to_workflow_stage_id != transition.to_workflow_stage_id.workflow_id.workflow_stage_id:
                raise ValidationError(_("The destination of a cross border workflow stage transition must be the "
                                        "starter stage of the destination parent workflow !"))

    @api.constrains('from_workflow_stage_id', 'to_workflow_stage_id')
    def _check_transition_parts(self):
        for transition in self:
            if transition.from_workflow_stage_id and transition.to_workflow_stage_id:
                if transition.from_workflow_stage_id.id == transition.to_workflow_stage_id.id:
                    raise ValidationError(_("The source and destination of the transition must be different !"))

    @api.constrains('can_return')
    def _check_return_setting(self):
        for transition in self:
            if transition.can_return and not transition.return_action_name:
                raise ValidationError(_('The return action name is mandatory if the transaction can return !'))

    @api.onchange('can_return')
    def _onchange_can_return(self):
        if self.workflow_transition_id:
            self.workflow_transition_id._compute_can_return()

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
            if transition.from_workflow_stage_id.workflow_id != transition.to_workflow_stage_id.workflow_id:
                transition.cross_border = True
            else:
                transition.cross_border = False

    @api.depends('workflow_id', 'workflow_transition_id')
    def _compute_context_type(self):
        for transition in self:
            if transition.workflow_id and not transition.workflow_transition_id:
                transition.context_type = 'sibling'
            elif not transition.workflow_id and transition.workflow_transition_id:
                transition.context_type = 'transition'

    @api.depends('workflow_id', 'workflow_transition_id')
    def _compute_workflow_allowed(self):
        for transition in self:
            if transition.workflow_id and not transition.workflow_transition_id:
                transition.workflow_allowed = True
            else:
                transition.workflow_allowed = False

    @api.depends('workflow_id', 'workflow_transition_id')
    def _compute_workflow_transition_allowed(self):
        for transition in self:
            if not transition.workflow_id and transition.workflow_transition_id:
                transition.workflow_transition_allowed = True
            else:
                transition.workflow_transition_allowed = False

    @api.depends('workflow_procedure_stage_transition_ids')
    def _compute_has_procedure_stage_transitions(self):
        for transition in self:
            transition.has_procedure_stage_transitions = len(
                transition.workflow_procedure_stage_transition_ids
            ) > 0

    @api.depends('workflow_procedure_stage_transition_ids')
    def _compute_procedure_stage_transitions_count(self):
        for transition in self:
            transition.procedure_stage_transitions_count = len(
                transition.workflow_procedure_stage_transition_ids
            )

    @api.depends()
    def _compute_is_ready(self):
        for transition in self:
            transition.is_ready = True
            if transition.cross_border and transition.to_workflow_stage_id != transition.to_workflow_stage_id.workflow_id.workflow_stage_id:
                transition.is_ready = False

    @api.depends('from_workflow_stage_id', 'to_workflow_stage_id', 'workflow_id', 'workflow_transition_id')
    def _compute_from_workflow_stage_domain(self):
        for transition in self:
            domain = []
            if transition.workflow_id and not transition.to_workflow_stage_id and not transition.workflow_transition_id:
                domain = [('workflow_id', '=', transition.workflow_id.id)]
            elif not transition.workflow_id and transition.to_workflow_stage_id and not transition.workflow_transition_id:
                domain = [('id', '!=', transition.to_workflow_stage_id.id)]
            elif transition.workflow_id and transition.to_workflow_stage_id and not transition.workflow_transition_id:
                domain = [
                    '&', ('workflow_id', '=', transition.workflow_id.id),
                    ('id', '!=', transition.to_workflow_stage_id.id)
                ]
            elif transition.workflow_transition_id and not transition.to_workflow_stage_id and not transition.workflow_id:
                domain = [('workflow_id', '=', transition.workflow_transition_id.from_workflow_id.id)]
            elif not transition.workflow_transition_id and transition.to_workflow_stage_id and not transition.workflow_id:
                domain = [('id', '!=', transition.to_workflow_stage_id.id)]
            elif transition.workflow_transition_id and transition.to_workflow_stage_id and not transition.workflow_id:
                domain = [
                    '&', ('id', '!=', transition.to_workflow_stage_id.id),
                    ('workflow_id', '=', transition.workflow_transition_id.from_workflow_id.id)
                ]
            transition.from_workflow_stage_domain = self.env['workflow.stage'].search(domain).ids

    @api.depends('from_workflow_stage_id', 'to_workflow_stage_id', 'workflow_id', 'workflow_transition_id')
    def _compute_to_workflow_stage_domain(self):
        for transition in self:
            domain = []
            if transition.workflow_id and not transition.from_workflow_stage_id and not transition.workflow_transition_id:
                domain = [('workflow_id', '=', transition.workflow_id.id)]
            elif not transition.workflow_id and transition.from_workflow_stage_id and not transition.workflow_transition_id:
                domain = [('id', '!=', transition.from_workflow_stage_id.id)]
            elif transition.workflow_id and transition.from_workflow_stage_id and not transition.workflow_transition_id:
                domain = [
                    '&', ('workflow_id', '=', transition.workflow_id.id),
                    ('id', '!=', transition.from_workflow_stage_id.id)
                ]
            elif transition.workflow_transition_id and not transition.from_workflow_stage_id and not transition.workflow_id:
                domain = [('id', '=', transition.workflow_transition_id.to_workflow_id.workflow_stage_id.id)]
            elif not transition.workflow_transition_id and transition.from_workflow_stage_id and not transition.workflow_id:
                domain = [('id', '!=', transition.from_workflow_stage_id.id)]
            elif transition.workflow_transition_id and transition.from_workflow_stage_id and not transition.workflow_id:
                domain = [
                    '&', ('id', '!=', transition.from_workflow_stage_id.id),
                    ('id', '=', transition.workflow_transition_id.to_workflow_id.workflow_stage_id.id)
                ]
            transition.to_workflow_stage_domain = self.env['workflow.stage'].search(domain).ids

    @api.depends('from_workflow_stage_id', 'to_workflow_stage_id', 'workflow_id')
    def _compute_workflow_domain(self):
        for transition in self:
            domain = [('activity_workflow', '=', True)]
            if transition.from_workflow_stage_id and transition.to_workflow_stage_id:
                domain = [
                    '&', '&', ('activity_workflow', '=', True),
                    ('id', '=', transition.to_workflow_stage_id.workflow_id.id),
                    ('id', '=', transition.from_workflow_stage_id.workflow_id.id)
                ]
            elif not transition.from_workflow_stage_id and transition.to_workflow_stage_id:
                domain = [
                    '&', ('activity_workflow', '=', True),
                    ('id', '=', transition.from_workflow_stage_id.workflow_id.id)
                ]
            elif transition.from_workflow_stage_id and not transition.to_workflow_stage_id:
                domain = [
                    '&', ('activity_workflow', '=', True),
                    ('id', '=', transition.to_workflow_stage_id.workflow_id.id)
                ]
            transition.workflow_domain = self.env['workflow'].search(domain).ids

    @api.depends('from_workflow_stage_id', 'to_workflow_stage_id', 'workflow_transition_id')
    def _compute_workflow_transition_domain(self):
        for transition in self:
            domain = [
                '&', ('to_workflow_id.activity_workflow', '=', True),
                ('from_workflow_id.activity_workflow', '=', True)
            ]
            if transition.from_workflow_stage_id and transition.to_workflow_stage_id:
                domain = [
                    '&', '&', ('to_workflow_id.activity_workflow', '=', True),
                    ('from_workflow_id.activity_workflow', '=', True),
                    '&', ('from_workflow_id', '=', transition.from_workflow_stage_id.workflow_id.id),
                    ('to_workflow_id.workflow_stage_id', '=', transition.to_workflow_stage_id.id)
                ]
            elif not transition.from_workflow_stage_id and transition.to_workflow_stage_id:
                domain = [
                    '&', '&', ('to_workflow_id.activity_workflow', '=', True),
                    ('from_workflow_id.activity_workflow', '=', True),
                    ('to_workflow_id.workflow_stage_id', '=', transition.to_workflow_stage_id.id)
                ]
            elif transition.from_workflow_stage_id and not transition.to_workflow_stage_id:
                domain = [
                    '&', '&', ('to_workflow_id.activity_workflow', '=', True),
                    ('from_workflow_id.activity_workflow', '=', True),
                    ('from_workflow_id', '=', transition.from_workflow_stage_id.workflow_id.id)
                ]
            transition.workflow_transition_domain = self.env['workflow.transition'].search(domain).ids

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=False, compute="_compute_context_type",
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')],
                                    store=True)
    root_workflow_id = fields.Many2one('workflow', required=False, string="Root Workflow",
                                       readonly=True, related="from_workflow_stage_id.root_workflow_id",
                                       store=True)
    from_workflow_stage_id = fields.Many2one('workflow.stage', required=True,
                                             string="From Workflow Stage")
    to_workflow_stage_id = fields.Many2one('workflow.stage', required=True,
                                           string="To Workflow Stage")
    workflow_id = fields.Many2one('workflow', required=False, string="Workflow")
    workflow_transition_id = fields.Many2one('workflow.transition', required=False,
                                             string="Workflow Transition")
    can_return = fields.Boolean(string="Can Return", default=False)
    return_action_name = fields.Char(string="Return Action Name", required=False, translate=True)
    return_action_title = fields.Char(string='Return Action Title', required=False, translate=True)
    action_name = fields.Char(string="Action Name", required=True, translate=True)
    action_title = fields.Char(string='Action Title', required=False, translate=True)
    button_type = fields.Selection(
        selection=[
            ("btn-primary", "Primary"),
            ("btn-secondary", "Secondary"),
            ("btn-success", "Success"),
            ("btn-danger", "Danger"),
            ("btn-warning", "Warning"),
            ("btn-info", "Info"),
            ("btn-light", "Light"),
            ("btn-dark", "Dark"),
            ("btn-link", "Link")
        ],
        string="Button Type", required=True, default='btn-primary'
    )
    workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                              'workflow_stage_transition_id',
                                                              string="Procedure Stage Transitions")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cross_border = fields.Boolean(default=False, readonly=True, compute="_compute_cross_border")
    workflow_allowed = fields.Boolean(readonly=True, compute="_compute_workflow_allowed")
    is_ready = fields.Boolean(readonly=True, compute="_compute_is_ready")
    workflow_transition_allowed = fields.Boolean(readonly=True, compute="_compute_workflow_transition_allowed")
    has_procedure_stage_transitions = fields.Boolean(readonly=True, compute="_compute_has_procedure_stage_transitions")
    procedure_stage_transitions_count = fields.Integer(readonly=True,
                                                       compute="_compute_procedure_stage_transitions_count")
    from_workflow_stage_domain = fields.Many2many('workflow.stage', readonly=True,
                                                  relation="workflow_stage_transition_from_domain_ids",
                                                  compute="_compute_from_workflow_stage_domain")
    to_workflow_stage_domain = fields.Many2many('workflow.stage', readonly=True,
                                                relation="workflow_stage_transition_to_domain_ids",
                                                compute="_compute_to_workflow_stage_domain")
    workflow_domain = fields.Many2many('workflow', compute="_compute_workflow_domain",
                                       relation="workflow_stage_transition_workflow_domain_ids",
                                       readonly=True)
    workflow_transition_domain = fields.Many2many('workflow.transition', readonly=True,
                                                  compute="_compute_workflow_transition_domain",
                                                  relation="workflow_stage_transition_workflow_trans_domain_ids")

    def get_corresponding_procedure_stage_transition_data(self, root_procedure_id, full=False):
        self.ensure_one()
        data = {}
        from_workflow_procedure_stage = self.env['workflow.procedure.stage'].search([
            '&', ('root_workflow_procedure_id', '=', root_procedure_id.id),
            ('workflow_stage_id', '=', self.from_workflow_stage_id.id)
        ], limit=1)
        to_workflow_procedure_stage = self.env['workflow.procedure.stage'].search([
            '&', ('root_workflow_procedure_id', '=', root_procedure_id.id),
            ('workflow_stage_id', '=', self.to_workflow_stage_id.id)
        ], limit=1)
        if from_workflow_procedure_stage and to_workflow_procedure_stage:
            data['context_type'] = self.context_type
            data['workflow_stage_transition_id'] = self.id
            data['from_workflow_procedure_stage_id'] = from_workflow_procedure_stage.id
            data['to_workflow_procedure_stage_id'] = to_workflow_procedure_stage.id
        if full and self.context_type == 'sibling':
            procedure = self.workflow_id.get_workflow_procedure_by_id(root_procedure_id)
            if procedure.exists():
                data['workflow_procedure_id'] = procedure.id
        elif full and self.context_type == 'transition':
            procedure_transition = self.workflow_transition_id.get_workflow_procedure_transition_by_id(
                root_procedure_id
            )
            if procedure_transition.exists():
                data['workflow_procedure_transition_id'] = procedure_transition.id
        return data

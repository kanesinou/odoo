# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval


class WorkflowProcedureTransition(models.Model):
    _name = "workflow.procedure.transition"
    _description = "WorkflowProcedureTransition"

    @api.constrains('workflow_procedure_id', 'workflow_procedure_transition_id')
    def _check_workflow_procedure_context(self):
        for transition in self:
            if not transition.workflow_procedure_id and not transition.workflow_procedure_transition_id:
                raise ValidationError(_("Either a workflow procedure or workflow procedure transition must be set as "
                                        "context !"))
            elif transition.workflow_procedure_id and transition.workflow_procedure_transition_id:
                raise ValidationError(_("The context of the procedure transition must be unique. Set either a "
                                        "workflow procedure or workflow procedure transition, not both !"))
            if transition.workflow_procedure_id and transition.workflow_procedure_id.activity_procedure:
                raise ValidationError(_("""Procedure Activity cannot have sub procedure, therefore it cannot be the 
                the context of a sub procedure transition !"""))
            if transition.cross_border and transition.to_workflow_procedure_id and transition.to_workflow_procedure_id.parent_id.starter_workflow_procedure_id:
                if transition.to_workflow_procedure_id != transition.to_workflow_procedure_id.parent_id.starter_workflow_procedure_id:
                    raise ValidationError(_("The destination of a cross border procedure transition must be the "
                                            "starter sub procedure of the destination parent procedure !"))

    @api.onchange('from_workflow_procedure_id')
    def _onchange_from_workflow_procedure(self):
        if self.from_workflow_procedure_id:
            return {
                'domain': {
                    'to_workflow_procedure_id': [('id', '!=', self.from_workflow_procedure_id.id)]
                }
            }

    @api.onchange('to_workflow_procedure_id')
    def _onchange_to_workflow_procedure(self):
        if self.to_workflow_procedure_id:
            return {
                'domain': {
                    'from_workflow_procedure_id': [('id', '!=', self.to_workflow_procedure_id.id)]
                }
            }

    @api.onchange('workflow_procedure_id', 'workflow_procedure_transition_id')
    def _onchange_transition_context(self):
        if self.workflow_procedure_id and not self.workflow_procedure_transition_id:
            self.context_type = 'sibling'
            return [
                {'domain': {'from_workflow_procedure_id': [('parent_id', '=', self.workflow_procedure_id.id)]}},
                {'domain': {'to_workflow_procedure_id': [('parent_id', '=', self.workflow_procedure_id.id)]}}
            ]
        elif not self.workflow_procedure_id and self.workflow_procedure_transition_id:
            self.context_type = 'transition'
            return [
                {
                    'domain': {
                        'from_workflow_procedure_id': [
                            ('id', 'in', self.workflow_procedure_transition_id.from_workflow_procedure_id.workflow_procedure_ids)
                        ]
                    }
                },
                {
                    'domain': {
                        'to_workflow_procedure_id': [
                            ('id', 'in', self.workflow_procedure_transition_id.to_workflow_procedure_id.workflow_procedure_ids)
                        ]
                    }
                }
            ]

    @api.depends('from_workflow_procedure_id', 'to_workflow_procedure_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_procedure_id:
                name_str = transition.from_workflow_procedure_id.name
            name_str += ' ---> '
            if transition.to_workflow_procedure_id:
                name_str += transition.to_workflow_procedure_id.name
            transition.name = name_str

    @api.depends('from_workflow_procedure_id', 'to_workflow_procedure_id')
    def _compute_cross_border(self):
        for transition in self:
            if transition.from_workflow_procedure_id.parent_id != transition.to_workflow_procedure_id.parent_id:
                transition.cross_border = True
            else:
                transition.cross_border = False

    @api.depends("workflow_procedure_transition_ids", "has_sub_transitions")
    def _compute_has_sub_transitions(self):
        for transition in self:
            if len(transition.workflow_procedure_transition_ids) > 0:
                transition.has_sub_transitions = True
            else:
                transition.has_sub_transitions = False

    @api.depends("workflow_procedure_stage_transition_ids", "has_stage_transitions")
    def _compute_has_stage_transitions(self):
        for transition in self:
            if len(transition.workflow_procedure_stage_transition_ids) > 0:
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

    @api.depends('workflow_procedure_id', 'workflow_procedure_transition_id')
    def _compute_root_workflow_procedure(self):
        for transition in self:
            if transition.workflow_procedure_id:
                transition.root_workflow_procedure_id = transition.workflow_procedure_id.root_workflow_procedure_id.id
                if not transition.workflow_procedure_id:
                    transition.context_type = 'sibling'
            else:
                transition.root_workflow_procedure_id = transition.workflow_procedure_transition_id.root_workflow_procedure_id.id
                if not transition.workflow_procedure_transition_id:
                    transition.context_type = 'transition'

    @api.depends('workflow_process_transition_ids')
    def _compute_can_return(self):
        for transition in self:
            transition.can_return = False
            for sub_transition in transition.workflow_process_transition_ids:
                if sub_transition.can_return:
                    transition.can_return = True
                    break

    @api.depends('from_workflow_procedure_id', 'to_workflow_procedure_id', 'workflow_procedure_cycle_id')
    def _compute_from_workflow_procedure_cycle_domain(self):
        for transition in self:
            domain = [
                '&', '|', ('parent_id', '=', False), ('base_procedure', '=', True),
                ('released', '=', True)
            ]
            if transition.workflow_procedure_cycle_id and not transition.from_workflow_procedure_id and transition.to_workflow_procedure_id:
                domain = [
                    '&', '|', ('parent_id', '=', False), ('base_procedure', '=', True),
                    '&', ('released', '=', True), ('id', '!=', transition.to_workflow_procedure_id.id)
                ]
            transition.from_workflow_procedure_cycle_domain = self.env['workflow.procedure'].search(domain).ids

    @api.depends('from_workflow_procedure_id', 'to_workflow_procedure_id', 'workflow_procedure_cycle_id')
    def _compute_to_workflow_procedure_cycle_domain(self):
        for transition in self:
            domain = [
                '&', '|', ('parent_id', '=', False), ('base_procedure', '=', True),
                ('released', '=', True)
            ]
            if transition.workflow_procedure_cycle_id and transition.from_workflow_procedure_id and not transition.to_workflow_procedure_id:
                domain = [
                    '&', '|', ('parent_id', '=', False), ('base_procedure', '=', True),
                    '&', ('released', '=', True), ('id', '!=', transition.from_workflow_procedure_id.id)
                ]
            transition.to_workflow_procedure_cycle_domain = self.env['workflow.procedure'].search(domain).ids

    @api.depends('workflow_procedure_cycle_id', 'to_workflow_procedure_id', 'to_workflow_procedure_cycle_stage_id')
    def _compute_to_cycle_stage(self):
        for transition in self:
            to_workflow_procedure = transition.to_workflow_procedure_id
            transition.to_workflow_procedure_cycle_stage_id = None
            if to_workflow_procedure:
                transition.to_workflow_procedure_cycle_stage_id = to_workflow_procedure.find_starter_workflow_procedure_stage()

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=True,
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')])
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False, readonly=True,
                                                 string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    from_workflow_procedure_id = fields.Many2one('workflow.procedure', required=True, string="From Procedure")
    to_workflow_procedure_id = fields.Many2one('workflow.procedure', required=True, string="To Procedure")
    workflow_procedure_cycle_id = fields.Many2one('workflow.procedure.cycle', string="Context Procedure Cycle",
                                                  required=False)
    workflow_procedure_id = fields.Many2one('workflow.procedure', string="Context Procedure", required=False)
    workflow_procedure_transition_id = fields.Many2one('workflow.procedure.transition', required=False,
                                                       string="Context Procedures Transition")
    workflow_transition_id = fields.Many2one('workflow.transition', string="Workflow Transition",
                                             required=True)
    workflow_process_transition_ids = fields.One2many('workflow.process.transition',
                                                      'workflow_procedure_transition_id',
                                                      string="Process Transitions")
    workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                              'workflow_procedure_transition_id',
                                                              string="Procedure Stage Transitions")
    workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                        'workflow_procedure_transition_id',
                                                        string="Procedure Transitions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    can_return = fields.Boolean(readonly=True, compute="_compute_can_return")
    cross_border = fields.Boolean(default=False, readonly=True, compute="_compute_cross_border")
    has_sub_transitions = fields.Boolean(readonly=True, compute="_compute_has_sub_transitions")
    has_stage_transitions = fields.Boolean(readonly=True, compute="_compute_has_stage_transitions")
    has_process_transitions = fields.Boolean(readonly=True, compute="_compute_has_process_transitions")
    from_workflow_procedure_cycle_domain = fields.Many2many('workflow.procedure', readonly=True,
                                                            compute="_compute_from_workflow_procedure_cycle_domain",
                                                            relation="workflow_procedure_transition_cycle_from_domain_ids")
    to_workflow_procedure_cycle_domain = fields.Many2many('workflow.procedure', readonly=True,
                                                          compute="_compute_to_workflow_procedure_cycle_domain",
                                                          relation="workflow_procedure_transition_cycle_to_domain_ids")
    from_workflow_procedure_cycle_stage_id = fields.Many2one('workflow.procedure.stage', required=False,
                                                             string="From Cycle Stage")
    to_workflow_procedure_cycle_stage_id = fields.Many2one('workflow.procedure.stage', required=False,
                                                           string="To Cycle Stage",
                                                           compute="_compute_to_cycle_stage")
    model_name = fields.Char(string="Domain Model", readonly=True, required=False,
                             related="from_workflow_procedure_id.model_name")
    filter_domain = fields.Text(string="Domain", required=False)

    def get_corresponding_process_transition_data(self, workflowable_record):
        self.ensure_one()
        data = {
            'workflow_procedure_transition_id': self.id,
            'context_type': self.context_type
        }
        return data

    def get_parent_bridge_transitions_branch(self, collector=False):
        self.ensure_one()
        if not collector:
            collector = []
        if self.context_type == 'sibling':
            return collector
        else:
            workflow_procedure_transition = self.workflow_procedure_transition_id
            collector.insert(0, workflow_procedure_transition)
            return workflow_procedure_transition.get_parent_bridge_transitions_branch(collector)

    def eval_filter_domain(self, context=False):
        self.ensure_one()
        if not context:
            context = self.env.context
        domain_filter = safe_eval.safe_eval(self.filter_domain, context)
        return self.env[self.model_name].search(domain_filter)

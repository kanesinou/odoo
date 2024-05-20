# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError


class WorkflowTransition(models.Model):
    _name = "workflow.transition"
    _description = "Workflow Transition"
    _sql_constraints = [
        ('from_to_wkfs_uniq', 'unique (from_workflow_id,to_workflow_id)', 'This workflow transition already exists !')
    ]

    @api.constrains('workflow_id', 'workflow_transition_id')
    def _check_workflow_context(self):
        for transition in self:
            if not transition.workflow_id and not transition.workflow_transition_id:
                raise ValidationError(_("Either a workflow or workflow transition must be set as context !"))
            if transition.workflow_id and transition.workflow_transition_id:
                raise ValidationError(_("The context of the transition must be unique. Set either a workflow or "
                                        "workflow transition, not both !"))
            if transition.workflow_id and transition.workflow_id.activity_workflow:
                raise ValidationError(_("""Workflow Activity cannot have sub workflow, therefore it cannot be the 
                the context of a sub workflow transition !"""))
            if transition.cross_border and transition.to_workflow_id != transition.to_workflow_id.parent_id.starter_workflow_id:
                raise ValidationError(_("The destination of a cross border workflow transition must be the starter "
                                        "sub workflow of the destination parent workflow !"))
            if transition.from_workflow_id.base_workflow or transition.to_workflow_id.base_workflow:
                raise ValidationError(_("The Origin or Destination of a workflow transition cannot be a base workflow !"))

    @api.constrains('from_workflow_id', 'to_workflow_id')
    def _check_part_types(self):
        for transition in self:
            if transition.from_workflow_id and transition.to_workflow_id:
                from_ready = transition.from_workflow_id.is_ready
                to_ready = transition.to_workflow_id.is_ready
                if not from_ready or not to_ready:
                    raise ValidationError(_("Workflow must be ready to take part of a workflow transition !"))
                if transition.from_workflow_id.id == transition.to_workflow_id.id:
                    raise ValidationError(_("The source and destination of the transition must be different !"))

    @api.depends('workflow_id', 'workflow_transition_id')
    def _compute_workflow_allowed(self):
        for transition in self:
            transition.workflow_allowed = transition.workflow_id and not transition.workflow_transition_id

    @api.depends('workflow_id', 'workflow_transition_id')
    def _compute_workflow_transition_allowed(self):
        for transition in self:
            transition.workflow_transition_allowed = transition.workflow_transition_id and not transition.workflow_id

    @api.depends('workflow_stage_transition_ids')
    def _compute_has_stage_transitions(self):
        for transition in self:
            transition.has_stage_transitions = len(transition.workflow_stage_transition_ids) > 0

    @api.depends('workflow_stage_transition_ids')
    def _compute_stage_transitions_count(self):
        for transition in self:
            transition.stage_transitions_count = len(transition.workflow_stage_transition_ids)

    @api.depends('workflow_procedure_transition_ids')
    def _compute_has_procedure_transitions(self):
        for transition in self:
            transition.has_procedure_transitions = len(transition.workflow_procedure_transition_ids) > 0

    @api.depends('workflow_procedure_transition_ids')
    def _compute_procedure_transitions_count(self):
        for transition in self:
            transition.procedure_transitions_count = len(transition.workflow_procedure_transition_ids)

    @api.depends('workflow_transition_ids')
    def _compute_has_sub_workflow_transitions(self):
        for transition in self:
            transition.has_sub_workflow_transitions = len(transition.workflow_transition_ids) > 0

    @api.depends('workflow_transition_ids')
    def _compute_sub_workflow_transitions_count(self):
        for transition in self:
            transition.sub_workflow_transitions_count = len(transition.workflow_transition_ids)

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

    @api.depends('from_workflow_id', 'to_workflow_id')
    def _compute_stage_transitions_allowed(self):
        for transition in self:
            if transition.from_workflow_id.activity_workflow and transition.to_workflow_id.activity_workflow:
                transition.stage_transitions_allowed = True
            else:
                transition.stage_transitions_allowed = False

    @api.depends('from_workflow_id', 'to_workflow_id')
    def _compute_workflow_transitions_allowed(self):
        for transition in self:
            if transition.from_workflow_id.activity_workflow and transition.to_workflow_id.activity_workflow:
                transition.workflow_transitions_allowed = False
            else:
                transition.workflow_transitions_allowed = True

    @api.depends('workflow_id', 'workflow_transition_id')
    def _compute_context_type(self):
        for transition in self:
            if transition.workflow_id and not transition.workflow_transition_id:
                transition.context_type = 'sibling'
            elif not transition.workflow_id and transition.workflow_transition_id:
                transition.context_type = 'transition'

    @api.depends('workflow_id', 'workflow_transition_id')
    def _compute_root_workflow(self):
        for transition in self:
            if transition.workflow_id:
                transition.root_workflow_id = transition.workflow_id.root_workflow_id.id
            else:
                transition.root_workflow_id = transition.workflow_transition_id.root_workflow_id.id

    @api.depends('from_workflow_id', 'to_workflow_id')
    def _compute_is_ready(self):
        for transition in self:
            if transition.stage_transitions_allowed:
                if len(transition.workflow_stage_transition_ids) < 1:
                    transition.is_ready = False
                else:
                    transition.is_ready = True
                    for stage_transition in transition.workflow_stage_transition_ids:
                        if not stage_transition.is_ready:
                            transition.is_ready = False
                            break
            else:
                if len(transition.workflow_transition_ids) < 1:
                    transition.is_ready = False
                else:
                    for sub_workflow_transition in transition.workflow_transition_ids:
                        if not sub_workflow_transition.is_ready:
                            transition.is_ready = False
                            break

    @api.depends('workflow_transition_ids')
    def _compute_can_return(self):
        for transition in self:
            transition.can_return = False
            for sub_transition in transition.workflow_transition_ids:
                if sub_transition.can_return:
                    transition.can_return = True
                    break
            if transition.workflow_transition_id:
                transition.workflow_transition_id._compute_can_return()

    @api.depends('from_workflow_id', 'to_workflow_id', 'workflow_transition_id')
    def _compute_workflow_transition_domain(self):
        for transition in self:
            domain = []
            if transition.from_workflow_id and not transition.to_workflow_id:
                if transition.from_workflow_id.activity_workflow:
                    domain = [('from_workflow_id', '=', transition.from_workflow_id.id)]
                elif transition.from_workflow_id.parent_id:
                    domain = [('from_workflow_id', '=', transition.from_workflow_id.parent_id.id)]
            elif not transition.from_workflow_id and transition.to_workflow_id:
                domain = [('to_workflow_id.starter_workflow_id', '=', transition.to_workflow_id.id)]
            elif transition.from_workflow_id and transition.to_workflow_id:
                if transition.from_workflow_id.parent_id and transition.to_workflow_id.parent_id:
                    domain = [
                        '&', ('to_workflow_id', '=', transition.to_workflow_id.parent_id.id),
                        '|', ('from_workflow_id', '=', transition.from_workflow_id.id),
                        ('from_workflow_id', '=', transition.from_workflow_id.parent_id.id)
                    ]
            transition.workflow_transition_domain = self.env['workflow.transition'].search(domain).ids

    @api.depends('from_workflow_id', 'to_workflow_id', 'workflow_id')
    def _compute_workflow_domain(self):
        for transition in self:
            domain = [('activity_workflow', '=', False)]
            if transition.to_workflow_id and not transition.from_workflow_id:
                if transition.to_workflow_id.parent_id:
                    domain = [('id', '=', transition.to_workflow_id.parent_id.id)]
            elif not transition.to_workflow_id and transition.from_workflow_id:
                if transition.from_workflow_id.parent_id:
                    domain = [('id', '=', transition.from_workflow_id.parent_id.id)]
            elif transition.to_workflow_id and transition.from_workflow_id:
                if transition.from_workflow_id.parent_id and transition.to_workflow_id.parent_id:
                    domain = [
                        '&', ('id', '=', transition.to_workflow_id.parent_id.id),
                        ('id', '=', transition.from_workflow_id.parent_id.id)
                    ]
            transition.workflow_domain = self.env['workflow'].search(domain).ids

    @api.depends('from_workflow_id', 'to_workflow_id', 'workflow_id', 'workflow_transition_id')
    def _compute_from_workflow_domain(self):
        for transition in self:
            domain = [('parent_id', '!=', False)]
            if transition.to_workflow_id and not transition.workflow_id and not transition.workflow_transition_id:
                if transition.to_workflow_id.parent_id:
                    domain = [
                        '&', ('id', '!=', transition.to_workflow_id.id),
                        ('parent_id', '=', transition.to_workflow_id.parent_id.id)
                    ]
                else:
                    domain = [
                        '&', ('id', '!=', transition.to_workflow_id.id),
                        ('base_workflow', '=', True)
                    ]
            elif not transition.to_workflow_id and transition.workflow_id and not transition.workflow_transition_id:
                domain = [('parent_id', '=', transition.workflow_id.id)]
            elif transition.to_workflow_id and transition.workflow_id and not transition.workflow_transition_id:
                domain = [
                    '&', ('parent_id', '=', transition.workflow_id.id),
                    ('id', '!=', transition.to_workflow_id.id)
                ]
            elif not transition.to_workflow_id and transition.workflow_transition_id and not transition.workflow_id:
                if not transition.workflow_transition_id.from_workflow_id.activity_workflow:
                    domain = [('parent_id', '=', transition.workflow_transition_id.from_workflow_id.id)]
                else:
                    domain = [('id', '=', transition.workflow_transition_id.from_workflow_id.id)]
            elif transition.to_workflow_id and not transition.workflow_transition_id and not transition.workflow_id:
                domain = [('id', '!=', transition.to_workflow_id.id)]
            elif transition.to_workflow_id and transition.workflow_transition_id and not transition.workflow_id:
                domain = [
                    '|', ('id', '=', transition.workflow_transition_id.from_workflow_id.id),
                    ('parent_id', '=', transition.workflow_transition_id.from_workflow_id.id)
                ]
            transition.from_workflow_domain = self.env['workflow'].search(domain).ids

    @api.depends('from_workflow_id', 'to_workflow_id', 'workflow_id', 'workflow_transition_id')
    def _compute_to_workflow_domain(self):
        for transition in self:
            domain = [('parent_id', '!=', False)]
            if transition.from_workflow_id and not transition.workflow_id and not transition.workflow_transition_id:
                if transition.from_workflow_id.parent_id:
                    domain = [
                        '&', ('id', '!=', transition.from_workflow_id.id),
                        ('parent_id', '=', transition.from_workflow_id.parent_id.id)
                    ]
                else:
                    domain = [
                        '&', ('id', '!=', transition.from_workflow_id.id),
                        ('base_workflow', '=', True)
                    ]
            elif not transition.from_workflow_id and transition.workflow_id and not transition.workflow_transition_id:
                domain = [('parent_id', '=', transition.workflow_id.id)]
            elif transition.from_workflow_id and transition.workflow_id and not transition.workflow_transition_id:
                domain = [
                    '&', ('parent_id', '=', transition.workflow_id.id),
                    ('id', '!=', transition.from_workflow_id.id)
                ]
            elif not transition.from_workflow_id and transition.workflow_transition_id and not transition.workflow_id:
                if not transition.workflow_transition_id.to_workflow_id.activity_workflow:
                    domain = [('id', '=', transition.workflow_transition_id.to_workflow_id.starter_workflow_id.id)]
                else:
                    domain = [('id', '=', transition.workflow_transition_id.to_workflow_id.id)]
            elif transition.from_workflow_id and not transition.workflow_transition_id and not transition.workflow_id:
                domain = [('id', '!=', transition.from_workflow_id.id)]
            elif transition.from_workflow_id and transition.workflow_transition_id and not transition.workflow_id:
                domain = [
                    '&', ('id', '!=', transition.from_workflow_id.id),
                    ('id', '=', transition.workflow_transition_id.to_workflow_id.starter_workflow_id.id)
                ]
            transition.to_workflow_domain = self.env['workflow'].search(domain).ids

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=False, compute="_compute_context_type",
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')],
                                    store=True)
    root_workflow_id = fields.Many2one('workflow', required=False, string="Root Workflow",
                                       readonly=True, store=True, compute="_compute_root_workflow")
    from_workflow_id = fields.Many2one('workflow', required=True, string="From  workflow")
    to_workflow_id = fields.Many2one('workflow', required=True, string="To  workflow")
    workflow_id = fields.Many2one('workflow', required=False, string="Workflow")
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
    can_return = fields.Boolean(readonly=True, compute="_compute_can_return")
    is_ready = fields.Boolean(readonly=True, compute="_compute_is_ready")
    cross_border = fields.Boolean(default=False, readonly=True, compute="_compute_cross_border")
    workflow_allowed = fields.Boolean(readonly=True, compute="_compute_workflow_allowed")
    workflow_transition_allowed = fields.Boolean(readonly=True, compute="_compute_workflow_transition_allowed")
    stage_transitions_allowed = fields.Boolean(readonly=True, compute="_compute_stage_transitions_allowed")
    workflow_transitions_allowed = fields.Boolean(readonly=True, compute="_compute_workflow_transitions_allowed")
    has_stage_transitions = fields.Boolean(readonly=True, compute="_compute_has_stage_transitions")
    stage_transitions_count = fields.Integer(readonly=True, compute="_compute_stage_transitions_count")
    has_procedure_transitions = fields.Boolean(readonly=True, compute="_compute_has_procedure_transitions")
    procedure_transitions_count = fields.Integer(readonly=True, compute="_compute_procedure_transitions_count")
    has_sub_workflow_transitions = fields.Boolean(readonly=True, compute="_compute_has_sub_workflow_transitions")
    sub_workflow_transitions_count = fields.Integer(readonly=True, compute="_compute_sub_workflow_transitions_count")
    from_workflow_domain = fields.Many2many('workflow', readonly=True,
                                            relation="workflow_transition_from_domain_ids",
                                            compute="_compute_from_workflow_domain")
    to_workflow_domain = fields.Many2many('workflow', readonly=True,
                                          relation="workflow_transition_to_domain_ids",
                                          compute="_compute_to_workflow_domain")
    workflow_domain = fields.Many2many('workflow', compute="_compute_workflow_domain",
                                       relation="workflow_transition_workflow_domain_ids",
                                       readonly=True)
    workflow_transition_domain = fields.Many2many('workflow.transition', readonly=True,
                                                  compute="_compute_workflow_transition_domain",
                                                  relation="workflow_transition_workflow_trans_domain_ids")

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        records = super(WorkflowTransition, self).create(vals_list)
        """for record in records:
            record.complete_transition_bridges()"""
        return records

    def get_workflow_transition_complement_bridges(
            self, branches, leaning_side='None', init_data={}, collector=False
    ):
        self.ensure_one()
        if not collector:
            collector = {}
        from_workflow = self.from_workflow_id
        to_workflow = self.to_workflow_id
        if init_data.get('from_workflow', False):
            from_workflow = init_data.get('from_workflow')
        if init_data.get('to_workflow', False):
            to_workflow = init_data.get('to_workflow')
        if len(branches) == 0:
            return collector
        else:
            branch = branches[0]
            data = {'workflow_id': None}
            if branch._name == 'workflow':
                if leaning_side == 'from':
                    data['from_workflow_id'] = from_workflow.id
                    data['to_workflow_id'] = branch.id
                elif leaning_side == 'to':
                    data['from_workflow_id'] = branch.id
                    data['to_workflow_id'] = to_workflow.id
            elif branch._name == 'workflow.stage' and collector.get('from_workflow_id', False) and collector.get(
                    'to_workflow_id', False):
                from_state = False
                to_state = False
                if leaning_side == 'from' and len(from_workflow.workflow_stage_ids) == 1:
                    from_state = from_workflow.workflow_stage_id.workflow_state_id
                    to_state = branch.workflow_state_id
                elif leaning_side == 'to' and len(branch.workflow_id.workflow_stage_ids) == 1:
                    from_state = branch.workflow_state_id
                    to_state = to_workflow.workflow_stage_id.workflow_state_id
                if from_state and to_state:
                    state_transition = self.env['workflow.state.transition'].search([
                        '&', ('from_workflow_state_id', '=', from_state.id),
                        ('to_workflow_state_id', '=', to_state.id)
                    ], limit=1)
                    if state_transition.exists():
                        data['workflow_state_transition_id'] = state_transition.id
                        if leaning_side == 'from':
                            data['from_workflow_stage_id'] = from_workflow.workflow_stage_id.id
                            data['to_workflow_stage_id'] = branch.id
                        elif leaning_side == 'to':
                            data['from_workflow_stage_id'] = branch.id
                            data['to_workflow_stage_id'] = to_workflow.workflow_stage_id.id
            if len(branches) == 1:
                if branch._name == 'workflow' and data.get('from_workflow_id', False) and data.get('to_workflow_id',
                                                                                                   False):
                    create_command = Command.create(data)
                    if not collector.get('workflow_transition_ids', False):
                        collector['workflow_transition_ids'] = [create_command]
                    else:
                        collector['workflow_transition_ids'].append(create_command)
                elif branch._name == 'workflow.stage' and data.get('from_workflow_stage_id', False) and data.get(
                        'to_workflow_stage_id', False):
                    create_command = Command.create(data)
                    if not collector.get('workflow_stage_transition_ids', False):
                        collector['workflow_stage_transition_ids'] = [create_command]
                    else:
                        collector['workflow_stage_transition_ids'].append(create_command)
                return collector
            else:
                next_data = self.get_workflow_transition_complement_bridges(
                    branches[1:], leaning_side, init_data, data
                )
                if next_data:
                    create_command = Command.create(next_data)
                    if not collector.get('workflow_transition_ids', False):
                        collector['workflow_transition_ids'] = [create_command]
                    else:
                        collector['workflow_transition_ids'].append(create_command)
                return collector

    def get_workflow_transition_balanced_complement_bridges(
            self, from_branches, to_branches, collector=False
    ):
        self.ensure_one()
        if not collector:
            collector = {}
        from_length = len(from_branches)
        to_length = len(to_branches)
        min_length = from_length
        if from_length > to_length:
            min_length = to_length
        elif to_length > from_length:
            min_length = from_length
        if min_length == 0:
            return collector
        else:
            from_branch = from_branches[0]
            to_branch = to_branches[0]
            init_data = {'from_workflow': from_branch, 'to_workflow': to_branch}
            if from_branch._name == 'workflow' and to_branch._name == 'workflow.stage':
                path_to_starter_from_stage = from_branch.get_path_to_starter_stage()
                command_data = self.get_workflow_transition_complement_bridges(
                    path_to_starter_from_stage, 'to', init_data
                )
                if not collector.get('workflow_transition_ids', False) and command_data.get('workflow_transition_ids',
                                                                                            False):
                    collector['workflow_transition_ids'] = [command_data['workflow_transition_ids']]
                else:
                    collector['workflow_transition_ids'].append([command_data['workflow_transition_ids']])
            elif from_branch._name == 'workflow.stage' and to_branch._name == 'workflow':
                path_to_starter_to_stage = to_branch.get_path_to_starter_stage()
                command_data = self.get_workflow_transition_complement_bridges(
                    path_to_starter_to_stage, 'from', init_data
                )
                if not collector.get('workflow_transition_ids', False) and command_data.get('workflow_transition_ids',
                                                                                            False):
                    collector['workflow_transition_ids'] = [command_data['workflow_transition_ids']]
                else:
                    collector['workflow_transition_ids'].append([command_data['workflow_transition_ids']])
            elif from_branch._name == 'workflow.stage' and to_branch._name == 'workflow.stage':
                from_state = from_branch.workflow_state_id
                to_state = to_branch.workflow_state_id
                if from_state and to_state:
                    state_transition = self.env['workflow.state.transition'].search([
                        '&', ('from_workflow_state_id', '=', from_state.id),
                        ('to_workflow_state_id', '=', to_state.id)
                    ], limit=1)
                    if state_transition.exists():
                        create_command = Command.create({
                            'from_workflow_stage_id': from_branch.id,
                            'to_workflow_stage_id': to_branch.id,
                            'workflow_state_transition_id': state_transition.id,
                            'workflow_id': None
                        })
                        if not collector.get('workflow_stage_transition_ids', False):
                            collector['workflow_stage_transition_ids'] = [create_command]
                        else:
                            collector['workflow_stage_transition_ids'].append(create_command)
            else:
                data = {
                    'workflow_id': None,
                    'from_workflow_id': from_branch.id,
                    'to_workflow_id': to_branch.id
                }
                if min_length == 1:
                    create_command = Command.create(data)
                    if not collector.get('workflow_transition_ids', False):
                        collector['workflow_transition_ids'] = [create_command]
                    else:
                        collector['workflow_transition_ids'].append(create_command)
                else:
                    next_data = self.get_workflow_transition_balanced_complement_bridges(
                        from_branches[1:], to_branches[1:], data
                    )
                    if next_data:
                        create_command = Command.create(next_data)
                        if not collector.get('workflow_transition_ids', False):
                            collector['workflow_transition_ids'] = [create_command]
                        else:
                            collector['workflow_transition_ids'].append(create_command)
        return collector

    def get_corresponding_procedure_transition_data(self, root_procedure_id, full=False):
        self.ensure_one()
        data = {}
        from_workflow_procedure = self.env['workflow.procedure'].search([
            '&', ('root_workflow_procedure_id', '=', root_procedure_id.id),
            ('workflow_id', '=', self.from_workflow_id.id)
        ])
        to_workflow_procedure = self.env['workflow.procedure'].search([
            '&', ('root_workflow_procedure_id', '=', root_procedure_id.id),
            ('workflow_id', '=', self.to_workflow_id.id)
        ])
        if from_workflow_procedure and to_workflow_procedure:
            data['context_type'] = self.context_type
            data['workflow_transition_id'] = self.id
            data['from_workflow_procedure_id'] = from_workflow_procedure.id
            data['to_workflow_procedure_id'] = to_workflow_procedure.id
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
        if len(self.workflow_transition_ids) > 0:
            for sub_transition in self.workflow_transition_ids:
                sub_transition_data = sub_transition.get_corresponding_procedure_transition_data(
                    root_procedure_id, True
                )
                if sub_transition_data:
                    create_command = Command.create(sub_transition_data)
                    if not data.get('workflow_procedure_transition_ids', False):
                        data['workflow_procedure_transition_ids'] = [create_command]
                    else:
                        data['workflow_procedure_transition_ids'].append(create_command)
        elif len(self.workflow_stage_transition_ids) > 0:
            for sub_stage_transition in self.workflow_stage_transition_ids:
                sub_stage_transition_data = sub_stage_transition.get_corresponding_procedure_stage_transition_data(
                    root_procedure_id, True
                )
                if sub_stage_transition_data:
                    create_command = Command.create(sub_stage_transition_data)
                    if not data.get('workflow_procedure_stage_transition_ids', False):
                        data['workflow_procedure_stage_transition_ids'] = [create_command]
                    else:
                        data['workflow_procedure_stage_transition_ids'].append(create_command)
        return data

    def get_workflow_procedure_transition_by_id(self, root_procedure_id):
        self.ensure_one()
        return self.env['workflow.procedure.transition'].search([
            '&', ('workflow_transition_id', '=', self.id),
            ('root_workflow_procedure_id', '=', root_procedure_id.id)
        ], limit=1)

# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError


STAGES_MISSING_KEY = "stages_missing"
STATES_MISSING_KEY = "states_missing"
STARTER_STAGE_MISSING_KEY = "starter_stage_missing"
STARTER_WORKFLOW_MISSING_KEY = "starter_workflow_missing"
CHILDREN_MISSING_KEY = "children_missing"
CHILD_NOT_READY_KEY = "child_not_ready"
STAGES_MISSING_TEXT = _("Activity Workflow must have at least one stage. Add one or many stages and declare one of "
                        "them as its starter stage !")
STATES_MISSING_TEXT = _("Activity Workflow must declare all the states displayed by its child stages. You can add the "
                        "missing states using the 'States' Tab !")
STARTER_STAGE_MISSING_TEXT = _("Activity Workflow must declare one of its child stages as its entry point. Fill the "
                               "'Starter Stage' field !")
STARTER_WORKFLOW_MISSING_TEXT = _("Base or Sub Workflow must declare one of its child workflows as its entry point. "
                                  "Fill the 'Starter Workflow' field !")
CHILDREN_MISSING_TEXT = _("Base or Sub Workflow which is not at the same time an activity must have at least one sub "
                          "workflow !")
CHILD_NOT_READY_TEXT = _("At least one of the sub workflow of the workflow is not ready. You can identify them in the "
                         "'Sub Workflows' tab and make them ready !")
NOT_READY_REASONS_DICT = {
    STAGES_MISSING_KEY: STAGES_MISSING_TEXT,
    STATES_MISSING_KEY: STATES_MISSING_TEXT,
    STARTER_STAGE_MISSING_KEY: STARTER_STAGE_MISSING_TEXT,
    STARTER_WORKFLOW_MISSING_KEY: STARTER_WORKFLOW_MISSING_TEXT,
    CHILDREN_MISSING_KEY: CHILDREN_MISSING_TEXT,
    CHILD_NOT_READY_KEY: CHILD_NOT_READY_TEXT
}


class Workflow(models.Model):
    _name = "workflow"
    _description = "Workflow"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow must be unique per '
                                                                  'company !')
    ]

    @api.constrains('base_workflow', 'activity_workflow', 'parent_id', 'workflow_stage_ids', 'workflow_state_ids')
    def _check_base_workflow_integrity(self):
        for workflow in self:
            if workflow.base_workflow and workflow.parent_id:
                raise ValidationError(_("A Base Workflow cannot be the sub workflow of another Workflow !"))
            if workflow.base_workflow and not workflow.activity_workflow and len(workflow.workflow_stage_ids) > 0:
                raise ValidationError(_("""A workflow which is not both base and activity workflow cannot contain 
                stages."""))
            if workflow.base_workflow and not workflow.activity_workflow and len(workflow.workflow_state_ids) > 0:
                raise ValidationError(_("""A workflow which is not both base and activity workflow cannot contain 
                states."""))

    @api.constrains('activity_workflow', 'workflow_ids', 'workflow_stage_ids', 'workflow_state_ids')
    def _check_activity_workflow_integrity(self):
        for workflow in self:
            if workflow.activity_workflow and len(workflow.workflow_ids) > 0:
                raise ValidationError(_("""Activity is the finer-grain workflow subdivision. Hence activity 
                workflows cannot be split in sub workflows !"""))
            if not workflow.activity_workflow and len(workflow.workflow_stage_ids) > 0:
                raise ValidationError(_("Workflow Stages can only be inserted into workflow activities !"))
            if not workflow.activity_workflow and len(workflow.workflow_state_ids) > 0:
                raise ValidationError(_("Workflow States can only be inserted into workflow activities !"))
            if workflow.activity_workflow and not workflow.base_workflow and not workflow.parent_id:
                raise ValidationError(_("Activity Workflow must be included in another workflow(base or sub) !"))

    @api.onchange('workflow_stage_ids')
    def _onchange_workflow_stages(self):
        if len(self.workflow_stage_ids) > 0:
            states_commands = []
            for stage in self.workflow_stage_ids:
                if stage.workflow_state_id not in self.workflow_state_ids:
                    states_commands.append(Command.link(stage.workflow_state_id.id))
            self.write({'workflow_state_ids': states_commands})
            if len(self.workflow_stage_ids) == 1:
                self.workflow_stage_id = self.workflow_stage_ids[0].id

    @api.onchange('workflow_ids')
    def _onchange_sub_workflows(self):
        if len(self.workflow_ids) == 1:
            self.starter_workflow_id = self.workflow_ids[0].id

    @api.depends('parent_id', 'root_workflow_id')
    def _compute_root_workflow(self):
        for workflow in self:
            workflow.root_workflow_id = workflow.get_root_workflow_id()

    @api.depends('base_workflow')
    def _compute_parent_allowed(self):
        for workflow in self:
            workflow.parent_allowed = not workflow.base_workflow

    @api.depends('activity_workflow')
    def _compute_children_allowed(self):
        for workflow in self:
            workflow.children_allowed = not workflow.activity_workflow

    @api.depends('activity_workflow')
    def _compute_stages_allowed(self):
        for workflow in self:
            workflow.stages_allowed = workflow.activity_workflow

    @api.depends('activity_workflow')
    def _compute_states_allowed(self):
        for workflow in self:
            workflow.states_allowed = workflow.activity_workflow

    @api.depends('workflow_ids')
    def _compute_sub_transitions_allowed(self):
        for workflow in self:
            workflow.sub_transitions_allowed = len(workflow.workflow_ids) >= 2

    @api.depends('workflow_stage_ids')
    def _compute_stage_transitions_allowed(self):
        for workflow in self:
            workflow.stage_transitions_allowed = len(workflow.workflow_stage_ids) >= 2

    @api.depends('started_workflow_ids')
    def _compute_has_started_workflows(self):
        for workflow in self:
            workflow.has_started_workflows = len(workflow.started_workflow_ids) > 0

    @api.depends('started_workflow_ids')
    def _compute_started_workflows_count(self):
        for workflow in self:
            workflow.started_workflows_count = len(workflow.started_workflow_ids)

    @api.depends('workflow_ids')
    def _compute_has_sub_workflows(self):
        for workflow in self:
            workflow.has_sub_workflows = len(workflow.workflow_ids) > 0

    @api.depends('workflow_ids')
    def _compute_sub_workflows_count(self):
        for workflow in self:
            workflow.sub_workflows_count = len(workflow.workflow_ids)

    @api.depends('workflow_procedure_ids')
    def _compute_has_procedures(self):
        for workflow in self:
            workflow.has_procedures = len(workflow.workflow_procedure_ids) > 0

    @api.depends('workflow_procedure_ids')
    def _compute_procedures_count(self):
        for workflow in self:
            workflow.procedures_count = len(workflow.workflow_procedure_ids)

    @api.depends('workflow_transition_ids')
    def _compute_has_sub_transitions(self):
        for workflow in self:
            workflow.has_sub_transitions = len(workflow.workflow_transition_ids) > 0

    @api.depends('workflow_transition_ids')
    def _compute_sub_transitions_count(self):
        for workflow in self:
            workflow.sub_transitions_count = len(workflow.workflow_transition_ids)

    @api.depends('workflow_stage_ids')
    def _compute_has_stages(self):
        for workflow in self:
            workflow.has_stages = len(workflow.workflow_stage_ids) > 0

    @api.depends('workflow_stage_ids')
    def _compute_stages_count(self):
        for workflow in self:
            workflow.stages_count = len(workflow.workflow_stage_ids)

    @api.depends('workflow_state_ids')
    def _compute_has_states(self):
        for workflow in self:
            workflow.has_states = len(workflow.workflow_state_ids) > 0

    @api.depends('workflow_state_ids')
    def _compute_states_count(self):
        for workflow in self:
            workflow.states_count = len(workflow.workflow_state_ids)

    @api.depends('workflow_stage_transition_ids')
    def _compute_has_stage_transitions(self):
        for workflow in self:
            workflow.has_stage_transitions = len(workflow.workflow_stage_transition_ids) > 0

    @api.depends('workflow_stage_transition_ids')
    def _compute_stage_transitions_count(self):
        for workflow in self:
            workflow.stage_transitions_count = len(workflow.workflow_stage_transition_ids)

    @api.depends('inbound_workflow_transition_ids')
    def _compute_has_inbound_transitions(self):
        for workflow in self:
            workflow.has_inbound_transitions = len(workflow.inbound_workflow_transition_ids) > 0

    @api.depends('inbound_workflow_transition_ids')
    def _compute_inbound_transitions_count(self):
        for workflow in self:
            workflow.inbound_transitions_count = len(workflow.inbound_workflow_transition_ids)

    @api.depends('outbound_workflow_transition_ids')
    def _compute_has_outbound_transitions(self):
        for workflow in self:
            workflow.has_outbound_transitions = len(workflow.outbound_workflow_transition_ids) > 0

    @api.depends('outbound_workflow_transition_ids')
    def _compute_outbound_transitions_count(self):
        for workflow in self:
            workflow.outbound_transitions_count = len(workflow.outbound_workflow_transition_ids)

    @api.depends('activity_workflow', 'workflow_stage_id', 'workflow_stage_ids', 'starter_workflow_id', 'workflow_ids', 'workflow_state_ids')
    def _compute_is_ready(self):
        for workflow in self:
            if str(workflow.id).startswith('NewId'):
                workflow.is_ready = True
            elif workflow.activity_workflow:
                workflow.is_ready = (len(workflow.workflow_stage_ids) > 0) and workflow.workflow_stage_id and (len(workflow.workflow_state_ids) > 0)
            elif not workflow.starter_workflow_id:
                workflow.is_ready = False
            else:
                workflow.is_ready = True
                for sub_workflow in workflow.workflow_ids:
                    if not sub_workflow.is_ready:
                        workflow.is_ready = False
                        break
            if workflow.parent_id:
                workflow.parent_id._compute_is_ready()

    @api.onchange('activity_workflow', 'workflow_state_ids', 'workflow_stage_id', 'workflow_stage_ids', 'starter_workflow_id', 'workflow_ids')
    def _onchange_is_ready(self):
        self._compute_is_ready()

    @api.depends('workflow_stage_ids', 'workflow_state_ids', 'workflow_stage_id', 'workflow_ids', 'starter_workflow_id')
    def _compute_not_ready_reason(self):
        for workflow in self:
            wrapper = ''
            present_keys = []
            if not workflow.is_ready and not str(workflow.id).startswith('New'):
                wrapper = '<ul class="list-group rounded-0">'
                if workflow.activity_workflow:
                    if len(workflow.workflow_stage_ids) == 0:
                        if STAGES_MISSING_KEY not in present_keys:
                            li = '<li class="list-group-item list-group-item-danger">%s</li>\n' % NOT_READY_REASONS_DICT[STAGES_MISSING_KEY]
                            wrapper += li
                            present_keys.append(STAGES_MISSING_KEY)
                    if len(workflow.workflow_state_ids) == 0:
                        if STATES_MISSING_KEY not in present_keys:
                            li = '<li class="list-group-item list-group-item-danger">%s</li>\n' % NOT_READY_REASONS_DICT[STATES_MISSING_KEY]
                            wrapper += li
                            present_keys.append(STATES_MISSING_KEY)
                    if not workflow.workflow_stage_id:
                        if STARTER_STAGE_MISSING_KEY not in present_keys:
                            li = '<li class="list-group-item list-group-item-danger">%s</li>\n' % NOT_READY_REASONS_DICT[STARTER_STAGE_MISSING_KEY]
                            wrapper += li
                            present_keys.append(STARTER_STAGE_MISSING_KEY)
                else:
                    if len(workflow.workflow_ids) == 0 and STARTER_STAGE_MISSING_KEY not in present_keys:
                        li = '<li class="list-group-item list-group-item-danger">%s</li>\n' % NOT_READY_REASONS_DICT[CHILDREN_MISSING_KEY]
                        wrapper += li
                        present_keys.append(CHILDREN_MISSING_KEY)
                    if not workflow.starter_workflow_id and STARTER_WORKFLOW_MISSING_KEY not in present_keys:
                        li = '<li class="list-group-item list-group-item-danger">%s</li>\n' % NOT_READY_REASONS_DICT[STARTER_WORKFLOW_MISSING_KEY]
                        wrapper += li
                        present_keys.append(STARTER_WORKFLOW_MISSING_KEY)
                    for sub in workflow.workflow_ids:
                        if not sub.is_ready and CHILD_NOT_READY_KEY not in present_keys:
                            li = '<li class="list-group-item list-group-item-danger">%s</li>\n' % NOT_READY_REASONS_DICT[CHILD_NOT_READY_KEY]
                            wrapper += li
                            present_keys.append(CHILD_NOT_READY_KEY)
                wrapper += "</ul>"
            workflow.not_ready_reason = wrapper

    @api.depends('workflow_stage_ids')
    def _compute_default_starter_stage(self):
        for workflow in self:
            if workflow.activity_workflow and len(workflow.workflow_stage_ids) > 0:
                return workflow.workflow_stage_ids[0].id
            return None

    codename = fields.Char(string='Codename', required=True, copy=False)
    name = fields.Char(string='Name', required=True, translate=True)
    base_workflow = fields.Boolean(default=False, string="Base ?")
    activity_workflow = fields.Boolean(default=False, string="Activity ?")
    root_workflow_id = fields.Many2one('workflow', required=False, readonly=True,
                                       string="Root Workflow", compute="_compute_root_workflow",
                                       store=True)
    workflow_stage_id = fields.Many2one('workflow.stage', required=False,
                                        string="Starter Stage", default=_compute_default_starter_stage)
    parent_id = fields.Many2one('workflow', string="Parent Workflow")
    starter_workflow_id = fields.Many2one('workflow', required=False, string="Starter Workflow")
    started_workflow_ids = fields.One2many('workflow', 'starter_workflow_id',
                                           string="Started Workflows")
    workflow_ids = fields.One2many('workflow', 'parent_id',
                                   string="Sub workflows")
    workflow_procedure_ids = fields.One2many('workflow.procedure',
                                             'workflow_id', string='Procedures')
    workflow_transition_ids = fields.One2many('workflow.transition',
                                              'workflow_id',
                                              string="Workflow Transitions")
    workflow_stage_ids = fields.One2many('workflow.stage', 'workflow_id',
                                         string="Workflow Stages")
    workflow_stage_transition_ids = fields.One2many('workflow.stage.transition',
                                                    'workflow_id',
                                                    string="Workflow Stage Transitions")
    inbound_workflow_transition_ids = fields.One2many('workflow.transition',
                                                      'to_workflow_id',
                                                      string="Inbound Workflow Transitions")
    outbound_workflow_transition_ids = fields.One2many('workflow.transition',
                                                       'from_workflow_id',
                                                       string="Outbound Workflow Transitions")
    workflow_state_ids = fields.Many2many('workflow.state',
                                          'workflow_workflow_state', string='States')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    pass_on_changes = fields.Boolean(string="Pass On Changes", default=False)
    active = fields.Boolean(default=True)
    is_ready = fields.Boolean(readonly=True, compute="_compute_is_ready", string="Is Ready ?",
                              store=True)
    parent_allowed = fields.Boolean(readonly=True, compute="_compute_parent_allowed")
    children_allowed = fields.Boolean(readonly=True, compute="_compute_children_allowed")
    states_allowed = fields.Boolean(readonly=True, compute="_compute_states_allowed")
    stages_allowed = fields.Boolean(readonly=True, compute="_compute_stages_allowed")
    stage_transitions_allowed = fields.Boolean(readonly=True, compute="_compute_stage_transitions_allowed")
    has_started_workflows = fields.Boolean(readonly=True, compute="_compute_has_started_workflows")
    started_workflows_count = fields.Integer(readonly=True, compute="_compute_started_workflows_count")
    sub_transitions_allowed = fields.Boolean(readonly=True, compute="_compute_sub_transitions_allowed")
    has_sub_workflows = fields.Boolean(readonly=True, compute="_compute_has_sub_workflows")
    sub_workflows_count = fields.Boolean(readonly=True, compute="_compute_sub_workflows_count")
    has_procedures = fields.Boolean(readonly=True, compute="_compute_has_procedures")
    procedures_count = fields.Boolean(readonly=True, compute="_compute_procedures_count")
    has_sub_transitions = fields.Boolean(readonly=True, compute="_compute_has_sub_transitions")
    sub_transitions_count = fields.Boolean(readonly=True, compute="_compute_sub_transitions_count")
    has_stages = fields.Boolean(readonly=True, compute="_compute_has_stages")
    stages_count = fields.Boolean(readonly=True, compute="_compute_stages_count")
    has_stage_transitions = fields.Boolean(readonly=True, compute="_compute_has_stage_transitions")
    stage_transitions_count = fields.Boolean(readonly=True, compute="_compute_stage_transitions_count")
    has_states = fields.Boolean(readonly=True, compute="_compute_has_states")
    states_count = fields.Boolean(readonly=True, compute="_compute_states_count")
    has_inbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_inbound_transitions")
    inbound_transitions_count = fields.Boolean(readonly=True, compute="_compute_inbound_transitions_count")
    has_outbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_outbound_transitions")
    outbound_transitions_count = fields.Boolean(readonly=True, compute="_compute_outbound_transitions_count")
    not_ready_reason = fields.Html("Not Ready reason", required=False, compute="_compute_not_ready_reason")

    def get_descendant_workflow_ids(self, collector=False):
        self.ensure_one()
        if not collector:
            collector = []
        if self.activity_workflow:
            return collector
        else:
            children_ids = self.workflow_ids.mapped('id')
            collector += children_ids
            for child in self.workflow_ids:
                collector = child.get_descendant_workflow_ids(collector)
            return collector

    def get_descendant_workflows(self):
        self.ensure_one()
        if self.base_workflow:
            return self.env['workflow'].search([('root_workflow_id', '=', self.id)])
        else:
            descendant_ids = self.get_descendant_workflow_ids()
            return self.browse(descendant_ids)

    def get_descendant_workflow_stages(self):
        self.ensure_one()
        if self.base_workflow:
            return self.env['workflow.stage'].search([('root_workflow_id', '=', self.id)])
        return self.env['workflow.stage'].search([('id', '=', 0)])

    def get_descendant_workflow_transitions(self):
        self.ensure_one()
        if self.base_workflow:
            return self.env['workflow.transition'].search([('root_workflow_id', '=', self.id)])
        return self.env['workflow.transition'].search([('id', '=', 0)])

    def get_descendant_workflow_stage_transitions(self):
        self.ensure_one()
        if self.base_workflow:
            return self.env['workflow.stage.transition'].search([('root_workflow_id', '=', self.id)])
        return self.env['workflow.stage.transition'].search([('id', '=', 0)])

    def get_corresponding_procedure_data(self, workflowable_type_id, collector=False, root_included=False):
        self.ensure_one()
        data = {}
        if root_included:
            procedure_codename = self.codename + '_procedure'
            procedure_name = self.name + ' Procedure'
            if 'workflow' in self.codename:
                procedure_codename = self.codename.replace('workflow', 'procedure')
            if 'workflow' in self.name:
                procedure_name = self.name.replace('Workflow', 'Procedure')
            data = {
                'codename': procedure_codename,
                'name': procedure_name,
                'base_procedure': self.base_workflow,
                'activity_procedure': self.activity_workflow,
                'workflow_id': self.id,
                'workflowable_type_id': workflowable_type_id.id
            }
        if len(self.workflow_stage_ids) > 0:
            for workflow_stage in self.workflow_stage_ids:
                procedure_stage_data = workflow_stage.get_corresponding_procedure_stage_data()
                create_command = Command.create(procedure_stage_data)
                if not data.get('workflow_procedure_stage_ids'):
                    data['workflow_procedure_stage_ids'] = [create_command]
                else:
                    data['workflow_procedure_stage_ids'].append(create_command)
        elif len(self.workflow_ids) > 0:
            for workflow in self.workflow_ids:
                procedure_data = workflow.get_corresponding_procedure_data(
                    workflowable_type_id, {}, True
                )
                create_command = Command.create(procedure_data)
                if not data.get('workflow_procedure_ids'):
                    data['workflow_procedure_ids'] = [create_command]
                else:
                    data['workflow_procedure_ids'].append(create_command)
        if not collector:
            return data
        return collector

    def get_corresponding_procedure_transitions_data(self, root_procedure_id):
        self.ensure_one()
        descendants = self.get_descendant_workflow_transitions()
        skipped_transitions = []
        transitions_data = []
        if self.base_workflow:
            for workflow_transition in descendants:
                if workflow_transition.workflow_transition_id and workflow_transition not in skipped_transitions:
                    skipped_transitions.append(workflow_transition)
            for sub_workflow_transition in list(set(descendants) - set(skipped_transitions)):
                corresponding_procedure_transition_data = sub_workflow_transition.get_corresponding_procedure_transition_data(
                    root_procedure_id, True
                )
                transitions_data.append(corresponding_procedure_transition_data)
        return transitions_data

    def get_corresponding_procedure_stage_transitions_data(self, root_procedure_id):
        self.ensure_one()
        transitions_data = []
        for workflow_stage_transition in self.get_descendant_workflow_stage_transitions():
            if workflow_stage_transition.workflow_id:
                corresponding_procedure_stage_transition_data = workflow_stage_transition.get_corresponding_procedure_stage_transition_data(
                    root_procedure_id, True
                )
                transitions_data.append(corresponding_procedure_stage_transition_data)
        return transitions_data

    def get_root_workflow_id(self):
        self.ensure_one()
        if self.base_workflow:
            return self.id
        else:
            return self.parent_id.get_root_workflow_id()

    def get_workflow_starter_branch(self, collector=False):
        self.ensure_one()
        if not collector:
            collector = []
        if self.activity_workflow:
            collector.append(self)
            if self.workflow_stage_id:
                collector.append(self.workflow_stage_id)
        else:
            collector.append(self)
            if self.starter_workflow_id:
                collector = self.starter_workflow_id.get_workflow_starter_branch(collector)
        return collector

    def get_corresponding_base_procedure_data(self, workflowable_type_id):
        self.ensure_one()
        if self.base_workflow:
            return self.get_corresponding_procedure_data(
                workflowable_type_id, {}
            )

    @api.model
    def find_procedure_by_workflow_id(self, root_workflow_id, workflow_id):
        return self.env['workflow.procedure'].search([
            '&', ('workflow_id.root_workflow_id', '=', root_workflow_id),
            ('workflow_id', '=', workflow_id.id)
        ], limit=1)

    def get_path_to_starter_stage(self, collector=None):
        self.ensure_one()
        if collector is None:
            collector = []
        if self.activity_workflow:
            if self.workflow_stage_id:
                collector.append(self.workflow_stage_id)
            return collector
        elif self.starter_workflow_id:
            collector.append(self.starter_workflow_id)
            collector = self.starter_workflow_id.get_path_to_starter_stage(collector)
            return collector

    def get_workflow_procedure_by_id(self, root_procedure_id):
        self.ensure_one()
        return self.env['workflow.procedure'].search([
            '&', ('workflow_id', '=', self.id),
            ('root_workflow_procedure_id', '=', root_procedure_id.id)
        ], limit=1)

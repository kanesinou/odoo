# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
from odoo.tools import safe_eval
from ..utils import date_utils


def get_model_base_procedures(env, model_name):
    all_procedures = env['workflow.procedure'].search([
        '&', '&', ('base_procedure', '=', True), ('released', '=', True),
        ('workflowable_type_id.model_id.model', '=', model_name)
    ])
    default_procedures = all_procedures.filtered(lambda p: p.is_default)
    non_default_procedures = all_procedures.filtered(lambda p: not p.is_default)
    default_procedure_ids = []
    non_default_procedure_ids = []
    for default_procedure in default_procedures:
        specialised_procedures = non_default_procedures.filtered(
            lambda p: p.workflow_id.id == default_procedure.workflow_id.id
        )
        if len(specialised_procedures) > 0:
            non_default_procedure_ids.extend(specialised_procedures.mapped('id'))
        else:
            default_procedure_ids.append(default_procedure.id)
    return env['workflow.procedure'].search([
        '&', ('base_procedure', '=', True),
        ('id', 'in', default_procedure_ids + non_default_procedure_ids)
    ])


class WorkflowProcedure(models.Model):
    _name = "workflow.procedure"
    _description = "Workflow Procedure"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow procedure must be '
                                                                  'unique per company !'),
        ('config_params_uniq', 'unique (workflowable_type_id,filter_domain,workflow_id)', 'The workflow procedure is '
                                                                                          'already defined !')
    ]

    @api.onchange('workflow_id')
    def _onchange_workflow(self):
        if self.workflow_id:
            if self.workflow_id.activity_workflow:
                self.starter_stage_allowed = True
            else:
                self.starter_stage_allowed = False

    @api.onchange("base_procedure", "parent_allowed")
    def _onchange_base_procedure(self):
        if self.base_procedure:
            self.parent_allowed = False
        else:
            self.parent_allowed = True

    @api.onchange("activity_procedure", "children_allowed")
    def _onchange_activity_procedure(self):
        if self.activity_procedure:
            self.children_allowed = False
        else:
            self.children_allowed = True

    @api.onchange('workflow_procedure_stage_id', 'release_allowed', 'released')
    def _onchange_starter_stage(self):
        if self.workflow_procedure_stage_id and not self.released:
            self.release_allowed = True
        else:
            self.release_allowed = False

    @api.onchange('workflow_procedure_stage_id')
    def _on_change_starter_stage(self):
        if self.workflow_procedure_stage_id:
            self.expand_starters()
        else:
            self.unexpand_starters()

    @api.onchange('released')
    def _onchange_released(self):
        if self.released:
            self.release_allowed = False

    @api.depends('parent_id')
    def _compute_root_workflow_procedure(self):
        for procedure in self:
            procedure.root_workflow_procedure_id = procedure.get_root_workflow_procedure_id()

    @api.depends('time_unit', 'workflow_procedure_duration_ids')
    def _compute_min_duration(self):
        for procedure in self:
            procedure.min_duration = 0
            if procedure.time_unit:
                duration_instance = procedure.workflow_procedure_duration_ids.filtered(
                    lambda d: d.time_unit == procedure.time_unit
                )
                if duration_instance.exists():
                    procedure.min_duration = duration_instance[0].min_duration

    @api.depends('time_unit', 'workflow_procedure_duration_ids')
    def _compute_max_duration(self):
        for procedure in self:
            procedure.max_duration = 0
            if procedure.time_unit:
                duration_instance = procedure.workflow_procedure_duration_ids.filtered(
                    lambda d: d.time_unit == procedure.time_unit
                )
                if duration_instance.exists():
                    procedure.max_duration = duration_instance[0].max_duration

    @api.depends('min_duration', 'max_duration')
    def _compute_duration_range(self):
        for procedure in self:
            procedure.duration_range = procedure.max_duration - procedure.min_duration

    @api.depends('min_estimated_duration', 'max_estimated_duration')
    def _compute_estimated_duration_range(self):
        for procedure in self:
            procedure.estimated_duration_range = procedure.max_estimated_duration - procedure.min_estimated_duration

    @api.depends('min_execution_duration', 'max_execution_duration')
    def _compute_execution_duration_range(self):
        for procedure in self:
            procedure.execution_duration_range = procedure.max_execution_duration - procedure.min_execution_duration

    @api.depends('activity_procedure', 'time_unit', 'workflow_procedure_stage_ids', 'workflow_procedure_ids')
    def _compute_min_estimated_duration(self):
        for procedure in self:
            procedure.min_estimated_duration = 0
            if procedure.time_unit:
                procedure.min_estimated_duration = procedure.get_min_duration_for_time_unit(procedure.time_unit)

    @api.depends('activity_procedure', 'time_unit', 'workflow_procedure_stage_ids', 'workflow_procedure_ids')
    def _compute_max_estimated_duration(self):
        for procedure in self:
            procedure.max_estimated_duration = 0
            if procedure.time_unit:
                procedure.max_estimated_duration = procedure.get_max_duration_for_time_unit(procedure.time_unit)

    @api.depends('activity_procedure', 'time_unit', 'workflow_procedure_stage_ids', 'workflow_procedure_ids')
    def _compute_min_execution_duration(self):
        for procedure in self:
            procedure.min_execution_duration = 0
            if procedure.time_unit:
                procedure.min_execution_duration = procedure.get_min_execution_duration_for_time_unit(
                    procedure.time_unit
                )

    @api.depends('activity_procedure', 'time_unit', 'workflow_procedure_stage_ids', 'workflow_procedure_ids')
    def _compute_max_execution_duration(self):
        for procedure in self:
            procedure.max_execution_duration = 0
            if procedure.time_unit:
                procedure.max_execution_duration = procedure.get_max_execution_duration_for_time_unit(
                    procedure.time_unit
                )

    @api.depends('activity_procedure', 'workflow_procedure_stage_ids', 'workflow_procedure_ids')
    def _compute_can_be_cancelled(self):
        for procedure in self:
            if procedure.activity_procedure:
                cancellable_stages = procedure.workflow_procedure_stage_ids.filtered(lambda s: s.can_be_cancelled)
                procedure.can_be_cancelled = len(cancellable_stages) > 0
            else:
                cancellable_subs = procedure.workflow_procedure_ids.filtered(lambda s: s.can_be_cancelled)
                procedure.can_be_cancelled = len(cancellable_subs) > 0

    @api.depends('activity_procedure', 'workflow_procedure_stage_ids', 'workflow_procedure_ids')
    def _compute_can_be_breaked(self):
        for procedure in self:
            if procedure.activity_procedure:
                breakable_stages = procedure.workflow_procedure_stage_ids.filtered(lambda s: s.can_be_breaked)
                procedure.can_be_breaked = len(breakable_stages) > 0
            else:
                breakable_subs = procedure.workflow_procedure_ids.filtered(lambda s: s.can_be_breaked)
                procedure.can_be_breaked = len(breakable_subs) > 0

    @api.depends('activity_procedure', 'workflow_procedure_stage_ids', 'workflow_procedure_ids')
    def _compute_can_be_resumed(self):
        for procedure in self:
            if procedure.activity_procedure:
                resumable_stages = procedure.workflow_procedure_stage_ids.filtered(lambda s: s.can_be_resumed)
                procedure.can_be_resumed = len(resumable_stages) > 0
            else:
                resumable_subs = procedure.workflow_procedure_ids.filtered(lambda s: s.can_be_resumed)
                procedure.can_be_resumed = len(resumable_subs) > 0

    @api.depends('base_procedure')
    def _compute_parent_allowed(self):
        for procedure in self:
            procedure.parent_allowed = not procedure.base_procedure

    @api.depends('activity_procedure')
    def _compute_children_allowed(self):
        for procedure in self:
            procedure.children_allowed = not procedure.activity_procedure

    @api.depends('released')
    def _compute_release_allowed(self):
        for procedure in self:
            procedure.release_allowed = not procedure.released

    @api.depends('activity_procedure')
    def _compute_starter_stage_allowed(self):
        for procedure in self:
            procedure.starter_stage_allowed = not procedure.activity_procedure

    @api.depends('workflow_procedure_duration_ids')
    def _compute_has_durations(self):
        for procedure in self:
            procedure.has_durations = len(procedure.workflow_procedure_duration_ids) > 0

    @api.depends('workflow_procedure_duration_ids')
    def _compute_durations_count(self):
        for procedure in self:
            procedure.durations_count = len(procedure.workflow_procedure_duration_ids)

    @api.depends('workflow_procedure_ids')
    def _compute_has_sub_procedures(self):
        for procedure in self:
            procedure.has_sub_procedures = len(procedure.workflow_procedure_ids) > 0

    @api.depends('workflow_procedure_ids')
    def _compute_sub_procedures_count(self):
        for procedure in self:
            procedure.sub_procedures_count = len(procedure.workflow_procedure_ids)

    @api.depends('workflow_process_ids')
    def _compute_has_processes(self):
        for procedure in self:
            procedure.has_processes = len(procedure.workflow_process_ids) > 0

    @api.depends('workflow_process_ids')
    def _compute_processes_count(self):
        for procedure in self:
            procedure.processes_count = len(procedure.workflow_process_ids)

    @api.depends('workflow_procedure_transition_ids')
    def _compute_has_sub_transitions(self):
        for procedure in self:
            procedure.has_sub_transitions = len(procedure.workflow_procedure_transition_ids) > 0

    @api.depends('workflow_procedure_transition_ids')
    def _compute_sub_transitions_count(self):
        for procedure in self:
            procedure.sub_transitions_count = len(procedure.workflow_procedure_transition_ids)

    @api.depends('workflow_procedure_stage_ids')
    def _compute_has_stages(self):
        for procedure in self:
            procedure.has_stages = len(procedure.workflow_procedure_stage_ids) > 0

    @api.depends('workflow_procedure_stage_ids')
    def _compute_stages_count(self):
        for procedure in self:
            procedure.stages_count = len(procedure.workflow_procedure_stage_ids)

    @api.depends('workflow_procedure_stage_transition_ids')
    def _compute_has_stage_transitions(self):
        for procedure in self:
            procedure.has_stage_transitions = len(procedure.workflow_procedure_stage_transition_ids) > 0

    @api.depends('workflow_procedure_stage_transition_ids')
    def _compute_stage_transitions_count(self):
        for procedure in self:
            procedure.stage_transitions_count = len(procedure.workflow_procedure_stage_transition_ids)

    @api.depends('inbound_workflow_procedure_transition_ids')
    def _compute_has_inbound_transitions(self):
        for procedure in self:
            procedure.has_inbound_transitions = len(procedure.inbound_workflow_procedure_transition_ids) > 0

    @api.depends('inbound_workflow_procedure_transition_ids')
    def _compute_inbound_transitions_count(self):
        for procedure in self:
            procedure.inbound_transitions_count = len(procedure.inbound_workflow_procedure_transition_ids)

    @api.depends('outbound_workflow_procedure_transition_ids')
    def _compute_has_outbound_transitions(self):
        for procedure in self:
            procedure.has_outbound_transitions = len(procedure.outbound_workflow_procedure_transition_ids) > 0

    @api.depends('outbound_workflow_procedure_transition_ids')
    def _compute_outbound_transitions_count(self):
        for procedure in self:
            procedure.outbound_transitions_count = len(procedure.outbound_workflow_procedure_transition_ids)

    @api.depends('filter_domain')
    def _compute_is_default(self):
        for procedure in self:
            procedure.is_default = True
            if procedure.filter_domain:
                procedure.is_default = False

    codename = fields.Char(string='Codename', required=True, copy=False)
    name = fields.Char(string='Name', required=True, translate=True)
    base_procedure = fields.Boolean(string="Base ?", related="workflow_id.base_workflow")
    activity_procedure = fields.Boolean(string="Activity ?", related="workflow_id.activity_workflow")
    is_default = fields.Boolean(string="Is Default", compute="_compute_is_default")
    released = fields.Boolean(string="Released ?", default=False)
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    workflow_id = fields.Many2one('workflow', string="Workflow",
                                  required=True)
    workflowable_type_id = fields.Many2one('workflowable.type', ondelete='cascade',
                                           string="Model",  required=True, auto_join=True)
    model_name = fields.Char(string="Domain Model", readonly=True, required=False,
                             related="workflowable_type_id.model_id.model")
    filter_domain = fields.Text(string="Domain", required=False)
    state = fields.Selection(selection=[('new', 'New'), ('released', 'Released'), ('unreleased', 'Unreleased')],
                             string="State", required=True, default='new')
    starter_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                    readonly=True, invisible=True,
                                                    string="Starter Procedure")
    started_workflow_procedure_ids = fields.One2many('workflow.procedure',
                                                     'starter_workflow_procedure_id',
                                                     string="Started Procedures")
    workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage',
                                                  string="Starter Stage", required=False,
                                                  domain="[('root_workflow_procedure_id', '=', root_workflow_procedure_id)]")
    parent_id = fields.Many2one('workflow.procedure', string="Parent")
    workflow_procedure_ids = fields.One2many('workflow.procedure',
                                             'parent_id', string="Sub Procedures")
    workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                        'workflow_procedure_id',
                                                        string="Procedure Transitions")
    workflow_procedure_stage_ids = fields.One2many('workflow.procedure.stage',
                                                   'workflow_procedure_id',
                                                   string="Procedure Stages")
    workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                              'workflow_procedure_id',
                                                              string="Procedure Stage Transitions")
    workflow_process_ids = fields.One2many('workflow.process',
                                           'workflow_procedure_id',
                                           string="Processes")
    workflow_procedure_collision_ids = fields.One2many('workflow.procedure.collision',
                                                       'workflow_procedure_id',
                                                       string="Procedure Collisions")
    inbound_workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                                'to_workflow_procedure_id',
                                                                string="Inbound Procedure Transitions")
    outbound_workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                                 'from_workflow_procedure_id',
                                                                 string="Outbound Procedure Transitions")
    workflow_procedure_duration_ids = fields.One2many('workflow.procedure.duration',
                                                      'workflow_procedure_id',
                                                      string="Durations")
    action_server_id = fields.Many2one('ir.actions.server', readonly=True, required=False)
    automation_id = fields.Many2one('base.automation', readonly=True, required=False)
    trigger_type = fields.Selection(default="automatic", string="Trigger type",
                                    selection=[('automatic', 'Automatic'), ('manual', 'Manual')])
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    pass_on_changes = fields.Boolean(string="Pass On Changes", default=False)
    apply_workflow_changes = fields.Boolean(string="Apply Workflow Changes", default=False)
    active = fields.Boolean(default=True)
    can_be_cancelled = fields.Boolean(readonly=True, compute="_compute_can_be_cancelled")
    can_be_breaked = fields.Boolean(readonly=True, compute="_compute_can_be_breaked")
    can_be_resumed = fields.Boolean(readonly=True, compute="_compute_can_be_resumed")
    parent_allowed = fields.Boolean(invisible=True, compute="_compute_parent_allowed")
    children_allowed = fields.Boolean(invisible=True, compute="_compute_children_allowed")
    release_allowed = fields.Boolean(invisible=True, compute="_compute_release_allowed")
    starter_stage_allowed = fields.Boolean(invisible=True, compute="_compute_starter_stage_allowed")
    new_procedure = fields.Boolean(invisible=True, default=True)
    configured = fields.Boolean(invisible=True, default=False)
    time_unit = fields.Selection(
        selection=[
            ("minute", "Minute"),
            ("hour", "Hour"),
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month"),
            ("quarter", "Quarter"),
            ("semester", "Semester"),
            ("year", "Year")
        ],
        string="Time Unit", required=False, default='hour'
    )
    min_duration = fields.Float(string="Minimum Duration", default=0, digits=(11, 5),
                                compute="_compute_min_duration")
    max_duration = fields.Float(string="Maximum Duration", default=0, digits=(11, 5),
                                compute="_compute_max_duration")
    duration_range = fields.Float(string="Duration Range", readonly=True, default=0,
                                  compute="_compute_duration_range", digits=(11, 5))
    min_estimated_duration = fields.Float(readonly=True, compute="_compute_min_estimated_duration",
                                          default=0, digits=(11, 5))
    max_estimated_duration = fields.Float(readonly=True, compute="_compute_max_estimated_duration",
                                          default=0, digits=(11, 5))
    estimated_duration_range = fields.Float(string="Estimated Duration Range", readonly=True, default=0,
                                            compute="_compute_estimated_duration_range", digits=(11, 5))
    min_execution_duration = fields.Float(readonly=True, compute="_compute_min_execution_duration",
                                          default=0, digits=(11, 5))
    max_execution_duration = fields.Float(readonly=True, compute="_compute_max_execution_duration",
                                          default=0, digits=(11, 5))
    execution_duration_range = fields.Float(string="Execution Duration Range", readonly=True, default=0,
                                            compute="_compute_execution_duration_range", digits=(11, 5))
    has_durations = fields.Boolean(readonly=True, compute="_compute_has_durations")
    durations_count = fields.Boolean(readonly=True, compute="_compute_durations_count")
    has_sub_procedures = fields.Boolean(readonly=True, compute="_compute_has_sub_procedures")
    sub_procedures_count = fields.Boolean(readonly=True, compute="_compute_sub_procedures_count")
    has_processes = fields.Boolean(readonly=True, compute="_compute_has_processes")
    processes_count = fields.Boolean(readonly=True, compute="_compute_processes_count")
    has_sub_transitions = fields.Boolean(readonly=True, compute="_compute_has_sub_transitions")
    sub_transitions_count = fields.Boolean(readonly=True, compute="_compute_sub_transitions_count")
    has_stages = fields.Boolean(readonly=True, compute="_compute_has_stages")
    stages_count = fields.Boolean(readonly=True, compute="_compute_stages_count")
    has_stage_transitions = fields.Boolean(readonly=True, compute="_compute_has_stage_transitions")
    stage_transitions_count = fields.Boolean(readonly=True, compute="_compute_stage_transitions_count")
    has_inbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_inbound_transitions")
    inbound_transitions_count = fields.Boolean(readonly=True, compute="_compute_inbound_transitions_count")
    has_outbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_outbound_transitions")
    outbound_transitions_count = fields.Boolean(readonly=True, compute="_compute_outbound_transitions_count")

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        records = super(WorkflowProcedure, self).create(vals_list)
        for record in records:
            record.complete_procedure_structure()
        return records

    def unlink(self):
        action_server_id = False
        automation_id = False
        if self.action_server_id:
            action_server_id = self.action_server_id.id
        if self.automation_id:
            automation_id = self.automation_id.id
        res = super(WorkflowProcedure, self).unlink()
        if automation_id:
            automation_instance = self.env['base.automation'].browse(automation_id)
            if automation_instance.exists():
                automation_instance.unlink()
        if action_server_id:
            action_server_instance = self.env['ir.actions.server'].browse(action_server_id)
            if action_server_instance.exists():
                action_server_instance.unlink()
        return res

    def eval_filter_domain(self, context=False):
        self.ensure_one()
        if not context:
            context = self.env.context
        domain_filter = safe_eval.safe_eval(self.filter_domain, context)
        return self.env[self.model_name].search(domain_filter)

    def complete_procedure_structure(self):
        self.ensure_one()
        if self.base_procedure and self.workflow_id and self.workflowable_type_id:
            structure_data = self.workflow_id.get_corresponding_base_procedure_data(
                self.workflowable_type_id
            )
            self.write(structure_data)
            self.complete_procedure_starters_structure()
            transitions_data = self.workflow_id.get_corresponding_procedure_transitions_data(self)
            stage_transitions_data = self.workflow_id.get_corresponding_procedure_stage_transitions_data(self)
            if len(transitions_data) > 0:
                self.env['workflow.procedure.transition'].create(transitions_data)
            if len(stage_transitions_data) > 0:
                self.env['workflow.procedure.stage.transition'].create(stage_transitions_data)

    def complete_procedure_starters_structure(self):
        self.ensure_one()
        if self.base_procedure and self.workflow_id:
            for descendant_workflow in self.workflow_id.get_descendant_workflows():
                procedure = descendant_workflow.get_workflow_procedure_by_id(self)
                if procedure.exists() and len(descendant_workflow.started_workflow_ids) > 0:
                    started_procedures = self.env['workflow.procedure'].search([
                        '&', ('workflow_id', 'in', descendant_workflow.started_workflow_ids.mapped('id')),
                        ('root_workflow_procedure_id', '=', self.id)
                    ])
                    if started_procedures.exists():
                        procedure.write({'started_workflow_procedure_ids': started_procedures})
            for descendant_stage in self.workflow_id.get_descendant_workflow_stages():
                procedure_stage = descendant_stage.get_workflow_procedure_stage_by_id(self)
                if procedure_stage.exists() and len(descendant_stage.workflow_ids) > 0:
                    started_procedures = self.env['workflow.procedure'].search([
                        '&', ('workflow_id', 'in', descendant_stage.workflow_ids.mapped('id')),
                        ('root_workflow_procedure_id', '=', self.id)
                    ])
                    if started_procedures.exists():
                        procedure_stage.write({'workflow_procedure_ids': started_procedures})
                if procedure_stage.exists():
                    procedure_execution_commands = descendant_stage.get_mandatory_procedure_executions_create_data(
                        procedure_stage.id
                    )
                    procedure_execution_commands.extend(descendant_stage.get_optional_procedure_executions_create_data(
                        procedure_stage.id
                    ))
                    procedure_stage.write({'workflow_procedure_execution_ids': procedure_execution_commands})

    def get_descendant_procedure_ids(self, collector=False):
        self.ensure_one()
        if not collector:
            collector = []
        if self.activity_procedure:
            return collector
        else:
            children_ids = self.workflow_procedure_ids.mapped('id')
            collector += children_ids
            for child in self.workflow_procedure_ids:
                collector = child.get_descendant_procedure_ids(collector)
            return collector

    def get_descendant_procedures(self):
        self.ensure_one()
        if self.base_procedure:
            return self.env['workflow.procedure'].search([('root_workflow_procedure_id', '=', self.id)])
        else:
            descendant_ids = self.get_descendant_procedure_ids()
            return self.browse(descendant_ids)

    def get_descendant_procedure_execution_ids(self):
        self.ensure_one()
        ids = []
        if self.activity_procedure:
            for stage in self.workflow_procedure_stage_ids:
                ids.extend(stage.workflow_procedure_execution_ids.ids)
        else:
            for sub in self.workflow_procedure_ids:
                ids.extend(sub.get_descendant_procedure_execution_ids())
        return list(set(ids))

    def get_execution_durations_for_time_unit(self, time_unit):
        self.ensure_one()
        return self.env['workflow.procedure.execution.duration'].search([
            '&', ('time_unit', '=', time_unit),
            ('workflow_procedure_execution_id', 'in', self.get_descendant_procedure_execution_ids())
        ])

    def get_min_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        duration_list = [0]
        if self.activity_procedure:
            duration_list.extend(
                [stage.get_min_duration_for_time_unit(time_unit) for stage in self.workflow_procedure_stage_ids]
            )
        else:
            duration_list.extend(
                [sub.get_min_duration_for_time_unit(time_unit) for sub in self.workflow_procedure_ids]
            )
        return sum(duration_list)

    def get_max_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        duration_list = [0]
        if self.activity_procedure:
            duration_list.extend(
                [stage.get_max_duration_for_time_unit(time_unit) for stage in self.workflow_procedure_stage_ids]
            )
        else:
            duration_list.extend(
                [sub.get_max_duration_for_time_unit(time_unit) for sub in self.workflow_procedure_ids]
            )
        return sum(duration_list)

    def get_min_execution_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        return sum([0] + self.get_execution_durations_for_time_unit(time_unit).mapped('min_duration'))

    def get_max_execution_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        return sum([0] + self.get_execution_durations_for_time_unit(time_unit).mapped('max_duration'))

    def register_workflowable(self, record_id):
        self.ensure_one()
        workflowable = self.env['workflowable'].search([
            '&', ('workflowable_type_id', '=', self.workflowable_type_id.id),
            ('object_id', '=', record_id)
        ])
        if not workflowable.exists():
            workflowable_data = {
                'workflowable_type_id': self.workflowable_type_id.id,
                'object_id': record_id
            }
            workflowable = self.env['workflowable'].create(workflowable_data)
        return workflowable

    def register_procedure_listener(self):
        self.ensure_one()
        action_data = {
            'model_id': self.workflowable_type_id.model_id.id,
            'name': _('%s Trigger') % self.name.replace('Procedure', 'Process'),
            'state': 'code',
            'type': 'ir.actions.server',
            'usage': 'base_automation',
            'code': "env['workflow.procedure'].register_processes(record._name, record.id)"
        }
        action_server = self.env['ir.actions.server'].create(action_data)
        if action_server.exists():
            automation_data = {
                'action_server_id': action_server.id,
                'trigger': 'on_create'
            }
            listener = self.env['base.automation'].create(automation_data)
            if listener.exists():
                self.write({'action_server_id': action_server.id, 'automation_id': listener.id})

    def get_corresponding_process_data(self, record_id, with_starter=True):
        self.ensure_one()
        workflowable = self.env['workflowable'].search([
            '&', ('workflowable_type_id', '=', self.workflowable_type_id.id),
            ('object_id', '=', record_id)
        ])
        if workflowable:
            process_codename = workflowable.name + "[%s]" % self.codename.replace('procedure', 'process')
            process_name = workflowable.name + "[%s]" % self.name.replace('Procedure', 'Process')
            data = {
                'codename': process_codename,
                'name': process_name,
                'base_process': self.base_procedure,
                'activity_process': self.activity_procedure,
                'workflow_procedure_id': self.id,
                'start_datetime': fields.Datetime.now(),
                'workflowable_id': workflowable.id
            }
            if with_starter and self.starter_workflow_procedure_id:
                init_data = {
                    'start_datetime': data['start_datetime'],
                    'workflowable_record': workflowable
                }
                starter_process_data = self.starter_workflow_procedure_id.get_corresponding_process_starter_descendants_data(
                    init_data
                )
                if starter_process_data and not data.get('workflow_process_ids', False):
                    data['workflow_process_ids'] = [Command.create(starter_process_data)]
                else:
                    data['workflow_process_ids'].append(Command.create(starter_process_data))
            elif with_starter and self.workflow_procedure_stage_id:
                starter_stage = self.workflow_procedure_stage_id
                starter_stage_data = starter_stage.get_corresponding_process_stage_data(workflowable)
                starter_stage_data['start_datetime'] = data['start_datetime']
                if starter_stage_data and not data.get('workflow_process_stage_ids', False):
                    data['workflow_process_stage_ids'] = [Command.create(starter_stage_data)]
                else:
                    data['workflow_process_stage_ids'].append(Command.create(starter_stage_data))
            return data
        return {}

    def get_corresponding_process_starter_descendants_data(self, init_data):
        self.ensure_one()
        workflowable = init_data.get('workflowable_record')
        start_datetime = init_data.get('start_datetime')
        data = {
            'codename': self.codename + '_%d_process' % workflowable.object_id,
            'name': self.name + ' %d Process' % workflowable.object_id,
            'base_process': self.base_procedure,
            'activity_process': self.activity_procedure,
            'workflow_procedure_id': self.id,
            'workflowable_id': workflowable.id
        }
        if start_datetime:
            data['start_datetime'] = start_datetime
        if not self.activity_procedure and self.starter_workflow_procedure_id:
            starter_process_data = self.starter_workflow_procedure_id.get_corresponding_process_starter_descendants_data(
                init_data
            )
            if not data.get('workflow_process_ids'):
                data['workflow_process_ids'] = [Command.create(starter_process_data)]
            else:
                data['workflow_process_ids'].append(Command.create(starter_process_data))
        elif self.activity_procedure and self.workflow_procedure_stage_id.exists():
            starter_stage = self.workflow_procedure_stage_id
            starter_process_stage_data = {
                'codename': starter_stage.codename + '_%d_process_stage' % workflowable.object_id,
                'name': starter_stage.name + ' %d Process Stage' % workflowable.object_id,
                'workflow_procedure_stage_id': starter_stage.id,
                'workflow_state_id': starter_stage.workflow_state_id.id
            }
            if start_datetime:
                starter_process_stage_data['start_datetime'] = start_datetime
            if not data.get('workflow_process_stage_ids'):
                data['workflow_process_stage_ids'] = [Command.create(starter_process_stage_data)]
            else:
                data['workflow_process_stage_ids'].append(Command.create(starter_process_stage_data))
        return data

    def get_root_workflow_procedure_id(self):
        self.ensure_one()
        if self.base_procedure or not self.parent_id:
            return self.id
        else:
            return self.parent_id.get_root_workflow_procedure_id()

    def get_workflow_process_by_id(self, root_process_id):
        self.ensure_one()
        return self.env['workflow.process'].search([
            '&', ('workflow_procedure_id', '=', self.id),
            ('root_workflow_process_id', '=', root_process_id.id)
        ], limit=1)

    def get_corresponding_process_starter_stage_by_id(self, root_process_id):
        self.ensure_one()
        if self.activity_procedure:
            return self.workflow_procedure_stage_id.get_workflow_process_stage_by_id(
                root_process_id
            )
        return self.starter_workflow_procedure_id.get_corresponding_process_starter_stage_by_id(
            root_process_id
        )

    def get_corresponding_process_starter_by_id(self, root_process_id):
        self.ensure_one()
        if self.activity_procedure:
            return self.workflow_procedure_stage_id.get_workflow_process_stage_by_id(root_process_id)
        return self.starter_workflow_procedure_id.get_workflow_process_by_id(root_process_id)

    def expand_starters(self):
        self.ensure_one()
        if self.parent_id:
            parent = self.parent_id
            parent.workflow_procedure_stage_id = self.workflow_procedure_stage_id.id
            parent.starter_workflow_procedure_id = self.id
            if not parent.base_procedure:
                parent.expand_starters()
        elif self.base_procedure:
            self.starter_workflow_procedure_id = self.id

    def unexpand_starters(self):
        self.ensure_one()
        if self.parent_id:
            parent = self.parent_id
            parent.workflow_procedure_stage_id = None
            parent.starter_workflow_procedure_id = None
            if not parent.base_procedure:
                parent.unexpand_starters()
        elif self.base_procedure:
            self.starter_workflow_procedure_id = None

    def get_workflow_starter_branch(self, collector=False):
        self.ensure_one()
        if not collector:
            collector = []
        if self.activity_procedure:
            collector.append(self)
            if self.workflow_procedure_stage_id:
                collector.append(self.workflow_procedure_stage_id)
        else:
            collector.append(self)
            if self.starter_workflow_procedure_id:
                collector = self.starter_workflow_procedure_id.get_workflow_starter_branch(collector)
        return collector

    def find_starter_workflow_procedure_stage(self):
        self.ensure_one()
        if self.activity_procedure:
            return self.workflow_procedure_stage_id
        else:
            return self.starter_workflow_procedure_id.find_starter_workflow_procedure_stage()

    def trigger_process(self, record_id):
        self.ensure_one()
        workflow_process = self.env['workflow.process'].create(
            self.get_corresponding_process_data(record_id)
        )
        starter_process_stage = workflow_process.get_workflow_process_starter_stage()
        if starter_process_stage.exists():
            starter_procedure_stage = starter_process_stage.workflow_procedure_stage_id
            execution_data = {}
            for procedure_execution in starter_procedure_stage.workflow_procedure_execution_ids.filtered(
                lambda pe: not pe.parent_id
            ):
                process_execution_data = procedure_execution.get_corresponding_process_execution_data(
                    starter_process_stage.id
                )
                process_execution_data['workflow_process_stage_id'] = starter_process_stage.id
                if not execution_data.get('workflow_process_execution_ids', False):
                    execution_data['workflow_process_execution_ids'] = [Command.create(process_execution_data)]
                else:
                    execution_data['workflow_process_execution_ids'].append(Command.create(process_execution_data))
            starter_process_stage.write(execution_data)
            acl_data = {}
            for stage_acl in starter_procedure_stage.workflow_procedure_stage_acl_ids:
                process_stage_acl_data = stage_acl.get_corresponding_process_stage_acl_data()
                if not acl_data.get('workflow_process_stage_acl_ids', False):
                    acl_data['workflow_process_stage_acl_ids'] = [Command.create(process_stage_acl_data)]
                else:
                    acl_data['workflow_process_stage_acl_ids'].append(Command.create(process_stage_acl_data))
            starter_process_stage.write(acl_data)
        if starter_process_stage.exists() and starter_process_stage.workflow_process_id:
            starter_process_stage.workflow_process_id.write({
                'workflow_process_stage_id': starter_process_stage.id
            })
            starter_process_stage.workflow_process_id.expend_starter_descendants()
        return workflow_process

    def trigger_base_process(self, record_id):
        self.ensure_one()
        base_workflow_process = self.trigger_process(record_id)
        if base_workflow_process.exists():
            starter_position_data = base_workflow_process.get_starter_position_data()
            if starter_position_data:
                self.env['workflowable.position'].create(starter_position_data)

    def trigger_manual_process(self, record_id):
        self.ensure_one()
        workflow_process = self.env['workflow.process'].create(
            self.get_corresponding_process_data(record_id)
        )
        if workflow_process.exists() and workflow_process.base_process:
            starter_position_data = workflow_process.get_starter_position_data()
            if starter_position_data:
                self.env['workflowable.position'].create(starter_position_data)

    @api.model
    def register_processes(self, model_name, record_id):
        released_procedures = get_model_base_procedures(self.env, model_name)
        workflowable_instance = False
        procedure_ids = []
        automatic_procedure_ids = []
        manual_procedure_ids = []
        awaiting_manual_procedure_ids = []
        for released_procedure in released_procedures:
            if not workflowable_instance or not workflowable_instance.exists():
                workflowable_instance = released_procedure.register_workflowable(record_id)
            if released_procedure.trigger_type == 'automatic':
                procedure_ids.append(released_procedure.id)
                automatic_procedure_ids.append(released_procedure.id)
                released_procedure.trigger_base_process(record_id)
            elif released_procedure.trigger_type == 'manual':
                procedure_domain_ids = released_procedure.eval_filter_domain().ids
                if record_id in procedure_domain_ids:
                    procedure_ids.append(released_procedure.id)
                    manual_procedure_ids.append(released_procedure.id)
                    awaiting_manual_procedure_ids.append(released_procedure.id)
        if workflowable_instance and workflowable_instance.exists():
            new_data = False
            procedures_data = {}
            if len(procedure_ids) > 0:
                procedures_data['workflow_procedure_ids'] = procedure_ids
                new_data = True
            if len(automatic_procedure_ids) > 0:
                procedures_data['automatic_workflow_procedure_ids'] = automatic_procedure_ids
                new_data = True
            if len(manual_procedure_ids) > 0:
                procedures_data['manual_workflow_procedure_ids'] = manual_procedure_ids
                new_data = True
            if len(awaiting_manual_procedure_ids) > 0:
                procedures_data['awaiting_manual_workflow_procedure_ids'] = awaiting_manual_procedure_ids
                new_data = True
            if new_data:
                workflowable_instance.write(procedures_data)
            if not workflowable_instance.displayed_workflow_process_id and len(workflowable_instance.workflow_process_ids) > 0:
                workflowable_instance.write({
                    'displayed_workflow_process_id': workflowable_instance.workflow_process_ids.ids[0]
                })

    def action_configure_duration(self):
        wizard = self.env['workflow.procedure.duration.wizard'].create({
            'workflow_procedure_id': self.id
        })
        return {
            'name': _('Configure Procedure Duration'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.procedure.duration.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new'
        }

    def action_release_workflow_procedure(self):
        if self.base_procedure and not self.released:
            self.register_procedure_listener()
            self.write({'released': True, 'state': 'released'})
            for descendant in self.get_descendant_procedures():
                descendant.write({'released': True, 'state': 'released'})

    def action_unrelease_workflow_procedure(self):
        if self.base_procedure and self.released:
            self.write({'released': False, 'state': 'unreleased'})
            for descendant in self.get_descendant_procedures():
                descendant.write({'released': False, 'state': 'unreleased'})

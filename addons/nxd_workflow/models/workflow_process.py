# -*- coding: utf-8 -*-

from odoo import api, fields, models


def expand_starters(workflow_process_record):
    if workflow_process_record.parent_id:
        parent = workflow_process_record.parent_id
        parent.workflow_process_stage_id = workflow_process_record.workflow_process_stage_id.id
        parent.starter_workflow_process_id = workflow_process_record.id
        if not parent.base_process:
            expand_starters(parent)
    elif workflow_process_record.base_process:
        workflow_process_record.starter_workflow_process_id = workflow_process_record.id


def unexpand_starters(workflow_process_record):
    if workflow_process_record.parent_id:
        parent = workflow_process_record.parent_id
        parent.workflow_process_stage_id = None
        parent.starter_workflow_process_id = None
        if not parent.base_process:
            unexpand_starters(parent)
    elif workflow_process_record.base_process:
        workflow_process_record.starter_workflow_process_id = None


def get_root_workflow_process_id(workflow_process_record):
    if not workflow_process_record.parent_id:
        return workflow_process_record.id
    else:
        return get_root_workflow_process_id(workflow_process_record.parent_id.id)


def set_starter_workflow_process(workflow_process_record):
    if workflow_process_record.activity_process:
        workflow_process_record.parent_id.starter_workflow_process_id = workflow_process_record.id
        set_starter_workflow_process(workflow_process_record.parent_id)
    elif workflow_process_record.base_process:
        return
    else:
        set_starter_workflow_process(workflow_process_record.parent_id)


def find_starter_workflow_process_stage(workflow_process_record):
    if workflow_process_record.activity_process:
        return workflow_process_record.workflow_process_stage_id
    else:
        return find_starter_workflow_process_stage(
            workflow_process_record.starter_workflow_process_id
        )


def get_base_workflow_process_starter_position_data(base_process_record):
    if base_process_record.workflow_process_stage_id:
        return {
            'workflowable_id': base_process_record.workflowable_id.id,
            'workflow_process_id': base_process_record.id,
            'workflow_process_stage_id': base_process_record.workflow_process_stage_id.id
        }
    return {}


class WorkflowProcess(models.Model):
    _name = "workflow.process"
    _description = "Workflow Process"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow process must be '
                                                                  'unique per company !')
    ]

    @api.depends("base_process", "parent_allowed")
    def _compute_parent_allowed(self):
        for process in self:
            if process.base_process:
                process.parent_allowed = False
            else:
                process.parent_allowed = True

    @api.depends("workflow_process_ids", "has_sub_processes")
    def _compute_has_sub_processes(self):
        for process in self:
            if len(process.workflow_process_ids) > 0:
                process.has_sub_processes = True
            else:
                process.has_sub_processes = False

    @api.depends("workflow_process_duration_ids", "has_durations")
    def _compute_has_durations(self):
        for process in self:
            if len(process.workflow_process_duration_ids) > 0:
                process.has_durations = True
            else:
                process.has_durations = False

    @api.depends("workflow_process_transition_ids", "has_sub_process_transitions")
    def _compute_has_sub_process_transitions(self):
        for process in self:
            if len(process.workflow_process_transition_ids) > 0:
                process.has_sub_process_transitions = True
            else:
                process.has_sub_process_transitions = False

    @api.depends("workflow_process_stage_ids", "has_process_stages")
    def _compute_has_process_stages(self):
        for process in self:
            if len(process.workflow_process_stage_ids) > 0:
                process.has_process_stages = True
            else:
                process.has_process_stages = False

    @api.depends("workflow_process_stage_transition_ids", "has_process_stage_transitions")
    def _compute_has_process_stage_transitions(self):
        for process in self:
            if len(process.workflow_process_stage_transition_ids) > 0:
                process.has_process_stage_transitions = True
            else:
                process.has_process_stage_transitions = False

    @api.depends("inbound_workflow_process_transition_ids", "has_inbound_transitions")
    def _compute_has_inbound_transitions(self):
        for process in self:
            if len(process.inbound_workflow_process_transition_ids) > 0:
                process.has_inbound_transitions = True
            else:
                process.has_inbound_transitions = False

    @api.depends("outbound_workflow_process_transition_ids", "has_outbound_transitions")
    def _compute_has_outbound_transitions(self):
        for process in self:
            if len(process.outbound_workflow_process_transition_ids) > 0:
                process.has_outbound_transitions = True
            else:
                process.has_outbound_transitions = False

    @api.depends('workflow_process_stage_id')
    def _onchange_starter_workflow_process_stage(self):
        set_starter_workflow_process(self)

    @api.depends('parent_id')
    def _compute_root_workflow_process(self):
        for process in self:
            process.root_workflow_process_id = get_root_workflow_process_id(process)

    @api.depends('workflowable_id', 'workflow_procedure_id')
    def _compute_name(self):
        for process in self:
            process.name = process.workflowable_id.name + ' Process[%s]' % process.workflow_procedure_id.name

    codename = fields.Char(string='Codename', required=True, size=154)
    name = fields.Char(string='Name', required=True, translate=True, store=True,
                       compute="_compute_name")
    base_process = fields.Boolean(string="Base Process", default=False)
    activity_process = fields.Boolean(string="Activity Process", default=False)
    start_datetime = fields.Datetime(string="Start Datetime", copy=False,
                                     required=True)
    end_datetime = fields.Datetime(string="End Datetime", copy=False,
                                   required=False)
    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               compute="_compute_root_workflow_process")
    workflow_procedure_id = fields.Many2one('workflow.procedure', required=True,
                                            string="Procedure")
    workflowable_id = fields.Many2one('workflowable', required=True,
                                      string="Workflowable")
    parent_id = fields.Many2one('workflow.process', required=False, string="Parent")
    starter_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                                  readonly=True, invisible=True,
                                                  string="Starter Process")
    workflow_process_stage_id = fields.Many2one('workflow.process.stage',
                                                string="Starter Stage", required=False)
    workflow_process_ids = fields.One2many('workflow.process',
                                           'parent_id', string="Sub processes")
    workflow_process_duration_ids = fields.One2many('workflow.process.duration',
                                                    'workflow_process_id',
                                                    string="Process durations")
    workflow_process_transition_ids = fields.One2many('workflow.process.transition',
                                                      'workflow_process_id',
                                                      string="Process Transitions")
    workflow_process_stage_transition_ids = fields.One2many('workflow.process.stage.transition',
                                                            'workflow_process_id',
                                                            string="Process Stage Transitions")
    workflow_process_stage_ids = fields.One2many('workflow.process.stage',
                                                 'workflow_process_id',
                                                 string="Process Stages")
    inbound_workflow_process_transition_ids = fields.One2many('workflow.process.transition',
                                                              'to_workflow_process_id',
                                                              string="Inbound Process Transitions")
    outbound_workflow_process_transition_ids = fields.One2many('workflow.process.transition',
                                                               'from_workflow_process_id',
                                                               string="Outbound Process Transitions")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    parent_allowed = fields.Boolean(readonly=True, compute="_compute_parent_allowed")
    has_sub_processes = fields.Boolean(readonly=True, compute="_compute_has_sub_processes")
    has_durations = fields.Boolean(readonly=True, compute="_compute_has_durations")
    has_sub_process_transitions = fields.Boolean(readonly=True,
                                                 compute="_compute_has_sub_process_transitions")
    has_process_stages = fields.Boolean(readonly=True, compute="_compute_has_process_stages")
    has_process_stage_transitions = fields.Boolean(readonly=True,
                                                   compute="_compute_has_process_stage_transitions")
    has_inbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_inbound_transitions")
    has_outbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_outbound_transitions")

    def get_child_workflow_processes_by_id(self, process_id):
        return self.workflow_process_ids.filtered(lambda p: p.id == process_id)

    def get_child_workflow_process_by_id(self, process_id):
        records = self.get_child_workflow_processes_by_id(process_id)
        if len(records) > 0:
            return records[0]
        return

    def get_child_workflow_processes_by_ids(self, process_ids):
        return self.workflow_process_ids.filtered(lambda p: p.id in process_ids)

    def get_workflow_process_transitions_by_id(self, transition_id):
        return self.workflow_process_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_workflow_process_transition_by_id(self, transition_id):
        records = self.get_workflow_process_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_transitions_by_ids(self, transition_ids):
        return self.workflow_process_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_workflow_process_stages_by_id(self, stage_id):
        return self.workflow_process_stage_ids.filtered(lambda s: s.id == stage_id)

    def get_workflow_process_stage_by_id(self, stage_id):
        records = self.get_workflow_process_stages_by_id(stage_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_stages_by_ids(self, stage_ids):
        return self.workflow_process_stage_ids.filtered(lambda s: s.id in stage_ids)

    def get_workflow_process_stage_transitions_by_id(self, transition_id):
        return self.workflow_process_stage_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_workflow_process_stage_transition_by_id(self, transition_id):
        records = self.get_workflow_process_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_stage_transitions_by_ids(self, transition_ids):
        return self.workflow_process_stage_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_inbound_workflow_process_transitions_by_id(self, transition_id):
        return self.inbound_workflow_process_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_inbound_workflow_process_transition_by_id(self, transition_id):
        records = self.get_inbound_workflow_process_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_inbound_workflow_process_transitions_by_ids(self, transition_ids):
        return self.inbound_workflow_process_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_outbound_workflow_process_transitions_by_id(self, transition_id):
        return self.outbound_workflow_process_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_outbound_workflow_process_transition_by_id(self, transition_id):
        records = self.get_outbound_workflow_process_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_outbound_workflow_process_transitions_by_ids(self, transition_ids):
        return self.outbound_workflow_process_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_starter_workflow_process_stage(self):
        find_starter_workflow_process_stage(self)

    def get_starter_position_data(self):
        return get_base_workflow_process_starter_position_data(self)

    def expend_starter_descendants(self):
        expand_starters(self)

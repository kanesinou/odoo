# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcessStage(models.Model):
    _name = "workflow.process.stage"
    _description = "Workflow Process Stage"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,workflow_process_id,company_id)', 'The codename must be unique '
                                                                                      'per workflow process and per '
                                                                                      'company !')
    ]

    @api.depends("workflow_process_stage_duration_ids", "has_durations")
    def _compute_has_durations(self):
        for stage in self:
            if len(stage.workflow_process_stage_duration_ids) > 0:
                stage.has_durations = True
            else:
                stage.has_durations = False

    @api.depends("workflow_process_ids", "has_started_processes")
    def _compute_has_started_processes(self):
        for stage in self:
            if len(stage.workflow_process_ids) > 0:
                stage.has_started_processes = True
            else:
                stage.has_started_processes = False

    @api.depends("workflow_process_execution_ids", "has_executions")
    def _compute_has_executions(self):
        for stage in self:
            if len(stage.workflow_process_execution_ids) > 0:
                stage.has_executions = True
            else:
                stage.has_executions = False

    @api.depends("inbound_workflow_process_stage_transition_ids", "has_inbound_transitions")
    def _compute_has_inbound_transitions(self):
        for stage in self:
            if len(stage.inbound_workflow_process_stage_transition_ids) > 0:
                stage.has_inbound_transitions = True
            else:
                stage.has_inbound_transitions = False

    @api.depends("outbound_workflow_process_stage_transition_ids", "has_outbound_transitions")
    def _compute_has_outbound_transitions(self):
        for stage in self:
            if len(stage.outbound_workflow_process_stage_transition_ids) > 0:
                stage.has_outbound_transitions = True
            else:
                stage.has_outbound_transitions = False

    @api.depends('workflow_process_id')
    def _compute_root_workflow_process(self):
        for stage in self:
            stage.root_workflow_process_id = stage.workflow_process_id.root_workflow_process_id.id

    @api.depends('workflow_process_id', 'workflow_procedure_stage_id')
    def _compute_name(self):
        for stage in self:
            stage.name = stage.workflow_process_id.workflowable_id.name + ' Process Stage[%s]' % stage.workflow_procedure_stage_id.name

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True, store=True,
                       compute="_compute_name")
    aborted = fields.Boolean(string='Aborted', default=False)
    start_datetime = fields.Datetime(string="Start Datetime", copy=False,
                                     required=True)
    end_datetime = fields.Datetime(string="End Datetime", copy=False, required=False)
    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               compute="_compute_root_workflow_process")
    workflow_process_execution_id = fields.Many2one('workflow.process.execution',
                                                    required=False,
                                                    string="Aborter Process Execution")
    workflow_process_id = fields.Many2one('workflow.process', string="Process",
                                          required=True)
    workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage',
                                                  string="Procedure Stage", required=True)
    workflow_state_id = fields.Many2one('workflow.state', string='State', required=False,
                                        store=True,
                                        related="workflow_procedure_stage_id.workflow_state_id")
    workflow_process_stage_duration_ids = fields.One2many('workflow.process.stage.duration',
                                                          'workflow_process_stage_id',
                                                          string="Process Stage Durations")
    workflow_process_ids = fields.One2many('workflow.process',
                                           'workflow_process_stage_id',
                                           string="Started Processes")
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_process_stage_id',
                                                     string="Process Executions")
    inbound_workflow_process_stage_transition_ids = fields.One2many('workflow.process.stage.transition',
                                                                    'to_workflow_process_stage_id',
                                                                    string="Inbound Process Stage Transitions")
    outbound_workflow_process_stage_transition_ids = fields.One2many('workflow.process.stage.transition',
                                                                     'from_workflow_process_stage_id',
                                                                     string="Outbound Process Stage Transitions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    has_durations = fields.Boolean(readonly=True, compute="_compute_has_durations")
    has_started_processes = fields.Boolean(readonly=True, compute="_compute_has_started_processes")
    has_executions = fields.Boolean(readonly=True, compute="_compute_has_executions")
    has_inbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_inbound_transitions")
    has_outbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_outbound_transitions")

    def get_workflow_process_stage_durations_by_id(self, duration_id):
        return self.workflow_process_stage_duration_ids.filtered(lambda d: d.id == duration_id)

    def get_workflow_process_stage_duration_by_id(self, duration_id):
        records = self.get_workflow_process_stage_durations_by_id(duration_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_stage_durations_by_ids(self, duration_ids):
        return self.workflow_process_stage_duration_ids.filtered(lambda d: d.id in duration_ids)

    def get_workflow_process_executions_by_id(self, execution_id):
        return self.workflow_process_execution_ids.filtered(lambda e: e.id == execution_id)

    def get_workflow_process_execution_by_id(self, execution_id):
        records = self.get_workflow_process_executions_by_id(execution_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_executions_by_ids(self, execution_ids):
        return self.workflow_process_execution_ids.filtered(lambda e: e.id in execution_ids)

    def get_inbound_workflow_process_stage_transitions_by_id(self, transition_id):
        return self.inbound_workflow_process_stage_transition_ids.filtered(
            lambda t: t.id == transition_id
        )

    def get_inbound_workflow_process_stage_transition_by_id(self, transition_id):
        records = self.get_inbound_workflow_process_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_inbound_workflow_process_stage_transitions_by_ids(self, transition_ids):
        return self.inbound_workflow_process_stage_transition_ids.filtered(
            lambda t: t.id in transition_ids
        )

    def get_outbound_workflow_process_stage_transitions_by_id(self, transition_id):
        return self.outbound_workflow_process_stage_transition_ids.filtered(
            lambda t: t.id == transition_id
        )

    def get_outbound_workflow_process_stage_transition_by_id(self, transition_id):
        records = self.get_outbound_workflow_process_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_outbound_workflow_process_stage_transitions_by_ids(self, transition_ids):
        return self.outbound_workflow_process_stage_transition_ids.filtered(
            lambda t: t.id in transition_ids
        )

    def get_started_workflow_processes_by_id(self, process_id):
        return self.workflow_process_ids.filtered(lambda p: p.id == process_id)

    def get_started_workflow_process_by_id(self, process_id):
        records = self.get_started_workflow_processes_by_id(process_id)
        if len(records) > 0:
            return records[0]
        return

    def get_started_workflow_processes_by_ids(self, process_ids):
        return self.workflow_process_ids.filtered(lambda p: p.id in process_ids)

# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcessCycle(models.Model):
    _name = "workflow.process.cycle"
    _description = "Workflow Process Cycle"

    @api.depends("workflow_process_cycle_duration_ids", "has_durations")
    def _compute_has_durations(self):
        for cycle in self:
            if len(cycle.workflow_process_cycle_duration_ids) > 0:
                cycle.has_durations = True
            else:
                cycle.has_durations = False

    @api.depends("workflow_process_ids", "has_processes")
    def _compute_has_processes(self):
        for cycle in self:
            if len(cycle.workflow_process_ids) > 0:
                cycle.has_processes = True
            else:
                cycle.has_processes = False

    @api.depends("workflow_process_transition_ids", "has_process_transitions")
    def _compute_has_process_transitions(self):
        for cycle in self:
            if len(cycle.workflow_process_transition_ids) > 0:
                cycle.has_process_transitions = True
            else:
                cycle.has_process_transitions = False

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    start_datetime = fields.Datetime(string="Start Datetime", copy=False,
                                     required=True)
    end_datetime = fields.Datetime(string="End Datetime", copy=False,
                                   required=False)
    workflow_procedure_cycle_id = fields.Many2one('workflow.procedure.cycle',
                                                  string="Procedure Cycle", required=True)
    workflow_process_cycle_duration_ids = fields.One2many('workflow.process.cycle.duration',
                                                          'workflow_process_cycle_id',
                                                          string="Process Cycle Durations")
    workflow_process_ids = fields.Many2many('workflow.process',
                                            'workflow_process_cycle_process',
                                            string="Processes")
    workflow_process_transition_ids = fields.Many2many('workflow.process.transition',
                                                       'workflow_process_cycle_process_transition',
                                                       string="Process Transitions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    has_processes = fields.Boolean(readonly=True, compute="_compute_has_processes")
    has_process_transitions = fields.Boolean(readonly=True, compute="_compute_has_processes")
    has_durations = fields.Boolean(readonly=True, compute="_compute_has_durations")

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from ..utils import date_utils


class WorkflowProcessCycleStage(models.Model):
    _name = "workflow.process.cycle.stage"
    _description = "Workflow Process Cycle Stage"
    _sql_constraints = [
        ('codename_cycle_company_uniq', 'unique (codename,workflow_process_cycle_id, company_id)', 'The codename of '
                                                                                                   'the workflow '
                                                                                                   'process cycle '
                                                                                                   'stage must be '
                                                                                                   'unique per cycle '
                                                                                                   'and per company !')
    ]

    @api.depends('time_unit')
    def _compute_time_label(self):
        for stage in self:
            if stage.time_unit:
                stage.time_label = date_utils.TIME_LABELS.get(stage.time_unit)

    @api.depends('time_unit')
    def _compute_time_label_plural(self):
        for stage in self:
            if stage.time_unit:
                stage.time_label_plural = date_utils.TIME_LABEL_PLURALS.get(stage.time_unit)

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    workflow_process_cycle_id = fields.Many2one('workflow.process.cycle', required=True,
                                                string="Workflow Process Cycle")
    workflow_procedure_cycle_stage_id = fields.Many2one('workflow.procedure.cycle.stage', required=True,
                                                        string="Workflow Procedure Cycle Stage")
    workflow_process_ids = fields.Many2many('workflow.process',
                                            'workflow_process_cycle_stage_process',
                                            domain=['&', ('base_process', '=', True)])
    inbound_workflow_process_cycle_stage_transition_ids = fields.One2many('workflow.process.cycle.stage.transition',
                                                                          'to_workflow_process_cycle_stage_id')
    outbound_workflow_process_cycle_stage_transition_ids = fields.One2many('workflow.process.cycle.stage.transition',
                                                                           'from_workflow_process_cycle_stage_id')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    # TEMPORAL FIELDS
    start_datetime = fields.Datetime(string="Start Datetime", copy=False, required=True)
    end_datetime = fields.Datetime(string="End Datetime", copy=False, required=False)
    execution_start_datetime = fields.Datetime(string="Execution Start Datetime", copy=False, required=False)
    execution_end_datetime = fields.Datetime(string="Execution End Datetime", copy=False, required=False)
    expected_min_start_datetime = fields.Datetime(string="Expected Minimum Start Datetime", copy=False, required=False)
    expected_max_start_datetime = fields.Datetime(string="Expected Maximum Start Datetime", copy=False, required=False)
    expected_min_end_datetime = fields.Datetime(string="Expected Minimum End Datetime", copy=False, required=False)
    expected_max_end_datetime = fields.Datetime(string="Expected Maximum End Datetime", copy=False, required=False)
    expected_min_execution_start_datetime = fields.Datetime(string="Expected Minimum Execution Start Datetime",
                                                            copy=False, required=False)
    expected_max_execution_start_datetime = fields.Datetime(string="Expected Maximum Execution Start Datetime",
                                                            copy=False, required=False)
    expected_min_execution_end_datetime = fields.Datetime(string="Expected Minimum Execution End Datetime", copy=False,
                                                          required=False)
    expected_max_execution_end_datetime = fields.Datetime(string="Expected Maximum Execution End Datetime", copy=False,
                                                          required=False)
    time_label = fields.Char(string="Time Label", required=False, translate=True,
                             compute="_compute_time_label")
    time_label_plural = fields.Char(string="Time Label Plural", required=False, translate=True,
                                    compute="_compute_time_label_plural")
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
    elapsed_time = fields.Float("Elapsed Time", compute="_compute_elapsed_time", digits=(11, 5))
    duration_time = fields.Float("Duration", compute="_compute_duration_time", digits=(11, 5))
    remaining_min_duration = fields.Float("Remaining Minimum Duration", digits=(11, 5))
    remaining_max_duration = fields.Float("Remaining Maximum Duration", digits=(11, 5))
    exceeding_min_duration = fields.Float("Exceeding Minimum Duration", digits=(11, 5))
    exceeding_max_duration = fields.Float("Exceeding Maximum Duration", digits=(11, 5))
    exceeded_min_duration = fields.Float("Exceeded Minimum Duration", digits=(11, 5))
    exceeded_max_duration = fields.Float("Exceeded Maximum Duration", digits=(11, 5))
    execution_elapsed_time = fields.Float("Elapsed Execution Duration", digits=(11, 5))
    execution_duration_time = fields.Float("Execution Duration", digits=(11, 5))
    remaining_min_execution_duration = fields.Float("Remaining Minimum Execution Duration", digits=(11, 5))
    remaining_max_execution_duration = fields.Float("Remaining Maximum Execution Duration", digits=(11, 5))
    exceeding_min_execution_duration = fields.Float("Exceeding Minimum Execution Duration", digits=(11, 5))
    exceeding_max_execution_duration = fields.Float("Exceeding Maximum Execution Duration", digits=(11, 5))
    exceeded_min_execution_duration = fields.Float("Exceeded Minimum Execution Duration", digits=(11, 5))
    exceeded_max_execution_duration = fields.Float("Exceeded Maximum Execution Duration", digits=(11, 5))
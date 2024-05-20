# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models
from ..utils import date_utils


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

    @api.depends('workflow_process_ids')
    def _compute_end_datetime(self):
        for cycle in self:
            cycle.end_datetime = None
            datetimes_list = cycle.workflow_process_ids.mapped('end_datetime')
            valid_datetimes_list = [d for d in datetimes_list if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                cycle.end_datetime = max(valid_datetimes_list)

    @api.depends('workflow_process_ids')
    def _compute_execution_start_datetime(self):
        for cycle in self:
            cycle.execution_start_datetime = None
            start_datetime_list = cycle.workflow_process_ids.mapped('execution_start_datetime')
            valid_datetimes_list = [d for d in start_datetime_list if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                cycle.execution_start_datetime = min(valid_datetimes_list)

    @api.depends('workflow_process_ids')
    def _compute_execution_end_datetime(self):
        for cycle in self:
            cycle.execution_end_datetime = None
            end_datetime_list = cycle.workflow_process_ids.mapped('execution_end_datetime')
            valid_datetimes_list = [d for d in end_datetime_list if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                cycle.execution_end_datetime = min(valid_datetimes_list)

    @api.depends('workflow_process_transition_ids', 'start_datetime')
    def _compute_expected_min_start_datetime(self):
        for cycle in self:
            transition = cycle.find_latest_transition()
            if transition.exists():
                cycle.expected_min_start_datetime = transition.from_workflow_process_id.expected_min_end_datetime
            else:
                cycle.expected_min_start_datetime = cycle.start_datetime

    @api.depends('workflow_process_transition_ids', 'start_datetime')
    def _compute_expected_max_start_datetime(self):
        for cycle in self:
            transition = cycle.find_latest_transition()
            if transition.exists():
                cycle.expected_max_start_datetime = transition.from_workflow_process_id.expected_max_end_datetime
            else:
                cycle.expected_max_start_datetime = cycle.start_datetime

    @api.depends('workflow_procedure_cycle_id', 'start_datetime')
    def _compute_expected_min_end_datetime(self):
        for cycle in self:
            cycle.expected_min_end_datetime = None
            if cycle.workflow_procedure_cycle_id and cycle.start_datetime:
                min_duration = cycle.workflow_procedure_cycle_id.get_min_duration_for_time_unit(cycle.time_unit)
                delta = date_utils.get_timedelta_from_duration(min_duration, cycle.time_unit)
                cycle.expected_min_end_datetime = cycle.start_datetime + delta

    @api.depends('workflow_procedure_cycle_id', 'start_datetime')
    def _compute_expected_max_end_datetime(self):
        for cycle in self:
            cycle.expected_max_end_datetime = None
            if cycle.workflow_procedure_cycle_id and cycle.start_datetime:
                max_duration = cycle.workflow_procedure_cycle_id.get_max_duration_for_time_unit(cycle.time_unit)
                delta = date_utils.get_timedelta_from_duration(max_duration, cycle.time_unit)
                cycle.expected_max_end_datetime = cycle.start_datetime + delta

    @api.depends('workflow_process_transition_ids', 'execution_start_datetime')
    def _compute_expected_min_execution_start_datetime(self):
        for cycle in self:
            transition = cycle.find_latest_transition()
            if transition.exists() and cycle.execution_start_datetime:
                cycle.expected_min_execution_start_datetime = transition.from_workflow_process_id.expected_min_execution_end_datetime
            else:
                cycle.expected_min_execution_start_datetime = cycle.execution_start_datetime

    @api.depends('workflow_process_transition_ids', 'execution_start_datetime')
    def _compute_expected_max_execution_start_datetime(self):
        for cycle in self:
            transition = cycle.find_latest_transition()
            if transition.exists() and cycle.execution_start_datetime:
                cycle.expected_max_execution_start_datetime = transition.from_workflow_process_id.expected_max_execution_end_datetime
            else:
                cycle.expected_max_execution_start_datetime = cycle.execution_start_datetime

    @api.depends('workflow_procedure_cycle_id', 'execution_start_datetime')
    def _compute_expected_min_execution_end_datetime(self):
        for cycle in self:
            cycle.expected_min_execution_end_datetime = None
            if cycle.workflow_procedure_cycle_id and cycle.execution_start_datetime:
                min_duration = cycle.workflow_procedure_cycle_id.get_min_execution_duration_for_time_unit(
                    cycle.time_unit
                )
                delta = date_utils.get_timedelta_from_duration(min_duration, cycle.time_unit)
                cycle.expected_min_execution_end_datetime = cycle.execution_start_datetime + delta

    @api.depends('workflow_procedure_cycle_id', 'execution_start_datetime')
    def _compute_expected_max_execution_end_datetime(self):
        for cycle in self:
            cycle.expected_max_execution_end_datetime = None
            if cycle.workflow_procedure_cycle_id and cycle.execution_start_datetime:
                max_duration = cycle.workflow_procedure_cycle_id.get_max_execution_duration_for_time_unit(
                    cycle.time_unit
                )
                delta = date_utils.get_timedelta_from_duration(max_duration, cycle.time_unit)
                cycle.expected_max_execution_end_datetime = cycle.execution_start_datetime + delta

    @api.depends('end_datetime')
    def _compute_is_ended(self):
        for cycle in self:
            cycle.is_ended = True if cycle.end_datetime else False

    @api.depends('workflow_process_ids', )
    def _compute_is_execution_started(self):
        for cycle in self:
            started_process_executions = cycle.workflow_process_ids.filtered(
                lambda p: p.is_execution_started
            )
            cycle.is_execution_started = True if started_process_executions.exists() else False

    @api.depends('workflow_process_ids', )
    def _compute_is_execution_complete(self):
        for cycle in self:
            not_complete_sub_executions = cycle.workflow_process_ids.filtered(
                lambda p: not p.is_execution_complete
            )
            cycle.is_execution_started = True if not not_complete_sub_executions.exists() else False

    @api.depends('start_datetime', 'time_unit', 'is_ended')
    def _compute_elapsed_time(self):
        for cycle in self:
            cycle.elapsed_time = 0
            if cycle.start_datetime and cycle.time_unit:
                diff = fields.Datetime.now() - cycle.start_datetime
                if cycle.is_ended:
                    diff = cycle.end_datetime - cycle.start_datetime
                cycle.elapsed_time = date_utils.get_time_total(diff, cycle.time_unit)

    @api.depends('start_datetime', 'end_datetime', 'time_unit', 'is_ended')
    def _compute_duration_time(self):
        for cycle in self:
            cycle.duration_time = 0
            if cycle.start_datetime and cycle.time_unit:
                diff = fields.Datetime.now() - cycle.start_datetime
                if cycle.is_ended:
                    diff = cycle.end_datetime - cycle.start_datetime
                cycle.duration_time = date_utils.get_time_total(diff, cycle.time_unit)

    @api.depends('elapsed_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_ended')
    def _compute_remaining_min_duration(self):
        for cycle in self:
            cycle.remaining_min_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and not cycle.is_ended:
                min_duration = cycle.workflow_procedure_cycle_id.get_min_duration_for_time_unit(
                    cycle.time_unit
                )
                if min_duration > 0:
                    diff = min_duration - cycle.elapsed_time
                    cycle.remaining_min_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('elapsed_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_ended')
    def _compute_remaining_max_duration(self):
        for cycle in self:
            cycle.remaining_max_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and not cycle.is_ended:
                max_duration = cycle.workflow_procedure_cycle_id.get_max_duration_for_time_unit(
                    cycle.time_unit
                )
                if max_duration > 0:
                    diff = max_duration - cycle.elapsed_time
                    cycle.remaining_max_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('elapsed_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_ended')
    def _compute_exceeding_min_duration(self):
        for cycle in self:
            cycle.exceeding_min_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and not cycle.is_ended:
                min_duration = cycle.workflow_procedure_cycle_id.get_min_duration_for_time_unit(
                    cycle.time_unit
                )
                if (min_duration == 0) or cycle.elapsed_time <= min_duration:
                    cycle.exceeding_min_duration = 0
                else:
                    diff = cycle.elapsed_time - min_duration
                    cycle.exceeding_min_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('duration_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_ended')
    def _compute_exceeding_max_duration(self):
        for cycle in self:
            cycle.exceeding_max_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and not cycle.is_ended:
                max_duration = cycle.workflow_procedure_cycle_id.get_max_duration_for_time_unit(
                    cycle.time_unit
                )
                if (max_duration == 0) or cycle.elapsed_time <= max_duration:
                    cycle.exceeding_max_duration = 0
                else:
                    diff = cycle.elapsed_time - max_duration
                    cycle.exceeding_max_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('duration_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_ended')
    def _compute_exceeded_min_duration(self):
        for cycle in self:
            cycle.exceeded_min_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and cycle.is_ended:
                min_duration = cycle.workflow_procedure_cycle_id.get_min_duration_for_time_unit(
                    cycle.time_unit
                )
                if (min_duration == 0) or cycle.duration_time <= min_duration:
                    cycle.exceeded_min_duration = 0
                else:
                    diff = cycle.duration_time - min_duration
                    cycle.exceeded_min_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('duration_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_ended')
    def _compute_exceeded_max_duration(self):
        for cycle in self:
            cycle.exceeded_max_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and cycle.is_ended:
                max_duration = cycle.workflow_procedure_cycle_id.get_max_duration_for_time_unit(
                    cycle.time_unit
                )
                if (max_duration == 0) or cycle.duration_time <= max_duration:
                    cycle.exceeded_max_duration = 0
                else:
                    diff = cycle.duration_time - max_duration
                    cycle.exceeded_max_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('execution_start_datetime', 'execution_end_datetime', 'time_unit', 'is_execution_started', 'is_execution_complete')
    def _compute_execution_elapsed_time(self):
        for cycle in self:
            cycle.execution_elapsed_time = 0
            if cycle.is_execution_started and cycle.time_unit:
                diff = fields.Datetime.now() - cycle.execution_start_datetime
                if cycle.is_execution_complete:
                    diff = cycle.execution_end_datetime - cycle.execution_start_datetime
                cycle.execution_elapsed_time = date_utils.get_time_total(diff, cycle.time_unit)

    @api.depends('execution_start_datetime', 'execution_end_datetime', 'time_unit', 'is_execution_started', 'is_execution_complete')
    def _compute_execution_duration_time(self):
        for cycle in self:
            cycle.execution_duration_time = 0
            if cycle.is_execution_started and cycle.time_unit:
                diff = fields.Datetime.now() - cycle.execution_start_datetime
                if cycle.is_execution_complete:
                    diff = cycle.execution_end_datetime - cycle.execution_start_datetime
                cycle.execution_duration_time = date_utils.get_time_total(diff, cycle.time_unit)

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_execution_complete')
    def _compute_remaining_min_execution_duration(self):
        for cycle in self:
            cycle.remaining_min_execution_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and not cycle.is_execution_complete:
                min_duration = cycle.workflow_procedure_cycle_id.get_min_execution_duration_for_time_unit(
                    cycle.time_unit
                )
                if min_duration > 0:
                    diff = min_duration - cycle.execution_elapsed_time
                    cycle.remaining_min_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_execution_complete')
    def _compute_remaining_max_execution_duration(self):
        for cycle in self:
            cycle.remaining_max_execution_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and not cycle.is_execution_complete:
                max_duration = cycle.workflow_procedure_cycle_id.get_max_execution_duration_for_time_unit(
                    cycle.time_unit
                )
                if max_duration > 0:
                    diff = max_duration - cycle.execution_elapsed_time
                    cycle.remaining_max_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_execution_complete')
    def _compute_exceeding_min_execution_duration(self):
        for cycle in self:
            cycle.exceeding_min_execution_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and not cycle.is_execution_complete:
                min_duration = cycle.workflow_procedure_cycle_id.get_min_execution_duration_for_time_unit(
                    cycle.time_unit
                )
                if (min_duration == 0) or cycle.execution_elapsed_time <= min_duration:
                    cycle.exceeding_min_execution_duration = 0
                else:
                    diff = cycle.execution_elapsed_time - min_duration
                    cycle.exceeding_min_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_execution_complete')
    def _compute_exceeding_max_execution_duration(self):
        for cycle in self:
            cycle.exceeding_max_execution_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and not cycle.is_execution_complete:
                max_duration = cycle.workflow_procedure_cycle_id.get_max_execution_duration_for_time_unit(
                    cycle.time_unit
                )
                if (max_duration == 0) or cycle.execution_elapsed_time <= max_duration:
                    cycle.exceeding_max_execution_duration = 0
                else:
                    diff = cycle.execution_elapsed_time - max_duration
                    cycle.exceeding_max_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('execution_duration_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_execution_complete')
    def _compute_exceeded_min_execution_duration(self):
        for cycle in self:
            cycle.exceeded_min_execution_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and cycle.is_execution_complete:
                min_duration = cycle.workflow_procedure_cycle_id.get_min_execution_duration_for_time_unit(
                    cycle.time_unit
                )
                if (min_duration == 0) or cycle.execution_duration_time <= min_duration:
                    cycle.exceeded_min_execution_duration = 0
                else:
                    diff = cycle.execution_duration_time - min_duration
                    cycle.exceeded_min_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    @api.depends('execution_duration_time', 'time_unit', 'workflow_procedure_cycle_id', 'is_execution_complete')
    def _compute_exceeded_max_execution_duration(self):
        for cycle in self:
            cycle.exceeded_max_execution_duration = 0
            if cycle.time_unit and cycle.workflow_procedure_cycle_id and cycle.is_execution_complete:
                max_duration = cycle.workflow_procedure_cycle_id.get_max_execution_duration_for_time_unit(
                    cycle.time_unit
                )
                if (max_duration == 0) or cycle.execution_duration_time <= max_duration:
                    cycle.exceeded_max_execution_duration = 0
                else:
                    diff = cycle.execution_duration_time - max_duration
                    cycle.exceeded_max_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, cycle.time_unit),
                        cycle.time_unit
                    )

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    workflow_procedure_cycle_id = fields.Many2one('workflow.procedure.cycle',
                                                  string="Procedure Cycle", required=True)
    workflow_process_cycle_duration_ids = fields.One2many('workflow.process.cycle.duration',
                                                          'workflow_process_cycle_id',
                                                          string="Process Cycle Durations")
    workflow_process_ids = fields.Many2many('workflow.process',
                                            'workflow_process_cycle_process',string="Processes",
                                            domain=[('base_process', '=', True)])
    workflow_process_transition_ids = fields.One2many('workflow.process.transition',
                                                      'workflow_process_cycle_id',
                                                      domain=[
                                                          '&',
                                                          ('from_workflow_process_id.base_process', '=', True),
                                                          ('to_workflow_process_id.base_process', '=', True)
                                                      ])
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    has_processes = fields.Boolean(readonly=True, compute="_compute_has_processes")
    has_process_transitions = fields.Boolean(readonly=True, compute="_compute_has_process_transitions")
    has_durations = fields.Boolean(readonly=True, compute="_compute_has_durations")
    is_ended = fields.Boolean(string="Is ended", readonly=True, compute="_compute_is_ended")
    is_execution_started = fields.Boolean(string="Is Execution Started", readonly=True,
                                          compute="_compute_is_execution_started")
    is_execution_complete = fields.Boolean(string="Is Execution Complete", readonly=True,
                                           compute="_compute_is_execution_complete")
    # TEMPORAL FIELDS
    start_datetime = fields.Datetime(string="Start Datetime", copy=False, required=True)
    end_datetime = fields.Datetime(string="End Datetime", compute="_compute_end_datetime", copy=False,
                                   required=False)
    execution_start_datetime = fields.Datetime(string="Execution Start Datetime", copy=False,
                                               required=False, compute="_compute_execution_start_datetime")
    execution_end_datetime = fields.Datetime(string="Execution End Datetime", copy=False, required=False,
                                             compute="_compute_execution_end_datetime")
    expected_min_start_datetime = fields.Datetime(string="Expected Minimum Start Datetime", copy=False,
                                                  required=False, compute="_compute_expected_min_start_datetime")
    expected_max_start_datetime = fields.Datetime(string="Expected Maximum Start Datetime", copy=False,
                                                  required=False, compute="_compute_expected_max_start_datetime")
    expected_min_end_datetime = fields.Datetime(string="Expected Minimum End Datetime", copy=False,
                                                required=False, compute="_compute_expected_min_end_datetime")
    expected_max_end_datetime = fields.Datetime(string="Expected Maximum End Datetime", copy=False,
                                                required=False, compute="_compute_expected_max_end_datetime")
    expected_min_execution_start_datetime = fields.Datetime(string="Expected Minimum Execution Start Datetime",
                                                            copy=False, required=False,
                                                            compute="_compute_expected_min_execution_start_datetime")
    expected_max_execution_start_datetime = fields.Datetime(string="Expected Maximum Execution Start Datetime",
                                                            copy=False, required=False,
                                                            compute="_compute_expected_max_execution_start_datetime")
    expected_min_execution_end_datetime = fields.Datetime(string="Expected Minimum Execution End Datetime",
                                                          copy=False, required=False,
                                                            compute="_compute_expected_min_execution_end_datetime")
    expected_max_execution_end_datetime = fields.Datetime(string="Expected Maximum Execution End Datetime",
                                                          copy=False, required=False,
                                                            compute="_compute_expected_max_execution_end_datetime")
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
        string="Time Unit", required=False
    )
    scheduled_min_end_datetime = fields.Datetime(string="Scheduled Minimum End Datetime", copy=False,
                                                 required=False,
                                                 compute="_compute_scheduled_min_end_datetime")
    scheduled_max_end_datetime = fields.Datetime(string="Scheduled Maximum End Datetime", copy=False,
                                                 required=False,
                                                 compute="_compute_scheduled_max_end_datetime")
    elapsed_time = fields.Integer("Elapsed Time", compute="_compute_elapsed_time")
    duration_time = fields.Integer("Duration", compute="_compute_duration_time")
    remaining_min_duration = fields.Integer("Remaining Minimum Duration",
                                            compute="_compute_remaining_min_duration")
    remaining_max_duration = fields.Integer("Remaining Maximum Duration",
                                            compute="_compute_remaining_max_duration")
    exceeding_min_duration = fields.Integer("Exceeding Minimum Duration",
                                            compute="_compute_exceeding_min_duration")
    exceeding_max_duration = fields.Integer("Exceeding Maximum Duration",
                                            compute="_compute_exceeding_max_duration")
    exceeded_min_duration = fields.Integer("Exceeded Minimum Duration",
                                           compute="_compute_exceeded_min_duration")
    exceeded_max_duration = fields.Integer("Exceeded Maximum Duration",
                                           compute="_compute_exceeded_max_duration")
    execution_elapsed_time = fields.Float("Execution Elapsed Time",
                                          compute="_compute_execution_elapsed_time")
    execution_duration_time = fields.Float("Execution Duration Time",
                                           compute="_compute_execution_duration_time")
    remaining_min_execution_duration = fields.Float("Remaining Minimum Execution Duration",
                                                    compute="_compute_remaining_min_execution_duration")
    remaining_max_execution_duration = fields.Float("Remaining Maximum Execution Duration",
                                                    compute="_compute_remaining_max_execution_duration")
    exceeding_min_execution_duration = fields.Float("Exceeding Minimum Execution Duration",
                                                    compute="_compute_exceeding_min_execution_duration")
    exceeding_max_execution_duration = fields.Float("Exceeding Maximum Execution Duration",
                                                    compute="_compute_exceeding_max_execution_duration")
    exceeded_min_execution_duration = fields.Float("Exceeded Minimum Execution Duration",
                                                   compute="_compute_exceeded_min_execution_duration")
    exceeded_max_execution_duration = fields.Float("Exceeded Maximum Execution Duration",
                                                   compute="_compute_exceeded_max_execution_duration")

    def find_latest_transition(self):
        self.ensure_one()
        return self.env['workflow.process.transition'].search(
            [('id', 'in', self.workflow_process_transition_ids.ids)],
            order="create_date desc", limit=1
        )

    def get_descendant_process_execution_ids(self):
        self.ensure_one()
        ids = []
        for procedure in self.workflow_process_ids:
            ids.extend(procedure.get_descendant_process_execution_ids())
        return list(set(ids))

    def get_execution_durations_for_time_unit(self, time_unit):
        self.ensure_one()
        return self.env['workflow.process.execution.duration'].search([
            '&', ('time_unit', '=', time_unit),
            ('workflow_process_execution_id', 'in', self.get_descendant_process_execution_ids())
        ])

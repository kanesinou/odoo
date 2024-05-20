# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

from odoo import api, fields, models
from ..utils import date_utils


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
        self.set_starter_workflow_process()

    @api.depends('parent_id')
    def _compute_root_workflow_process(self):
        for process in self:
            process.root_workflow_process_id = process.get_root_workflow_process_id()

    @api.depends('workflowable_id', 'workflow_procedure_id')
    def _compute_name(self):
        for process in self:
            process.name = process.workflowable_id.name + ' Process[%s]' % process.workflow_procedure_id.name

    @api.depends('end_datetime')
    def _compute_is_ended(self):
        for process in self:
            process.is_ended = False
            if process.activity_process:
                not_ended_stages = process.workflow_process_stage_ids.filtered(
                    lambda s: not s.is_ended
                )
                if not not_ended_stages.exists():
                    process.is_ended = True
            else:
                not_ended_sub_processes = process.workflow_process_ids.filtered(
                    lambda p: not p.is_ended
                )
                if not not_ended_sub_processes.exists():
                    process.is_ended = True

    @api.depends('workflow_process_ids', 'workflow_process_stage_ids', 'activity_process')
    def _compute_is_execution_started(self):
        for process in self:
            if process.activity_process:
                started_stage_executions = process.workflow_process_stage_ids.filtered(
                    lambda s: s.is_execution_started
                )
                process.is_execution_started = True if started_stage_executions.exists() else False
            else:
                started_sub_executions = process.workflow_process_ids.filtered(
                    lambda p: p.is_execution_started
                )
                process.is_execution_started = True if started_sub_executions.exists() else False

    @api.depends('workflow_process_ids', 'workflow_process_stage_ids', 'activity_process')
    def _compute_is_execution_current(self):
        for process in self:
            if process.activity_process:
                current_stage_executions = process.workflow_process_stage_ids.filtered(
                    lambda s: s.is_execution_current
                )
                process.is_execution_current = True if current_stage_executions.exists() else False
            else:
                current_sub_executions = process.workflow_process_ids.filtered(
                    lambda p: p.is_execution_current
                )
                process.is_execution_current = True if current_sub_executions.exists() else False

    @api.depends('workflow_process_ids', 'workflow_process_stage_ids', 'activity_process')
    def _compute_is_execution_complete(self):
        for process in self:
            if process.activity_process:
                not_complete_stage_executions = process.workflow_process_stage_ids.filtered(
                    lambda s: not s.is_execution_complete
                )
                process.is_execution_complete = True if not not_complete_stage_executions.exists() else False
            else:
                not_complete_sub_executions = process.workflow_process_ids.filtered(
                    lambda p: not p.is_execution_complete
                )
                process.is_execution_complete = True if not not_complete_sub_executions.exists() else False

    @api.depends('start_datetime', 'time_unit', 'is_ended')
    def _compute_elapsed_time(self):
        for process in self:
            process.elapsed_time = 0
            if process.start_datetime and process.time_unit:
                diff = fields.Datetime.now() - process.start_datetime
                if process.is_ended:
                    diff = process.end_datetime - process.start_datetime
                process.elapsed_time = date_utils.get_time_total(diff, process.time_unit)

    @api.depends('start_datetime', 'end_datetime', 'time_unit', 'is_ended')
    def _compute_duration_time(self):
        for process in self:
            process.duration_time = 0
            if process.start_datetime and process.time_unit:
                diff = fields.Datetime.now() - process.start_datetime
                if process.is_ended:
                    diff = process.end_datetime - process.start_datetime
                process.duration_time = date_utils.get_time_total(diff, process.time_unit)

    @api.depends('elapsed_time', 'time_unit', 'workflow_procedure_id', 'is_ended')
    def _compute_remaining_min_duration(self):
        for process in self:
            process.remaining_min_duration = 0
            if process.time_unit and process.workflow_procedure_id and not process.is_ended:
                min_duration = process.workflow_procedure_id.get_min_duration_for_time_unit(
                    process.time_unit
                )
                if min_duration > 0:
                    diff = min_duration - process.elapsed_time
                    process.remaining_min_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('elapsed_time', 'time_unit', 'workflow_procedure_id', 'is_ended')
    def _compute_remaining_max_duration(self):
        for process in self:
            process.remaining_max_duration = 0
            if process.time_unit and process.workflow_procedure_id and not process.is_ended:
                max_duration = process.workflow_procedure_id.get_max_duration_for_time_unit(
                    process.time_unit
                )
                if max_duration > 0:
                    diff = max_duration - process.elapsed_time
                    process.remaining_max_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('elapsed_time', 'time_unit', 'workflow_procedure_id', 'is_ended')
    def _compute_exceeding_min_duration(self):
        for process in self:
            process.exceeding_min_duration = 0
            if process.time_unit and process.workflow_procedure_id and not process.is_ended:
                min_duration = process.workflow_procedure_id.get_min_duration_for_time_unit(
                    process.time_unit
                )
                if (min_duration == 0) or process.elapsed_time <= min_duration:
                    process.exceeding_min_duration = 0
                else:
                    diff = process.elapsed_time - min_duration
                    process.exceeding_min_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('duration_time', 'time_unit', 'workflow_procedure_id', 'is_ended')
    def _compute_exceeding_max_duration(self):
        for process in self:
            process.exceeding_max_duration = 0
            if process.time_unit and process.workflow_procedure_id and not process.is_ended:
                max_duration = process.workflow_procedure_id.get_max_duration_for_time_unit(
                    process.time_unit
                )
                if (max_duration == 0) or process.elapsed_time <= max_duration:
                    process.exceeding_max_duration = 0
                else:
                    diff = process.elapsed_time - max_duration
                    process.exceeding_max_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('duration_time', 'time_unit', 'workflow_procedure_id', 'is_ended')
    def _compute_exceeded_min_duration(self):
        for process in self:
            process.exceeded_min_duration = 0
            if process.time_unit and process.workflow_procedure_id and process.is_ended:
                min_duration = process.workflow_procedure_id.get_min_duration_for_time_unit(
                    process.time_unit
                )
                if (min_duration == 0) or process.duration_time <= min_duration:
                    process.exceeded_min_duration = 0
                else:
                    diff = process.duration_time - min_duration
                    process.exceeded_min_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('duration_time', 'time_unit', 'workflow_procedure_id', 'is_ended')
    def _compute_exceeded_max_duration(self):
        for process in self:
            process.exceeded_max_duration = 0
            if process.time_unit and process.workflow_procedure_id and process.is_ended:
                max_duration = process.workflow_procedure_id.get_max_duration_for_time_unit(
                    process.time_unit
                )
                if (max_duration == 0) or process.duration_time <= max_duration:
                    process.exceeded_max_duration = 0
                else:
                    diff = process.duration_time - max_duration
                    process.exceeded_max_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('execution_start_datetime', 'execution_end_datetime', 'time_unit', 'is_execution_started',
                 'is_execution_complete')
    def _compute_execution_elapsed_time(self):
        for process in self:
            process.execution_elapsed_time = 0
            if process.is_execution_started and process.time_unit:
                diff = fields.Datetime.now() - process.execution_start_datetime
                if process.is_execution_complete:
                    diff = process.execution_end_datetime - process.execution_start_datetime
                process.execution_elapsed_time = date_utils.get_time_total(diff, process.time_unit)

    @api.depends('execution_start_datetime', 'execution_end_datetime', 'time_unit', 'is_execution_started',
                 'is_execution_complete')
    def _compute_execution_duration_time(self):
        for process in self:
            process.execution_duration_time = 0
            if process.is_execution_started and process.time_unit:
                diff = fields.Datetime.now() - process.execution_start_datetime
                if process.is_execution_complete:
                    diff = process.execution_end_datetime - process.execution_start_datetime
                process.execution_duration_time = date_utils.get_time_total(diff, process.time_unit)

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_id', 'is_execution_complete')
    def _compute_remaining_min_execution_duration(self):
        for process in self:
            process.remaining_min_execution_duration = 0
            if process.time_unit and process.workflow_procedure_id and not process.is_execution_complete:
                min_duration = process.workflow_procedure_id.get_min_execution_duration_for_time_unit(
                    process.time_unit
                )
                if min_duration > 0:
                    diff = min_duration - process.execution_elapsed_time
                    process.remaining_min_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_id', 'is_execution_complete')
    def _compute_remaining_max_execution_duration(self):
        for process in self:
            process.remaining_max_execution_duration = 0
            if process.time_unit and process.workflow_procedure_id and not process.is_execution_complete:
                max_duration = process.workflow_procedure_id.get_max_execution_duration_for_time_unit(
                    process.time_unit
                )
                if max_duration > 0:
                    diff = max_duration - process.execution_elapsed_time
                    process.remaining_max_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_id', 'is_execution_complete')
    def _compute_exceeding_min_execution_duration(self):
        for process in self:
            process.exceeding_min_execution_duration = 0
            if process.time_unit and process.workflow_procedure_id and not process.is_execution_complete:
                min_duration = process.workflow_procedure_id.get_min_execution_duration_for_time_unit(
                    process.time_unit
                )
                if (min_duration == 0) or process.execution_elapsed_time <= min_duration:
                    process.exceeding_min_execution_duration = 0
                else:
                    diff = process.execution_elapsed_time - min_duration
                    process.exceeding_min_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_id', 'is_execution_complete')
    def _compute_exceeding_max_execution_duration(self):
        for process in self:
            process.exceeding_max_execution_duration = 0
            if process.time_unit and process.workflow_procedure_id and not process.is_execution_complete:
                max_duration = process.workflow_procedure_id.get_max_execution_duration_for_time_unit(
                    process.time_unit
                )
                if (max_duration == 0) or process.execution_elapsed_time <= max_duration:
                    process.exceeding_max_execution_duration = 0
                else:
                    diff = process.execution_elapsed_time - max_duration
                    process.exceeding_max_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('execution_duration_time', 'time_unit', 'workflow_procedure_id', 'is_execution_complete')
    def _compute_exceeded_min_execution_duration(self):
        for process in self:
            process.exceeded_min_execution_duration = 0
            if process.time_unit and process.workflow_procedure_id and process.is_execution_complete:
                min_duration = process.workflow_procedure_id.get_min_execution_duration_for_time_unit(
                    process.time_unit
                )
                if (min_duration == 0) or process.execution_duration_time <= min_duration:
                    process.exceeded_min_execution_duration = 0
                else:
                    diff = process.execution_duration_time - min_duration
                    process.exceeded_min_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('execution_duration_time', 'time_unit', 'workflow_procedure_id', 'is_execution_complete')
    def _compute_exceeded_max_execution_duration(self):
        for process in self:
            process.exceeded_max_execution_duration = 0
            if process.time_unit and process.workflow_procedure_id and process.is_execution_complete:
                max_duration = process.workflow_procedure_id.get_max_execution_duration_for_time_unit(
                    process.time_unit
                )
                if (max_duration == 0) or process.execution_duration_time <= max_duration:
                    process.exceeded_max_execution_duration = 0
                else:
                    diff = process.execution_duration_time - max_duration
                    process.exceeded_max_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, process.time_unit),
                        process.time_unit
                    )

    @api.depends('time_unit')
    def _compute_time_label(self):
        for process in self:
            if process.time_unit:
                process.time_label = date_utils.TIME_LABELS.get(process.time_unit)
            else:
                process.time_label = None

    @api.depends('time_unit')
    def _compute_time_label_plural(self):
        for process in self:
            if process.time_unit:
                process.time_label_plural = date_utils.TIME_LABEL_PLURALS.get(process.time_unit)
            else:
                process.time_label_plural = None

    @api.depends('workflow_process_stage_ids')
    def _compute_can_be_resumed(self):
        for process in self:
            resumable_stages = process.workflow_process_stage_ids.filtered(lambda s: s.can_be_resumed)
            process.can_be_resumed = len(resumable_stages) > 0

    @api.depends('workflow_process_stage_ids')
    def _compute_cancelled(self):
        for process in self:
            cancelled_stages = process.workflow_process_stage_ids.filtered(lambda s: s.cancelled)
            process.cancelled = len(cancelled_stages) > 0

    @api.depends('workflow_process_stage_ids')
    def _compute_breaked(self):
        for process in self:
            breaked_stages = process.workflow_process_stage_ids.filtered(lambda s: s.breaked)
            process.breaked = len(breaked_stages) > 0

    @api.depends('workflow_process_stage_ids')
    def _compute_resumed(self):
        for process in self:
            resumed_stages = process.workflow_process_stage_ids.filtered(lambda s: s.resumed)
            process.resumed = len(resumed_stages) > 0

    @api.depends('activity_process', 'workflow_process_stage_ids', 'workflow_process_ids')
    def _compute_end_datetime(self):
        for process in self:
            process.end_datetime = None
            if process.is_ended:
                if process.activity_process:
                    datetime_list = process.workflow_process_stage_ids.mapped('end_datetime')
                else:
                    datetime_list = process.workflow_process_ids.mapped('end_datetime')
                valid_datetime_list = [dl for dl in datetime_list if isinstance(dl, datetime)]
                if len(valid_datetime_list) > 0:
                    process.end_datetime = max(valid_datetime_list)

    @api.depends('workflow_process_stage_ids', 'workflow_process_ids', 'activity_process')
    def _compute_execution_start_datetime(self):
        for process in self:
            process.execution_start_datetime = None
            if process.activity_process:
                start_datetime_list = process.workflow_process_stage_ids.mapped(
                    'execution_start_datetime'
                )
            else:
                start_datetime_list = process.workflow_process_ids.mapped(
                    'execution_start_datetime'
                )
            valid_datetimes_list = [d for d in start_datetime_list if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                process.execution_start_datetime = min(valid_datetimes_list)

    @api.depends('workflow_process_stage_ids', 'workflow_process_ids', 'activity_process')
    def _compute_execution_end_datetime(self):
        for process in self:
            process.execution_end_datetime = None
            if process.activity_process:
                end_datetime_list = process.workflow_process_stage_ids.mapped('execution_end_datetime')
            else:
                end_datetime_list = process.workflow_process_ids.mapped('execution_end_datetime')
            valid_datetimes_list = [d for d in end_datetime_list if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                process.execution_end_datetime = max(valid_datetimes_list)

    @api.depends('inbound_workflow_process_transition_ids', 'start_datetime')
    def _compute_expected_min_start_datetime(self):
        for process in self:
            process.expected_min_start_datetime = False
            if process.activity_process:
                start_datetime_list = process.workflow_process_stage_ids.mapped('expected_min_start_datetime')
            else:
                start_datetime_list = process.workflow_process_ids.mapped('expected_min_start_datetime')
            valid_datetimes_list = [d for d in start_datetime_list if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                process.expected_min_start_datetime = min(valid_datetimes_list)

    @api.depends('inbound_workflow_process_transition_ids', 'start_datetime')
    def _compute_expected_max_start_datetime(self):
        for process in self:
            process.expected_max_start_datetime = None
            if process.activity_process:
                start_datetime_list = process.workflow_process_stage_ids.mapped('expected_max_start_datetime')
            else:
                start_datetime_list = process.workflow_process_ids.mapped('expected_max_start_datetime')
            valid_datetimes_list = [d for d in start_datetime_list if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                process.expected_max_start_datetime = min(valid_datetimes_list)

    @api.depends('workflow_procedure_id', 'start_datetime')
    def _compute_expected_min_end_datetime(self):
        for process in self:
            process.expected_min_end_datetime = None
            if process.activity_process:
                end_datetime_list = process.workflow_process_stage_ids.mapped('expected_min_end_datetime')
            else:
                end_datetime_list = process.workflow_process_ids.mapped('expected_min_end_datetime')
            valid_datetimes_list = [d for d in end_datetime_list if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                process.expected_min_end_datetime = min(valid_datetimes_list)

    @api.depends('workflow_procedure_id', 'start_datetime')
    def _compute_expected_max_end_datetime(self):
        for process in self:
            process.expected_max_end_datetime = None
            if process.activity_process:
                end_datetime_list = process.workflow_process_stage_ids.mapped('expected_max_end_datetime')
            else:
                end_datetime_list = process.workflow_process_ids.mapped('expected_max_end_datetime')
            valid_datetimes_list = [d for d in end_datetime_list if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                process.expected_max_end_datetime = min(valid_datetimes_list)

    @api.depends('inbound_workflow_process_transition_ids', 'execution_start_datetime')
    def _compute_expected_min_execution_start_datetime(self):
        for process in self:
            inbound_transition = process.find_latest_inbound_transition()
            if inbound_transition.exists() and process.execution_start_datetime:
                process.expected_min_execution_start_datetime = inbound_transition.from_workflow_process_id.expected_min_execution_end_datetime
            else:
                process.expected_min_execution_start_datetime = process.execution_start_datetime

    @api.depends('inbound_workflow_process_transition_ids', 'execution_start_datetime')
    def _compute_expected_max_execution_start_datetime(self):
        for process in self:
            inbound_transition = process.find_latest_inbound_transition()
            if inbound_transition.exists() and process.execution_start_datetime:
                process.expected_max_execution_start_datetime = inbound_transition.from_workflow_process_id.expected_max_execution_end_datetime
            else:
                process.expected_max_execution_start_datetime = process.execution_start_datetime

    @api.depends('workflow_procedure_id', 'execution_start_datetime')
    def _compute_expected_min_execution_end_datetime(self):
        for process in self:
            process.expected_min_execution_end_datetime = None
            if process.workflow_procedure_id and process.execution_start_datetime:
                min_duration = process.workflow_procedure_id.get_min_execution_duration_for_time_unit(
                    process.time_unit
                )
                delta = date_utils.get_timedelta_from_duration(min_duration, process.time_unit)
                process.expected_min_execution_end_datetime = process.execution_start_datetime + delta

    @api.depends('workflow_procedure_id', 'execution_start_datetime')
    def _compute_expected_max_execution_end_datetime(self):
        for process in self:
            process.expected_max_execution_end_datetime = None
            if process.workflow_procedure_id and process.execution_start_datetime:
                max_duration = process.workflow_procedure_id.get_max_execution_duration_for_time_unit(
                    process.time_unit
                )
                delta = date_utils.get_timedelta_from_duration(max_duration, process.time_unit)
                process.expected_max_execution_end_datetime = process.execution_start_datetime + delta

    codename = fields.Char(string='Codename', required=True, size=154)
    name = fields.Char(string='Name', required=True, compute="_compute_name", translate=True, store=True)
    base_process = fields.Boolean(string="Base Process", default=False)
    activity_process = fields.Boolean(string="Activity Process", default=False)
    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               compute="_compute_root_workflow_process")
    workflow_procedure_id = fields.Many2one('workflow.procedure', string="Procedure",
                                            required=True)
    workflowable_id = fields.Many2one('workflowable', string="Workflowable",
                                      required=True)
    parent_id = fields.Many2one('workflow.process', required=False, string="Parent")
    starter_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                                  readonly=True, invisible=True, string="Starter Process")
    workflow_process_stage_id = fields.Many2one('workflow.process.stage', required=False,
                                                string="Starter Stage")
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
    apply_procedure_changes = fields.Boolean(string="Apply Procedure Changes", default=False)
    active = fields.Boolean(default=True)
    cancelled = fields.Boolean(readonly=True, compute="_compute_cancelled")
    breaked = fields.Boolean(readonly=True, compute="_compute_breaked")
    can_be_resumed = fields.Boolean(readonly=True, compute="_compute_can_be_resumed")
    resumed = fields.Boolean(readonly=True, compute="_compute_resumed")
    is_ended = fields.Boolean(string="Is ended", readonly=True, compute="_compute_is_ended")
    is_execution_started = fields.Boolean(string="Is Execution Started", readonly=True,
                                          compute="_compute_is_execution_started")
    is_execution_current = fields.Boolean(string="Is Execution Current", readonly=True,
                                          compute="_compute_is_execution_current")
    is_execution_complete = fields.Boolean(string="Is Execution Complete", readonly=True,
                                           compute="_compute_is_execution_complete")
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
    elapsed_time = fields.Float("Elapsed Time", compute="_compute_elapsed_time", digits=(11, 5))
    duration_time = fields.Float("Duration", compute="_compute_duration_time", digits=(11, 5))
    remaining_min_duration = fields.Float("Remaining Minimum Duration",
                                          compute="_compute_remaining_min_duration", digits=(11, 5))
    remaining_max_duration = fields.Float("Remaining Maximum Duration",
                                          compute="_compute_remaining_max_duration", digits=(11, 5))
    exceeding_min_duration = fields.Float("Exceeding Minimum Duration",
                                          compute="_compute_exceeding_min_duration", digits=(11, 5))
    exceeding_max_duration = fields.Float("Exceeding Maximum Duration",
                                          compute="_compute_exceeding_max_duration", digits=(11, 5))
    exceeded_min_duration = fields.Float("Exceeded Minimum Duration",
                                         compute="_compute_exceeded_min_duration", digits=(11, 5))
    exceeded_max_duration = fields.Float("Exceeded Maximum Duration",
                                         compute="_compute_exceeded_max_duration", digits=(11, 5))
    execution_elapsed_time = fields.Float("Elapsed Execution Time",
                                          compute="_compute_execution_elapsed_time", digits=(11, 5))
    execution_duration_time = fields.Float("Execution Duration",
                                           compute="_compute_execution_duration_time", digits=(11, 5))
    remaining_min_execution_duration = fields.Float("Remaining Minimum Execution Duration",
                                                    compute="_compute_remaining_min_execution_duration",
                                                    digits=(11, 5))
    remaining_max_execution_duration = fields.Float("Remaining Maximum Execution Duration",
                                                    compute="_compute_remaining_max_execution_duration",
                                                    digits=(11, 5))
    exceeding_min_execution_duration = fields.Float("Exceeding Minimum Execution Duration",
                                                    compute="_compute_exceeding_min_execution_duration",
                                                    digits=(11, 5))
    exceeding_max_execution_duration = fields.Float("Exceeding Maximum Execution Duration",
                                                    compute="_compute_exceeding_max_execution_duration",
                                                    digits=(11, 5))
    exceeded_min_execution_duration = fields.Float("Exceeded Minimum Execution Duration",
                                                   compute="_compute_exceeded_min_execution_duration",
                                                   digits=(11, 5))
    exceeded_max_execution_duration = fields.Float("Exceeded Maximum Execution Duration",
                                                   compute="_compute_exceeded_max_execution_duration",
                                                   digits=(11, 5))

    def find_latest_inbound_transition(self):
        self.ensure_one()
        return self.env['workflow.process.transition'].search(
            [('id', 'in', self.inbound_workflow_process_transition_ids.ids)],
            order="create_date desc", limit=1
        )

    def expand_starters(self):
        self.ensure_one()
        if self.parent_id:
            parent = self.parent_id
            parent.workflow_process_stage_id = self.workflow_process_stage_id.id
            parent.starter_workflow_process_id = self.id
            if not parent.base_process:
                parent.expand_starters()
        elif self.base_process:
            self.starter_workflow_process_id = self.id

    def unexpand_starters(self):
        self.ensure_one()
        if self.parent_id:
            parent = self.parent_id
            parent.workflow_process_stage_id = None
            parent.starter_workflow_process_id = None
            if not parent.base_process:
                parent.unexpand_starters()
        elif self.base_process:
            self.starter_workflow_process_id = None

    def get_workflow_process_starter_stage(self):
        self.ensure_one()
        starter_procedure_stage = self.workflow_procedure_id.find_starter_workflow_procedure_stage()
        if starter_procedure_stage.exists():
            return self.env['workflow.process.stage'].search([(
                'workflow_procedure_stage_id', '=', starter_procedure_stage.id
            )], limit=1)
        return self.env['workflow.process.stage'].browse()

    def get_root_workflow_process_id(self):
        self.ensure_one()
        if self.base_process or not self.parent_id:
            return self.id
        else:
            return self.parent_id.get_root_workflow_process_id()

    def set_starter_workflow_process(self):
        self.ensure_one()
        if self.activity_process:
            self.parent_id.starter_workflow_process_id = self.id
            self.parent_id.set_starter_workflow_process()
        elif self.base_process:
            return
        else:
            self.parent_id.set_starter_workflow_process()

    def find_starter_workflow_process_stage(self):
        self.ensure_one()
        if self.activity_process:
            return self.workflow_process_stage_id
        else:
            return self.starter_workflow_process_id.find_starter_workflow_process_stage()

    def get_base_workflow_process_starter_position_data(self):
        self.ensure_one()
        if self.workflow_process_stage_id:
            return {
                'workflowable_id': self.workflowable_id.id,
                'workflow_process_id': self.id,
                'workflow_process_stage_id': self.workflow_process_stage_id.id
            }
        return {}

    def get_descendant_process_execution_ids(self):
        self.ensure_one()
        ids = []
        if self.activity_process:
            for stage in self.workflow_process_stage_ids:
                ids.extend(stage.workflow_process_execution_ids.ids)
        else:
            for sub in self.workflow_process_ids:
                ids.extend(sub.get_descendant_process_execution_ids())
        return list(set(ids))

    def get_execution_durations_for_time_unit(self, time_unit):
        self.ensure_one()
        return self.env['workflow.process.execution.duration'].search([
            '&', ('time_unit', '=', time_unit),
            ('workflow_process_execution_id', 'in', self.get_descendant_process_execution_ids())
        ])

    def get_scheduled_min_end_datetime_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.start_datetime:
            delta = date_utils.get_timedelta_from_duration(
                self.workflow_procedure_id.get_min_duration_for_time_unit(time_unit), time_unit
            )
            return self.start_datetime + delta
        else:
            return 0

    def get_scheduled_max_end_datetime_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.start_datetime:
            delta = date_utils.get_timedelta_from_duration(
                self.workflow_procedure_id.get_max_duration_for_time_unit(time_unit), time_unit
            )
            return self.start_datetime + delta
        else:
            return 0

    def get_elapsed_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.start_datetime:
            current = fields.Datetime.now()
            if self.end_datetime:
                ref_datetime = current if self.end_datetime >= current else self.end_datetime
            else:
                ref_datetime = current
            diff = ref_datetime - self.start_datetime
            return date_utils.get_time_total(diff, time_unit)
        else:
            return 0

    def get_duration_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.start_datetime and self.end_datetime:
            diff = self.end_datetime - self.start_datetime
            return date_utils.get_time_total(diff, time_unit)
        else:
            return 0

    def get_remaining_min_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.start_datetime and self.get_scheduled_min_end_datetime_for_time_unit(time_unit):
            diff = self.get_scheduled_min_end_datetime_for_time_unit(time_unit) - self.start_datetime
            return date_utils.get_time_total(diff, time_unit)
        else:
            return 0

    def get_remaining_max_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.start_datetime and self.get_scheduled_max_end_datetime_for_time_unit(time_unit):
            diff = self.get_scheduled_max_end_datetime_for_time_unit(time_unit) - self.start_datetime
            return date_utils.get_time_total(diff, time_unit)
        else:
            return 0

    def get_exceeding_min_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.get_scheduled_min_end_datetime_for_time_unit(time_unit):
            current = fields.Datetime.now()
            if self.end_datetime:
                ref_datetime = current if self.end_datetime >= current else self.end_datetime
            else:
                ref_datetime = current
            if ref_datetime > self.get_scheduled_min_end_datetime_for_time_unit(time_unit):
                diff = ref_datetime - self.get_scheduled_min_end_datetime_for_time_unit(time_unit)
                return date_utils.get_time_total(diff, time_unit)
            else:
                return 0
        else:
            return 0

    def get_exceeded_min_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.get_scheduled_min_end_datetime_for_time_unit(time_unit) and self.end_datetime:
            if self.end_datetime > self.get_scheduled_min_end_datetime_for_time_unit(time_unit):
                diff = self.end_datetime - self.get_scheduled_min_end_datetime_for_time_unit(time_unit)
                return date_utils.get_time_total(diff, time_unit)
            else:
                return 0
        else:
            return 0

    def get_exceeding_max_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.get_scheduled_max_end_datetime_for_time_unit(time_unit):
            current = fields.Datetime.now()
            if self.end_datetime:
                ref_datetime = current if self.end_datetime >= current else self.end_datetime
            else:
                ref_datetime = current
            if ref_datetime > self.get_scheduled_max_end_datetime_for_time_unit(time_unit):
                diff = ref_datetime - self.get_scheduled_max_end_datetime_for_time_unit(time_unit)
                return date_utils.get_time_total(diff, time_unit)
            else:
                return 0
        else:
            return 0

    def get_exceeded_max_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.get_scheduled_max_end_datetime_for_time_unit(time_unit) and self.end_datetime:
            if self.end_datetime > self.get_scheduled_max_end_datetime_for_time_unit(time_unit):
                diff = self.end_datetime - self.get_scheduled_max_end_datetime_for_time_unit(time_unit)
                return date_utils.get_time_total(diff, time_unit)
            else:
                return 0
        else:
            return 0

    def action_remaining_procedures(self):
        pass

    def get_child_workflow_processes_by_id(self, process_id):
        self.ensure_one()
        return self.workflow_process_ids.filtered(lambda p: p.id == process_id)

    def get_child_workflow_process_by_id(self, process_id):
        self.ensure_one()
        records = self.get_child_workflow_processes_by_id(process_id)
        if len(records) > 0:
            return records[0]
        return

    def get_child_workflow_processes_by_ids(self, process_ids):
        self.ensure_one()
        return self.workflow_process_ids.filtered(lambda p: p.id in process_ids)

    def get_workflow_process_transitions_by_id(self, transition_id):
        self.ensure_one()
        return self.workflow_process_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_workflow_process_transition_by_id(self, transition_id):
        self.ensure_one()
        records = self.get_workflow_process_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_transitions_by_ids(self, transition_ids):
        self.ensure_one()
        return self.workflow_process_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_workflow_process_stages_by_id(self, stage_id):
        self.ensure_one()
        return self.workflow_process_stage_ids.filtered(lambda s: s.id == stage_id)

    def get_workflow_process_stage_by_id(self, stage_id):
        self.ensure_one()
        records = self.get_workflow_process_stages_by_id(stage_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_stages_by_ids(self, stage_ids):
        self.ensure_one()
        return self.workflow_process_stage_ids.filtered(lambda s: s.id in stage_ids)

    def get_workflow_process_stage_transitions_by_id(self, transition_id):
        self.ensure_one()
        return self.workflow_process_stage_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_workflow_process_stage_transition_by_id(self, transition_id):
        self.ensure_one()
        records = self.get_workflow_process_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_stage_transitions_by_ids(self, transition_ids):
        self.ensure_one()
        return self.workflow_process_stage_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_inbound_workflow_process_transitions_by_id(self, transition_id):
        self.ensure_one()
        return self.inbound_workflow_process_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_inbound_workflow_process_transition_by_id(self, transition_id):
        self.ensure_one()
        records = self.get_inbound_workflow_process_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_inbound_workflow_process_transitions_by_ids(self, transition_ids):
        self.ensure_one()
        return self.inbound_workflow_process_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_outbound_workflow_process_transitions_by_id(self, transition_id):
        self.ensure_one()
        return self.outbound_workflow_process_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_outbound_workflow_process_transition_by_id(self, transition_id):
        self.ensure_one()
        records = self.get_outbound_workflow_process_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_outbound_workflow_process_transitions_by_ids(self, transition_ids):
        self.ensure_one()
        return self.outbound_workflow_process_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_starter_workflow_process_stage(self):
        self.ensure_one()
        self.find_starter_workflow_process_stage()

    def get_starter_position_data(self):
        self.ensure_one()
        return self.get_base_workflow_process_starter_position_data()

    def expend_starter_descendants(self):
        self.ensure_one()
        self.expand_starters()

    def action_execution_status(self):
        pass

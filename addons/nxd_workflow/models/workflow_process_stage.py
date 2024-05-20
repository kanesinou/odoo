# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

from odoo import api, fields, models
from ..utils import date_utils


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

    @api.depends('workflow_process_id', 'workflow_procedure_stage_id')
    def _compute_name(self):
        for stage in self:
            if not stage.name or stage.name == '':
                stage.name = stage.workflow_process_id.workflowable_id.name + ' Process Stage[%s]' % stage.workflow_procedure_stage_id.name

    @api.depends('end_datetime')
    def _compute_is_ended(self):
        for stage in self:
            stage.is_ended = True if stage.end_datetime else False

    @api.depends('workflow_process_execution_ids')
    def _compute_is_execution_started(self):
        for stage in self:
            started_executions = stage.workflow_process_execution_ids.filtered(
                lambda s: s.has_started
            )
            stage.is_execution_started = True if started_executions.exists() else False

    @api.depends('workflow_process_execution_ids')
    def _compute_is_execution_current(self):
        for stage in self:
            current_executions = stage.workflow_process_execution_ids.filtered(
                lambda s: s.is_execution_current
            )
            stage.is_execution_current = True if current_executions.exists() else False

    @api.depends('workflow_process_execution_ids')
    def _compute_is_execution_complete(self):
        for stage in self:
            not_complete_executions = stage.workflow_process_execution_ids.filtered(
                lambda s: not s.is_complete
            )
            stage.is_execution_complete = True if not not_complete_executions.exists() else False

    @api.depends('start_datetime', 'end_datetime', 'time_unit', 'is_ended')
    def _compute_elapsed_time(self):
        for stage in self:
            stage.elapsed_time = 0
            if stage.start_datetime and stage.time_unit:
                diff = fields.Datetime.now() - stage.start_datetime
                if stage.is_ended:
                    diff = stage.end_datetime - stage.start_datetime
                stage.elapsed_time = date_utils.get_time_total(diff, stage.time_unit)

    @api.depends('start_datetime', 'end_datetime', 'time_unit', 'is_ended')
    def _compute_duration_time(self):
        for stage in self:
            stage.duration_time = 0
            if stage.start_datetime and stage.time_unit:
                diff = fields.Datetime.now() - stage.start_datetime
                if stage.is_ended:
                    diff = stage.end_datetime - stage.start_datetime
                stage.duration_time = date_utils.get_time_total(diff, stage.time_unit)

    @api.depends('elapsed_time', 'time_unit', 'workflow_procedure_stage_id', 'is_ended')
    def _compute_remaining_min_duration(self):
        for stage in self:
            stage.remaining_min_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and not stage.is_ended:
                procedure_min_duration = stage.workflow_procedure_stage_id.get_min_duration_for_time_unit(
                    stage.time_unit
                )
                if procedure_min_duration > 0:
                    diff = procedure_min_duration - stage.elapsed_time
                    stage.remaining_min_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('elapsed_time', 'time_unit', 'workflow_procedure_stage_id', 'is_ended')
    def _compute_remaining_max_duration(self):
        for stage in self:
            stage.remaining_max_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and not stage.is_ended:
                procedure_max_duration = stage.workflow_procedure_stage_id.get_max_duration_for_time_unit(
                    stage.time_unit
                )
                if procedure_max_duration > 0:
                    diff = procedure_max_duration - stage.elapsed_time
                    stage.remaining_max_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('elapsed_time', 'time_unit', 'workflow_procedure_stage_id', 'is_ended')
    def _compute_exceeding_min_duration(self):
        for stage in self:
            stage.exceeding_min_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and not stage.is_ended:
                min_duration = stage.workflow_procedure_stage_id.get_min_duration_for_time_unit(
                    stage.time_unit
                )
                if (min_duration == 0) or stage.elapsed_time <= min_duration:
                    stage.exceeding_min_duration = 0
                else:
                    diff = stage.elapsed_time - min_duration
                    stage.exceeding_min_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('duration_time', 'time_unit', 'workflow_procedure_stage_id', 'is_ended')
    def _compute_exceeding_max_duration(self):
        for stage in self:
            stage.exceeding_max_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and not stage.is_ended:
                max_duration = stage.workflow_procedure_stage_id.get_max_duration_for_time_unit(
                    stage.time_unit
                )
                if (max_duration == 0) or stage.elapsed_time <= max_duration:
                    stage.exceeding_max_duration = 0
                else:
                    diff = stage.elapsed_time - max_duration
                    stage.exceeding_max_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('duration_time', 'time_unit', 'workflow_procedure_stage_id', 'is_ended')
    def _compute_exceeded_min_duration(self):
        for stage in self:
            stage.exceeded_min_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and stage.is_ended:
                min_duration = stage.workflow_procedure_stage_id.get_min_duration_for_time_unit(
                    stage.time_unit
                )
                if (min_duration == 0) or stage.duration_time <= min_duration:
                    stage.exceeded_min_duration = 0
                else:
                    diff = stage.duration_time - min_duration
                    stage.exceeded_min_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('duration_time', 'time_unit', 'workflow_procedure_stage_id', 'is_ended')
    def _compute_exceeded_max_duration(self):
        for stage in self:
            stage.exceeded_max_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and stage.is_ended:
                max_duration = stage.workflow_procedure_stage_id.get_max_duration_for_time_unit(
                    stage.time_unit
                )
                if (max_duration == 0) or stage.duration_time <= max_duration:
                    stage.exceeded_max_duration = 0
                else:
                    diff = stage.duration_time - max_duration
                    stage.exceeded_max_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('execution_start_datetime', 'execution_end_datetime', 'time_unit', 'is_execution_started', 'is_execution_complete')
    def _compute_execution_elapsed_time(self):
        for stage in self:
            stage.execution_elapsed_time = 0
            if stage.is_execution_started and stage.time_unit:
                diff = fields.Datetime.now() - stage.execution_start_datetime
                if stage.is_execution_complete:
                    diff = stage.execution_end_datetime - stage.execution_start_datetime
                stage.execution_elapsed_time = date_utils.get_time_total(diff, stage.time_unit)

    @api.depends('execution_start_datetime', 'execution_end_datetime', 'time_unit', 'is_execution_started', 'is_execution_complete')
    def _compute_execution_duration_time(self):
        for stage in self:
            stage.execution_duration_time = 0
            if stage.is_execution_started and stage.time_unit:
                diff = fields.Datetime.now() - stage.execution_start_datetime
                if stage.is_execution_complete:
                    diff = stage.execution_end_datetime - stage.execution_start_datetime
                stage.execution_duration_time = date_utils.get_time_total(diff, stage.time_unit)

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_stage_id', 'is_execution_complete')
    def _compute_remaining_min_execution_duration(self):
        for stage in self:
            stage.remaining_min_execution_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and not stage.is_execution_complete:
                execution_min_duration = stage.workflow_procedure_stage_id.get_min_execution_duration_for_time_unit(
                    stage.time_unit
                )
                if execution_min_duration > 0:
                    diff = execution_min_duration - stage.execution_elapsed_time
                    stage.remaining_min_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_stage_id', 'is_execution_complete')
    def _compute_remaining_max_execution_duration(self):
        for stage in self:
            stage.remaining_max_execution_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and not stage.is_execution_complete:
                execution_max_duration = stage.workflow_procedure_stage_id.get_max_execution_duration_for_time_unit(
                    stage.time_unit
                )
                if execution_max_duration > 0:
                    diff = execution_max_duration - stage.execution_elapsed_time
                    stage.remaining_max_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_stage_id', 'is_execution_complete')
    def _compute_exceeding_min_execution_duration(self):
        for stage in self:
            stage.exceeding_min_execution_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and not stage.is_execution_complete:
                min_duration = stage.workflow_procedure_stage_id.get_min_execution_duration_for_time_unit(
                    stage.time_unit
                )
                if (min_duration == 0) or stage.execution_elapsed_time <= min_duration:
                    stage.exceeding_min_execution_duration = 0
                else:
                    diff = stage.execution_elapsed_time - min_duration
                    stage.exceeding_min_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('execution_elapsed_time', 'time_unit', 'workflow_procedure_stage_id', 'is_execution_complete')
    def _compute_exceeding_max_execution_duration(self):
        for stage in self:
            stage.exceeding_max_execution_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and not stage.is_execution_complete:
                max_duration = stage.workflow_procedure_stage_id.get_max_execution_duration_for_time_unit(
                    stage.time_unit
                )
                if (max_duration == 0) or stage.execution_elapsed_time <= max_duration:
                    stage.exceeding_max_execution_duration = 0
                else:
                    diff = stage.execution_elapsed_time - max_duration
                    stage.exceeding_max_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('execution_duration_time', 'time_unit', 'workflow_procedure_stage_id', 'is_execution_complete')
    def _compute_exceeded_min_execution_duration(self):
        for stage in self:
            stage.exceeded_min_execution_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and stage.is_execution_complete:
                min_duration = stage.workflow_procedure_stage_id.get_min_execution_duration_for_time_unit(
                    stage.time_unit
                )
                if (min_duration == 0) or stage.execution_duration_time <= min_duration:
                    stage.exceeded_min_execution_duration = 0
                else:
                    diff = stage.execution_duration_time - min_duration
                    stage.exceeded_min_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

    @api.depends('execution_duration_time', 'time_unit', 'workflow_procedure_stage_id', 'is_execution_complete')
    def _compute_exceeded_max_execution_duration(self):
        for stage in self:
            stage.exceeded_max_execution_duration = 0
            if stage.time_unit and stage.workflow_procedure_stage_id and stage.is_execution_complete:
                max_duration = stage.workflow_procedure_stage_id.get_max_execution_duration_for_time_unit(
                    stage.time_unit
                )
                if (max_duration == 0) or stage.execution_duration_time <= max_duration:
                    stage.exceeded_max_execution_duration = 0
                else:
                    diff = stage.execution_duration_time - max_duration
                    stage.exceeded_max_execution_duration = date_utils.get_time_total(
                        date_utils.get_timedelta_from_duration(diff, stage.time_unit),
                        stage.time_unit
                    )

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

    @api.depends('breaked')
    def _compute_can_be_resumed(self):
        for stage in self:
            stage.can_be_resumed = not stage.resumed and stage.breaked

    @api.depends('workflow_process_stage_acl_ids')
    def _compute_is_protected(self):
        for stage in self:
            stage.is_protected = len(stage.workflow_process_stage_acl_ids) > 0

    @api.depends('workflow_process_stage_acl_ids')
    def _compute_is_access_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_access_protected = False
            else:
                acl = stage.workflow_process_stage_acl_ids[0]
                stage.is_access_protected = len(acl.access_workflow_user_ids) > 0 or len(acl.access_workflow_role_ids)

    @api.depends('workflow_process_stage_acl_ids')
    def _compute_is_cancel_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_cancel_protected = False
            else:
                acl = stage.workflow_process_stage_acl_ids[0]
                stage.is_cancel_protected = len(acl.cancel_workflow_user_ids) > 0 or len(acl.cancel_workflow_role_ids)

    @api.depends('workflow_process_stage_acl_ids')
    def _compute_is_break_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_break_protected = False
            else:
                acl = stage.workflow_process_stage_acl_ids[0]
                stage.is_break_protected = len(acl.break_workflow_user_ids) > 0 or len(acl.break_workflow_role_ids)

    @api.depends('workflow_process_stage_acl_ids')
    def _compute_is_resume_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_resume_protected = False
            else:
                acl = stage.workflow_process_stage_acl_ids[0]
                stage.is_resume_protected = len(acl.resume_workflow_user_ids) > 0 or len(acl.resume_workflow_role_ids)

    @api.depends('workflow_process_execution_ids')
    def _compute_execution_start_datetime(self):
        for stage in self:
            stage.execution_start_datetime = None
            start_datetimes = stage.workflow_process_execution_ids.mapped('execution_start_datetime')
            valid_datetimes_list = [d for d in start_datetimes if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                stage.execution_start_datetime = min(valid_datetimes_list)

    @api.depends('workflow_process_execution_ids')
    def _compute_execution_end_datetime(self):
        for stage in self:
            stage.execution_end_datetime = None
            end_datetimes = stage.workflow_process_execution_ids.mapped('execution_end_datetime')
            valid_datetimes_list = [d for d in end_datetimes if isinstance(d, datetime)]
            if len(valid_datetimes_list) > 0:
                stage.execution_end_datetime = min(valid_datetimes_list)

    @api.depends('inbound_workflow_process_stage_transition_ids', 'start_datetime')
    def _compute_expected_min_start_datetime(self):
        for stage in self:
            inbound_transition = stage.find_latest_inbound_stage_transition()
            if inbound_transition.exists():
                stage.expected_min_start_datetime = inbound_transition.from_workflow_process_stage_id.expected_min_end_datetime
            else:
                stage.expected_min_start_datetime = stage.start_datetime

    @api.depends('inbound_workflow_process_stage_transition_ids', 'start_datetime')
    def _compute_expected_max_start_datetime(self):
        for stage in self:
            stage.expected_max_start_datetime = None
            inbound_transition = stage.find_latest_inbound_stage_transition()
            if inbound_transition.exists():
                stage.expected_max_start_datetime = inbound_transition.from_workflow_process_stage_id.expected_max_end_datetime
            else:
                stage.expected_max_start_datetime = stage.start_datetime

    @api.depends('workflow_procedure_stage_id', 'start_datetime')
    def _compute_expected_min_end_datetime(self):
        for stage in self:
            stage.expected_min_end_datetime = None
            if stage.workflow_procedure_stage_id and stage.start_datetime:
                min_duration = stage.workflow_procedure_stage_id.get_min_duration_for_time_unit(stage.time_unit)
                delta = date_utils.get_timedelta_from_duration(min_duration, stage.time_unit)
                stage.expected_min_end_datetime = stage.start_datetime + delta

    @api.depends('workflow_procedure_stage_id', 'start_datetime')
    def _compute_expected_max_end_datetime(self):
        for stage in self:
            stage.expected_max_end_datetime = None
            if stage.workflow_procedure_stage_id and stage.start_datetime:
                max_duration = stage.workflow_procedure_stage_id.get_max_duration_for_time_unit(stage.time_unit)
                delta = date_utils.get_timedelta_from_duration(max_duration, stage.time_unit)
                stage.expected_max_end_datetime = stage.start_datetime + delta

    codename = fields.Char(string='Codename', required=True)
    name = fields.Char(string='Name', required=False, translate=True, store=True, compute="_compute_name")
    aborted = fields.Boolean(string='Aborted', default=False)
    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               related="workflow_process_id.root_workflow_process_id")
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
    cancel_action_name = fields.Char(required=False, string="Cancel Action Name",
                                     related="workflow_procedure_stage_id.cancel_action_name")
    cancel_action_title = fields.Char(string='Cancel Action Title', required=False, translate=True,
                                      related="workflow_procedure_stage_id.cancel_action_name")
    cancel_button_type = fields.Selection(string="Cancel Button Type", required=False,
                                          related="workflow_procedure_stage_id.cancel_button_type")
    cancel_workflow_state_id = fields.Many2one('workflow.state', required=False,
                                               string="Cancel State", readonly=True,
                                               related="workflow_procedure_stage_id.cancel_workflow_state_id")
    break_action_name = fields.Char(required=False, string="Break Action Name", translate=True,
                                    related="workflow_procedure_stage_id.break_action_name")
    break_action_title = fields.Char(string='Break Action Title', required=False, translate=True,
                                     related="workflow_procedure_stage_id.break_action_name")
    break_button_type = fields.Selection(string="Break Button Type", required=False,
                                         related="workflow_procedure_stage_id.break_button_type")
    break_workflow_state_id = fields.Many2one('workflow.state', required=False,
                                              string="Break State", readonly=True,
                                              related="workflow_procedure_stage_id.break_workflow_state_id")
    resume_action_name = fields.Char(required=False, string="Resume Action Name", translate=True,
                                     related="workflow_procedure_stage_id.resume_action_name")
    resume_action_title = fields.Char(string='Resume Action Title', required=False, translate=True,
                                      related="workflow_procedure_stage_id.resume_action_title")
    resume_button_type = fields.Selection(string="Resume Button Type", required=False,
                                          related="workflow_procedure_stage_id.resume_button_type")
    resume_workflow_state_id = fields.Many2one('workflow.state', required=False,
                                               string="Resume State", readonly=True,
                                               related="workflow_procedure_stage_id.resume_workflow_state_id")
    cancel_datetime = fields.Datetime(string="Cancel Datetime", copy=False, readonly=True, required=False)
    break_datetime = fields.Datetime(string="Break Datetime", copy=False, readonly=True, required=False)
    resume_datetime = fields.Datetime(string="Resume Datetime", copy=False, readonly=True, required=False)
    workflow_process_stage_duration_ids = fields.One2many('workflow.process.stage.duration',
                                                          'workflow_process_stage_id',
                                                          string="Process Stage Durations")
    workflow_process_ids = fields.One2many('workflow.process',
                                           'workflow_process_stage_id',
                                           string="Started Processes", readonly=True)
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_process_stage_id',
                                                     string="Process Executions")
    inbound_workflow_process_stage_transition_ids = fields.One2many('workflow.process.stage.transition',
                                                                    'to_workflow_process_stage_id',
                                                                    string="Inbound Process Stage Transitions")
    outbound_workflow_process_stage_transition_ids = fields.One2many('workflow.process.stage.transition',
                                                                     'from_workflow_process_stage_id',
                                                                     string="Outbound Process Stage Transitions")
    cancel_user_id = fields.Many2one('workflow.user', string='Cancelled By', required=False,
                                     readonly=True)
    break_user_id = fields.Many2one('workflow.user', string='Paused By', required=False,
                                    readonly=True)
    resume_user_id = fields.Many2one('workflow.user', string='Resumed By', required=False,
                                     readonly=True)
    workflow_process_stage_acl_ids = fields.One2many('workflow.process.stage.acl',
                                                     'workflow_process_stage_id',
                                                     string="Process Stage Access Control List")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cancelled = fields.Boolean(default=False, readonly=True, string="Cancelled")
    breaked = fields.Boolean(default=False, readonly=True, string="Paused")
    can_be_resumed = fields.Boolean(readonly=True, compute="_compute_can_be_resumed")
    resumed = fields.Boolean(default=False, readonly=True, string="Resumed")
    is_ended = fields.Boolean(string="Is ended", readonly=True, compute="_compute_is_ended")
    is_execution_started = fields.Boolean(string="Is Execution Started", readonly=True,
                                          compute="_compute_is_execution_started")
    is_execution_current = fields.Boolean(string="Is Execution Current", readonly=True,
                                          compute="_compute_is_execution_current")
    is_execution_complete = fields.Boolean(string="Is Execution Complete", readonly=True,
                                           compute="_compute_is_execution_complete")
    has_durations = fields.Boolean(readonly=True, compute="_compute_has_durations")
    has_started_processes = fields.Boolean(readonly=True, compute="_compute_has_started_processes")
    has_executions = fields.Boolean(readonly=True, compute="_compute_has_executions")
    has_inbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_inbound_transitions")
    has_outbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_outbound_transitions")
    # TEMPORAL FIELDS
    start_datetime = fields.Datetime(string="Start Datetime", copy=False, required=True)
    end_datetime = fields.Datetime(string="End Datetime", copy=False, required=False)
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
    execution_elapsed_time = fields.Float("Elapsed Execution Duration",
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
    is_protected = fields.Boolean(readonly=True, compute="_compute_is_protected")
    is_access_protected = fields.Boolean(readonly=True, compute="_compute_is_access_protected")
    is_cancel_protected = fields.Boolean(readonly=True, compute="_compute_is_cancel_protected")
    is_break_protected = fields.Boolean(readonly=True, compute="_compute_is_break_protected")
    is_resume_protected = fields.Boolean(readonly=True, compute="_compute_is_resume_protected")

    def find_latest_inbound_stage_transition(self):
        self.ensure_one()
        return self.env['workflow.process.stage.transition'].search(
            [('id', 'in', self.inbound_workflow_process_stage_transition_ids.ids)],
            order="create_date desc", limit=1
        )

    def get_execution_durations_for_time_unit(self, time_unit):
        self.ensure_one()
        return self.env['workflow.process.execution.duration'].search([
            '&', ('time_unit', '=', time_unit),
            ('workflow_process_execution_id', 'in', self.workflow_process_execution_ids.ids)
        ])

    def get_execution_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        execution_durations = self.get_execution_durations_for_time_unit(time_unit)
        if len(execution_durations) > 0:
            return sum(execution_durations.mapped('execution_duration'))
        else:
            return 0

    def get_scheduled_min_end_datetime_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.start_datetime and self.time_unit:
            procedure_stage_duration = self.workflow_procedure_stage_id.get_min_duration_for_time_unit(
                time_unit
            )
            delta = date_utils.get_timedelta_from_duration(procedure_stage_duration, time_unit)
            return self.start_datetime + delta
        else:
            return self.start_datetime

    def get_scheduled_max_end_datetime_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.start_datetime and self.time_unit:
            procedure_stage_duration = self.workflow_procedure_stage_id.get_max_duration_for_time_unit(
                time_unit
            )
            delta = date_utils.get_timedelta_from_duration(procedure_stage_duration, time_unit)
            return self.start_datetime + delta
        else:
            return self.start_datetime

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

    def get_exceeding_min_time_for_time_unit(self, time_unit):
        self.ensure_one()
        scheduled_min_end_datetime = self.get_scheduled_min_end_datetime_for_time_unit(time_unit)
        current = fields.Datetime.now()
        if self.end_datetime:
            ref_datetime = current if self.end_datetime >= current else self.end_datetime
        else:
            ref_datetime = current
        if ref_datetime > scheduled_min_end_datetime:
            diff = ref_datetime - scheduled_min_end_datetime
            return date_utils.get_time_total(diff, time_unit)
        else:
            return 0

    def get_exceeded_min_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.end_datetime:
            scheduled_min_end_datetime = self.get_scheduled_min_end_datetime_for_time_unit(time_unit)
            if self.end_datetime > scheduled_min_end_datetime:
                diff = self.end_datetime - scheduled_min_end_datetime
                return date_utils.get_time_total(diff, time_unit)
            else:
                return 0
        else:
            return 0

    def get_exceeding_max_time_for_time_unit(self, time_unit):
        self.ensure_one()
        scheduled_max_end_datetime = self.get_scheduled_max_end_datetime_for_time_unit(time_unit)
        current = fields.Datetime.now()
        if self.end_datetime:
            ref_datetime = current if self.end_datetime >= current else self.end_datetime
        else:
            ref_datetime = current
        if ref_datetime > scheduled_max_end_datetime:
            diff = ref_datetime - scheduled_max_end_datetime
            return date_utils.get_time_total(diff, time_unit)
        else:
            return 0

    def get_exceeded_max_time_for_time_unit(self, time_unit):
        self.ensure_one()
        if self.end_datetime:
            scheduled_max_end_datetime = self.get_scheduled_max_end_datetime_for_time_unit(time_unit)
            if self.end_datetime > scheduled_max_end_datetime:
                diff = self.end_datetime - scheduled_max_end_datetime
                return date_utils.get_time_total(diff, time_unit)
            else:
                return 0
        else:
            return 0

    def user_can_access(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_access_protected:
            return True
        else:
            return self.workflow_process_stage_acl_ids[0].user_can_access(workflow_user)

    def user_can_cancel(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_access_protected:
            return True
        else:
            if not self.user_can_access(workflow_user):
                return False
            return self.workflow_process_stage_acl_ids[0].user_can_cancel(workflow_user)

    def user_can_break(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_access_protected:
            return True
        else:
            if not self.user_can_access(workflow_user):
                return False
            return self.workflow_process_stage_acl_ids[0].user_can_break(workflow_user)

    def user_can_resume(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_access_protected:
            return True
        else:
            if not self.user_can_access(workflow_user):
                return False
            return self.workflow_process_stage_acl_ids[0].user_can_resume(workflow_user)

    def action_remaining_procedure_stages(self):
        pass

    def action_execution_status(self):
        pass

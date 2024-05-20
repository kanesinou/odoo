# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from ..utils import date_utils


class WorkflowProcessExecution(models.Model):
    _name = "workflow.process.execution"
    _description = "Workflow Process Execution"
    _sql_constraints = [
        ('stage_job_uniq', 'unique (workflow_process_stage_id,workflow_job_id)', 'The job must unique per workflow '
                                                                                 'process stage !')
    ]

    @api.constrains('execution_datetime', 'execution_start_datetime', 'execution_complete_datetime')
    def _check_datetime(self):
        for execution in self:
            if not execution.execution_datetime and not execution.execution_start_datetime:
                raise ValidationError(_("The execution start or exact datetime must be set !"))

    @api.constrains('execution_start_datetime', 'execution_complete_datetime')
    def _check_start_before_complete(self):
        for execution in self:
            if not execution.execution_start_datetime and execution.execution_complete_datetime:
                raise ValidationError(_("Execution must be started before complete ! Set either start or execution "
                                        "datetime !"))

    @api.constrains('workflow_user_id', 'workflow_user_role_id', 'substitute_workflow_user_ids')
    def _check_assignment_before_subs(self):
        for execution in self:
            if not execution.workflow_user_id and not execution.workflow_user_role_id:
                if len(execution.substitute_workflow_user_ids) > 0:
                    raise ValidationError(_("Set assignment(User or Role) Before substitutes !"))

    @api.depends('workflow_process_stage_id', 'workflow_job_id')
    def _compute_name(self):
        for execution in self:
            name_str = ''
            if execution.workflow_job_id:
                name_str = execution.workflow_job_id.name
            if execution.workflow_process_stage_id:
                name_str += "(%s)" % execution.workflow_process_stage_id.name
            execution.name = name_str

    @api.onchange('execution_datetime')
    def _onchange_execution_datetime(self):
        if self.execution_datetime:
            self.execution_start_datetime = self.execution_datetime
            self.execution_complete_datetime = self.execution_datetime

    @api.depends("workflow_process_stage_ids", "has_aborted_process_stages")
    def _compute_has_aborted_process_stages(self):
        for execution in self:
            if len(execution.workflow_process_stage_ids) > 0:
                execution.has_aborted_process_stages = True
            else:
                execution.has_aborted_process_stages = False

    @api.depends('workflow_process_stage_id')
    def _compute_root_workflow_process(self):
        for execution in self:
            execution.root_workflow_process_id = execution.workflow_process_stage_id.root_workflow_process_id.id

    @api.depends('workflow_job_id')
    def _compute_is_base_execution(self):
        for execution in self:
            execution.is_base_execution = False
            if not execution.parent_id:
                execution.is_base_execution = True

    @api.depends('workflow_job_id')
    def _compute_is_task_execution(self):
        for execution in self:
            execution.is_task_execution = False
            if execution.workflow_job_id.is_task:
                execution.is_task_execution = True

    @api.depends('workflow_job_id', 'is_base_execution', 'is_task_execution')
    def _compute_is_sub_execution(self):
        for execution in self:
            execution.is_sub_execution = not execution.is_base_execution and not execution.is_task_execution

    @api.depends('workflow_user_id', 'workflow_user_role_id')
    def _compute_is_assigned(self):
        for execution in self:
            execution.is_assigned = False
            if execution.workflow_user_id or execution.workflow_user_role_id:
                execution.is_assigned = True

    @api.depends('workflow_user_id', 'is_assigned')
    def _compute_is_user_assigned(self):
        for execution in self:
            execution.is_user_assigned = False
            if not execution.is_assigned:
                execution.is_user_assigned = False
            elif execution.workflow_user_id or len(execution.substitute_workflow_user_ids) > 0:
                execution.is_user_assigned = True

    @api.depends('workflow_user_role_id', 'is_assigned')
    def _compute_is_role_assigned(self):
        for execution in self:
            execution.is_role_assigned = False
            if not execution.is_assigned:
                execution.is_role_assigned = False
            elif execution.workflow_user_role_id:
                execution.is_role_assigned = True

    @api.depends('has_started', 'execution_datetime', 'is_complete')
    def _compute_is_executed(self):
        for execution in self:
            execution.is_executed = False
            if execution.execution_datetime or (execution.has_started and execution.is_complete):
                execution.is_executed = True

    @api.depends('execution_start_datetime')
    def _compute_has_started(self):
        for execution in self:
            if execution.is_task_execution:
                execution.has_started = True if execution.execution_start_datetime else False
            else:
                started_executions = execution.workflow_process_execution_ids.filtered(
                    lambda pe: pe.has_started
                )
                execution.has_started = True if started_executions.exists() else False

    @api.depends('execution_start_datetime', 'execution_complete_datetime')
    def _compute_is_execution_current(self):
        for execution in self:
            if execution.is_task_execution:
                if execution.execution_start_datetime and not execution.execution_complete_datetime:
                    execution.is_execution_current = True
                else:
                    execution.is_execution_current = False
            else:
                current_executions = execution.workflow_process_execution_ids.filtered(
                    lambda pe: pe.is_execution_current
                )
                execution.is_execution_current = True if current_executions.exists() else False

    @api.depends('execution_start_datetime', 'execution_complete_datetime', 'execution_datetime')
    def _compute_is_complete(self):
        for execution in self:
            if execution.is_task_execution:
                if execution.execution_start_datetime and execution.execution_complete_datetime:
                    execution.is_complete = True
                else:
                    execution.is_complete = False
            else:
                incomplete_executions = execution.workflow_process_execution_ids.filtered(
                    lambda pe: not pe.is_complete
                )
                execution.is_complete = False if incomplete_executions.exists() else False

    @api.depends('execution_start_datetime', 'execution_complete_datetime', 'time_unit')
    def _compute_effective_duration(self):
        for execution in self:
            execution.effective_duration = 0
            if execution.execution_start_datetime and execution.time_unit:
                if not execution.execution_complete_datetime :
                    diff = fields.Datetime.now() - execution.execution_start_datetime
                else:
                    diff = execution.execution_complete_datetime - execution.execution_start_datetime
                execution.effective_duration = date_utils.get_time_total(diff, execution.time_unit)

    @api.depends('execution_start_datetime', 'execution_complete_datetime', 'time_unit')
    def _compute_elapsed_duration(self):
        for execution in self:
            execution.elapsed_duration = 0
            if execution.execution_start_datetime and execution.time_unit:
                if not execution.execution_complete_datetime:
                    diff = fields.Datetime.now() - execution.execution_start_datetime
                else:
                    diff = execution.execution_complete_datetime - execution.execution_start_datetime
                execution.elapsed_duration = date_utils.get_time_total(diff, execution.time_unit)

    @api.depends('elapsed_duration', 'execution_start_datetime', 'execution_complete_datetime', 'time_unit', 'workflow_procedure_execution_id')
    def _compute_remaining_min_duration(self):
        for execution in self:
            execution_min_duration = execution.workflow_procedure_execution_id.get_execution_min_duration_for_time_unit(
                execution.time_unit
            )
            if execution.execution_complete_datetime or (execution_min_duration == 0):
                execution.remaining_min_duration = 0
            else:
                remaining_duration = execution_min_duration - execution.elapsed_duration
                execution.remaining_min_duration = max([0, remaining_duration])

    @api.depends('elapsed_duration', 'execution_start_datetime', 'execution_complete_datetime', 'time_unit', 'workflow_procedure_execution_id')
    def _compute_remaining_max_duration(self):
        for execution in self:
            execution_max_duration = execution.workflow_procedure_execution_id.get_execution_max_duration_for_time_unit(
                execution.time_unit
            )
            if execution.execution_complete_datetime or (execution_max_duration == 0):
                execution.remaining_max_duration = 0
            else:
                remaining_duration = execution_max_duration - execution.elapsed_duration
                execution.remaining_max_duration = max([0, remaining_duration])

    @api.depends('elapsed_duration', 'execution_start_datetime', 'execution_complete_datetime', 'time_unit', 'workflow_procedure_execution_id')
    def _compute_exceeding_min_duration(self):
        for execution in self:
            execution_min_duration = execution.workflow_procedure_execution_id.get_execution_min_duration_for_time_unit(
                execution.time_unit
            )
            if execution.execution_complete_datetime or (execution_min_duration == 0):
                execution.exceeding_min_duration = 0
            else:
                exceeding_duration = execution.elapsed_duration - execution_min_duration
                execution.exceeding_min_duration = max([0, exceeding_duration])

    @api.depends('elapsed_duration', 'execution_start_datetime', 'execution_complete_datetime', 'time_unit', 'workflow_procedure_execution_id')
    def _compute_exceeding_max_duration(self):
        for execution in self:
            execution_max_duration = execution.workflow_procedure_execution_id.get_execution_max_duration_for_time_unit(
                execution.time_unit
            )
            if execution.execution_complete_datetime or (execution_max_duration == 0):
                execution.exceeding_max_duration = 0
            else:
                exceeding_duration = execution.elapsed_duration - execution_max_duration
                execution.exceeding_max_duration = max([0, exceeding_duration])

    @api.depends('elapsed_duration', 'execution_start_datetime', 'execution_complete_datetime', 'time_unit', 'workflow_procedure_execution_id')
    def _compute_exceeded_min_duration(self):
        for execution in self:
            execution_min_duration = execution.workflow_procedure_execution_id.get_execution_min_duration_for_time_unit(
                execution.time_unit
            )
            if not execution.execution_complete_datetime or (execution_min_duration == 0):
                execution.exceeded_min_duration = 0
            else:
                exceeded_duration = execution.effective_duration - execution_min_duration
                execution.exceeded_min_duration = max([0, exceeded_duration])

    @api.depends('elapsed_duration', 'execution_start_datetime', 'execution_complete_datetime', 'time_unit', 'workflow_procedure_execution_id')
    def _compute_exceeded_max_duration(self):
        for execution in self:
            execution_max_duration = execution.workflow_procedure_execution_id.get_execution_max_duration_for_time_unit(
                execution.time_unit
            )
            if not execution.execution_complete_datetime or (execution_max_duration == 0):
                execution.exceeded_max_duration = 0
            else:
                exceeded_duration = execution.effective_duration - execution_max_duration
                execution.exceeded_max_duration = max([0, exceeded_duration])

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    mandatory = fields.Boolean(string='Mandatory', readonly=True,
                               related="workflow_procedure_execution_id.mandatory")
    execution_user_id = fields.Many2one('workflow.user', required=False, readonly=True,
                                        string="Executor")
    root_workflow_process_id = fields.Many2one('workflow.process', string="Root Process",
                                               required=False, readonly=True, store=True,
                                               compute="_compute_root_workflow_process")
    workflow_procedure_execution_id = fields.Many2one('workflow.procedure.execution',
                                                      string="Procedure Execution", required=True)
    workflow_process_stage_id = fields.Many2one('workflow.process.stage', string="Process Stage",
                                                required=True)
    workflow_job_id = fields.Many2one('workflow.job', string="Workflow Job", required=True,
                                      readonly=True,
                                      related="workflow_procedure_execution_id.workflow_job_id")
    workflow_user_id = fields.Many2one('workflow.user', string="Assigned User",
                                       required=False, readonly=True,
                                       related="workflow_procedure_execution_id.workflow_user_id")
    workflow_user_role_id = fields.Many2one('workflow.user.role', readonly=True,
                                            string="Assigned Role", required=False,
                                            related="workflow_procedure_execution_id.workflow_user_role_id")
    substitute_workflow_user_ids = fields.Many2many('workflow.user', string="Substitute Users",
                                                    relation="workflow_process_execution_subs_users",
                                                    related="workflow_procedure_execution_id.substitute_workflow_user_ids")
    parent_id = fields.Many2one('workflow.process.execution', required=False,
                                string="Parent Execution", domain=[('workflow_job_id.is_task', '=', False)])
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'parent_id', string="Sub Executions")
    workflow_process_stage_ids = fields.One2many('workflow.process.stage',
                                                 'workflow_process_execution_id',
                                                 string="Aborted Process Stages")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    has_aborted_process_stages = fields.Boolean(readonly=True,
                                                compute="_compute_has_aborted_process_stages")
    is_base_execution = fields.Boolean(readonly=True, compute="_compute_is_base_execution")
    is_sub_execution = fields.Boolean(readonly=True, compute="_compute_is_sub_execution")
    is_task_execution = fields.Boolean(readonly=True, compute="_compute_is_task_execution")
    is_assigned = fields.Boolean(readonly=True, compute="_compute_is_assigned")
    is_role_assigned = fields.Boolean(readonly=True, compute="_compute_is_role_assigned")
    is_user_assigned = fields.Boolean(readonly=True, compute="_compute_is_user_assigned")
    is_executed = fields.Boolean(readonly=True, compute="_compute_is_executed")
    has_started = fields.Boolean(readonly=True, compute="_compute_has_started")
    is_complete = fields.Boolean(readonly=True, compute="_compute_is_complete")
    is_execution_current = fields.Boolean(readonly=True, compute="_compute_is_execution_current")
    # TEMPORAL FIELDS
    execution_datetime = fields.Datetime(string="Execution Datetime", copy=False, required=False)
    execution_start_datetime = fields.Datetime(string="Execution Start Datetime", copy=False,
                                               required=False)
    execution_complete_datetime = fields.Datetime(string="Execution Complete Datetime", copy=False,
                                                  required=False)
    time_unit = fields.Selection(
        selection=[
            ("minute", "Minute"),
            ("hour", "Hour"),
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month"),
            ("quarter", "Quarter"),
            ("year", "Year")
        ], string="Time Unit", required=False, default='hour'
    )
    elapsed_duration = fields.Float(string="Elapsed Duration", compute="_compute_elapsed_duration",
                                    readonly=True)
    effective_duration = fields.Float(string="Effective Duration", readonly=True,
                                      compute="_compute_effective_duration")
    remaining_min_duration = fields.Float(string="Remaining Minimum Duration", readonly=True,
                                          compute="_compute_remaining_min_duration")
    remaining_max_duration = fields.Float(string="Remaining Maximum Duration", readonly=True,
                                          compute="_compute_remaining_max_duration")
    exceeding_min_duration = fields.Float(string="Exceeding Minimum Duration", readonly=True,
                                          compute="_compute_exceeding_min_duration")
    exceeding_max_duration = fields.Float(string="Exceeding Maximum Duration", readonly=True,
                                          compute="_compute_exceeding_max_duration")
    exceeded_min_duration = fields.Float(string="Exceeded Minimum Duration", readonly=True,
                                         compute="_compute_exceeded_min_duration")
    exceeded_max_duration = fields.Float(string="Exceeded Maximum Duration", readonly=True,
                                         compute="_compute_exceeded_max_duration")

    def user_can_execute(self, workflow_user):
        self.ensure_one()
        if self.env.is_superuser() or self.env.is_admin() or self.env.is_system():
            return True
        if self.workflow_user_id == workflow_user.id:
            return True
        if workflow_user.id in self.substitute_workflow_user_ids.mapped('id'):
            return True
        if self.env.user.has_group(self.workflow_user_role_id.name):
            return True
        return False

    def get_execution_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        return self.env['workflow.process.execution.duration'].search([
            '&', ('time_unit', '=', time_unit), ('workflow_process_execution_id', '=', self.id)
        ])

    def get_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        execution_duration = self.get_execution_duration_for_time_unit(time_unit)
        if execution_duration.exists():
            return execution_duration.duration
        return 0

    def action_configure_execution(self):
        wizard = self.env['workflow.process.execution.wizard'].create({
            'workflow_process_execution_id': self.id
        })
        return {
            'name': _('Configure Process Execution'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.process.execution.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new'
        }

    def action_execution_status(self):
        pass

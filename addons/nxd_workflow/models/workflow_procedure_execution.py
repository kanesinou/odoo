# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError


class WorkflowProcedureExecution(models.Model):
    _name = "workflow.procedure.execution"
    _description = "Workflow Procedure Execution"
    _sql_constraints = [
        ('stage_job_uniq', 'unique (workflow_procedure_stage_id,workflow_job_id)', 'The job must unique per workflow '
                                                                                   'procedure stage !')
    ]

    @api.constrains('workflow_user_id', 'workflow_user_role_id', 'substitute_workflow_user_ids')
    def _check_assignment_before_subs(self):
        for execution in self:
            if not execution.workflow_user_id and not execution.workflow_user_role_id:
                if len(execution.substitute_workflow_user_ids) > 0:
                    raise ValidationError(_("Set assignment(User or Role) Before substitutes !"))

    @api.constrains('workflow_job_id', 'workflow_procedure_execution_ids')
    def _check_non_subdivide_task_execution(self):
        for execution in self:
            if execution.workflow_job_id.is_task and len(execution.workflow_procedure_execution_ids) > 0:
                raise ValidationError(_("Execution of workflow job cannot be divided in sub executions !"))

    @api.depends('workflow_procedure_stage_id', 'workflow_job_id')
    def _compute_name(self):
        for execution in self:
            name_str = ''
            if execution.workflow_job_id:
                name_str = execution.workflow_job_id.name
            if execution.workflow_procedure_stage_id:
                name_str += "(%s)" % execution.workflow_procedure_stage_id.name
            execution.name = name_str

    @api.depends('workflow_procedure_stage_id')
    def _compute_root_workflow_procedure(self):
        for execution in self:
            execution.root_workflow_procedure_id = execution.workflow_procedure_stage_id.root_workflow_procedure_id.id

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

    @api.depends('time_unit', 'workflow_procedure_execution_duration_ids')
    def _compute_min_duration(self):
        for execution in self:
            execution.min_duration = 0
            if execution.time_unit:
                durations = execution.workflow_procedure_execution_duration_ids.filtered(
                    lambda d: d.time_unit == execution.time_unit
                )
                if durations.exists():
                    execution.min_duration = durations[0].min_duration

    @api.depends('time_unit', 'workflow_procedure_execution_duration_ids')
    def _compute_max_duration(self):
        for execution in self:
            execution.max_duration = 0
            if execution.time_unit:
                durations = execution.workflow_procedure_execution_duration_ids.filtered(
                    lambda d: d.time_unit == execution.time_unit
                )
                if durations.exists():
                    execution.max_duration = durations[0].max_duration

    @api.depends('time_unit', 'workflow_procedure_execution_ids')
    def _compute_estimated_min_duration(self):
        for execution in self:
            execution.estimated_min_duration = execution.min_duration
            if execution.time_unit and not execution.is_task_execution:
                durations = execution.workflow_procedure_execution_ids.mapped('min_duration')
                execution.estimated_min_duration = sum([0] + durations)

    @api.depends('time_unit', 'workflow_procedure_execution_ids')
    def _compute_estimated_max_duration(self):
        for execution in self:
            execution.estimated_max_duration = execution.max_duration
            if execution.time_unit and not execution.is_task_execution:
                durations = execution.workflow_procedure_execution_ids.mapped('max_duration')
                execution.estimated_max_duration = sum([0] + durations)

    @api.depends('estimated_min_duration', 'estimated_max_duration')
    def _compute_estimated_duration_range(self):
        for execution in self:
            execution.estimated_duration_range = execution.estimated_max_duration - execution.estimated_min_duration

    @api.depends('min_duration', 'max_duration')
    def _compute_duration_range(self):
        for execution in self:
            execution.duration_range = execution.max_duration - execution.min_duration

    @api.depends('workflow_procedure_execution_ids')
    def _compute_has_sub_executions(self):
        for execution in self:
            execution.has_sub_executions = False
            if len(execution.workflow_procedure_execution_ids) > 0:
                execution.has_sub_executions = True

    @api.depends('workflow_procedure_execution_ids')
    def _compute_sub_executions_count(self):
        for execution in self:
            execution.sub_executions_count = len(execution.workflow_procedure_execution_ids)

    @api.depends('substitute_workflow_user_ids')
    def _compute_has_substitute_users(self):
        for execution in self:
            execution.has_substitute_users = False
            if len(execution.substitute_workflow_user_ids) > 0:
                execution.has_substitute_users = True

    @api.depends('substitute_workflow_user_ids')
    def _compute_substitute_users_count(self):
        for execution in self:
            execution.substitute_users_count = len(execution.substitute_workflow_user_ids)

    @api.depends('workflow_procedure_execution_duration_ids')
    def _compute_has_durations(self):
        for execution in self:
            execution.has_durations = False
            if len(execution.workflow_procedure_execution_duration_ids) > 0:
                execution.has_durations = True

    @api.depends('workflow_procedure_execution_duration_ids')
    def _compute_durations_count(self):
        for execution in self:
            execution.durations_count = len(execution.workflow_procedure_execution_duration_ids)

    @api.depends('workflow_process_execution_ids')
    def _compute_has_process_executions(self):
        for execution in self:
            execution.has_process_executions = False
            if len(execution.workflow_process_execution_ids) > 0:
                execution.has_process_executions = True

    @api.depends('workflow_process_execution_ids')
    def _compute_process_executions_count(self):
        for execution in self:
            execution.process_executions_count = len(execution.workflow_process_execution_ids)

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    mandatory = fields.Boolean(string='Mandatory', default=False, readonly=True)
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage',
                                                  string="Procedure Stage", required=True)
    workflow_job_id = fields.Many2one('workflow.job', required=True,
                                      string="Workflow Job")
    workflow_user_id = fields.Many2one('workflow.user', string="Assigned User",
                                       required=False)
    workflow_user_role_id = fields.Many2one('workflow.user.role', required=False,
                                            string="Assigned Role")
    substitute_workflow_user_ids = fields.Many2many('workflow.user', string="Substitute Users",
                                                    relation="workflow_procedure_execution_subs_users")
    parent_id = fields.Many2one('workflow.procedure.execution', required=False,
                                string="Parent Execution", domain=[('workflow_job_id.is_task', '=', False)])
    workflow_procedure_execution_ids = fields.One2many('workflow.procedure.execution',
                                                       'parent_id', string="Sub Executions")
    workflow_procedure_execution_duration_ids = fields.One2many('workflow.procedure.execution.duration',
                                                                'workflow_procedure_execution_id',
                                                                string="Execution Durations")
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_procedure_execution_id',
                                                     string="Process Executions")
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
        string="Time Unit", required=True, default='hour'
    )
    min_duration = fields.Float(string="Minimum Duration", default=0, digits=(11, 5),
                                compute="_compute_min_duration")
    max_duration = fields.Float(string="Maximum Duration", default=0, digits=(11, 5),
                                compute="_compute_max_duration")
    duration_range = fields.Float(string="Duration Range", readonly=True,
                                  compute="_compute_duration_range", digits=(11, 5))
    estimated_min_duration = fields.Float(string="Estimated Minimum Duration", default=0, digits=(11, 5),
                                          compute="_compute_estimated_min_duration")
    estimated_max_duration = fields.Float(string="Estimated Maximum Duration", default=0, digits=(11, 5),
                                          compute="_compute_estimated_max_duration")
    estimated_duration_range = fields.Float(string="Estimated Duration Range", readonly=True, digits=(11, 5),
                                            compute="_compute_estimated_duration_range")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    is_base_execution = fields.Boolean(readonly=True, compute="_compute_is_base_execution")
    is_sub_execution = fields.Boolean(readonly=True, compute="_compute_is_sub_execution")
    is_task_execution = fields.Boolean(readonly=True, compute="_compute_is_task_execution")
    is_assigned = fields.Boolean(readonly=True, compute="_compute_is_assigned")
    is_role_assigned = fields.Boolean(readonly=True, compute="_compute_is_role_assigned")
    is_user_assigned = fields.Boolean(readonly=True, compute="_compute_is_user_assigned")
    has_sub_executions = fields.Boolean(readonly=True, compute="_compute_has_sub_executions")
    sub_executions_count = fields.Integer(readonly=True, compute="_compute_sub_executions_count")
    has_substitute_users = fields.Boolean(readonly=True, compute="_compute_has_substitute_users")
    substitute_users_count = fields.Integer(readonly=True, compute="_compute_substitute_users_count")
    has_durations = fields.Boolean(readonly=True, compute="_compute_has_durations")
    durations_count = fields.Integer(readonly=True, compute="_compute_durations_count")
    has_process_executions = fields.Boolean(readonly=True, compute="_compute_has_process_executions")
    process_executions_count = fields.Integer(readonly=True, compute="_compute_process_executions_count")

    def user_can_execute(self, workflow_user):
        self.ensure_one()
        if self.env.is_superuser() or self.env.is_admin() or self.env.is_system():
            return True
        if self.workflow_user_id == workflow_user.id:
            return True
        if workflow_user.id in self.substitute_workflow_user_ids.mapped('id'):
            return True
        if workflow_user.res_users_id.has_group(self.workflow_user_role_id.name):
            return True
        return False

    def get_corresponding_process_execution_data(self, process_stage_id):
        self.ensure_one()
        data = {
            'workflow_procedure_execution_id': self.id, 'workflow_process_stage_id': process_stage_id
        }
        for sub_execution in self.workflow_procedure_execution_ids:
            sub_execution_process_data = sub_execution.get_corresponding_process_execution_data(
                process_stage_id
            )
            if not data.get('workflow_process_execution_ids', False):
                data['workflow_process_execution_ids'] = [Command.create(sub_execution_process_data)]
            else:
                data['workflow_process_execution_ids'].append(Command.create(sub_execution_process_data))
        for execution_duration in self.workflow_procedure_execution_duration_ids:
            process_execution_duration = execution_duration.get_corresponding_process_execution_duration_data(
                process_stage_id
            )
            if not data.get('workflow_process_execution_duration_ids', False):
                data['workflow_process_execution_duration_ids'] = [Command.create(process_execution_duration)]
            else:
                data['workflow_process_execution_duration_ids'].append(Command.create(process_execution_duration))
        return data

    def get_sub_task_execution_ids(self):
        self.ensure_one()
        sub_execution_ids = self.workflow_procedure_execution_ids.filtered(
            lambda e: e.is_task_execution
        ).mapped('id')
        for sub_exec in self.workflow_procedure_execution_ids.filtered(
            lambda e: not e.is_task_execution
        ):
            sub_execution_ids.extend(sub_exec.get_sub_task_execution_ids())
        return sub_execution_ids

    def get_sub_task_execution_durations_for_time_unit(self, time_unit):
        self.ensure_one()
        return self.env['workflow.procedure.execution.duration'].search([
            '&', ('time_unit', '=', time_unit),
            ('workflow_procedure_execution_id', 'in', self.get_sub_task_execution_ids())
        ])

    def get_execution_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        return self.env['workflow.procedure.execution.duration'].search([
            '&', ('workflow_procedure_execution_id', '=', self.id),
            ('time_unit', '=', time_unit)
        ], limit=1)

    def get_execution_min_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        execution_duration = self.get_execution_duration_for_time_unit(time_unit)
        if execution_duration.exists():
            return execution_duration.min_duration
        return 0

    def get_execution_max_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        execution_duration = self.get_execution_duration_for_time_unit(time_unit)
        if execution_duration.exists():
            return execution_duration.max_duration
        return 0

    def action_configure_duration(self):
        wizard = self.env['workflow.procedure.execution.duration.wizard'].create({
            'workflow_procedure_execution_id': self.id
        })
        return {
            'name': _('Configure Procedure Execution Duration'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.procedure.execution.duration.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new'
        }

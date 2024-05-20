# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcedureExecutionDuration(models.Model):
    _name = "workflow.procedure.execution.duration"
    _description = "Workflow Procedure Execution Duration"
    _sql_constraints = [
        ('execution_time_unit_uniq', 'unique (workflow_procedure_execution_id,time_unit)', 'The time unit must be '
                                                                                           'unique per workflow '
                                                                                           'procedure execution !')
    ]

    @api.constrains('min_duration')
    def _check_pos_min_duration(self):
        for duration in self:
            if duration.min_duration < 0:
                raise ValidationError(_("The minimum duration must be positive or null !"))

    @api.constrains('max_duration')
    def _check_pos_max_duration(self):
        for duration in self:
            if duration.max_duration < 0:
                raise ValidationError(_("The maximum duration must be positive or null !"))

    @api.constrains('min_duration', 'max_duration')
    def _check_range_duration(self):
        for duration in self:
            if duration.min_duration > duration.max_duration:
                raise ValidationError(_("The minimum duration must be less than or equal to the maximum !"))

    @api.depends('min_duration', 'max_duration')
    def _compute_duration_range(self):
        for duration in self:
            duration.duration_range = duration.max_duration - duration.min_duration

    @api.depends('workflow_procedure_execution_id')
    def _compute_name(self):
        for duration in self:
            duration.name = duration.workflow_procedure_execution_id.name + ' Duration (%s)' % duration.time_unit

    name = fields.Char(string="Name", compute="_compute_name")
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure",
                                                 related="workflow_procedure_execution_id.root_workflow_procedure_id")
    workflow_procedure_execution_id = fields.Many2one('workflow.procedure.execution',
                                                      string="Procedure Execution", required=True)
    workflow_process_execution_duration_ids = fields.One2many('workflow.process.execution.duration',
                                                              'workflow_procedure_execution_duration_id',
                                                              string="Process Execution Durations")
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
    min_duration = fields.Float(string="Minimum Duration", default=0, digits=(11, 5))
    max_duration = fields.Float(string="Maximum Duration", default=0, digits=(11, 5))
    duration_range = fields.Float(string="Duration Range", readonly=True,
                                  compute="_compute_duration_range", digits=(11, 5))
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    def get_corresponding_process_execution_duration_data(self, workflowable_record):
        self.ensure_one()
        data = {
            'min_duration': self.min_duration, 'max_duration': self.max_duration,
            'workflow_procedure_execution_duration_id': self.id
        }
        return data

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcedureDuration(models.Model):
    _name = "workflow.procedure.duration"
    _description = "Workflow Procedure Duration"
    _sql_constraints = [
        ('procedure_time_unit_uniq', 'unique (workflow_procedure_id,time_unit)', 'The time unit must be unique per '
                                                                                 'workflow procedure !')
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

    @api.depends('workflow_procedure_id')
    def _compute_root_workflow_procedure(self):
        for duration in self:
            duration.root_workflow_procedure_id = duration.workflow_procedure_id.root_workflow_procedure_id.id

    @api.depends('workflow_procedure_id')
    def _compute_name(self):
        for duration in self:
            duration.name = duration.workflow_procedure_id.name + ' Duration (%s)' % duration.time_unit

    @api.depends('min_duration', 'max_duration')
    def _compute_duration_range(self):
        for duration in self:
            duration.duration_range = duration.max_duration - duration.min_duration

    name = fields.Char(string="Name", compute="_compute_name")
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    workflow_procedure_id = fields.Many2one('workflow.procedure',
                                            string="Procedure", required=True)
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
        string="Time Unit", required=True, default="hour"
    )
    min_duration = fields.Float(string="Minimum Duration", default=0, digits=(11, 5))
    max_duration = fields.Float(string="Maximum Duration", default=0, digits=(11, 5))
    duration_range = fields.Float(string="Duration Range", readonly=True, compute="_compute_duration_range",
                                  digits=(11, 5))
    workflow_process_duration_ids = fields.One2many('workflow.process.duration',
                                                    'workflow_procedure_duration_id',
                                                    string="Process Durations")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    def get_stage_durations(self):
        self.ensure_one()
        return self.env['workflow.procedure.stage.duration'].search([
            '&', ('time_unit', '=', self.time_unit),
            ('workflow_procedure_stage_id.workflow_procedure_id', '=', self.workflow_procedure_id.id)
        ])

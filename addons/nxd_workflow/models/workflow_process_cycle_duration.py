# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcessCycleDuration(models.Model):
    _name = "workflow.process.cycle.duration"
    _description = "Workflow Process cycle Duration"

    @api.constrains('duration')
    def _check_pos_duration(self):
        for duration in self:
            if duration.duration < 0:
                raise ValidationError(_("The duration must be positive or null !"))

    @api.constrains('execution_duration')
    def _check_pos_execution_duration(self):
        for duration in self:
            if duration.execution_duration < 0:
                raise ValidationError(_("The execution duration must be positive or null !"))

    workflow_process_cycle_id = fields.Many2one('workflow.process.cycle', required=True,
                                                string="Process Cycle")
    workflow_procedure_cycle_duration_id = fields.Many2one('workflow.procedure.cycle.duration',
                                                           string="Procedure Cycle Duration", required=True)
    time_unit = fields.Selection(string="Time Unit", required=True,
                                 related="workflow_procedure_cycle_duration_id.time_unit")
    duration = fields.Float(string="Duration", required=True, readonly=True, digits=(11, 5))
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

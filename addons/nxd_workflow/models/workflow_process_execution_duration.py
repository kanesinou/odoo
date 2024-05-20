# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcessExecutionDuration(models.Model):
    _name = "workflow.process.execution.duration"
    _description = "Workflow Process Execution Duration"

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

    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Procedure",
                                               related="workflow_process_execution_id.root_workflow_process_id")
    workflow_process_execution_id = fields.Many2one('workflow.process.execution',
                                                    string="Process Execution", required=True)
    workflow_procedure_execution_duration_id = fields.Many2one('workflow.procedure.execution.duration',
                                                               string="Procedure Execution Duration",
                                                               required=True)
    time_unit = fields.Selection(string="Time Unit", required=True,
                                 related="workflow_procedure_execution_duration_id.time_unit")
    duration = fields.Float(string="Duration", default=0, digits=(11, 5))
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

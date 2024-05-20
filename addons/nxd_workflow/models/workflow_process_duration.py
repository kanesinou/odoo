# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcessDuration(models.Model):
    _name = "workflow.process.duration"
    _description = "Workflow Process Duration"

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

    @api.depends('workflow_process_id')
    def _compute_root_workflow_process(self):
        for duration in self:
            duration.root_workflow_process_id = duration.workflow_process_id.root_workflow_process_id.id

    @api.depends('workflow_process_id')
    def _compute_name(self):
        for duration in self:
            duration.name = duration.workflow_process_id.name + ' Duration'

    name = fields.Char(string="Name", compute="_compute_name")
    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               compute="_compute_root_workflow_process")
    workflow_process_id = fields.Many2one('workflow.process', string="Process",
                                          required=True)
    workflow_procedure_duration_id = fields.Many2one('workflow.procedure.duration', required=True,
                                                     string="Procedure Duration")
    time_unit = fields.Selection(string="Time Unit", required=True,
                            related="workflow_procedure_duration_id.time_unit")
    duration = fields.Float(string="Duration", default=0, readonly=True, digits=(11, 5))
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

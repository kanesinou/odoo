# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcessStageDuration(models.Model):
    _name = "workflow.process.stage.duration"
    _description = "Workflow Process stage Duration"

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

    @api.depends('workflow_process_stage_id')
    def _compute_root_workflow_process(self):
        for stage in self:
            stage.root_workflow_process_id = stage.workflow_process_stage_id.root_workflow_process_id.id

    @api.depends('workflow_process_stage_id')
    def _compute_name(self):
        for duration in self:
            duration.name = duration.workflow_process_stage_id.name + ' Duration'

    name = fields.Char(string="Name", compute="_compute_name")
    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               compute="_compute_root_workflow_process")
    workflow_process_stage_id = fields.Many2one('workflow.process.stage',
                                                string="Process Stage", required=True)
    workflow_procedure_cycle_duration_id = fields.Many2one('workflow.procedure.cycle.duration',
                                                           required=True, string="Procedure Cycle Duration")
    time_unit = fields.Selection(string="Time Unit", required=True,
                                 related="workflow_procedure_cycle_duration_id.time_unit")
    duration = fields.Float(string="Duration", default=0, readonly=True, digits=(11, 5))
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

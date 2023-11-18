# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcessStageDuration(models.Model):
    _name = "workflow.process.stage.duration"
    _description = "Workflow Process stage Duration"

    @api.depends('workflow_process_stage_id')
    def _compute_root_workflow_process(self):
        for stage in self:
            stage.root_workflow_process_id = stage.workflow_process_stage_id.root_workflow_process_id.id

    root_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                               readonly=True, string="Root Process", store=True,
                                               compute="_compute_root_workflow_process")
    workflow_process_stage_id = fields.Many2one('workflow.process.stage',
                                                string="Process Stage", required=True)
    unit = fields.Selection(
        selection=[
            ("minute", "Minute"),
            ("hour", "Hour"),
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month")
        ],
        string="Unit", required=True
    )
    duration = fields.Float(string="Duration", default=0)
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

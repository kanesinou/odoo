# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcessCycleDuration(models.Model):
    _name = "workflow.process.cycle.duration"
    _description = "Workflow Process cycle Duration"

    workflow_process_cycle_id = fields.Many2one('workflow.process.cycle',
                                                string="Process Cycle", required=True)
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

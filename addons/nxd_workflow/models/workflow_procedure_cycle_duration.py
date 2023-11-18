# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcedureCycleDuration(models.Model):
    _name = "workflow.procedure.cycle.duration"
    _description = "Workflow Procedure Cycle Duration"

    workflow_procedure_cycle_id = fields.Many2one('workflow.procedure.cycle',
                                                  string="Procedure",
                                                  required=True)
    scheduled = fields.Boolean(string="Scheduled", default=True)
    minimum = fields.Boolean(string="Minimum", default=False)
    maximum = fields.Boolean(string="Maximum", default=False)
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
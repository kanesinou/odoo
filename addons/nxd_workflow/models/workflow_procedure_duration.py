# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcedureDuration(models.Model):
    _name = "workflow.procedure.duration"
    _description = "Workflow Procedure Duration"

    @api.depends('workflow_procedure_id')
    def _compute_root_workflow_procedure(self):
        for duration in self:
            duration.root_workflow_procedure_id = duration.workflow_procedure_id.root_workflow_procedure_id.id

    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    workflow_procedure_id = fields.Many2one('workflow.procedure',
                                            string="Procedure", required=True)
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

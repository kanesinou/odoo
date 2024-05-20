# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowState(models.Model):
    _name = "workflow.state"
    _description = "Workflow State"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow state must be unique '
                                                                  'per company !')
    ]

    @api.depends('workflow_stage_ids')
    def _compute_has_workflow_stages(self):
        for state in self:
            state.has_workflow_stages = len(state.workflow_stage_ids) > 0

    @api.depends('workflow_stage_ids')
    def _compute_workflow_stages_count(self):
        for state in self:
            state.workflow_stages_count = len(state.workflow_stage_ids)

    @api.depends('workflow_procedure_stage_ids')
    def _compute_has_procedure_stages(self):
        for state in self:
            state.has_procedure_stages = len(state.workflow_procedure_stage_ids) > 0

    @api.depends('workflow_procedure_stage_ids')
    def _compute_procedure_stages_count(self):
        for state in self:
            state.procedure_stages_count = len(state.workflow_procedure_stage_ids)

    @api.depends('workflow_process_stage_ids')
    def _compute_has_process_stages(self):
        for state in self:
            state.has_process_stages = len(state.workflow_process_stage_ids) > 0

    @api.depends('workflow_process_stage_ids')
    def _compute_process_stages_count(self):
        for state in self:
            state.process_stages_count = len(state.workflow_process_stage_ids)

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    decoration_type = fields.Selection(
        selection=[
            ("info", "Info"),
            ("bf", "Bold Face"),
            ("it", "Italic"),
            ("success", "Success"),
            ("primary", "Primary"),
            ("secondary", "Secondary"),
            ("warning", "Warning"),
            ("danger", "Danger"),
            ("muted", "Muted")
        ],
        string="Decoration", required=False, default="info"
    )
    workflow_stage_ids = fields.One2many('workflow.stage',
                                         'workflow_state_id', string="Workflow Stages")
    workflow_procedure_stage_ids = fields.One2many('workflow.procedure.stage',
                                                   'workflow_state_id',
                                                   string="Procedure Stages")
    workflow_process_stage_ids = fields.One2many('workflow.process.stage',
                                                 'workflow_state_id',
                                                 string="Process Stages")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    has_workflow_stages = fields.Boolean(readonly=True, compute="_compute_has_workflow_stages")
    workflow_stages_count = fields.Boolean(readonly=True, compute="_compute_workflow_stages_count")
    has_procedure_stages = fields.Boolean(readonly=True, compute="_compute_has_procedure_stages")
    procedure_stages_count = fields.Boolean(readonly=True, compute="_compute_procedure_stages_count")
    has_process_stages = fields.Boolean(readonly=True, compute="_compute_has_process_stages")
    process_stages_count = fields.Boolean(readonly=True, compute="_compute_process_stages_count")

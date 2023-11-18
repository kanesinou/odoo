# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowStage(models.Model):
    _name = "workflow.stage"
    _description = "Workflow Stage"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,workflow_id,company_id)', 'The codename must be unique per '
                                                                              'workflow and per company !')
    ]

    @api.depends('workflow_id')
    def _compute_root_workflow(self):
        for stage in self:
            stage.root_workflow_id = stage.workflow_id.root_workflow_id.id

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    root_workflow_id = fields.Many2one('workflow', required=False, string="Root Workflow",
                                       readonly=True, store=True, compute="_compute_root_workflow")
    workflow_id = fields.Many2one('workflow', string='Workflow', required=True,
                                  ondelete='cascade')
    workflow_state_id = fields.Many2one('workflow.state', string='State', required=True)
    workflow_procedure_stage_ids = fields.One2many('workflow.procedure.stage',
                                                   'workflow_stage_id',
                                                   string="Procedure Stages")
    inbound_workflow_stage_transition_ids = fields.One2many('workflow.stage.transition',
                                                            'to_workflow_stage_id',
                                                            string="Inbound Stage Transitions")
    outbound_workflow_stage_transition_ids = fields.One2many('workflow.stage.transition',
                                                             'from_workflow_stage_id',
                                                             string="Outbound Stage Transitions")
    required_workflow_job_ids = fields.Many2many('workflow.job',
                                                 'workflow_stage_required_job',
                                                 string="Required Jobs")
    optional_workflow_job_ids = fields.Many2many('workflow.job',
                                                 'workflow_stage_optional_job',
                                                 string="Optional Jobs")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    def get_workflow_procedure_stages_by_id(self, stage_id):
        return self.workflow_procedure_stage_ids.filtered(lambda s: s.id == stage_id)

    def get_workflow_procedure_stage_by_id(self, stage_id):
        records = self.get_workflow_procedure_stages_by_id(stage_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_stages_by_ids(self, stage_ids):
        return self.workflow_procedure_stage_ids.filtered(lambda s: s.id in stage_ids)

    def get_inbound_workflow_stage_transitions_by_id(self, transition_id):
        return self.inbound_workflow_stage_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_inbound_workflow_stage_transition_by_id(self, transition_id):
        records = self.get_inbound_workflow_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_inbound_workflow_stage_transitions_by_ids(self, transition_ids):
        return self.inbound_workflow_stage_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_outbound_workflow_stage_transitions_by_id(self, transition_id):
        return self.outbound_workflow_stage_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_outbound_workflow_stage_transition_by_id(self, transition_id):
        records = self.get_outbound_workflow_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_outbound_workflow_stage_transitions_by_ids(self, transition_ids):
        return self.outbound_workflow_stage_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_required_workflow_jobs_by_id(self, job_id):
        return self.required_workflow_job_ids.filtered(lambda j: j.id == job_id)

    def get_required_workflow_job_by_id(self, job_id):
        records = self.get_required_workflow_jobs_by_id(job_id)
        if len(records) > 0:
            return records[0]
        return

    def get_required_workflow_jobs_by_ids(self, job_ids):
        return self.required_workflow_job_ids.filtered(lambda j: j.id in job_ids)

    def get_optional_workflow_jobs_by_id(self, job_id):
        return self.optional_workflow_job_ids.filtered(lambda j: j.id == job_id)

    def get_optional_workflow_job_by_id(self, job_id):
        records = self.get_optional_workflow_jobs_by_id(job_id)
        if len(records) > 0:
            return records[0]
        return

    def get_optional_workflow_jobs_by_ids(self, job_ids):
        return self.optional_workflow_job_ids.filtered(lambda j: j.id in job_ids)

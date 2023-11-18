# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcedureStage(models.Model):
    _name = "workflow.procedure.stage"
    _description = "Workflow Procedure Stage"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,workflow_procedure_id,company_id)', 'The codename must be unique '
                                                                                        'per workflow procedure and '
                                                                                        'per company !')
    ]

    @api.depends('workflow_procedure_id')
    def _compute_root_workflow_procedure(self):
        for stage in self:
            stage.root_workflow_procedure_id = stage.workflow_procedure_id.root_workflow_procedure_id.id

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    workflow_procedure_id = fields.Many2one('workflow.procedure', required=True,
                                            string="Procedure")
    workflow_stage_id = fields.Many2one('workflow.stage', required=True,
                                        string="Workflow Stage")
    workflow_state_id = fields.Many2one('workflow.state', string='State', required=False,
                                        store=True, related="workflow_stage_id.workflow_state_id")
    workflow_procedure_stage_duration_ids = fields.One2many('workflow.procedure.stage.duration',
                                                            'workflow_procedure_stage_id')
    workflow_procedure_ids = fields.One2many('workflow.procedure',
                                             'workflow_procedure_stage_id',
                                             string="Started Procedures")
    workflow_process_stage_ids = fields.One2many('workflow.process.stage',
                                                 'workflow_procedure_stage_id',
                                                 string="Process Stages")
    inbound_workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                                      'to_workflow_procedure_stage_id',
                                                                      string="Inbound Procedure Stage Transitions")
    outbound_workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                                       'from_workflow_procedure_stage_id',
                                                                       string="Outbound Procedure Stage Transitions")
    workflow_procedure_execution_ids = fields.One2many('workflow.procedure.execution',
                                                       'workflow_procedure_stage_id',
                                                       string="Procedure Executions")
    allowed_workflow_user_ids = fields.Many2many('workflow.user',
                                                 'workflow_procedure_stage_allowed_user',
                                                 string="Allowed Users")
    allowed_workflow_user_role_ids = fields.Many2many('workflow.user.role',
                                                      'workflow_procedure_stage_allowed_role',
                                                      string="Allowed Roles")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    def get_workflow_process_stages_by_id(self, stage_id):
        return self.workflow_process_stage_ids.filtered(lambda s: s.id == stage_id)

    def get_workflow_process_stage_by_id(self, stage_id):
        records = self.get_workflow_process_stages_by_id(stage_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_stages_by_ids(self, stage_ids):
        return self.workflow_process_stage_ids.filtered(lambda s: s.id in stage_ids)

    def get_inbound_workflow_procedure_stage_transitions_by_id(self, transition_id):
        return self.inbound_workflow_procedure_stage_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_inbound_workflow_procedure_stage_transition_by_id(self, transition_id):
        records = self.get_inbound_workflow_procedure_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_inbound_workflow_procedure_stage_transitions_by_ids(self, transition_ids):
        return self.inbound_workflow_procedure_stage_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_outbound_workflow_procedure_stage_transitions_by_id(self, transition_id):
        return self.outbound_workflow_procedure_stage_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_outbound_workflow_procedure_stage_transition_by_id(self, transition_id):
        records = self.get_outbound_workflow_procedure_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_outbound_workflow_procedure_stage_transitions_by_ids(self, transition_ids):
        return self.outbound_workflow_procedure_stage_transition_ids.filtered(
            lambda t: t.id in transition_ids
        )

    def get_workflow_procedure_executions_by_id(self, execution_id):
        return self.workflow_procedure_execution_ids.filtered(lambda e: e.id == execution_id)

    def get_workflow_procedure_execution_by_id(self, execution_id):
        records = self.get_workflow_procedure_executions_by_id(execution_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_executions_by_ids(self, execution_ids):
        return self.workflow_procedure_execution_ids.filtered(lambda e: e.id in execution_ids)

    def get_started_workflow_procedures_by_id(self, procedure_id):
        return self.workflow_procedure_ids.filtered(lambda p: p.id == procedure_id)

    def get_started_workflow_procedure_by_id(self, procedure_id):
        records = self.get_started_workflow_procedures_by_id(procedure_id)
        if len(records) > 0:
            return records[0]
        return

    def get_started_workflow_procedures_by_ids(self, procedure_ids):
        return self.workflow_procedure_ids.filtered(lambda p: p.id in procedure_ids)

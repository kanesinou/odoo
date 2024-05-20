# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command


class WorkflowStage(models.Model):
    _name = "workflow.stage"
    _description = "Workflow Stage"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,workflow_id,company_id)', 'The codename must be unique per '
                                                                              'workflow and per company !')
    ]

    @api.depends('workflow_ids')
    def _compute_has_started_workflows(self):
        for stage in self:
            stage.has_started_workflows = len(stage.workflow_ids) > 0

    @api.depends('workflow_ids')
    def _compute_started_workflows_count(self):
        for stage in self:
            stage.started_workflows_count = len(stage.workflow_ids)

    @api.depends('workflow_procedure_stage_ids')
    def _compute_has_procedure_stages(self):
        for stage in self:
            stage.has_procedure_stages = len(stage.workflow_procedure_stage_ids) > 0

    @api.depends('workflow_procedure_stage_ids')
    def _compute_procedure_stages_count(self):
        for stage in self:
            stage.procedure_stages_count = len(stage.workflow_procedure_stage_ids)

    @api.depends('required_workflow_job_ids')
    def _compute_has_required_jobs(self):
        for stage in self:
            stage.has_required_jobs = len(stage.required_workflow_job_ids) > 0

    @api.depends('required_workflow_job_ids')
    def _compute_required_jobs_count(self):
        for stage in self:
            stage.required_jobs_count = len(stage.required_workflow_job_ids)

    @api.depends('optional_workflow_job_ids')
    def _compute_has_optional_jobs(self):
        for stage in self:
            stage.has_optional_jobs = len(stage.optional_workflow_job_ids) > 0

    @api.depends('optional_workflow_job_ids')
    def _compute_optional_jobs_count(self):
        for stage in self:
            stage.optional_jobs_count = len(stage.optional_workflow_job_ids)

    @api.depends('inbound_workflow_stage_transition_ids')
    def _compute_has_inbound_stage_transitions(self):
        for stage in self:
            stage.has_inbound_stage_transitions = len(stage.inbound_workflow_stage_transition_ids) > 0

    @api.depends('inbound_workflow_stage_transition_ids')
    def _compute_inbound_stage_transitions_count(self):
        for stage in self:
            stage.inbound_stage_transitions_count = len(stage.inbound_workflow_stage_transition_ids)

    @api.depends('outbound_workflow_stage_transition_ids')
    def _compute_has_outbound_stage_transitions(self):
        for stage in self:
            stage.has_outbound_stage_transitions = len(stage.outbound_workflow_stage_transition_ids) > 0

    @api.depends('inbound_workflow_stage_transition_ids')
    def _compute_outbound_stage_transitions_count(self):
        for stage in self:
            stage.outbound_stage_transitions_count = len(stage.outbound_workflow_stage_transition_ids)

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    root_workflow_id = fields.Many2one('workflow', required=False, string="Root Workflow",
                                       readonly=True, related="workflow_id.root_workflow_id", store=True)
    workflow_id = fields.Many2one('workflow', string='Workflow', required=True,
                                  ondelete='cascade')
    workflow_state_id = fields.Many2one('workflow.state', string='State', required=True)
    workflow_ids = fields.One2many('workflow', 'workflow_stage_id',
                                   string="Started Workflows")
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
    has_started_workflows = fields.Boolean(readonly=True, compute="_compute_has_started_workflows")
    started_workflows_count = fields.Integer(readonly=True, compute="_compute_started_workflows_count")
    has_procedure_stages = fields.Boolean(readonly=True, compute="_compute_has_procedure_stages")
    procedure_stages_count = fields.Integer(readonly=True, compute="_compute_procedure_stages_count")
    has_required_jobs = fields.Boolean(readonly=True, compute="_compute_has_required_jobs")
    required_jobs_count = fields.Integer(readonly=True, compute="_compute_required_jobs_count")
    has_optional_jobs = fields.Boolean(readonly=True, compute="_compute_has_optional_jobs")
    optional_jobs_count = fields.Integer(readonly=True, compute="_compute_optional_jobs_count")
    has_inbound_stage_transitions = fields.Boolean(readonly=True, compute="_compute_has_inbound_stage_transitions")
    inbound_stage_transitions_count = fields.Integer(readonly=True, compute="_compute_inbound_stage_transitions_count")
    has_outbound_stage_transitions = fields.Boolean(readonly=True, compute="_compute_has_outbound_stage_transitions")
    outbound_stage_transitions_count = fields.Integer(readonly=True,
                                                      compute="_compute_outbound_stage_transitions_count")

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        records = super(WorkflowStage, self).create(vals_list)
        for record in records:
            workflow = record.workflow_id
            workflow_states = workflow.workflow_state_ids.ids
            if record.workflow_state_id.id not in workflow_states:
                workflow_states.append(record.workflow_state_id.id)
                workflow.write({'workflow_state_ids': workflow_states})
        return records

    def get_corresponding_procedure_stage_data(self):
        self.ensure_one()
        procedure_stage_codename = self.codename + '_procedure_stage'
        procedure_stage_name = self.name + ' Procedure Stage'
        if 'workflow' in self.codename:
            procedure_stage_codename = self.codename.replace('workflow', 'procedure')
        if 'workflow' in self.name:
            procedure_stage_name = self.codename.replace('Workflow', 'Procedure')
        data = {
            'codename': procedure_stage_codename,
            'name': procedure_stage_name,
            'workflow_stage_id': self.id,
            'workflow_state_id': self.workflow_state_id.id
        }
        return data

    def get_workflow_procedure_stage_by_id(self, root_procedure_id):
        self.ensure_one()
        return self.env['workflow.procedure.stage'].search([
            '&', ('workflow_stage_id', '=', self.id),
            ('root_workflow_procedure_id', '=', root_procedure_id.id)
        ], limit=1)

    def get_mandatory_procedure_executions_create_data(self, procedure_stage_id):
        self.ensure_one()
        command_data_list = []
        for workflow_job in self.required_workflow_job_ids:
            command_data_list.append(Command.create(
                workflow_job.get_mandatory_procedure_execution_create_data(procedure_stage_id)
            ))
        return command_data_list

    def get_optional_procedure_executions_create_data(self, procedure_stage_id):
        self.ensure_one()
        command_data_list = []
        for workflow_job in self.optional_workflow_job_ids:
            command_data_list.append(Command.create(
                workflow_job.get_optional_procedure_execution_create_data(procedure_stage_id)
            ))
        return command_data_list

# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcedureExecution(models.Model):
    _name = "workflow.procedure.execution"
    _description = "Workflow Procedure Execution"

    @api.depends('workflow_procedure_stage_id', 'workflow_job_id')
    def _compute_name(self):
        name_str = ''
        if self.workflow_job_id:
            name_str = self.workflow_job_id.name
        if self.workflow_procedure_stage_id:
            name_str += "(%s)" % self.workflow_procedure_stage_id.name
        self.name = name_str

    @api.depends('workflow_procedure_stage_id')
    def _compute_root_workflow_procedure(self):
        for execution in self:
            execution.root_workflow_procedure_id = execution.workflow_procedure_stage_id.root_workflow_procedure_id.id

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    mandatory = fields.Boolean(string='Mandatory', default=False, readonly=True)
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage',
                                                  string="Procedure Stage",
                                                  required=True)
    workflow_job_id = fields.Many2one('workflow.job', required=True,
                                      string="Workflow Job")
    workflow_user_id = fields.Many2one('workflow.user', string="Assigned User",
                                       required=False)
    workflow_user_role_id = fields.Many2one('workflow.user.role', required=False,
                                            string="Assigned Role")
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_procedure_execution_id',
                                                     string="Process Executions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcessExecution(models.Model):
    _name = "workflow.process.execution"
    _description = "Workflow Process Execution"

    @api.depends("workflow_process_stage_ids", "has_aborted_process_stages")
    def _compute_has_aborted_process_stages(self):
        for execution in self:
            if len(execution.workflow_process_stage_ids) > 0:
                execution.has_aborted_process_stages = True
            else:
                execution.has_aborted_process_stages = False

    @api.depends('workflow_process_stage_id')
    def _compute_root_workflow_process(self):
        for execution in self:
            execution.root_workflow_process_id = execution.workflow_process_stage_id.root_workflow_process_id.id

    mandatory = fields.Boolean(string='Mandatory', default=False)
    execution_datetime = fields.Datetime(string="Execution Datetime", copy=False, required=True)
    root_workflow_process_id = fields.Many2one('workflow.process', string="Root Process",
                                               required=False, readonly=True, store=True,
                                               compute="_compute_root_workflow_process")
    workflow_procedure_execution_id = fields.Many2one('workflow.procedure.execution',
                                                      string="Procedure Execution", required=True)
    workflow_process_stage_id = fields.Many2one('workflow.process.stage', string="Process Stage",
                                                required=True)
    workflow_job_id = fields.Many2one('workflow.job', string="Workflow Job", required=True)
    workflow_action_id = fields.Many2one('workflow.action', string="Workflow Action",
                                         required=True)
    workflow_user_id = fields.Many2one('workflow.user', string="Assigned User",
                                       required=False)
    workflow_user_role_id = fields.Many2one('workflow.user.role',
                                            string="Assigned Role", required=False)
    workflow_process_stage_ids = fields.One2many('workflow.process.stage',
                                                 'workflow_process_execution_id',
                                                 string="Aborted Process Stages")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    has_aborted_process_stages = fields.Boolean(readonly=True,
                                                compute="_compute_has_aborted_process_stages")

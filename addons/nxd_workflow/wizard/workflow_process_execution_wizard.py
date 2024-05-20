# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WorkflowProcessExecutionWizard(models.TransientModel):
    _name = "workflow.process.execution.wizard"
    _description = "Configure Process Execution"

    @api.depends('workflow_process_execution_id')
    def _get_default_execution_user(self):
        user = self.workflow_process_execution_id.execution_user_id
        if user:
            return user.id
        return None

    @api.depends('workflow_process_execution_id')
    def _get_default_start_datetime(self):
        start_datetime = self.workflow_process_execution_id.execution_start_datetime
        if start_datetime:
            return start_datetime
        return None

    @api.depends('workflow_process_execution_id')
    def _get_default_complete_datetime(self):
        complete_datetime = self.workflow_process_execution_id.execution_complete_datetime
        if complete_datetime:
            return complete_datetime
        return None

    workflow_process_execution_id = fields.Many2one('workflow.process.execution', required=True,
                                                    readonly=True)
    execution_user_id = fields.Many2one('workflow.user', required=False, string="Executor",
                                        default=lambda self: self.workflow_process_execution_id.execution_user_id)
    execution_start_datetime = fields.Datetime(string="Start Datetime", copy=False, required=False,
                                               default=lambda self: self.workflow_process_execution_id.execution_start_datetime)
    execution_complete_datetime = fields.Datetime(string="Complete Datetime", copy=False, required=False,
                                                  default=lambda self: self.workflow_process_execution_id.execution_complete_datetime)

    def create_process_execution_from_wizard(self):
        data = {
            'execution_user_id': self.execution_user_id,
            'execution_start_datetime': self.execution_start_datetime
        }
        if self.execution_complete_datetime:
            data['execution_complete_datetime'] = self.execution_complete_datetime
        self.workflow_process_execution_id.write(data)

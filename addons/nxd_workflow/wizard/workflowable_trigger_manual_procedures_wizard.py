# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command


class ManualProcedureTriggerWizard(models.TransientModel):
    _name = "workflowable.manual.procedure.trigger.wizard"
    _description = "Trigger Procedures Manually"

    workflowable_id = fields.Many2one('workflowable', required=True, readonly=True)
    workflow_procedure_ids = fields.Many2many('workflow.procedure',
                                              related="workflowable_id.awaiting_manual_workflow_procedure_ids")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 required=True, default=lambda self: self.env.company)

    def trigger_procedures_from_wizard(self):
        print("Context : ", self.env.context)
        if len(self.workflow_procedure_ids) > 0:
            for workflow_procedure in self.workflow_procedure_ids:
                workflow_procedure.trigger_manual_process(self.workflowable_id.object_id)
            self.workflowable_id.write({
                'triggered_manual_workflow_procedure_ids': [
                    Command.update(
                        self.workflowable_id.id, self.workflow_procedure_ids.mapped('id')
                    )
                ]
            })

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class WorkflowProcedureCycleStageTransition(models.Model):
    _name = "workflow.procedure.cycle.stage.transition"
    _description = "WorkflowProcedureCycleStageTransition"

    @api.depends('from_workflow_procedure_cycle_stage_id', 'to_workflow_procedure_cycle_stage_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_procedure_cycle_stage_id:
                name_str = transition.from_workflow_procedure_cycle_stage_id.name
            name_str += ' ---> '
            if transition.to_workflow_procedure_cycle_stage_id:
                name_str += transition.to_workflow_procedure_cycle_stage_id.name
            transition.name = name_str

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    workflow_procedure_cycle_id = fields.Many2one('workflow.procedure.cycle', required=True,
                                                  string="Procedure Cycle")
    from_workflow_procedure_cycle_stage_id = fields.Many2one('workflow.procedure.cycle.stage',
                                                             required=True, string="From Procedure Cycle Stage")
    to_workflow_procedure_cycle_stage_id = fields.Many2one('workflow.procedure.cycle.stage',
                                                           required=True, string="To Procedure Cycle Stage")
    workflow_process_cycle_stage_transition_ids = fields.One2many('workflow.process.cycle.stage.transition',
                                                                  'workflow_procedure_cycle_stage_transition_id')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

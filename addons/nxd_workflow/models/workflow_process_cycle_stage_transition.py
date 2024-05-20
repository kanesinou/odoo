# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class WorkflowProcessCycleStageTransition(models.Model):
    _name = "workflow.process.cycle.stage.transition"
    _description = "WorkflowProcessCycleStageTransition"

    @api.depends('from_workflow_process_cycle_stage_id', 'to_workflow_process_cycle_stage_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_process_cycle_stage_id:
                name_str = transition.from_workflow_process_cycle_stage_id.name
            name_str += ' ---> '
            if transition.to_workflow_process_cycle_stage_id:
                name_str += transition.to_workflow_process_cycle_stage_id.name
            transition.name = name_str

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    transition_datetime = fields.Datetime(string="Transition Datetime", copy=False,
                                          required=True)
    workflow_process_cycle_id = fields.Many2one('workflow.process.cycle', required=True,
                                                string="Process Cycle")
    workflow_procedure_cycle_stage_transition_id = fields.Many2one('workflow.procedure.cycle.stage.transition',
                                                                   required=True,
                                                                   string="Procedure Cycle Stage Transition")
    from_workflow_process_cycle_stage_id = fields.Many2one('workflow.process.cycle.stage', required=True,
                                                           string="From Process Cycle Stage")
    to_workflow_process_cycle_stage_id = fields.Many2one('workflow.process.cycle.stage', required=True,
                                                         string="To Process Cycle Stage")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

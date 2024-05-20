# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from ..utils import date_utils


class WorkflowProcedureCycleStage(models.Model):
    _name = "workflow.procedure.cycle.stage"
    _description = "Workflow Procedure Cycle Stage"
    _sql_constraints = [
        ('codename_cycle_company_uniq', 'unique (codename,workflow_procedure_cycle_id, company_id)', 'The codename of '
                                                                                                     'the workflow '
                                                                                                     'procedure cycle '
                                                                                                     'stage must be '
                                                                                                     'unique per cycle '
                                                                                                     'and per company !')
    ]

    @api.depends('time_unit')
    def _compute_time_label(self):
        for stage in self:
            if stage.time_unit:
                stage.time_label = date_utils.TIME_LABELS.get(stage.time_unit)

    @api.depends('time_unit')
    def _compute_time_label_plural(self):
        for stage in self:
            if stage.time_unit:
                stage.time_label_plural = date_utils.TIME_LABEL_PLURALS.get(stage.time_unit)

    @api.depends("inbound_workflow_procedure_cycle_stage_transition_ids", "has_inbound_transitions")
    def _compute_has_inbound_transitions(self):
        for stage in self:
            if len(stage.inbound_workflow_procedure_cycle_stage_transition_ids) > 0:
                stage.has_inbound_transitions = True
            else:
                stage.has_inbound_transitions = False

    @api.depends("outbound_workflow_procedure_cycle_stage_transition_ids", "has_outbound_transitions")
    def _compute_has_outbound_transitions(self):
        for stage in self:
            if len(stage.outbound_workflow_procedure_cycle_stage_transition_ids) > 0:
                stage.has_outbound_transitions = True
            else:
                stage.has_outbound_transitions = False

    @api.depends("workflow_process_cycle_stage_ids", "has_outbound_transitions")
    def _compute_has_process_cycle_stages(self):
        for stage in self:
            if len(stage.workflow_process_cycle_stage_ids) > 0:
                stage.has_process_cycle_stages = True
            else:
                stage.has_process_cycle_stages = False

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    workflow_procedure_cycle_id = fields.Many2one('workflow.procedure.cycle', required=True,
                                                  string="Workflow Procedure Cycle")
    workflow_procedure_ids = fields.Many2many('workflow.procedure',
                                              'workflow_procedure_cycle_stage_procedure',
                                              domain=['&', ('base_procedure', '=', True), ('released', '=', True)])
    inbound_workflow_procedure_cycle_stage_transition_ids = fields.One2many('workflow.procedure.cycle.stage.transition',
                                                                            'to_workflow_procedure_cycle_stage_id')
    outbound_workflow_procedure_cycle_stage_transition_ids = fields.One2many('workflow.procedure.cycle.stage.transition',
                                                                             'from_workflow_procedure_cycle_stage_id')
    workflow_process_cycle_stage_ids = fields.One2many('workflow.process.cycle.stage',
                                                       'workflow_procedure_cycle_stage_id')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    has_inbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_inbound_transitions")
    has_outbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_outbound_transitions")
    has_process_cycle_stages = fields.Boolean(readonly=True, compute="_compute_has_process_cycle_stages")
    time_label = fields.Char(string="Time Label", required=False, translate=True,
                             compute="_compute_time_label")
    time_label_plural = fields.Char(string="Time Label Plural", required=False, translate=True,
                                    compute="_compute_time_label_plural")
    time_unit = fields.Selection(
        selection=[
            ("minute", "Minute"),
            ("hour", "Hour"),
            ("day", "Day"),
            ("week", "Week"),
            ("month", "Month"),
            ("quarter", "Quarter"),
            ("semester", "Semester"),
            ("year", "Year")
        ],
        string="Time Unit", required=False
    )
    min_duration = fields.Float(string="Minimum Duration", default=0,digits=(11, 5))
    max_duration = fields.Float(string="Maximum Duration", default=0, digits=(11, 5))
    min_estimated_duration = fields.Float(readonly=True, default=0, digits=(11, 5))
    max_estimated_duration = fields.Float(readonly=True, default=0, digits=(11, 5))
    min_execution_duration = fields.Float(readonly=True, default=0, digits=(11, 5))
    max_execution_duration = fields.Float(readonly=True, default=0, digits=(11, 5))

    def action_configure_duration(self):
        wizard = self.env['workflow.procedure.cycle.stage.duration.wizard'].create({
            'workflow_procedure_cycle_stage_id': self.id
        })
        return {
            'name': _('Configure Procedure Cycle Stage Duration'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.procedure.cycle.stage.duration.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new'
        }

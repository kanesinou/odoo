# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class WorkflowProcedureCycle(models.Model):
    _name = "workflow.procedure.cycle"
    _description = "Workflow Procedure Cycle"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow procedure cycle must '
                                                                  'be unique per company !')
    ]

    @api.depends('time_unit', 'workflow_procedure_ids')
    def _compute_min_estimated_duration(self):
        for cycle in self:
            cycle.min_estimated_duration = 0
            if cycle.time_unit:
                cycle.min_estimated_duration = cycle.get_min_duration_for_time_unit(cycle.time_unit)

    @api.depends('time_unit', 'workflow_procedure_ids')
    def _compute_max_estimated_duration(self):
        for cycle in self:
            cycle.max_estimated_duration = 0
            if cycle.time_unit:
                cycle.max_estimated_duration = cycle.get_max_duration_for_time_unit(cycle.time_unit)

    @api.depends('time_unit', 'workflow_procedure_ids')
    def _compute_min_execution_duration(self):
        for cycle in self:
            cycle.min_execution_duration = 0
            if cycle.time_unit:
                cycle.min_execution_duration = cycle.get_min_execution_duration_for_time_unit(
                    cycle.time_unit
                )

    @api.depends('time_unit', 'workflow_procedure_ids')
    def _compute_max_execution_duration(self):
        for cycle in self:
            cycle.max_execution_duration = 0
            if cycle.time_unit:
                cycle.max_execution_duration = cycle.get_max_execution_duration_for_time_unit(
                    cycle.time_unit
                )

    @api.depends("workflow_procedure_cycle_duration_ids", "has_durations")
    def _compute_has_durations(self):
        for cycle in self:
            if len(cycle.workflow_procedure_cycle_duration_ids) > 0:
                cycle.has_durations = True
            else:
                cycle.has_durations = False

    @api.depends("workflow_procedure_ids", "has_procedures")
    def _compute_has_procedures(self):
        for cycle in self:
            if len(cycle.workflow_procedure_ids) > 0:
                cycle.has_procedures = True
            else:
                cycle.has_procedures = False

    @api.depends("workflow_procedure_transition_ids", "has_procedure_transitions")
    def _compute_has_procedure_transitions(self):
        for cycle in self:
            if len(cycle.workflow_procedure_transition_ids) > 0:
                cycle.has_procedure_transitions = True
            else:
                cycle.has_procedure_transitions = False

    @api.depends('workflow_procedure_ids', 'procedure_transitions_allowed')
    def _compute_procedure_transitions_allowed(self):
        for cycle in self:
            if len(cycle.workflow_procedure_ids) >= 2:
                cycle.procedure_transitions_allowed = True
            else:
                cycle.procedure_transitions_allowed = False

    @api.depends('workflow_procedure_ids')
    def _compute_workflow_procedure_domain(self):
        for transition in self:
            domain = [
                '&', '&', ('parent_id', '=', False), ('base_procedure', '=', True),
                ('released', '=', True)
            ]
            if len(transition.workflow_procedure_ids) > 0:
                domain = [
                    '&', '&', ('parent_id', '=', False), ('base_procedure', '=', True),
                    '&', ('released', '=', True), ('id', 'not in', transition.workflow_procedure_ids.ids)
                ]
            transition.workflow_procedure_domain = self.env['workflow.procedure'].search(domain).ids

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    workflow_process_cycle_ids = fields.One2many('workflow.process.cycle',
                                                 'workflow_procedure_cycle_id')
    workflow_procedure_cycle_duration_ids = fields.One2many('workflow.procedure.cycle.duration',
                                                            'workflow_procedure_cycle_id')
    workflow_procedure_ids = fields.Many2many('workflow.procedure',
                                              'workflow_procedure_cycle_procedure',
                                              domain=['&', ('base_procedure', '=', True), ('released', '=', True)])
    workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                        'workflow_procedure_cycle_id',
                                                        domain=[
                                                            '&',
                                                            ('from_workflow_procedure_id.base_procedure', '=', True),
                                                            ('to_workflow_procedure_id.base_procedure', '=', True)
                                                        ])
    starter_workflow_procedure_cycle_stage = fields.Many2one('workflow.procedure.cycle.stage',
                                                             string="Starter Stage", required=False)
    finalizer_workflow_procedure_cycle_stage = fields.Many2one('workflow.procedure.cycle.stage',
                                                               string="Finalizer Stage", required=False)
    workflow_procedure_cycle_stage_ids = fields.One2many('workflow.procedure.cycle.stage',
                                                         'workflow_procedure_cycle_id')
    workflow_procedure_cycle_stage_transition_ids = fields.One2many('workflow.procedure.cycle.stage.transition',
                                                                    'workflow_procedure_cycle_id')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    procedure_transitions_allowed = fields.Boolean(readonly=True, compute="_compute_procedure_transitions_allowed")
    has_procedures = fields.Boolean(readonly=True, compute="_compute_has_procedures")
    has_procedure_transitions = fields.Boolean(readonly=True, compute="_compute_has_procedure_transitions")
    has_durations = fields.Boolean(readonly=True, compute="_compute_has_durations")
    workflow_procedure_domain = fields.Many2many('workflow.procedure', readonly=True,
                                                 compute="_compute_workflow_procedure_domain",
                                                 relation="workflow_procedure_cycle_procedure_domain_ids")
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
    min_estimated_duration = fields.Float(readonly=True, compute="_compute_min_estimated_duration",
                                          default=0, digits=(11, 5))
    max_estimated_duration = fields.Float(readonly=True, compute="_compute_max_estimated_duration",
                                          default=0, digits=(11, 5))
    min_execution_duration = fields.Float(readonly=True, compute="_compute_min_execution_duration",
                                          default=0, digits=(11, 5))
    max_execution_duration = fields.Float(readonly=True, compute="_compute_max_execution_duration",
                                          default=0, digits=(11, 5))

    def get_descendant_procedure_execution_ids(self):
        self.ensure_one()
        ids = []
        for procedure in self.workflow_procedure_ids:
            ids.extend(procedure.get_descendant_procedure_execution_ids())
        return list(set(ids))

    def get_execution_durations_for_time_unit(self, time_unit):
        self.ensure_one()
        return self.env['workflow.procedure.execution.duration'].search([
            '&', ('time_unit', '=', time_unit),
            ('workflow_procedure_execution_id', 'in', self.get_descendant_procedure_execution_ids())
        ])

    def get_min_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        return sum(
            [0] + [stage.get_min_duration_for_time_unit(time_unit) for stage in self.workflow_procedure_ids]
        )

    def get_max_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        return sum(
            [0] + [stage.get_max_duration_for_time_unit(time_unit) for stage in self.workflow_procedure_ids]
        )

    def get_min_execution_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        return sum([0] + self.get_execution_durations_for_time_unit(time_unit).mapped('min_duration'))

    def get_max_execution_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        return sum([0] + self.get_execution_durations_for_time_unit(time_unit).mapped('max_duration'))

    def action_configure_duration(self):
        wizard = self.env['workflow.procedure.cycle.duration.wizard'].create({
            'workflow_procedure_cycle_id': self.id
        })
        return {
            'name': _('Configure Procedure Cycle Duration'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.procedure.cycle.duration.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new'
        }

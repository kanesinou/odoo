# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcedureStageTransition(models.Model):
    _name = "workflow.procedure.stage.transition"
    _description = "Workflow Procedure Stage Transition"

    @api.constrains('workflow_procedure_id', 'workflow_procedure_transition_id')
    def _check_transition_context(self):
        for transition in self:
            if not transition.workflow_procedure_id and not transition.workflow_procedure_transition_id:
                raise ValidationError(_("A procedure stage transition must occur either in a workflow procedure or a "
                                        "procedure transition context !"))
            elif transition.workflow_procedure_id and transition.workflow_procedure_transition_id:
                raise ValidationError(_("The context of the transition must be unique. Set either a workflow "
                                        "procedure or workflow procedure transition, not both !"))

    @api.onchange('from_workflow_procedure_stage_id')
    def _onchange_from_workflow_procedure_stage(self):
        if self.from_workflow_procedure_stage_id:
            return {
                'domain': {
                    'to_workflow_procedure_stage_id': [
                        ('id', '!=', self.from_workflow_procedure_stage_id.id)
                    ]
                }
            }

    @api.onchange('to_workflow_procedure_stage_id')
    def _onchange_to_workflow_procedure_stage(self):
        if self.to_workflow_procedure_stage_id:
            return {
                'domain': {
                    'from_workflow_procedure_stage_id': [
                        ('id', '!=', self.to_workflow_procedure_stage_id.id)
                    ]
                }
            }

    @api.onchange('workflow_procedure_id', 'workflow_procedure_transition_id')
    def _onchange_transition_context(self):
        if self.workflow_procedure_id and not self.workflow_procedure_transition_id:
            self.context_type = 'sibling'
            return [
                {
                    'domain': {
                        'from_workflow_procedure_stage_id': [
                            ('workflow_procedure_id', '=', self.workflow_procedure_id.id)
                        ]
                    }
                },
                {
                    'domain': {
                        'to_workflow_procedure_stage_id': [
                            ('workflow_procedure_id', '=', self.workflow_procedure_id.id)
                        ]
                    }
                }
            ]
        elif not self.workflow_procedure_id and self.workflow_procedure_transition_id:
            self.context_type = 'transition'
            return [
                {
                    'domain': {
                        'from_workflow_procedure_stage_id': [
                            ('id', 'in', self.workflow_procedure_transition_id.from_workflow_procedure_id.workflow_procedure_stage_ids)
                        ]
                    }
                },
                {
                    'domain': {
                        'to_workflow_procedure_stage_id': [
                            ('id', 'in', self.workflow_procedure_transition_id.to_workflow_procedure_id.workflow_procedure_stage_id.id)
                        ]
                    }
                }
            ]

    @api.depends('from_workflow_procedure_stage_id', 'to_workflow_procedure_stage_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_procedure_stage_id:
                name_str = transition.from_workflow_procedure_stage_id.name
            name_str += ' ---> '
            if transition.to_workflow_procedure_stage_id:
                name_str += transition.to_workflow_procedure_stage_id.name
            transition.name = name_str

    @api.depends('from_workflow_procedure_stage_id', 'to_workflow_procedure_stage_id')
    def _compute_cross_border(self):
        for transition in self:
            if transition.from_workflow_procedure_stage_id.workflow_procedure_id != transition.to_workflow_procedure_stage_id.workflow_procedure_id:
                transition.cross_border = True
            else:
                transition.cross_border = False

    @api.depends('workflow_procedure_id', 'workflow_procedure_transition_id')
    def _compute_root_workflow_procedure(self):
        for transition in self:
            if transition.workflow_procedure_id:
                transition.root_workflow_procedure_id = transition.workflow_procedure_id.root_workflow_procedure_id.id
                if not self.workflow_procedure_transition_id:
                    self.context_type = 'sibling'
            else:
                transition.root_workflow_procedure_id = transition.workflow_procedure_transition_id.root_workflow_procedure_id.id
                if not self.workflow_procedure_id:
                    self.context_type = 'transition'

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=True,
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')])
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute='_compute_root_workflow_procedure')
    from_workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage',
                                                       required=True, string="From Procedure Stage")
    to_workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage',
                                                     required=True, string="To Procedure Stage")
    workflow_stage_transition_id = fields.Many2one('workflow.stage.transition',
                                                   required=True, string="Workflow Stage Transition")
    workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                            string="Procedure")
    workflow_procedure_transition_id = fields.Many2one('workflow.procedure.transition',
                                                       required=False, string="Procedure Transition")
    workflow_process_stage_transition_ids = fields.One2many('workflow.process.stage.transition',
                                                            'workflow_procedure_stage_transition_id',
                                                            string="Process Stage Transitions")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cross_border = fields.Boolean(default=False, readonly=True, compute="_compute_cross_border")

    def get_workflow_process_stage_transitions_by_id(self, workflow_procedure_stage_transition_id):
        return self.workflow_process_stage_transition_ids.filtered(
            lambda t: t.id == workflow_procedure_stage_transition_id
        )

    def get_workflow_process_stage_transition_by_id(self, workflow_procedure_stage_transition_id):
        records = self.get_workflow_process_stage_transitions_by_id(
            workflow_procedure_stage_transition_id
        )
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_stage_transitions_by_ids(self, workflow_procedure_stage_transition_ids):
        return self.workflow_process_stage_transition_ids.filtered(
            lambda t: t.id in workflow_procedure_stage_transition_ids
        )

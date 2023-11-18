# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WorkflowProcedureTransition(models.Model):
    _name = "workflow.procedure.transition"
    _description = "WorkflowProcedureTransition"

    @api.constrains('workflow_procedure_id', 'workflow_transition_procedure_id')
    def _check_workflow_procedure_context(self):
        for transition in self:
            if not transition.workflow_procedure_id and not transition.workflow_procedure_transition_id:
                raise ValidationError(_("Either a workflow procedure or workflow procedure transition must be set as "
                                        "context !"))
            elif transition.workflow_procedure_id and transition.workflow_procedure_transition_id:
                raise ValidationError(_("The context of the procedure transition must be unique. Set either a "
                                        "workflow procedure or workflow procedure transition, not both !"))

    @api.onchange('from_workflow_procedure_id')
    def _onchange_from_workflow_procedure(self):
        if self.from_workflow_procedure_id:
            return {
                'domain': {
                    'to_workflow_procedure_id': [('id', '!=', self.from_workflow_procedure_id.id)]
                }
            }

    @api.onchange('to_workflow_procedure_id')
    def _onchange_to_workflow_procedure(self):
        if self.to_workflow_procedure_id:
            return {
                'domain': {
                    'from_workflow_procedure_id': [('id', '!=', self.to_workflow_procedure_id.id)]
                }
            }

    @api.onchange('workflow_procedure_id', 'workflow_procedure_transition_id')
    def _onchange_transition_context(self):
        if self.workflow_procedure_id and not self.workflow_procedure_transition_id:
            self.context_type = 'sibling'
            return [
                {'domain': {'from_workflow_procedure_id': [('parent_id', '=', self.workflow_procedure_id.id)]}},
                {'domain': {'to_workflow_procedure_id': [('parent_id', '=', self.workflow_procedure_id.id)]}}
            ]
        elif not self.workflow_procedure_id and self.workflow_procedure_transition_id:
            self.context_type = 'transition'
            return [
                {
                    'domain': {
                        'from_workflow_procedure_id': [
                            ('id', 'in', self.workflow_procedure_transition_id.from_workflow_procedure_id.workflow_procedure_ids)
                        ]
                    }
                },
                {
                    'domain': {
                        'to_workflow_procedure_id': [
                            ('id', 'in', self.workflow_procedure_transition_id.to_workflow_procedure_id.workflow_procedure_ids)
                        ]
                    }
                }
            ]

    @api.depends('from_workflow_procedure_id', 'to_workflow_procedure_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_procedure_id:
                name_str = transition.from_workflow_procedure_id.name
            name_str += ' ---> '
            if transition.to_workflow_procedure_id:
                name_str += transition.to_workflow_procedure_id.name
            transition.name = name_str

    @api.depends('from_workflow_procedure_id', 'to_workflow_procedure_id')
    def _compute_cross_border(self):
        for transition in self:
            if transition.from_workflow_procedure_id.parent_id != transition.to_workflow_procedure_id.parent_id:
                transition.cross_border = True
            else:
                transition.cross_border = False

    @api.depends('workflow_procedure_id', 'workflow_procedure_transition_id')
    def _compute_root_workflow_procedure(self):
        for transition in self:
            if transition.workflow_procedure_id:
                transition.root_workflow_procedure_id = transition.workflow_procedure_id.root_workflow_procedure_id.id
                if not self.workflow_procedure_id:
                    self.context_type = 'sibling'
            else:
                transition.root_workflow_procedure_id = transition.workflow_procedure_transition_id.root_workflow_procedure_id.id
                if not self.workflow_procedure_transition_id:
                    self.context_type = 'transition'

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=True,
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')])
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    from_workflow_procedure_id = fields.Many2one('workflow.procedure',
                                                 required=True,
                                                 string="From Procedure")
    to_workflow_procedure_id = fields.Many2one('workflow.procedure',
                                               required=True, string="To Procedure")
    workflow_procedure_id = fields.Many2one('workflow.procedure',
                                            required=False, string="Context Procedure")
    workflow_procedure_transition_id = fields.Many2one('workflow.procedure.transition',
                                                       required=False,
                                                       string="Context Procedures Transition")
    workflow_transition_id = fields.Many2one('workflow.transition',
                                             required=True, string="Workflow Transition")
    workflow_process_transition_ids = fields.One2many('workflow.process.transition',
                                                      'workflow_procedure_transition_id',
                                                      string="Process Transitions")
    workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                              'workflow_procedure_transition_id',
                                                              string="Procedure Stage Transitions")
    workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                        'workflow_procedure_transition_id',
                                                        string="Procedure Transitions")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cross_border = fields.Boolean(default=False, readonly=True, compute="_compute_cross_border")

    def get_workflow_process_transitions_by_id(self, workflow_procedure_transition_id):
        return self.workflow_process_transition_ids.filtered(
            lambda t: t.id == workflow_procedure_transition_id
        )

    def get_workflow_process_transition_by_id(self, workflow_procedure_transition_id):
        records = self.get_workflow_process_transitions_by_id(workflow_procedure_transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_process_transitions_by_ids(self, workflow_procedure_transition_ids):
        return self.workflow_process_transition_ids.filtered(
            lambda t: t.id in workflow_procedure_transition_ids
        )

    def get_workflow_procedure_stage_transitions_by_id(self, workflow_procedure_transition_id):
        return self.workflow_procedure_stage_transition_ids.filtered(
            lambda t: t.id == workflow_procedure_transition_id
        )

    def get_workflow_procedure_stage_transition_by_id(self, workflow_procedure_transition_id):
        records = self.get_workflow_procedure_stage_transitions_by_id(
            workflow_procedure_transition_id
        )
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_stage_transitions_by_ids(self, workflow_procedure_transition_ids):
        return self.workflow_procedure_stage_transition_ids.filtered(
            lambda t: t.id in workflow_procedure_transition_ids
        )

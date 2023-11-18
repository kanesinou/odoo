# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class WorkflowStateTransition(models.Model):
    _name = "workflow.state.transition"
    _description = "Workflow State Transition"
    _sql_constraints = [
        ('from_to_company_uniq', 'unique (from_workflow_state_id,to_workflow_state_id,company_id)', 'The from and to '
                                                                                                    'states of the '
                                                                                                    'workflow state '
                                                                                                    'transition must '
                                                                                                    'be unique per '
                                                                                                    'company !')
    ]

    @api.depends('from_workflow_state_id', 'to_workflow_state_id')
    def _compute_name(self):
        for transition in self:
            name_str = ''
            if transition.from_workflow_state_id:
                name_str = transition.from_workflow_state_id.name
            name_str += ' ---> '
            if transition.to_workflow_state_id:
                name_str += transition.to_workflow_state_id.name
            transition.name = name_str

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    from_workflow_state_id = fields.Many2one('workflow.state', string=_("From state"),
                                             required=True)
    to_workflow_state_id = fields.Many2one('workflow.state', required=True,
                                           string=_("To state"))
    workflow_action_id = fields.Many2one('workflow.action', required=True,
                                         string=_("Action"))
    workflow_stage_transition_ids = fields.One2many('workflow.stage.transition',
                                                    'workflow_state_transition_id',
                                                    string=_("Workflow Stage Transitions"))
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

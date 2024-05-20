# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
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

    @api.constrains('can_return', 'return_action_name')
    def _check_return_setting(self):
        for transition in self:
            if transition.can_return and not transition.return_action_name:
                raise ValidationError(_('If the transition can return, the return action name must be set !'))

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

    @api.depends("workflow_process_stage_transition_ids", "has_process_stage_transitions")
    def _compute_has_process_stage_transitions(self):
        for transition in self:
            if len(transition.workflow_process_stage_transition_ids) > 0:
                transition.has_process_stage_transitions = True
            else:
                transition.has_process_stage_transitions = False

    @api.depends('workflow_procedure_id', 'workflow_procedure_transition_id')
    def _compute_root_workflow_procedure(self):
        for transition in self:
            if transition.workflow_procedure_id:
                transition.root_workflow_procedure_id = transition.workflow_procedure_id.root_workflow_procedure_id.id
                if not transition.workflow_procedure_transition_id:
                    transition.context_type = 'sibling'
            else:
                transition.root_workflow_procedure_id = transition.workflow_procedure_transition_id.root_workflow_procedure_id.id
                if not transition.workflow_procedure_id:
                    transition.context_type = 'transition'

    @api.depends('workflow_procedure_stage_transition_acl_ids')
    def _compute_is_protected(self):
        for transition in self:
            transition.is_protected = len(transition.workflow_procedure_stage_transition_acl_ids) > 0

    @api.depends('workflow_procedure_stage_transition_acl_ids')
    def _compute_is_execution_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_execution_protected = False
            else:
                acl = stage.workflow_procedure_stage_transition_acl_ids[0]
                stage.is_execution_protected = len(acl.workflow_user_ids) > 0 or len(acl.workflow_role_ids)

    @api.depends('from_workflow_procedure_stage_id')
    def _compute_has_executions(self):
        for transition in self:
            transition.has_executions = False
            if len(transition.get_procedure_stage_executions()) > 0:
                transition.has_executions = True

    @api.depends('from_workflow_procedure_stage_id')
    def _compute_has_mandatory_executions(self):
        for transition in self:
            transition.has_mandatory_executions = False
            if len(transition.get_mandatory_procedure_stage_executions()) > 0:
                transition.has_mandatory_executions = True

    @api.depends('from_workflow_procedure_stage_id')
    def _compute_has_optional_executions(self):
        for transition in self:
            transition.has_optional_executions = False
            if len(transition.get_optional_procedure_stage_executions()) > 0:
                transition.has_optional_executions = True

    name = fields.Char(string="Name", readonly=True, compute="_compute_name")
    context_type = fields.Selection(string="Context Type", required=True,
                                    selection=[('sibling', 'Sibling'), ('transition', 'Transition')])
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 related='from_workflow_procedure_stage_id.root_workflow_procedure_id')
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
    job_done_required = fields.Boolean(string="Job Done Required", default=True)
    can_return = fields.Boolean(string="Can Return",
                                related="workflow_stage_transition_id.can_return")
    return_action_name = fields.Char(string="Return Action Name", required=False,
                                     related="workflow_stage_transition_id.return_action_name")
    return_action_title = fields.Char(string='Return Action Title',
                                      related="workflow_stage_transition_id.return_action_title")
    action_name = fields.Char(string="Action Name",
                              related="workflow_stage_transition_id.action_name")
    action_title = fields.Char(string='Action Title', required=False, translate=True,
                               related="workflow_stage_transition_id.action_title")
    button_type = fields.Selection(string="Button Type",
                                   related="workflow_stage_transition_id.button_type")
    workflow_process_stage_transition_ids = fields.One2many('workflow.process.stage.transition',
                                                            'workflow_procedure_stage_transition_id',
                                                            string="Process Stage Transitions")
    workflow_procedure_stage_transition_acl_ids = fields.One2many('workflow.procedure.stage.transition.acl',
                                                                  'workflow_procedure_stage_transition_id',
                                                                  string="Procedure Stage Transition Access Control List")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 readonly=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    cross_border = fields.Boolean(default=False, readonly=True, compute="_compute_cross_border")
    has_process_stage_transitions = fields.Boolean(readonly=True,
                                                   compute="_compute_has_process_stage_transitions")
    is_protected = fields.Boolean(readonly=True, compute="_compute_is_protected")
    is_execution_protected = fields.Boolean(readonly=True, compute="_compute_is_execution_protected")
    has_executions = fields.Boolean(readonly=True, compute="_compute_has_executions")
    has_mandatory_executions = fields.Boolean(readonly=True, compute="_compute_has_mandatory_executions")
    has_optional_executions = fields.Boolean(readonly=True, compute="_compute_has_optional_executions")

    def get_corresponding_process_stage_transition_data(self, workflowable_record):
        self.ensure_one()
        data = {
            'workflow_procedure_stage_transition_id': self.id,
            'can_return': self.can_return,
            'context_type': self.context_type,
            'return_action_name': self.return_action_name
        }
        acls_data = []
        for transition_acl in self.workflow_procedure_stage_transition_acl_ids:
            transition_acl_process_data = transition_acl.get_corresponding_process_stage_transition_acl_data(
                workflowable_record
            )
            new_process_stage_transition_acl_data = {
                'workflow_procedure_stage_transition_acl_id': transition_acl_process_data['workflow_procedure_stage_transition_acl_id'],
                'filter_domain': transition_acl_process_data['filter_domain']
            }
            acl_users_command = []
            for acl_user in transition_acl_process_data['workflow_user_ids']:
                acl_users_command.append(Command.link(acl_user.id))
            new_process_stage_transition_acl_data['workflow_user_ids'] = acl_users_command
            acl_roles_command = []
            for acl_role in transition_acl_process_data['workflow_role_ids']:
                acl_roles_command.append(Command.link(acl_role.id))
            new_process_stage_transition_acl_data['workflow_role_ids'] = acl_roles_command
            acls_data.append(Command.create(new_process_stage_transition_acl_data))
        if len(acls_data) > 0:
            data['workflow_process_stage_transition_acl_ids'] = acls_data
        return data

    def get_parent_bridge_transitions_branch(self, collector=False):
        self.ensure_one()
        if not collector:
            collector = []
        if self.context_type == 'sibling':
            return collector
        else:
            workflow_procedure_transition = self.workflow_procedure_transition_id
            collector.insert(0, workflow_procedure_transition)
            return workflow_procedure_transition.get_parent_bridge_transitions_branch(collector)

    def user_can_execute(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_execution_protected:
            return True
        else:
            return self.workflow_procedure_stage_transition_acl_ids[0].user_can_execute(workflow_user)

    def get_procedure_stage_executions(self):
        self.ensure_one()
        return self.from_workflow_procedure_stage_id.workflow_procedure_execution_ids

    def get_mandatory_procedure_stage_executions(self):
        self.ensure_one()
        return self.from_workflow_procedure_stage_id.workflow_procedure_execution_ids.filtered(
            lambda e: e.mandatory
        )

    def get_optional_procedure_stage_executions(self):
        self.ensure_one()
        return self.from_workflow_procedure_stage_id.workflow_procedure_execution_ids.filtered(
            lambda e: not e.mandatory
        )

    def action_configure_acl(self):
        wizard = self.env['workflow.procedure.stage.transition.acl.wizard'].create({
            'workflow_procedure_stage_transition_id': self.id
        })
        return {
            'name': _('Configure Procedure Stage Transition Access Control List'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.procedure.stage.transition.acl.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new'
        }

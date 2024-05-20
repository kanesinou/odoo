# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from ..ext import schema


class Workflowable(models.Model):
    _name = "workflowable"
    _description = "Workflowable"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('reference_company_uniq', 'unique (workflowable_type_id,object_id,company_id)', 'The reference(model + '
                                                                                         'primary key) of the '
                                                                                         'workflowable must be unique '
                                                                                         'per company !')
    ]

    @api.depends('object_id')
    def _compute_name(self):
        for workflowable in self:
            record = self.env.get(workflowable.workflowable_type_id.model_id.model).search([
                ('id', '=', workflowable.object_id)
            ], limit=1)
            if record.exists():
                workflowable.name = record.name_get()[0][1]
            else:
                workflowable.name = ''

    @api.depends('workflow_process_ids')
    def _compute_default_workflow_process(self):
        for workflowable in self:
            if len(workflowable.workflow_process_ids) > 0:
                print("Default Id : ", workflowable.workflow_process_ids.ids[0])
                return workflowable.workflow_process_ids.ids[0]
            else:
                return None

    @api.depends('workflow_process_ids')
    def _compute_is_processed(self):
        for workflowable in self:
            if len(workflowable.workflow_process_ids) > 0:
                workflowable.is_processed = True
            else:
                workflowable.is_processed = False

    @api.depends('workflow_process_ids')
    def _compute_is_multi_processed(self):
        for workflowable in self:
            if len(workflowable.workflow_process_ids) > 1:
                workflowable.is_multi_processed = True
            else:
                workflowable.is_multi_processed = False

    @api.depends('displayed_workflow_process_id', 'process_buttons')
    def _compute_process_buttons(self):
        for workflowable in self:
            workflowable.process_buttons = None
            if workflowable.displayed_workflow_process_id:
                workflowable.process_buttons = ''
                workflowable_position = self.env['workflowable.position'].search([
                    '&',
                    ('workflowable_id', '=', workflowable.id),
                    ('workflow_process_id', '=', workflowable.displayed_workflow_process_id.id),
                ], limit=1)
                if workflowable_position.exists():
                    workflowable.process_buttons = workflowable_position.process_buttons

    def _automatic_procedures_domain(self):
        return [('id', 'in', self.workflow_procedure_ids.mapped('id'))]

    def _workflow_procedures_domain(self):
        return [('workflowable_type_id', '=', self.workflowable_type_id.id)]

    def _manual_procedures_domain(self):
        return [
            '&', ('id', 'in', self.workflow_procedure_ids.mapped('id')),
            ('id', 'not in', self.automatic_workflow_procedure_ids.mapped('id'))
        ]

    def _triggered_manual_procedures_domain(self):
        return [('id', 'in', self.manual_workflow_procedure_ids.mapped('id'))]

    def _awaiting_manual_procedures_domain(self):
        return [
            '&', ('id', 'in', self.manual_workflow_procedure_ids.mapped('id')),
            ('id', 'not in', self.triggered_manual_workflow_procedure_ids.mapped('id'))
        ]

    @api.depends('displayed_workflow_process_id', 'workflow_process_stage_id')
    def _compute_process_stage(self):
        for workflowable in self:
            workflowable.workflow_process_stage_id = None
            if workflowable.displayed_workflow_process_id:
                workflowable_position = self.env['workflowable.position'].search([
                    '&', ('workflowable_id', '=', workflowable.id),
                    ('workflow_process_id', '=', workflowable.displayed_workflow_process_id.id)
                ], limit=1)
                if not workflowable_position.exists():
                    workflowable_position = self.env['workflowable.position'].search([
                        '&', ('workflowable_id', '=', self.env.context.get('active_id')),
                        ('workflow_process_id', '=', workflowable.displayed_workflow_process_id.id)
                    ], limit=1)
                if not workflowable_position.exists() and self.env.context.get('params', False):
                    workflowable_position = self.env['workflowable.position'].search([
                        '&', ('workflowable_id', '=', self.env.context.get('params').get('id')),
                        ('workflow_process_id', '=', workflowable.displayed_workflow_process_id.id)
                    ], limit=1)
                if workflowable_position.exists():
                    workflowable.workflow_process_stage_id = workflowable_position.workflow_process_stage_id.id

    @api.depends('displayed_workflow_process_id', 'workflow_process_stage_id', 'state')
    def _compute_current_state(self):
        for workflowable in self:
            if workflowable.displayed_workflow_process_id:
                workflowable_position = self.env['workflowable.position'].search([
                    '&', ('workflowable_id', '=', workflowable.id),
                    ('workflow_process_id', '=', workflowable.displayed_workflow_process_id.id)
                ], limit=1)
                if not workflowable_position.exists():
                    workflowable_position = self.env['workflowable.position'].search([
                        '&', ('workflowable_id', '=', self.env.context.get('active_id')),
                        ('workflow_process_id', '=', workflowable.displayed_workflow_process_id.id)
                    ], limit=1)
                if not workflowable_position.exists() and self.env.context.get('params', False):
                    workflowable_position = self.env['workflowable.position'].search([
                        '&', ('workflowable_id', '=', self.env.context.get('params').get('id')),
                        ('workflow_process_id', '=', workflowable.displayed_workflow_process_id.id)
                    ], limit=1)
                if workflowable_position.exists() and workflowable.workflow_process_stage_id.exists():
                    displayed_state = workflowable.workflow_process_stage_id.workflow_state_id.codename
                    if workflowable.workflow_process_stage_id.cancelled:
                        displayed_state = workflowable.workflow_process_stage_id.cancel_workflow_state_id.codename
                    if workflowable.workflow_process_stage_id.breaked:
                        displayed_state = workflowable.workflow_process_stage_id.break_workflow_state_id.codename
                    if workflowable.workflow_process_stage_id.resumed:
                        displayed_state = workflowable.workflow_process_stage_id.resume_workflow_state_id.codename
                    states = schema.compute_state_selection(workflowable_position)
                    for state in states:
                        if state[0] == displayed_state:
                            workflowable.state = state[0]
                            break

    workflowable_type_id = fields.Many2one('workflowable.type', required=True,
                                           string='Type')
    model = fields.Char(string="Model", required=True, related="workflowable_type_id.name",
                        readonly=True)
    object_id = fields.Integer(string="Object Id", required=True, default=0)
    name = fields.Char(string="Name", readonly=True, required=False, compute="_compute_name")
    workflow_procedure_ids = fields.Many2many('workflow.procedure', string="Procedures",
                                              relation="workflowable_all_procedures",
                                              domain=_workflow_procedures_domain)
    automatic_workflow_procedure_ids = fields.Many2many('workflow.procedure',
                                                        relation="workflowable_automatic_procedures",
                                                        string="Automatic Procedures",
                                                        domain=_automatic_procedures_domain)
    manual_workflow_procedure_ids = fields.Many2many('workflow.procedure',
                                                     relation="workflowable_manual_procedures",
                                                     string="Manual Procedures",
                                                     domain=_manual_procedures_domain)
    triggered_manual_workflow_procedure_ids = fields.Many2many('workflow.procedure',
                                                               relation="workflowable_triggered_manual_procedures",
                                                               string="Triggered Manual Procedures",
                                                               domain=_triggered_manual_procedures_domain)
    awaiting_manual_workflow_procedure_ids = fields.Many2many('workflow.procedure',
                                                              relation="workflowable_awaiting_manual_procedures",
                                                              string="Awaiting Manual Procedures",
                                                              domain=_awaiting_manual_procedures_domain)
    workflow_process_ids = fields.One2many('workflow.process',
                                           'workflowable_id',
                                           domain=[('base_process', '=', True)])
    workflowable_position_ids = fields.One2many('workflowable.position',
                                                'workflowable_id', string="Positions")
    displayed_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                                    string="Displayed Process",
                                                    default=_compute_default_workflow_process)
    workflow_process_stage_id = fields.Many2one('workflow.process.stage', required=False,
                                                compute="_compute_process_stage")
    process_buttons = fields.Html(required=False, compute="_compute_process_buttons")
    state = schema.DynamicSelection(selection=schema.compute_state_selection, string="State", store=True,
                                    required=False, compute="_compute_current_state")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    is_processed = fields.Boolean(readonly=True, required=False, compute="_compute_is_processed")
    is_multi_processed = fields.Boolean(readonly=True, required=False,
                                        compute="_compute_is_multi_processed")

    def read(self, fields=None, load='_classic_read'):
        res = super(Workflowable, self).read(fields, load)
        fields_list = ['workflowable_id', 'workflow_process_id', 'workflow_process_stage_id',
                       'state', 'company_id', 'active']
        for workflowable in self:
            for position in workflowable.workflowable_position_ids:
                position.read(fields_list, load)
        return res

    def trigger_manual_procedures(self):
        wizard = self.env['workflowable.manual.procedure.trigger.wizard'].create({
            'workflowable_id': self.id
        })
        return {
            'name': _('Trigger Procedures Manually'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflowable.manual.procedure.trigger.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new'
        }

    def action_process(self):
        workflowable_position = self.env['workflowable.position'].search([
            '&',
            ('workflowable_id', '=', self.id),
            ('workflow_process_id', '=', self.displayed_workflow_process_id.id),
        ], limit=1)
        if workflowable_position.exists():
            workflowable_position.with_env(self.env).action_process()
        return {'type': 'ir.actions.client', 'tag': 'reload'}

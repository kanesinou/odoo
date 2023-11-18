# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Workflowable(models.Model):
    _name = "workflowable"
    _description = "Workflowable"
    _sql_constraints = [
        ('reference_company_uniq', 'unique (workflowable_type_id,object_id,company_id)', 'The reference(model + '
                                                                                         'primary key) of the '
                                                                                         'workflowable must be unique '
                                                                                         'per company !')
    ]


    @api.onchange('displayed_workflow_process_id')
    def _onchange_displayed_position(self):
        if self.displayed_workflow_process_id:
            self.compute_displayed_processbar()

    @api.depends('object_id')
    def _compute_name(self):
        for workflowable in self:
            record = self.env[workflowable.workflowable_type_id.model_id.model].search([
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
                workflowable.displayed_workflow_process_id = workflowable.workflow_process_ids[0].id
                print("Displayed Workflow : ", workflowable.displayed_workflow_process_id)

    @api.onchange('workflowable_position_ids')
    def _onchange_workflowable_position_ids(self):
        if len(self.workflowable_position_ids) > 0:
            for workflowable_position in self.workflowable_position_ids:
                workflowable_position.compute_current_state

    workflowable_type_id = fields.Many2one('workflowable.type', required=True,
                                           string='Type')
    model = fields.Char(string="Model", required=True, related="workflowable_type_id.name",
                        readonly=True)
    object_id = fields.Integer(string="Object Id", required=True, default=0)
    name = fields.Char(string="Name", readonly=True, required=False, compute="_compute_name")
    workflow_process_ids = fields.One2many('workflow.process',
                                           'workflowable_id')
    workflowable_position_ids = fields.One2many('workflowable.position',
                                                'workflowable_id', string="Positions")
    displayed_workflow_process_id = fields.Many2one('workflow.process', required=False,
                                                    store=False, string="Displayed Process",
                                                    default="_compute_default_workflow_process",
                                                    domain="[('id', 'in', workflow_process_ids)]")
    displayed_workflow_processbar = fields.Html(string="Displayed Workflow Processbar", store=False,
                                                required=False, compute="compute_displayed_processbar")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    def read(self, fields=None, load='_classic_read'):
        res = super(Workflowable, self).read(fields, load)
        fields_list = ['workflowable_id', 'workflow_process_id', 'workflow_process_stage_id',
                       'state', 'company_id', 'active']
        for workflowable in self:
            for position in workflowable.workflowable_position_ids:
                position.read(fields_list, load)
        return res

    def compute_displayed_processbar(self):
        for workflowable in self:
            if workflowable.displayed_workflow_process_id:
                workflowable_position = self.env['workflowable.position'].search([
                    '&', ('workflow_process_id', '=', workflowable.displayed_workflow_process_id.id),
                    '&',
                    ('workflowable_id.workflowable_type_id', '=', workflowable.workflowable_type_id.id),
                    ('workflowable_id.object_id', '=', workflowable.object_id),
                ])
                print("Workflowable Position : ", workflowable_position)
                processbar_string = ''
                if workflowable_position:
                    for next_stage_data in workflowable_position.get_next_stages_data():
                        action_name = next_stage_data[0].name
                        button_string = "<button name='action_release_workflow_procedure'" +\
                            "string='%s' type='object' class='oe_highlight'" % action_name +\
                            "title='%s the %s' />" % (action_name, workflowable.name)
                        processbar_string += button_string
                    processbar_string += "<field name='state' widget='statusbar' class='o_field_statusbar' />"
                workflowable.displayed_workflow_processbar = processbar_string
            else:
                workflowable.displayed_workflow_processbar = ''

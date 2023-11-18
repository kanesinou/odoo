# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command


def get_corresponding_procedure_stage_data(workflow_stage_record):
    data = {
        'codename': workflow_stage_record.codename + '_procedure_stage',
        'name': workflow_stage_record.name + ' Procedure Stage',
        'workflow_stage_id': workflow_stage_record.id
    }
    for required_workflow_job in workflow_stage_record.required_workflow_job_ids:
        if not data.get('workflow_procedure_execution_ids'):
            data['workflow_procedure_execution_ids'] = [
                Command.create({
                    'mandatory': True, 'workflow_job_id': required_workflow_job.id
                })
            ]
        else:
            data['workflow_procedure_execution_ids'].append(
                Command.create({
                    'mandatory': True, 'workflow_job_id': required_workflow_job.id
                })
            )
    for optional_workflow_job in workflow_stage_record.optional_workflow_job_ids:
        if not data.get('workflow_procedure_execution_ids'):
            data['workflow_procedure_execution_ids'] = [
                Command.create({
                    'mandatory': False, 'workflow_job_id': optional_workflow_job.id
                })
            ]
        else:
            data['workflow_procedure_execution_ids'].append(
                Command.create({
                    'mandatory': False, 'workflow_job_id': optional_workflow_job.id
                })
            )
    return data


def get_corresponding_procedure_data(workflow_record, workflowable_type_id, collector):
    if not workflow_record.base_workflow:
        data = {
            'codename': workflow_record.codename + '_procedure',
            'name': workflow_record.name + ' Procedure',
            'base_procedure': workflow_record.base_workflow,
            'activity_procedure': workflow_record.activity_workflow,
            'workflow_id': workflow_record.id,
            'workflowable_type_id': workflowable_type_id
        }
    else:
        data = {}
    if len(workflow_record.workflow_stage_ids) > 0:
        for workflow_stage in workflow_record.workflow_stage_ids:
            if not collector.get('workflow_procedure_stage_ids'):
                collector['workflow_procedure_stage_ids'] = [
                    Command.create(get_corresponding_procedure_stage_data(workflow_stage))
                ]
            else:
                collector['workflow_procedure_stage_ids'].append(
                    Command.create(get_corresponding_procedure_stage_data(workflow_stage))
                )
        return collector
    elif len(workflow_record.workflow_ids) == 0:
        if not collector:
            return data
        else:
            if not collector.get('workflow_procedure_ids'):
                collector['workflow_procedure_ids'] = [
                    Command.create(data)
                ]
            else:
                collector['workflow_procedure_ids'].append(
                    Command.create(data)
                )
            return collector
    else:
        for workflow in workflow_record.workflow_ids:
            procedure_data = get_corresponding_procedure_data(
                workflow, workflowable_type_id, data
            )
            if not collector.get('workflow_procedure_ids'):
                collector['workflow_procedure_ids'] = [
                    Command.create(procedure_data)
                ]
            else:
                collector['workflow_procedure_ids'].append(
                    Command.create(procedure_data)
                )
        return collector


def get_corresponding_procedure_transition_data(workflow_transition_record, root_procedure_id):
    data = {}
    from_workflow_procedure = workflow_transition_record.env['workflow.procedure'].search([
        '&', ('root_workflow_procedure_id', '=', root_procedure_id),
        ('workflow_id', '=', workflow_transition_record.from_workflow_id.id)
    ])
    to_workflow_procedure = workflow_transition_record.env['workflow.procedure'].search([
        '&', ('root_workflow_procedure_id', '=', root_procedure_id),
        ('workflow_id', '=', workflow_transition_record.to_workflow_id.id)
    ])
    if from_workflow_procedure and to_workflow_procedure:
        data['context_type'] = workflow_transition_record.context_type
        data['workflow_transition_id'] = workflow_transition_record.id
        data['from_workflow_procedure_id'] = from_workflow_procedure.id
        data['to_workflow_procedure_id'] = to_workflow_procedure.id
    return data


def get_corresponding_procedure_transitions_data(workflow_record, root_procedure_id):
    transitions_data = []
    for workflow_transition in workflow_record.workflow_transition_ids:
        corresponding_procedure_transition_data = get_corresponding_procedure_transition_data(
            workflow_transition, root_procedure_id
        )
        transitions_data.append(corresponding_procedure_transition_data)
    return transitions_data


def get_corresponding_procedure_transition_transitions_data(
        workflow_transition_record, root_procedure_id
):
    transitions_data = []
    for workflow_transition in workflow_transition_record.workflow_transition_ids:
        corresponding_procedure_transition_data = get_corresponding_procedure_transition_data(
            workflow_transition, root_procedure_id
        )
        transitions_data.append(corresponding_procedure_transition_data)
    return transitions_data


def create_corresponding_procedure_transitions_structure(workflow_record):
    if len(workflow_record.workflow_transition_ids) > 0:
        procedure_transitions_data = get_corresponding_procedure_transitions_data(workflow_record)
        if len(procedure_transitions_data) > 0:
            corresponding_procedure = workflow_record.get_workflow_procedure_by_id(
                workflow_record.id
            )
            new_transitions_commands = []
            for procedure_transition_data in procedure_transitions_data:
                new_transitions_commands.append(Command.create(procedure_transition_data))
            corresponding_procedure.env.write({
                'workflow_procedure_transition_ids': new_transitions_commands
            })
    if len(workflow_record.workflow_ids) == 0:
        return
    else:
        for sub_workflow in workflow_record.workflow_ids:
            create_corresponding_procedure_transitions_structure(sub_workflow)


def get_corresponding_procedure_stage_transition_data(
        workflow_stage_transition_record, root_procedure_id
):
    data = {}
    workflow_stage_transition = workflow_stage_transition_record.env['workflow.stage.transition'].search([
        ('id', '=', workflow_stage_transition_record.id)
    ], limit=1)
    from_workflow_procedure_stage = workflow_stage_transition_record.env['workflow.procedure.stage'].search([
        '&', ('root_workflow_procedure_id', '=', root_procedure_id),
        ('workflow_stage_id', '=', workflow_stage_transition.from_workflow_stage_id.id)
    ], limit=1)
    to_workflow_procedure_stage = workflow_stage_transition_record.env['workflow.procedure.stage'].search([
        '&', ('root_workflow_procedure_id', '=', root_procedure_id),
        ('workflow_stage_id', '=', workflow_stage_transition.to_workflow_stage_id.id)
    ], limit=1)
    if from_workflow_procedure_stage and to_workflow_procedure_stage:
        data['context_type'] = workflow_stage_transition.context_type
        data['workflow_stage_transition_id'] = workflow_stage_transition.id
        data['from_workflow_procedure_stage_id'] = from_workflow_procedure_stage.id
        data['to_workflow_procedure_stage_id'] = to_workflow_procedure_stage.id
    return data


def get_corresponding_procedure_stage_transitions_data(workflow_record, root_procedure_id):
    transitions_data = []
    for workflow_stage_transition in workflow_record.workflow_stage_transition_ids:
        corresponding_procedure_stage_transition_data = get_corresponding_procedure_stage_transition_data(
            workflow_stage_transition, root_procedure_id
        )
        transitions_data.append(corresponding_procedure_stage_transition_data)
    return transitions_data


def get_corresponding_procedure_transition_stage_transitions_data(
        workflow_transition_record, root_procedure_id
):
    transitions_data = []
    for workflow_stage_transition in workflow_transition_record.workflow_stage_transition_ids:
        corresponding_procedure_stage_transition_data = get_corresponding_procedure_stage_transition_data(
            workflow_stage_transition, root_procedure_id
        )
        transitions_data.append(corresponding_procedure_stage_transition_data)
    return transitions_data


def create_corresponding_procedure_stage_transitions_structure(workflow_record):
    if len(workflow_record.workflow_stage_transition_ids) > 0:
        procedure_stage_transitions_data = get_corresponding_procedure_stage_transitions_data(workflow_record)
        if len(procedure_stage_transitions_data) > 0:
            corresponding_procedure = workflow_record.get_workflow_procedure_by_id(
                workflow_record.id
            )
            new_stage_transitions_commands = []
            for procedure_stage_transition_data in procedure_stage_transitions_data:
                new_stage_transitions_commands.append(Command.create(procedure_stage_transition_data))
            corresponding_procedure.env.write({
                'workflow_procedure_stage_transition_ids': new_stage_transitions_commands
            })
    if len(workflow_record.workflow_ids) == 0:
        return
    else:
        for sub_workflow in workflow_record.workflow_ids:
            create_corresponding_procedure_stage_transitions_structure(sub_workflow)


def get_root_workflow_id(workflow_record):
    if not workflow_record.parent_id:
        return workflow_record.id
    else:
        return get_root_workflow_id(workflow_record.parent_id)


class Workflow(models.Model):
    _name = "workflow"
    _description = "Workflow"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow must be unique per '
                                                                  'company !')
    ]

    @api.onchange("base_workflow", "parent_allowed")
    def _onchange_base_workflow(self):
        if self.base_workflow:
            self.parent_allowed = False
        else:
            self.parent_allowed = True

    @api.onchange("activity_workflow", "children_allowed", "states_allowed", "stages_allowed")
    def _onchange_activity_workflow(self):
        if self.activity_workflow:
            self.children_allowed = False
            self.states_allowed = True
            self.stages_allowed = True
        else:
            self.children_allowed = True
            self.states_allowed = False
            self.stages_allowed = False

    @api.onchange('workflow_ids', 'sub_transitions_allowed')
    def _onchange_workflow_ids(self):
        if len(self.workflow_ids) <= 1:
            self.sub_transitions_allowed = False
        else:
            self.sub_transitions_allowed = True

    @api.onchange('workflow_stage_ids', 'stage_transitions_allowed', 'workflow_state_ids')
    def _onchange_workflow_stage_ids(self):
        if len(self.workflow_stage_ids) <= 1:
            self.stage_transitions_allowed = False
        else:
            self.stage_transitions_allowed = True
        if len(self.workflow_stage_ids) > 0:
            states_commands = []
            for stage in self.workflow_stage_ids:
                if stage.workflow_state_id not in self.workflow_state_ids:
                    states_commands.append(Command.link(stage.workflow_state_id.id))
            self.write({'workflow_state_ids': states_commands})

    @api.depends('parent_id')
    def _compute_root_workflow(self):
        for workflow in self:
            workflow.root_workflow_id = get_root_workflow_id(workflow)

    codename = fields.Char(string='Codename', required=True, size=64, copy=False)
    name = fields.Char(string='Name', required=True, translate=True)
    base_workflow = fields.Boolean(default=False, string="Base ?")
    activity_workflow = fields.Boolean(default=False, string="Activity ?")
    root_workflow_id = fields.Many2one('workflow', required=False, readonly=True,
                                       string="Root Workflow", compute="_compute_root_workflow",
                                       store=True)
    parent_id = fields.Many2one('workflow', string="Parent Workflow")
    workflow_ids = fields.One2many('workflow', 'parent_id',
                                   string="Sub workflows")
    workflow_procedure_ids = fields.One2many('workflow.procedure',
                                             'workflow_id', string='Procedures')
    workflow_transition_ids = fields.One2many('workflow.transition',
                                              'workflow_id',
                                              string="Workflow Transitions")
    workflow_stage_ids = fields.One2many('workflow.stage', 'workflow_id',
                                         string="Workflow Stages")
    workflow_stage_transition_ids = fields.One2many('workflow.stage.transition',
                                                    'workflow_id',
                                                    string="Workflow Stage Transitions")
    inbound_workflow_transition_ids = fields.One2many('workflow.transition',
                                                      'to_workflow_id',
                                                      string="Inbound Workflow Transitions")
    outbound_workflow_transition_ids = fields.One2many('workflow.transition',
                                                       'from_workflow_id',
                                                       string="Outbound Workflow Transitions")
    workflow_state_ids = fields.Many2many('workflow.state',
                                          'workflow_workflow_state',
                                          string='States')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    parent_allowed = fields.Boolean(invisible=True, default=True)
    children_allowed = fields.Boolean(invisible=True, default=True)
    states_allowed = fields.Boolean(invisible=True, default=False)
    stages_allowed = fields.Boolean(invisible=True, default=False)
    stage_transitions_allowed = fields.Boolean(invisible=True, default=False)
    sub_transitions_allowed = fields.Boolean(invisible=True, default=False)

    def initialize_corresponding_procedure_structure(self, workflowable_type_id):
        for workflow in self:
            if workflow.base_workflow:
                procedure_data = get_corresponding_procedure_data(
                    workflow, workflowable_type_id, {}
                )
                self.env['workflow.procedure'].create(procedure_data)
                corresponding_base_procedure = workflow.get_workflow_procedure_by_id(workflow.id)
                if corresponding_base_procedure is not None and corresponding_base_procedure.new_procedure:
                    create_corresponding_procedure_transitions_structure(workflow)
                    create_corresponding_procedure_stage_transitions_structure(workflow)
                    corresponding_base_procedure.env['workflow.procedure'].write({
                        'released': True, 'new_procedure': False
                    })

    def get_corresponding_base_procedure_data(self, workflowable_type_id):
        if self.base_workflow:
            return get_corresponding_procedure_data(
                self, workflowable_type_id, {}
            )

    def get_corresponding_procedure_stage_transitions_data(self, root_procedure_id):
        return get_corresponding_procedure_stage_transitions_data(self, root_procedure_id)

    def get_corresponding_procedure_transitions_data(self, root_procedure_id):
        return get_corresponding_procedure_transitions_data(self, root_procedure_id)

    @api.model
    def find_procedure_by_workflow_id(self, root_workflow_id, workflow_id):
        return self.env['workflow.procedure'].search([
            '&', ('workflow_id.root_workflow_id', '=', root_workflow_id),
            ('workflow_id', '=', workflow_id)
        ], limit=1)

    def get_workflow_procedures_by_id(self, workflow_id):
        return self.workflow_procedure_ids.filtered(lambda p: p.id == workflow_id)

    def get_workflow_procedure_by_id(self, workflow_id):
        records = self.get_workflow_procedures_by_id(workflow_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedures_by_ids(self, workflow_ids):
        return self.workflow_procedure_ids.filtered(lambda p: p.id in workflow_ids)

    def get_child_workflows_by_id(self, workflow_id):
        return self.workflow_ids.filtered(lambda w: w.id == workflow_id)

    def get_child_workflow_by_id(self, workflow_id):
        records = self.get_child_workflows_by_id(workflow_id)
        if len(records) > 0:
            return records[0]
        return

    def get_child_workflows_by_ids(self, workflow_ids):
        return self.workflow_ids.filtered(lambda w: w.id in workflow_ids)

    def get_workflow_stages_by_id(self, stage_id):
        return self.workflow_stage_ids.filtered(lambda s: s.id == stage_id)

    def find_workflow_stage_by_id(self, stage_id):
        records = self.get_workflow_stages_by_id(stage_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_stages_by_ids(self, stage_ids):
        return self.workflow_stage_ids.filtered(lambda s: s.id in stage_ids)

    def get_workflow_states_by_id(self, state_id):
        return self.workflow_state_ids.filtered(lambda s: s.id == state_id)

    def get_workflow_state_by_id(self, state_id):
        records = self.get_workflow_states_by_id(state_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_states_by_ids(self, state_ids):
        return self.workflow_state_ids.filtered(lambda s: s.id in state_ids)

    def get_workflow_transitions_by_id(self, transition_id):
        return self.workflow_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_workflow_transition_by_id(self, transition_id):
        records = self.get_workflow_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_transitions_by_ids(self, transition_ids):
        return self.workflow_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_workflow_stage_transitions_by_id(self, transition_id):
        return self.workflow_stage_transition_ids.filtered(lambda st: st.id == transition_id)

    def get_workflow_stage_transition_by_id(self, transition_id):
        records = self.get_workflow_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_stage_transitions_by_ids(self, transition_ids):
        return self.workflow_stage_transition_ids.filtered(lambda st: st.id in transition_ids)

    def get_inbound_workflow_transitions_by_id(self, transition_id):
        return self.inbound_workflow_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_inbound_workflow_transition_by_id(self, transition_id):
        records = self.get_inbound_workflow_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_inbound_workflow_transitions_by_ids(self, transition_ids):
        return self.inbound_workflow_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_outbound_workflow_transitions_by_id(self, transition_id):
        return self.outbound_workflow_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_outbound_workflow_transition_by_id(self, transition_id):
        records = self.get_outbound_workflow_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_outbound_workflow_transitions_by_ids(self, transition_ids):
        return self.outbound_workflow_transition_ids.filtered(lambda t: t.id in transition_ids)

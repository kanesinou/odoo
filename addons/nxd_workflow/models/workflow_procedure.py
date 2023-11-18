# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command


def register_workflowable(procedure_record, record_id):
    workflowable = procedure_record.env['workflowable'].search([
        '&', ('workflowable_type_id', '=', procedure_record.workflowable_type_id.id),
        ('object_id', '=', record_id)
    ])
    if not workflowable:
        workflowable_data = {
            'workflowable_type_id': procedure_record.workflowable_type_id.id,
            'object_id': record_id
        }
        """return workflowable_data"""
        return procedure_record.env['workflowable'].create(workflowable_data)


def get_model_procedures(env, model_name):
    return env['workflow.procedure'].search([('workflowable_type_id.model_id.model', '=', model_name)])


def register_procedure_listener(base_procedure_record):
    action_data = {
        'model_id': base_procedure_record.workflowable_type_id.model_id.id,
        'name': _('%s Process Trigger') % base_procedure_record.name,
        'state': 'code',
        'type': 'ir.actions.server',
        'usage': 'base_automation',
        'code': "env['workflow.procedure'].register_processes(record._name, record.id)"
    }
    automation_data = {
        'action_server_id': base_procedure_record.env['ir.actions.server'].create(action_data).id,
        'trigger': 'on_create'
    }
    base_procedure_record.env['base.automation'].create(automation_data)


def get_corresponding_base_process_data(base_procedure_record, record_id):
    workflowable = base_procedure_record.env['workflowable'].search([
        '&', ('workflowable_type_id', '=', base_procedure_record.workflowable_type_id.id),
        ('object_id', '=', record_id)
    ])
    if workflowable:
        data = {
            'codename': base_procedure_record.codename + '_%d_process' % record_id,
            'name': base_procedure_record.name + ' %s Process' % record_id,
            'base_process': base_procedure_record.base_procedure,
            'activity_process': base_procedure_record.activity_procedure,
            'workflow_procedure_id': base_procedure_record.id,
            'start_datetime': fields.Datetime.now(),
            'workflowable_id': workflowable.id
        }
        if base_procedure_record.starter_workflow_procedure_id:
            init_data = {
                'start_datetime': data['start_datetime'],
                'workflowable_record': workflowable
            }
            data = get_corresponding_process_starter_descendants_data(
                base_procedure_record.starter_workflow_procedure_id, init_data, data
            )
        if base_procedure_record.workflow_procedure_stage_id:
            init_data = {
                'start_datetime': data['start_datetime'],
                'workflowable_record': workflowable
            }
            data = get_corresponding_process_starter_descendants_data(
                base_procedure_record, init_data, data
            )
        return data
    return {}


def get_corresponding_process_starter_descendants_data(procedure_record, init_data, collector):
    if procedure_record.base_procedure:
        if not collector:
            collector = {}
    workflowable = init_data.get('workflowable_record')
    start_datetime = init_data.get('start_datetime')
    if not procedure_record.base_procedure:
        data = {
            'codename': procedure_record.codename + '_%d_process' % workflowable.object_id,
            'name': procedure_record.name + ' %d Process' % workflowable.object_id,
            'base_process': procedure_record.base_procedure,
            'activity_process': procedure_record.activity_process,
            'workflow_procedure_id': procedure_record.id,
            'workflowable_id': workflowable.id
        }
        if start_datetime:
            data['start_datetime'] = start_datetime
        if not procedure_record.activity_procedure and procedure_record.starter_workflow_procedure_id:
            starter_process_data = get_corresponding_process_starter_descendants_data(
                procedure_record.starter_workflow_process_id, init_data, data
            )
            if not collector.get('workflow_process_ids'):
                collector['workflow_process_ids'] = [Command.create(starter_process_data)]
            else:
                collector['workflow_process_ids'].append(Command.create(starter_process_data))
    if procedure_record.activity_procedure and procedure_record.workflow_procedure_stage_id:
        starter_process_stage_data = {
            'codename': procedure_record.codename + '_%d_process_stage' % workflowable.object_id,
            'name': procedure_record.name + ' %d Process Stage' % workflowable.object_id,
            'workflow_procedure_stage_id': procedure_record.workflow_procedure_stage_id.id,
        }
        if start_datetime:
            starter_process_stage_data['start_datetime'] = start_datetime
        if not collector.get('workflow_process_stage_ids'):
            collector['workflow_process_stage_ids'] = [Command.create(starter_process_stage_data)]
        else:
            collector['workflow_process_stage_ids'].append(Command.create(starter_process_stage_data))
    return collector


def get_workflow_process_starter_stage(workflow_process_record):
    return workflow_process_record.env['workflow.process.stage'].search([(
        'workflow_procedure_stage_id.root_workflow_procedure_id',
        '=',
        workflow_process_record.workflow_procedure_id.id
    )], limit=1)


def get_root_workflow_procedure_id(workflow_procedure_record):
    if not workflow_procedure_record.parent_id:
        return workflow_procedure_record.id
    else:
        return get_root_workflow_procedure_id(workflow_procedure_record.parent_id)


def expand_starters(workflow_procedure_record):
    if workflow_procedure_record.parent_id:
        parent = workflow_procedure_record.parent_id
        parent.workflow_procedure_stage_id = workflow_procedure_record.workflow_procedure_stage_id.id
        parent.starter_workflow_procedure_id = workflow_procedure_record.id
        if not parent.base_procedure:
            expand_starters(parent)
    elif workflow_procedure_record.base_procedure:
        workflow_procedure_record.starter_workflow_procedure_id = workflow_procedure_record.id


def unexpand_starters(workflow_procedure_record):
    if workflow_procedure_record.parent_id:
        parent = workflow_procedure_record.parent_id
        parent.workflow_procedure_stage_id = None
        parent.starter_workflow_procedure_id = None
        if not parent.base_procedure:
            unexpand_starters(parent)
    elif workflow_procedure_record.base_procedure:
        workflow_procedure_record.starter_workflow_procedure_id = None


def find_starter_workflow_procedure_stage(workflow_procedure_record):
    if workflow_procedure_record.activity_procedure:
        return workflow_procedure_record.workflow_procedure_stage_id
    else:
        return find_starter_workflow_procedure_stage(
            workflow_procedure_record.starter_workflow_procedure_id
        )


class WorkflowProcedure(models.Model):
    _name = "workflow.procedure"
    _description = "Workflow Procedure"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow procedure must be '
                                                                  'unique per company !')
    ]

    @api.onchange('workflow_id')
    def _onchange_workflow(self):
        if self.workflow_id:
            if self.workflow_id.activity_workflow:
                self.starter_stage_allowed = True
            else:
                self.starter_stage_allowed = False

    @api.onchange("base_procedure", "parent_allowed")
    def _onchange_base_procedure(self):
        if self.base_procedure:
            self.parent_allowed = False
        else:
            self.parent_allowed = True

    @api.onchange("activity_procedure", "children_allowed")
    def _onchange_activity_procedure(self):
        if self.activity_procedure:
            self.children_allowed = False
        else:
            self.children_allowed = True

    @api.onchange('workflow_procedure_stage_id', 'release_allowed', 'released')
    def _onchange_starter_stage(self):
        if self.workflow_procedure_stage_id and not self.released:
            self.release_allowed = True
        else:
            self.release_allowed = False

    @api.onchange('workflow_procedure_stage_id')
    def _on_change_starter_stage(self):
        if self.workflow_procedure_stage_id:
            expand_starters(self)
        else:
            unexpand_starters(self)

    @api.onchange('released')
    def _onchange_released(self):
        if self.released:
            self.release_allowed = False

    @api.depends('parent_id')
    def _compute_root_workflow_procedure(self):
        for procedure in self:
            procedure.root_workflow_procedure_id = get_root_workflow_procedure_id(procedure)

    codename = fields.Char(string='Codename', required=True, size=104, copy=False)
    name = fields.Char(string='Name', required=True, translate=True)
    base_procedure = fields.Boolean(string="Base ?", related="workflow_id.base_workflow")
    activity_procedure = fields.Boolean(string="Activity ?", related="workflow_id.activity_workflow")
    released = fields.Boolean(string="Released ?", default=False)
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 compute="_compute_root_workflow_procedure")
    workflow_id = fields.Many2one('workflow', string="Workflow",
                                  required=True)
    workflowable_type_id = fields.Many2one('workflowable.type', ondelete='cascade',
                                           string="Model",  required=True, auto_join=True)
    state = fields.Selection(selection=[('new', 'New'), ('released', 'Released'), ('unreleased', 'Unreleased')],
                             string="State", required=True, default='new')
    starter_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                    readonly=True, invisible=True,
                                                    string="Starter Procedure")
    workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage',
                                                  string="Starter Stage", required=False,
                                                  domain="[('root_workflow_procedure_id', '=', root_workflow_procedure_id)]")
    parent_id = fields.Many2one('workflow.procedure', string="Parent")
    workflow_procedure_ids = fields.One2many('workflow.procedure',
                                             'parent_id', string="Sub Procedures")
    workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                        'workflow_procedure_id',
                                                        string="Procedure Transitions")
    workflow_procedure_stage_ids = fields.One2many('workflow.procedure.stage',
                                                   'workflow_procedure_id',
                                                   string="Procedure Stages")
    workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                              'workflow_procedure_id',
                                                              string="Procedure Stage Transitions")
    workflow_process_ids = fields.One2many('workflow.process',
                                           'workflow_procedure_id',
                                           string="Processes")
    workflow_procedure_collision_ids = fields.One2many('workflow.procedure.collision',
                                                       'workflow_procedure_id',
                                                       string="Procedure Collisions")
    inbound_workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                                'to_workflow_procedure_id',
                                                                string="Inbound Procedure Transitions")
    outbound_workflow_procedure_transition_ids = fields.One2many('workflow.procedure.transition',
                                                                 'from_workflow_procedure_id',
                                                                 string="Outbound Procedure Transitions")
    workflow_procedure_duration_ids = fields.One2many('workflow.procedure.duration',
                                                      'workflow_procedure_id',
                                                      string="Durations")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    parent_allowed = fields.Boolean(invisible=True, default=True)
    children_allowed = fields.Boolean(invisible=True, default=True)
    release_allowed = fields.Boolean(invisible=True, default=True)
    starter_stage_allowed = fields.Boolean(invisible=True, default=False)
    new_procedure = fields.Boolean(invisible=True, default=True)
    configured = fields.Boolean(invisible=True, default=False)

    def get_child_workflow_procedures_by_id(self, procedure_id):
        return self.workflow_procedure_ids.filtered(lambda p: p.id == procedure_id)

    def get_child_workflow_procedure_by_id(self, procedure_id):
        records = self.get_child_workflow_procedures_by_id(procedure_id)
        if len(records) > 0:
            return records[0]
        return

    def get_child_workflow_procedures_by_ids(self, procedure_ids):
        return self.workflow_procedure_ids.filtered(lambda p: p.id in procedure_ids)

    def get_workflow_processes_by_id(self, process_id):
        return self.workflow_process_ids.filtered(lambda p: p.id == process_id)

    def get_workflow_process_by_id(self, process_id):
        records = self.get_workflow_processes_by_id(process_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_processes_by_ids(self, process_ids):
        return self.workflow_process_ids.filtered(lambda p: p.id in process_ids)

    def get_workflow_procedure_transitions_by_id(self, transition_id):
        return self.workflow_procedure_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_workflow_procedure_transition_by_id(self, transition_id):
        records = self.get_workflow_procedure_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_transitions_by_ids(self, transition_ids):
        return self.workflow_procedure_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_workflow_procedure_stages_by_id(self, stage_id):
        return self.workflow_procedure_stage_ids.filtered(lambda s: s.id == stage_id)

    def get_workflow_procedure_stage_by_id(self, stage_id):
        records = self.get_workflow_procedure_stages_by_id(stage_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_stages_by_ids(self, stage_ids):
        return self.workflow_procedure_stage_ids.filtered(lambda s: s.id in stage_ids)

    def get_workflow_procedure_stage_transitions_by_id(self, transition_id):
        return self.workflow_procedure_stage_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_workflow_procedure_stage_transition_by_id(self, transition_id):
        records = self.get_workflow_procedure_stage_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_stage_transitions_by_ids(self, transition_ids):
        return self.workflow_procedure_stage_transition_ids.filtered(lambda p: p.id in transition_ids)

    def get_inbound_workflow_procedure_transitions_by_id(self, transition_id):
        return self.inbound_workflow_procedure_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_inbound_workflow_procedure_transition_by_id(self, transition_id):
        records = self.get_inbound_workflow_procedure_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_inbound_workflow_procedure_transitions_by_ids(self, transition_ids):
        return self.inbound_workflow_procedure_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_outbound_workflow_procedure_transitions_by_id(self, transition_id):
        return self.outbound_workflow_procedure_transition_ids.filtered(lambda t: t.id == transition_id)

    def get_outbound_workflow_procedure_transition_by_id(self, transition_id):
        records = self.get_outbound_workflow_procedure_transitions_by_id(transition_id)
        if len(records) > 0:
            return records[0]
        return

    def get_outbound_workflow_procedure_transitions_by_ids(self, transition_ids):
        return self.outbound_workflow_procedure_transition_ids.filtered(lambda t: t.id in transition_ids)

    def get_workflow_procedure_durations_by_id(self, duration_id):
        return self.workflow_procedure_duration_ids.filtered(lambda d: d.id == duration_id)

    def get_workflow_procedure_duration_by_id(self, duration_id):
        records = self.get_workflow_procedure_durations_by_id(duration_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_durations_by_ids(self, duration_ids):
        return self.workflow_procedure_duration_ids.filtered(lambda d: d.id in duration_ids)

    def get_workflow_procedure_collisions_by_id(self, collision_id):
        return self.workflow_procedure_collision_ids.filtered(lambda c: c.id == collision_id)

    def get_workflow_procedure_collision_by_id(self, collision_id):
        records = self.get_workflow_procedure_collisions_by_id(collision_id)
        if len(records) > 0:
            return records[0]
        return

    def get_workflow_procedure_collisions_by_ids(self, collision_ids):
        return self.workflow_procedure_collision_ids.filtered(lambda c: c.id in collision_ids)

    def get_starter_workflow_procedure_stage(self):
        find_starter_workflow_procedure_stage(self)

    @api.model
    def register_processes(self, model_name, record_id):
        released_procedures = get_model_procedures(self.env, model_name)
        for released_procedure in released_procedures:
            register_workflowable(released_procedure, record_id)
            base_workflow_process = self.env['workflow.process'].create(
                get_corresponding_base_process_data(released_procedure, record_id)
            )
            starter_process_stage = get_workflow_process_starter_stage(base_workflow_process)
            if starter_process_stage and starter_process_stage.workflow_process_id:
                base_workflow_process.write({
                    'workflow_process_stage_id': starter_process_stage.id
                })
                starter_process_stage.workflow_process_id.expend_starter_descendants()
            starter_position_data = base_workflow_process.get_starter_position_data()
            if starter_position_data:
                starter_position = self.env['workflowable.position'].create(starter_position_data)
                starter_position.state = starter_position.workflow_process_stage_id.workflow_state_id.codename

    def action_release_workflow_procedure(self):
        register_procedure_listener(self)

    def action_configure_workflow_procedure(self):
        if self.base_procedure and self.workflow_id:
            structure_data = self.workflow_id.get_corresponding_base_procedure_data(
                self.workflowable_type_id.id
            )
            self.write(structure_data)
            transitions_data = self.workflow_id.get_corresponding_procedure_transitions_data(self.id)
            stage_transitions_data = self.workflow_id.get_corresponding_procedure_stage_transitions_data(
                self.id
            )
            if len(transitions_data) > 0:
                transition_commands = []
                for transition_data in transitions_data:
                    transition_commands.append(Command.create(transition_data))
                self.write({'workflow_procedure_transition_ids': transition_commands})
            if len(stage_transitions_data) > 0:
                stage_transition_commands = []
                for stage_transition_data in stage_transitions_data:
                    stage_transition_commands.append(Command.create(stage_transition_data))
                self.write({'workflow_procedure_stage_transition_ids': stage_transition_commands})

    def action_unrelease_workflow_procedure(self):
        pass

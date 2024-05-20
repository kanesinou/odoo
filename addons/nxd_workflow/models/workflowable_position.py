# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command
from ..ext import schema




def get_current_state(workflowable_position_records):
    states = schema.compute_state_selection(workflowable_position_records)
    for workflowable_position_record in workflowable_position_records:
        for state in states:
            if state[0] == workflowable_position_record.workflow_process_stage_id.workflow_state_id.codename:
                workflowable_position_record.state = state[0]
                break


class WorkflowablePosition(models.Model):
    _name = "workflowable.position"
    _description = "Workflowable Position"
    _sql_constraints = [
        ('position_company_uniq', 'unique (workflowable_id,workflow_process_id,company_id)', 'The workflowable must '
                                                                                             'be unique per workflow '
                                                                                             'process and per company '
                                                                                             '!')
    ]

    @api.onchange('workflow_process_id', 'workflowable_id')
    def _onchange_workflow_process_id(self):
        if self.workflow_process_id.exists() and self.workflowable_id.exists():
            get_current_state(self)

    @api.onchange('workflow_process_stage_id')
    def _onchange_workflow_process_stage(self):
        if self.workflow_process_stage_id.exists():
            self._compute_current_state()
            self._compute_process_buttons()

    @api.depends('workflow_process_stage_id', 'state')
    def _compute_current_state(self):
        for position in self:
            displayed_state = position.workflow_process_stage_id.workflow_state_id.codename
            if position.workflow_process_stage_id.cancelled:
                displayed_state = position.workflow_process_stage_id.cancel_workflow_state_id.codename
            if position.workflow_process_stage_id.breaked:
                displayed_state = position.workflow_process_stage_id.break_workflow_state_id.codename
            if position.workflow_process_stage_id.resumed:
                displayed_state = position.workflow_process_stage_id.resume_workflow_state_id.codename
            states = schema.compute_state_selection(position)
            for state in states:
                if state[0] == displayed_state:
                    position.state = state[0]
                    break

    @api.depends('workflowable_id', 'workflow_process_id')
    def _compute_name(self):
        for position in self:
            position.name = "%s Position On Process" % position.workflowable_id.name

    @api.depends('workflow_process_stage_id')
    def _compute_process_buttons(self):
        for position in self:
            if position.workflow_process_stage_id and not position.is_cancelled:
                position.process_buttons = position.create_process_buttons()

    @api.depends('workflow_process_stage_transition_id')
    def _compute_can_be_executed(self):
        for position in self:
            if not position.workflow_process_stage_transition_id:
                position.can_be_executed = True
            else:
                position.can_be_executed = position.workflow_process_stage_transition_id.can_be_executed

    name = fields.Char(string="Name", readonly=True, required=False, compute="_compute_name")
    workflowable_id = fields.Many2one('workflowable', required=True, readonly=True,
                                      string="Workflowable")
    workflow_process_id = fields.Many2one('workflow.process', required=True,
                                          readonly=True, string="Process")
    workflow_process_stage_id = fields.Many2one('workflow.process.stage',
                                                string="Current Stage", required=False)
    workflow_process_stage_transition_id = fields.Many2one('workflow.process.stage.transition',
                                                           required=False, readonly=True)
    state = schema.DynamicSelection(selection=schema.compute_state_selection, string="State", store=True,
                                    required=False, compute="_compute_current_state")
    process_buttons = fields.Html(store=False, required=False, compute="_compute_process_buttons",
                                  readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    is_returned = fields.Boolean(readonly=True, default=False)
    is_cancelled = fields.Boolean(readonly=True, related="workflow_process_stage_id.cancelled")
    can_be_executed = fields.Boolean(readonly=True, compute="_compute_can_be_executed")

    def read(self, fields=None, load='_classic_read'):
        dynamic_selection_fields = []
        for name in fields:
            field = self._fields.get(name)
            if isinstance(field, schema.DynamicSelection):
                dynamic_selection_fields.append(name)
        for position in self:
            for field_name in dynamic_selection_fields:
                position._fields.get(field_name).workflowable_id = position.workflowable_id.id
        res = super(WorkflowablePosition, self).read(fields, load)
        return res

    def compute_current_state(self):
        get_current_state(self)

    def _get_stages_data(self):
        self.ensure_one()
        procedure_stage = self.workflow_process_stage_id.workflow_procedure_stage_id
        stages = {
            'previous': procedure_stage.inbound_workflow_procedure_stage_transition_ids,
            'next': procedure_stage.outbound_workflow_procedure_stage_transition_ids,
            'cancel': False, 'break': False, 'resume': False
        }
        if procedure_stage.can_be_cancelled:
            stages['cancel'] = {
                'action_name': procedure_stage.cancel_action_name,
                'action_title': procedure_stage.cancel_action_title,
                'action_button_type': procedure_stage.cancel_button_type,
                'state': procedure_stage.cancel_workflow_state_id
            }
        if procedure_stage.can_be_breaked:
            stages['break'] = {
                'action_name': procedure_stage.break_action_name,
                'action_title': procedure_stage.break_action_title,
                'action_button_type': procedure_stage.break_button_type,
                'state': procedure_stage.break_workflow_state_id
            }
        if procedure_stage.can_be_resumed:
            stages['resume'] = {
                'action_name': procedure_stage.resume_action_name,
                'action_title': procedure_stage.resume_action_title,
                'action_button_type': procedure_stage.resume_button_type,
                'state': procedure_stage.resume_workflow_state_id
            }
        return stages

    def create_process_buttons(self):
        self.ensure_one()
        procedure_stage = self.workflow_process_stage_id.workflow_procedure_stage_id
        stages_data = self._get_stages_data()
        cancel_data = stages_data['cancel']
        break_data = stages_data['break']
        resume_data = stages_data['resume']
        action_user = self.env['workflow.user'].search([('res_users_id', '=', self.env.uid)])
        process_buttons_string = ''
        if self.can_be_executed:
            for procedure_stage_transition in stages_data['next']:
                if procedure_stage_transition.is_protected and not action_user.exists():
                    continue
                if procedure_stage_transition.is_protected and action_user.exists():
                    if not procedure_stage_transition.user_can_execute(action_user):
                        continue
                current_stage = procedure_stage_transition.from_workflow_procedure_stage_id
                current_state = current_stage.workflow_state_id
                next_stage = procedure_stage_transition.to_workflow_procedure_stage_id
                next_state = next_stage.workflow_state_id
                action_button_type = 'btn oe_highlight'
                if procedure_stage_transition.button_type:
                    action_button_type = procedure_stage_transition.button_type
                action_title = procedure_stage_transition.action_name
                if procedure_stage_transition.action_title:
                    action_title = procedure_stage_transition.action_title
                availability_states = current_state.codename
                context_data = '{\'procedure_stage_transition_id\': %d, ' % procedure_stage_transition.id +\
                               '\'is_return\': False, ' +\
                               '\'current_procedure_stage\': %d, ' % procedure_stage.id +\
                               '\'next_procedure_stage\': %d, ' % next_stage.id +\
                               '\'current_state\': %s, ' % procedure_stage.workflow_state_id.id +\
                               '\'next_state\': %s}' % next_state.id
                button_string = '&lt;button name="action_process" ' +\
                                'states="%s" ' % availability_states +\
                                'string="%s" type="object" ' % procedure_stage_transition.action_name +\
                                'title="%s" ' % action_title +\
                                'class="btn %s" ' % action_button_type +\
                                'context="%s"/&gt; ' % context_data
                process_buttons_string += button_string
            if not self.is_returned:
                for previous_procedure_stage_transition in stages_data['previous']:
                    if previous_procedure_stage_transition.can_return:
                        if previous_procedure_stage_transition.is_protected and not action_user.exists():
                            continue
                        if previous_procedure_stage_transition.is_protected and action_user.exists():
                            if not previous_procedure_stage_transition.user_can_execute(action_user):
                                continue
                        next_stage = previous_procedure_stage_transition.from_workflow_procedure_stage_id
                        next_state = next_stage.workflow_state_id
                        action_button_type = 'btn oe_highlight'
                        if previous_procedure_stage_transition.button_type:
                            action_button_type = previous_procedure_stage_transition.button_type
                        action_title = 'Review ' + previous_procedure_stage_transition.action_name
                        if previous_procedure_stage_transition.return_action_title:
                            action_title = previous_procedure_stage_transition.return_action_title
                        context_data = '{\'procedure_stage_transition_id\': %d, ' % previous_procedure_stage_transition.id + \
                                       '\'is_return\': True, ' + \
                                       '\'current_procedure_stage\': %d, ' % procedure_stage.id + \
                                       '\'next_procedure_stage\': %d, ' % next_stage.id + \
                                       '\'current_state\': %s, ' % procedure_stage.workflow_state_id.id + \
                                       '\'next_state\': %s}' % next_state.id
                        button_string = '&lt;button name="action_process" ' + \
                                        'states="%s" ' % procedure_stage.workflow_state_id.codename + \
                                        'string="%s" type="object" ' % previous_procedure_stage_transition.return_action_name + \
                                        'title="%s" ' % action_title + \
                                        'class="btn %s" ' % action_button_type + \
                                        'context="%s"/&gt; ' % context_data
                        process_buttons_string += button_string
        if break_data and procedure_stage.user_can_break(action_user) and not self.workflow_process_stage_id.breaked:
            break_action_name = break_data['action_name']
            break_state = break_data['state']
            break_button_type = 'btn-secondary'
            if break_data['action_button_type']:
                break_button_type = break_data['action_button_type']
            action_title = break_action_name
            if break_data['action_title']:
                action_title = break_data['action_title']
            context_data = '{\'current_procedure_stage\': %d, ' % procedure_stage.id +\
                           '\'next_procedure_stage\': %d, ' % procedure_stage.id +\
                           '\'current_state\': %s, ' % procedure_stage.workflow_state_id.id +\
                           '\'next_state\': %s, ' % break_state.id +\
                           '\'is_break\': True}'
            button_string = '&lt;button name="action_process" ' +\
                            'states="%s" ' % procedure_stage.workflow_state_id.codename +\
                            'string="%s" type="object" ' % break_action_name +\
                            'title="%s" ' % action_title +\
                            'class="btn %s oe_highlight" ' % break_button_type +\
                            'context="%s"/&gt; ' % context_data
            process_buttons_string += button_string
        if resume_data and procedure_stage.user_can_resume(action_user) and self.workflow_process_stage_id.breaked:
            resume_action_name = resume_data['action_name']
            resume_state = resume_data['state']
            resume_button_type = 'btn-success'
            if resume_data['action_button_type']:
                resume_button_type = resume_data['action_button_type']
            action_title = resume_action_name
            if resume_data['action_title']:
                action_title = resume_data['action_title']
            context_data = '{\'current_procedure_stage\': %d, ' % procedure_stage.id +\
                           '\'next_procedure_stage\': %d, ' % procedure_stage.id +\
                           '\'current_state\': %s, ' % procedure_stage.workflow_state_id.id +\
                           '\'next_state\': %s, ' % resume_state.id +\
                           '\'is_resume\': True}'
            button_string = '&lt;button name="action_process" ' +\
                            'states="%s" ' % procedure_stage.workflow_state_id.codename +\
                            'string="%s" type="object" ' % resume_action_name +\
                            'title="%s" ' % action_title +\
                            'class="btn %s oe_highlight" ' % resume_button_type +\
                            'context="%s"/&gt; ' % context_data
            process_buttons_string += button_string
        if cancel_data and procedure_stage.user_can_cancel(action_user):
            cancel_action_name = cancel_data['action_name']
            cancel_state = cancel_data['state']
            action_button_type = 'btn-danger'
            if cancel_data['action_button_type']:
                action_button_type = cancel_data['action_button_type']
            action_title = cancel_action_name
            if cancel_data['action_title']:
                action_title = cancel_data['action_title']
            context_data = '{\'current_procedure_stage\': %d, ' % procedure_stage.id +\
                           '\'next_procedure_stage\': %d, ' % procedure_stage.id +\
                           '\'current_state\': %s, ' % procedure_stage.workflow_state_id.id +\
                           '\'next_state\': %s, ' % cancel_state.id +\
                           '\'is_cancel\': True}'
            button_string = '&lt;button name="action_process" ' +\
                            'states="%s" ' % procedure_stage.workflow_state_id.codename +\
                            'string="%s" type="object" ' % cancel_action_name +\
                            'title="%s" ' % action_title +\
                            'class="btn %s oe_highlight" ' % action_button_type +\
                            'context="%s"/&gt; ' % context_data
            process_buttons_string += button_string
        return process_buttons_string

    def action_process(self):
        self.update_position()
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def update_position(self):
        self.ensure_one()
        current_procedure_stage_id = self.env.context.get('current_procedure_stage', False)
        next_procedure_stage_id = self.env.context.get('next_procedure_stage', False)
        current_state_id = self.env.context.get('current_state', False)
        next_state_id = self.env.context.get('next_state', False)
        is_return = self.env.context.get('is_return', False)
        procedure_stage_transition_id = self.env.context.get('procedure_stage_transition_id', False)
        conf_data_ok = True
        if not current_procedure_stage_id or not next_procedure_stage_id or not current_state_id or not next_state_id:
            conf_data_ok = False
        if conf_data_ok:
            workflow_process = self.workflow_process_stage_id.workflow_process_id
            action_datetime = fields.Datetime.now()
            action_user = self.env['workflow.user'].search([
                ('res_users_id', '=', self.env.uid)
            ])
            next_procedure_stage = self.env['workflow.procedure.stage'].search([
                ('id', '=', next_procedure_stage_id)
            ])
            next_state = self.env['workflow.state'].search([('id', '=', next_state_id)])
            if procedure_stage_transition_id and not is_return:
                procedure_stage_transition = self.env['workflow.procedure.stage.transition'].search([
                    ('id', '=', procedure_stage_transition_id)
                ])
                if procedure_stage_transition.exists():
                    if self.is_returned:
                        self.workflow_process_stage_transition_id.write({
                            'transition_datetime': action_datetime
                        })
                        to_stage = self.workflow_process_stage_transition_id.to_workflow_process_stage_id
                        to_state = to_stage.workflow_state_id
                        position_data = {
                            'workflow_process_stage_id': to_stage.id,
                            'state': to_state.codename, 'is_returned': False
                        }
                        self.write(position_data)
                    elif not procedure_stage_transition.cross_border:
                        next_process_stage_data = next_procedure_stage.get_corresponding_process_stage_data(
                            self.workflowable_id
                        )
                        next_process_stage_data['workflow_process_id'] = workflow_process.id
                        next_process_stage_data['start_datetime'] = action_datetime
                        process_execution_commands = []
                        for procedure_execution in next_procedure_stage.workflow_procedure_execution_ids:
                            process_execution_data = procedure_execution.get_corresponding_process_execution_data(
                                self.workflow_process_stage_id.id
                            )
                            process_execution_commands.append(Command.create(process_execution_data))
                        next_process_stage_data['workflow_process_execution_ids'] = process_execution_commands
                        next_process_stage = self.env['workflow.process.stage'].create(next_process_stage_data)
                        new_process_stage_transition_data = procedure_stage_transition.get_corresponding_process_stage_transition_data(
                            self.workflowable_id
                        )
                        new_process_stage_transition_data['transition_datetime'] = action_datetime
                        new_process_stage_transition_data['workflow_user_id'] = action_user.id
                        new_process_stage_transition_data['workflow_process_id'] = workflow_process.id
                        new_process_stage_transition_data['from_workflow_process_stage_id'] = self.workflow_process_stage_id.id
                        new_process_stage_transition_data['to_workflow_process_stage_id'] = next_process_stage.id
                        new_process_stage_transition = self.env['workflow.process.stage.transition'].create(
                            new_process_stage_transition_data
                        )
                        self.workflow_process_stage_id.write({'end_datetime': action_datetime})
                        self.write({
                            'workflow_process_stage_id': next_process_stage.id,
                            'state': next_state.codename, 'is_returned': False,
                            'workflow_process_stage_transition_id': new_process_stage_transition.id
                        })
                    else:
                        parent_transitions_branch = procedure_stage_transition.get_parent_bridge_transitions_branch()
                        if len(parent_transitions_branch) > 0:
                            root_parent_transition = parent_transitions_branch[0]
                            root_transition_context_procedure = root_parent_transition.workflow_procedure_id
                            root_transition_from_procedure = root_parent_transition.from_workflow_procedure_id
                            root_transition_to_procedure = root_parent_transition.to_workflow_procedure_id
                            ultimate_process_transition = False
                            next_process_stage_parent_branch_data = root_transition_to_procedure.get_corresponding_process_data(
                                self.workflowable_id.object_id, False
                            )
                            root_transition_to_process = self.env['workflow.process'].create(
                                next_process_stage_parent_branch_data
                            )
                            root_transition_context_process = root_transition_context_procedure.get_workflow_process_by_id(
                                self.workflow_process_id.root_workflow_process_id
                            )
                            root_transition_from_process = root_transition_from_procedure.get_workflow_process_by_id(
                                self.workflow_process_id.root_workflow_process_id
                            )
                            if root_transition_context_process and root_transition_from_process and root_transition_to_process:
                                root_process_transition = self.env['workflow.process.transition'].create({
                                    'from_workflow_process_id': root_transition_from_process.id,
                                    'to_workflow_process_id': root_transition_to_process.id,
                                    'context_type': root_parent_transition.context_type,
                                    'workflow_procedure_transition_id': root_parent_transition.id,
                                    'workflow_process_id': root_transition_context_process.id
                                })
                                ultimate_process_transition = root_process_transition
                            if ultimate_process_transition and len(parent_transitions_branch[1:]) > 0:
                                for bridge_transition in parent_transitions_branch[1:]:
                                    from_process = bridge_transition.from_workflow_procedure_id.get_workflow_process_by_id(
                                        self.workflow_process_id.root_workflow_process_id
                                    )
                                    to_process = bridge_transition.to_workflow_procedure_id.get_workflow_process_by_id(
                                        self.workflow_process_id.root_workflow_process_id
                                    )
                                    if not to_process.exists():
                                        to_process_data = bridge_transition.to_workflow_procedure_id.get_corresponding_process_data(
                                            self.workflowable_id.object_id, False
                                        )
                                        to_process = self.env['workflow.process'].create(to_process_data)
                                    if from_process.exists() and to_process.exists():
                                        bridge_process_transition_data = bridge_transition.get_corresponding_process_transition_data(
                                            self.workflowable_id
                                        )
                                        bridge_process_transition_data['from_workflow_process_id'] = from_process.id
                                        bridge_process_transition_data['to_workflow_process_id'] = to_process.id
                                        bridge_process_transition_data['workflow_process_transition_id'] = ultimate_process_transition.id
                                        bridge_process_transition = self.env['workflow.process.transition'].create(
                                            bridge_process_transition_data
                                        )
                                        ultimate_process_transition.to_workflow_process_id.write({
                                            'starter_workflow_process_id': to_process.id
                                        })
                                        ultimate_process_transition = bridge_process_transition
                            if ultimate_process_transition.exists():
                                next_process_stage = next_procedure_stage.get_workflow_process_stage_by_id(
                                    self.workflow_process_id.root_workflow_process_id
                                )
                                if not next_process_stage.exists():
                                    next_process_stage_data = next_procedure_stage.get_corresponding_process_stage_data(
                                        self.workflowable_id
                                    )
                                    next_process_stage_data['workflow_process_id'] = ultimate_process_transition.to_workflow_process_id.id
                                    next_process_stage_data['start_datetime'] = action_datetime
                                    process_execution_commands = []
                                    for procedure_execution in next_procedure_stage.workflow_procedure_execution_ids:
                                        process_execution_data = procedure_execution.get_corresponding_process_execution_data(
                                            self.workflow_process_stage_id.id
                                        )
                                        process_execution_commands.append(Command.create(process_execution_data))
                                    next_process_stage_data['workflow_process_execution_ids'] = process_execution_commands
                                    next_process_stage = self.env['workflow.process.stage'].create(
                                        next_process_stage_data
                                    )
                                ultimate_process_transition.to_workflow_process_id.write({
                                    'workflow_process_stage_id': next_process_stage.id
                                })
                                new_process_stage_transition_data = procedure_stage_transition.get_corresponding_process_stage_transition_data(
                                    self.workflowable_id
                                )
                                new_process_stage_transition_data['transition_datetime'] = action_datetime
                                new_process_stage_transition_data['workflow_user_id'] = action_user.id
                                new_process_stage_transition_data['workflow_process_transition_id'] = ultimate_process_transition.id
                                new_process_stage_transition_data['from_workflow_process_stage_id'] = self.workflow_process_stage_id.id
                                new_process_stage_transition_data['to_workflow_process_stage_id'] = next_process_stage.id
                                new_process_stage_transition = self.env['workflow.process.stage.transition'].create(
                                    new_process_stage_transition_data
                                )
                                self.workflow_process_stage_id.write({'end_datetime': action_datetime})
                                self.write({
                                    'workflow_process_stage_id': next_process_stage.id,
                                    'state': next_state.codename, 'is_returned': False,
                                    'workflow_process_stage_transition_id': new_process_stage_transition.id
                                })
                                self.workflow_process_stage_id = next_process_stage.id
                                self.workflow_process_stage_transition_id = new_process_stage_transition.id
            else:
                if is_return:
                    self.workflow_process_stage_transition_id.write({
                        'transition_datetime': action_datetime}
                    )
                    from_stage = self.workflow_process_stage_transition_id.from_workflow_process_stage_id
                    from_state = from_stage.workflow_state_id
                    return_data = {
                        'workflow_process_stage_id': from_stage.id,
                        'state': from_state.codename,
                        'is_returned': True
                    }
                    self.write(return_data)
                elif self.env.context.get('is_cancel', False):
                    new_cancel_data = {
                        'cancelled': True, 'breaked': False, 'resumed': False,
                        'cancel_workflow_state_id': next_state.id,
                        'cancel_action_name': next_procedure_stage.cancel_action_name,
                        'cancel_datetime': action_datetime, 'cancel_user_id': action_user.id
                    }
                    self.workflow_process_stage_id.write(new_cancel_data)
                    self.workflow_process_stage_transition_id.write({
                        'transition_datetime': action_datetime}
                    )
                    cancel_data = {'state': next_state.codename}
                    self.write(cancel_data)
                elif self.env.context.get('is_break', False):
                    new_break_data = {
                        'breaked': True, 'resumed': False, 'cancelled': False,
                        'break_workflow_state_id': next_state.id,
                        'break_action_name': next_procedure_stage.break_action_name,
                        'break_datetime': action_datetime, 'break_user_id': action_user.id
                    }
                    self.workflow_process_stage_id.write(new_break_data)
                    self.workflow_process_stage_transition_id.write({
                        'transition_datetime': action_datetime}
                    )
                    break_data = {'state': next_state.codename}
                    self.write(break_data)
                elif self.env.context.get('is_resume', False):
                    new_resume_data = {
                        'resumed': True, 'breaked': False, 'cancelled': False,
                        'resume_workflow_state_id': next_state.id,
                        'resume_action_name': next_procedure_stage.resume_action_name,
                        'resume_datetime': action_datetime, 'resume_user_id': action_user.id
                    }
                    self.workflow_process_stage_id.write(new_resume_data)
                    self.workflow_process_stage_transition_id.write({
                        'transition_datetime': action_datetime}
                    )
                    resume_data = {'state': next_state.codename}
                    self.write(resume_data)
        self.flush_recordset([
            'workflow_process_stage_id', 'workflow_process_stage_transition_id',
            'state'
        ])

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError


class WorkflowProcedureStage(models.Model):
    _name = "workflow.procedure.stage"
    _description = "Workflow Procedure Stage"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,workflow_procedure_id,company_id)', 'The codename must be unique '
                                                                                        'per workflow procedure and '
                                                                                        'per company !')
    ]

    @api.constrains('cancel_action_name', 'cancel_workflow_state_id')
    def _check_transition_context(self):
        for stage in self:
            if stage.cancel_action_name and not stage.cancel_workflow_state_id:
                raise ValidationError(_("If You set the cancel action, you must also set the cancel state !"))
            if not stage.cancel_action_name and stage.cancel_workflow_state_id:
                raise ValidationError(_("If You set the cancel state, you must also set the cancel action !"))
            if stage.break_action_name and not stage.break_workflow_state_id:
                raise ValidationError(_("If You set the break action, you must also set the break state !"))
            if not stage.break_action_name and stage.break_workflow_state_id:
                raise ValidationError(_("If You set the break state, you must also set the break action !"))
            if stage.resume_action_name and not stage.resume_workflow_state_id:
                raise ValidationError(_("If You set the resume action, you must also set the resume state !"))
            if not stage.resume_action_name and stage.resume_workflow_state_id:
                raise ValidationError(_("If You set the resume state, you must also set the resume action !"))

    @api.depends('workflow_procedure_stage_duration_ids')
    def _compute_has_min_duration(self):
        for stage in self:
            stage.has_min_duration = stage.workflow_procedure_stage_duration_ids.filtered(
                lambda d: len(True == d.minimum) > 0
            )

    @api.depends('workflow_procedure_stage_duration_ids')
    def _compute_has_max_duration(self):
        for stage in self:
            stage.has_max_duration = stage.workflow_procedure_stage_duration_ids.filtered(
                lambda d: len(True == d.maximum) > 0
            )

    @api.depends('workflow_procedure_stage_duration_ids')
    def _compute_has_duration(self):
        for stage in self:
            stage.has_duration = len(stage.workflow_procedure_stage_duration_ids) > 0

    @api.depends("workflow_procedure_ids", "has_started_procedures")
    def _compute_has_started_procedures(self):
        for stage in self:
            if len(stage.workflow_procedure_ids) > 0:
                stage.has_started_procedures = True
            else:
                stage.has_started_procedures = False

    @api.depends("workflow_process_stage_ids", "has_process_stages")
    def _compute_has_process_stages(self):
        for stage in self:
            if len(stage.workflow_process_stage_ids) > 0:
                stage.has_process_stages = True
            else:
                stage.has_process_stages = False

    @api.depends("workflow_procedure_execution_ids", "has_executions")
    def _compute_has_executions(self):
        for stage in self:
            if len(stage.workflow_procedure_execution_ids) > 0:
                stage.has_executions = True
            else:
                stage.has_executions = False

    @api.depends("inbound_workflow_procedure_stage_transition_ids", "has_inbound_transitions")
    def _compute_has_inbound_transitions(self):
        for stage in self:
            if len(stage.inbound_workflow_procedure_stage_transition_ids) > 0:
                stage.has_inbound_transitions = True
            else:
                stage.has_inbound_transitions = False

    @api.depends("outbound_workflow_procedure_stage_transition_ids", "has_outbound_transitions")
    def _compute_has_outbound_transitions(self):
        for stage in self:
            if len(stage.outbound_workflow_procedure_stage_transition_ids) > 0:
                stage.has_outbound_transitions = True
            else:
                stage.has_outbound_transitions = False

    @api.depends('time_unit')
    def _compute_min_duration(self):
        for stage in self:
            stage.min_duration = 0
            if stage.time_unit:
                stage.min_duration = stage.get_min_duration_for_time_unit(stage.time_unit)

    @api.depends('time_unit')
    def _compute_max_duration(self):
        for stage in self:
            stage.max_duration = 0
            if stage.time_unit:
                stage.max_duration = stage.get_max_duration_for_time_unit(stage.time_unit)

    @api.depends('time_unit')
    def _compute_min_execution_duration(self):
        for stage in self:
            stage.min_execution_duration = 0
            if stage.time_unit:
                stage.min_execution_duration = stage.get_min_execution_duration_for_time_unit(stage.time_unit)

    @api.depends('time_unit')
    def _compute_max_execution_duration(self):
        for stage in self:
            stage.max_execution_duration = 0
            if stage.time_unit:
                stage.max_execution_duration = stage.get_max_execution_duration_for_time_unit(stage.time_unit)

    @api.depends('cancel_action_name')
    def _compute_can_be_cancelled(self):
        for stage in self:
            stage.can_be_cancelled = True if stage.cancel_action_name else False

    @api.depends('break_action_name')
    def _compute_can_be_breaked(self):
        for stage in self:
            stage.can_be_breaked = True if stage.break_action_name else False

    @api.depends('resume_action_name')
    def _compute_can_be_resumed(self):
        for stage in self:
            stage.can_be_resumed = True if stage.resume_action_name else False

    @api.depends('workflow_state_id')
    def _compute_default_resume_state(self):
        for stage in self:
            stage.resume_workflow_state_id = stage.workflow_state_id.id

    @api.depends('workflow_procedure_stage_acl_ids')
    def _compute_is_protected(self):
        for stage in self:
            stage.is_protected = len(stage.workflow_procedure_stage_acl_ids) > 0

    @api.depends('workflow_procedure_stage_acl_ids')
    def _compute_is_access_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_access_protected = False
            else:
                acl = stage.workflow_procedure_stage_acl_ids[0]
                stage.is_access_protected = len(acl.access_workflow_user_ids) > 0 or len(acl.access_workflow_role_ids)

    @api.depends('workflow_procedure_stage_acl_ids')
    def _compute_is_cancel_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_cancel_protected = False
            else:
                acl = stage.workflow_procedure_stage_acl_ids[0]
                stage.is_cancel_protected = len(acl.cancel_workflow_user_ids) > 0 or len(acl.cancel_workflow_role_ids)

    @api.depends('workflow_procedure_stage_acl_ids')
    def _compute_is_break_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_break_protected = False
            else:
                acl = stage.workflow_procedure_stage_acl_ids[0]
                stage.is_break_protected = len(acl.break_workflow_user_ids) > 0 or len(acl.break_workflow_role_ids)

    @api.depends('workflow_procedure_stage_acl_ids')
    def _compute_is_resume_protected(self):
        for stage in self:
            if not stage.is_protected:
                stage.is_resume_protected = False
            else:
                acl = stage.workflow_procedure_stage_acl_ids[0]
                stage.is_resume_protected = len(acl.resume_workflow_user_ids) > 0 or len(acl.resume_workflow_role_ids)

    codename = fields.Char(string='Codename', required=True, size=64)
    name = fields.Char(string='Name', required=True, translate=True)
    root_workflow_procedure_id = fields.Many2one('workflow.procedure', required=False,
                                                 readonly=True, string="Root Procedure", store=True,
                                                 related="workflow_procedure_id.root_workflow_procedure_id")
    workflow_procedure_id = fields.Many2one('workflow.procedure', required=True,
                                            string="Procedure")
    workflow_stage_id = fields.Many2one('workflow.stage', required=True,
                                        string="Workflow Stage")
    workflow_state_id = fields.Many2one('workflow.state', string='State', required=False,
                                        store=True, related="workflow_stage_id.workflow_state_id")
    cancel_action_name = fields.Char(string="Cancel Action Name", required=False, translate=True)
    cancel_action_title = fields.Char(string='Cancel Action Title', required=False, translate=True)
    cancel_button_type = fields.Selection(
        selection=[
            ("btn-primary", "Primary"),
            ("btn-secondary", "Secondary"),
            ("btn-success", "Success"),
            ("btn-danger", "Danger"),
            ("btn-warning", "Warning"),
            ("btn-info", "Info"),
            ("btn-light", "Light"),
            ("btn-dark", "Dark"),
            ("btn-link", "Link")
        ], string="Cancel Button Type", required=True, default='btn-danger'
    )
    cancel_workflow_state_id = fields.Many2one('workflow.state', required=False,
                                               string="Cancel State")
    break_action_name = fields.Char(required=False, string="Break Action Name", translate=True)
    break_action_title = fields.Char(string='Break Action Title', required=False, translate=True)
    break_button_type = fields.Selection(
        selection=[
            ("btn-primary", "Primary"),
            ("btn-secondary", "Secondary"),
            ("btn-success", "Success"),
            ("btn-danger", "Danger"),
            ("btn-warning", "Warning"),
            ("btn-info", "Info"),
            ("btn-light", "Light"),
            ("btn-dark", "Dark"),
            ("btn-link", "Link")
        ], string="Break Button Type", required=False, default='btn-secondary'
    )
    break_workflow_state_id = fields.Many2one('workflow.state', required=False,
                                              string="Break State")
    resume_action_name = fields.Char(required=False, string="Resume Action Name", translate=True)
    resume_action_title = fields.Char(string='Resume Action Title', required=False, translate=True)
    resume_button_type = fields.Selection(
        selection=[
            ("btn-primary", "Primary"),
            ("btn-secondary", "Secondary"),
            ("btn-success", "Success"),
            ("btn-danger", "Danger"),
            ("btn-warning", "Warning"),
            ("btn-info", "Info"),
            ("btn-light", "Light"),
            ("btn-dark", "Dark"),
            ("btn-link", "Link")
        ], string="Resume Button Type", required=False, default='btn-success'
    )
    resume_workflow_state_id = fields.Many2one('workflow.state', required=False,
                                               string="Resume State",
                                               default="_compute_default_resume_state")
    workflow_procedure_stage_duration_ids = fields.One2many('workflow.procedure.stage.duration',
                                                            'workflow_procedure_stage_id')
    workflow_procedure_ids = fields.One2many('workflow.procedure',
                                             'workflow_procedure_stage_id',
                                             string="Started Procedures")
    workflow_process_stage_ids = fields.One2many('workflow.process.stage',
                                                 'workflow_procedure_stage_id',
                                                 string="Process Stages")
    inbound_workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                                      'to_workflow_procedure_stage_id',
                                                                      string="Inbound Procedure Stage Transitions")
    outbound_workflow_procedure_stage_transition_ids = fields.One2many('workflow.procedure.stage.transition',
                                                                       'from_workflow_procedure_stage_id',
                                                                       string="Outbound Procedure Stage Transitions")
    workflow_procedure_execution_ids = fields.One2many('workflow.procedure.execution',
                                                       'workflow_procedure_stage_id',
                                                       string="Procedure Executions")
    workflow_procedure_stage_acl_ids = fields.One2many('workflow.procedure.stage.acl',
                                                       'workflow_procedure_stage_id',
                                                       string="Procedure Stage Access Control List")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    can_be_cancelled = fields.Boolean(readonly=True, compute="_compute_can_be_cancelled")
    can_be_breaked = fields.Boolean(readonly=True, compute="_compute_can_be_breaked")
    can_be_resumed = fields.Boolean(readonly=True, compute="_compute_can_be_resumed")
    has_min_duration = fields.Boolean(readonly=True, compute="_compute_has_min_duration")
    has_max_duration = fields.Boolean(readonly=True, compute="_compute_has_max_duration")
    has_duration = fields.Boolean(readonly=True, compute="_compute_has_duration")
    has_started_procedures = fields.Boolean(readonly=True, compute="_compute_has_started_procedures")
    has_executions = fields.Boolean(readonly=True, compute="_compute_has_executions")
    has_inbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_inbound_transitions")
    has_outbound_transitions = fields.Boolean(readonly=True, compute="_compute_has_outbound_transitions")
    has_process_stages = fields.Boolean(readonly=True, compute="_compute_has_process_stages")
    maximum = fields.Boolean(string="Maximum", default=False)
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
        string="Time Unit", required=False, default='hour'
    )
    min_duration = fields.Float("Minimum duration", compute="_compute_min_duration", digits=(11, 5))
    max_duration = fields.Float("Maximum duration", compute="_compute_max_duration", digits=(11, 5))
    min_execution_duration = fields.Float("Minimum Execution duration", default=0,
                                          compute="_compute_min_execution_duration", digits=(11, 5))
    max_execution_duration = fields.Float("Maximum Execution duration", default=0,
                                          compute="_compute_max_execution_duration", digits=(11, 5))
    is_protected = fields.Boolean(readonly=True, compute="_compute_is_protected")
    is_access_protected = fields.Boolean(readonly=True, compute="_compute_is_access_protected")
    is_cancel_protected = fields.Boolean(readonly=True, compute="_compute_is_cancel_protected")
    is_break_protected = fields.Boolean(readonly=True, compute="_compute_is_break_protected")
    is_resume_protected = fields.Boolean(readonly=True, compute="_compute_is_resume_protected")

    def get_corresponding_process_stage_data(self, workflowable_record):
        self.ensure_one()
        process_stage_codename = workflowable_record.name + "[%s]" % self.codename.replace('procedure', 'process')
        process_stage_name = workflowable_record.name + "[%s]" % self.name.replace('Procedure', 'Process')
        data = {
            'codename': process_stage_codename,
            'name': process_stage_name,
            'workflow_procedure_stage_id': self.id,
            'workflow_state_id': self.workflow_state_id.id,
            'cancelled': False, 'breaked': False, 'resumed': False
        }
        for stage_acl in self.workflow_procedure_stage_acl_ids:
            process_stage_acl_data = stage_acl.get_corresponding_process_stage_acl_data()
            if not data.get('workflow_process_stage_acl_ids', False):
                data['workflow_process_stage_acl_ids'] = [
                    Command.create(process_stage_acl_data)
                ]
            else:
                data['workflow_process_stage_acl_ids'].append(
                    Command.create(process_stage_acl_data)
                )
        return data

    def user_can_access(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_access_protected:
            return True
        else:
            return self.workflow_procedure_stage_acl_ids[0].user_can_access(workflow_user)

    def user_can_cancel(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_access_protected:
            return True
        else:
            if not self.user_can_access(workflow_user):
                return False
            return self.workflow_procedure_stage_acl_ids[0].user_can_cancel(workflow_user)

    def user_can_break(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_access_protected:
            return True
        else:
            if not self.user_can_access(workflow_user):
                return False
            return self.workflow_procedure_stage_acl_ids[0].user_can_break(workflow_user)

    def user_can_resume(self, workflow_user):
        self.ensure_one()
        if not self.is_protected or not self.is_access_protected:
            return True
        else:
            if not self.user_can_access(workflow_user):
                return False
            return self.workflow_procedure_stage_acl_ids[0].user_can_resume(workflow_user)

    def get_workflow_process_stage_by_id(self, root_process_id):
        self.ensure_one()
        return self.env['workflow.process.stage'].search([
            '&', ('workflow_procedure_stage_id', '=', self.id),
            ('root_workflow_process_id', '=', root_process_id.id)
        ], limit=1)

    def get_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        return self.env['workflow.procedure.stage.duration'].search([
            '&', ('workflow_procedure_stage_id', '=', self.id),
            ('time_unit', '=', time_unit)
        ], limit=1)

    def get_min_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        duration_instance = self.get_duration_for_time_unit(time_unit)
        if duration_instance.exists():
            return duration_instance.min_duration
        return 0

    def get_max_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        duration_instance = self.get_duration_for_time_unit(time_unit)
        if duration_instance.exists():
            return duration_instance.max_duration
        return 0

    def get_min_execution_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        min_durations = [0] + [
            exe.get_execution_min_duration_for_time_unit(time_unit) for exe in self.workflow_procedure_execution_ids
        ]
        return sum(min_durations)

    def get_max_execution_duration_for_time_unit(self, time_unit):
        self.ensure_one()
        min_durations = [0] + [
            exe.get_execution_max_duration_for_time_unit(time_unit) for exe in self.workflow_procedure_execution_ids
        ]
        return sum(min_durations)

    def action_configure_duration(self):
        wizard = self.env['workflow.procedure.stage.duration.wizard'].create({
            'workflow_procedure_stage_id': self.id
        })
        return {
            'name': _('Configure Procedure Stage Duration'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.procedure.stage.duration.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new'
        }

    def action_configure_acl(self):
        wizard = self.env['workflow.procedure.stage.acl.wizard'].create({
            'workflow_procedure_stage_id': self.id
        })
        return {
            'name': _('Configure Procedure Stage Access Control List'),
            'type': 'ir.actions.act_window',
            'res_model': 'workflow.procedure.stage.acl.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new'
        }

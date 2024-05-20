# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError


def get_root_workflow_job_id(workflow_job_record):
    if not workflow_job_record.parent_id:
        return workflow_job_record.id
    else:
        return get_root_workflow_job_id(workflow_job_record.parent_id)


class WorkflowJob(models.Model):
    _name = "workflow.job"
    _description = "Workflow Job"
    _sql_constraints = [
        ('codename_company_uniq', 'unique (codename,company_id)', 'The codename of the workflow job must be unique '
                                                                  'per company !')
    ]

    @api.constrains('is_task', 'workflow_job_ids')
    def _check_task_indivisible(self):
        for job in self:
            if job.is_task and len(job.workflow_job_ids) > 0:
                raise ValidationError(_("Task is the atomic division of job. Hence task cannot have sub tasks !"))

    @api.depends('parent_id')
    def _compute_is_root_workflow_job(self):
        for job in self:
            job.is_root_workflow_job = False if job.parent_id else True

    @api.depends('parent_id')
    def _compute_root_workflow_job(self):
        for job in self:
            job.root_workflow_job_id = get_root_workflow_job_id(job)

    @api.depends('parent_id', 'is_task')
    def _compute_is_sub_workflow_job(self):
        for job in self:
            job.is_sub_workflow_job = True if job.parent_id and not job.is_task else False

    @api.depends('workflow_job_ids')
    def _compute_has_sub_workflow_jobs(self):
        for job in self:
            job.has_sub_workflow_jobs = len(job.workflow_job_ids) > 0

    @api.depends('workflow_job_ids')
    def _compute_sub_workflow_jobs_count(self):
        for job in self:
            job.sub_workflow_jobs_count = len(job.workflow_job_ids)

    @api.depends('workflow_job_ids')
    def _compute_has_tasks(self):
        for job in self:
            job.has_tasks = len(job.workflow_job_ids.filtered(lambda j: j.is_task==True)) > 0

    @api.depends('workflow_job_ids')
    def _compute_tasks_count(self):
        for job in self:
            job.sub_workflow_jobs_count = len(job.workflow_job_ids.filtered(lambda j: j.is_task==True))

    @api.depends('workflow_procedure_execution_ids')
    def _compute_has_procedure_executions(self):
        for job in self:
            job.has_procedure_executions = len(job.workflow_procedure_execution_ids) > 0

    @api.depends('workflow_procedure_execution_ids')
    def _compute_procedure_executions_count(self):
        for job in self:
            job.procedure_executions_count = len(job.workflow_procedure_execution_ids)

    @api.depends('workflow_process_execution_ids')
    def _compute_has_process_executions(self):
        for job in self:
            job.has_process_executions = len(job.workflow_process_execution_ids) > 0

    @api.depends('workflow_process_execution_ids')
    def _compute_process_executions_count(self):
        for job in self:
            job.process_executions_count = len(job.workflow_process_execution_ids)

    @api.depends('is_task')
    def _compute_can_have_sub_jobs(self):
        for job in self:
            job.can_have_sub_jobs = not job.is_task

    codename = fields.Char(string='Codename', required=True, copy=False)
    name = fields.Char(string='Name', required=True, translate=True)
    is_task = fields.Boolean(string="Is Task ?", default=False,
                             help="""Task is the lowest level of subdivision of a job. 
                             Hence, tasks cannot be subdivided in sub jobs.""")
    root_workflow_job_id = fields.Many2one('workflow.job', string="Root Job", required=False,
                                           compute="_compute_root_workflow_job", readonly=True,
                                           store=True)
    parent_id = fields.Many2one('workflow.job', string="Parent Job", required=False,
                                domain="[('is_task', '=', False)]")
    workflow_job_ids = fields.One2many('workflow.job', 'parent_id',
                                       string="Sub Jobs")
    workflow_procedure_execution_ids = fields.One2many('workflow.procedure.execution',
                                                       'workflow_job_id',
                                                       help="""The procedures where defining the execution of the 
                                                       job/task.""")
    workflow_process_execution_ids = fields.One2many('workflow.process.execution',
                                                     'workflow_job_id',
                                                     help="The processes where the job/task is executed.")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    can_have_sub_jobs = fields.Boolean(readonly=True, compute="_compute_can_have_sub_jobs")
    is_root_workflow_job = fields.Boolean(readonly=True, compute="_compute_is_root_workflow_job")
    is_sub_workflow_job = fields.Boolean(readonly=True, compute="_compute_is_sub_workflow_job")
    has_sub_workflow_jobs = fields.Boolean(readonly=True, compute="_compute_has_sub_workflow_jobs")
    sub_workflow_jobs_count = fields.Integer(readonly=True, compute="_compute_sub_workflow_jobs_count",
                                             default=0)
    has_tasks = fields.Boolean(readonly=True, compute="_compute_has_tasks")
    tasks_count = fields.Integer(readonly=True, compute="_compute_tasks_count",default=0)
    has_procedure_executions = fields.Boolean(readonly=True, compute="_compute_has_procedure_executions")
    procedure_executions_count = fields.Integer(readonly=True, compute="_compute_procedure_executions_count",
                                                default=0)
    has_process_executions = fields.Boolean(readonly=True, compute="_compute_has_process_executions")
    process_executions_count = fields.Integer(readonly=True, compute="_compute_process_executions_count",
                                              default=0)

    def get_mandatory_procedure_execution_create_data(self, procedure_stage_id):
        self.ensure_one()
        data = {
            'mandatory': True, 'workflow_job_id': self.id, 'workflow_procedure_stage_id': procedure_stage_id
        }
        sub_data_list = []
        for sub_job in self.workflow_job_ids:
            sub_data_list.append(sub_job.get_mandatory_procedure_execution_create_data(procedure_stage_id))
        if len(sub_data_list) > 0:
            for sub_data in sub_data_list:
                if not data.get('workflow_procedure_execution_ids', False):
                    data['workflow_procedure_execution_ids'] = [Command.create(sub_data)]
                else:
                    data['workflow_procedure_execution_ids'].append(Command.create(sub_data))
        print("Data : ", data)
        return data

    def get_optional_procedure_execution_create_data(self, procedure_stage_id):
        self.ensure_one()
        data = {
            'mandatory': False, 'workflow_job_id': self.id, 'workflow_procedure_stage_id': procedure_stage_id
        }
        sub_data_list = []
        for sub_job in self.workflow_job_ids:
            sub_data_list.append(sub_job.get_optional_procedure_execution_create_data(procedure_stage_id))
        if len(sub_data_list) > 0:
            for sub_data in sub_data_list:
                if not data.get('workflow_procedure_execution_ids', False):
                    data['workflow_procedure_execution_ids'] = [Command.create(sub_data)]
                else:
                    data['workflow_procedure_execution_ids'].append(Command.create(sub_data))
        return data

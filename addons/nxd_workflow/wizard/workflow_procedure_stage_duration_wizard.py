# -*- coding: utf-8 -*-

from odoo import api, fields, models
from ..utils import date_utils


class WorkflowProcedureStageDurationWizard(models.TransientModel):
    _name = "workflow.procedure.stage.duration.wizard"
    _description = "Configure Procedure Stage Duration"

    workflow_procedure_stage_id = fields.Many2one('workflow.procedure.stage', required=True,
                                                  readonly=True)
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
        string="Time Unit", required=True, default='hour'
    )
    min_duration = fields.Float(string="Minimum Duration", default=0)
    max_duration = fields.Float(string="Maximum Duration", default=0)

    def create_procedure_stage_duration_from_wizard(self):
        temporal_units = ['minute', 'hour', 'day', 'week', 'month', 'quarter', 'semester', 'year']
        time_unit = self.time_unit
        min_duration = self.min_duration
        max_duration = self.max_duration
        data_list = [{
            'workflow_procedure_stage_id': self.workflow_procedure_stage_id.id,
            'time_unit': time_unit,
            'min_duration': min_duration,
            'max_duration': max_duration
        }]
        for temporal_unit in temporal_units:
            if temporal_unit != time_unit:
                data_list.append({
                    'workflow_procedure_stage_id': self.workflow_procedure_stage_id.id,
                    'time_unit': temporal_unit,
                    'min_duration': date_utils.convert_datetime(
                        min_duration, time_unit, temporal_unit
                    ),
                    'max_duration': date_utils.convert_datetime(
                        max_duration, time_unit, temporal_unit
                    )
                })
        self.env['workflow.procedure.stage.duration'].create(data_list)

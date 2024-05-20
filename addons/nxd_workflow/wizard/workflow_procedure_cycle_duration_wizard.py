# -*- coding: utf-8 -*-

from odoo import api, fields, models
from ..utils import date_utils


class WorkflowProcedureCycleDurationWizard(models.TransientModel):
    _name = "workflow.procedure.cycle.duration.wizard"
    _description = "Configure Procedure Cycle Duration"

    workflow_procedure_cycle_id = fields.Many2one('workflow.procedure.stage', required=True,
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

    def create_procedure_cycle_duration_from_wizard(self):
        temporal_units = ['minute', 'hour', 'day', 'week', 'month', 'quarter', 'semester', 'year']
        data_list = [{
            'workflow_procedure_cycle_id': self.workflow_procedure_cycle_id.id,
            'time_unit': self.time_unit,
            'min_duration': self.min_duration,
            'max_duration': self.max_duration
        }]
        for temporal_unit in temporal_units:
            if temporal_unit != self.time_unit:
                data_list.append({
                    'workflow_procedure_cycle_id': self.workflow_procedure_cycle_id.id,
                    'time_unit': temporal_unit,
                    'min_duration': date_utils.convert_datetime(
                        self.min_duration, self.time_unit, temporal_unit
                    ),
                    'max_duration': date_utils.convert_datetime(
                        self.max_duration, self.time_unit, temporal_unit
                    )
                })
        self.env['workflow.procedure.cycle.duration'].create(data_list)

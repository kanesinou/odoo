# -*- coding: utf-8 -*-
from datetime import timedelta

SECOND_BASE = 60
MINUTE_BASE = 60
HOUR_BASE = 24
DAY_WEEK_BASE = 7
DAY_MONTH_BASE = 30
WEEK_MONTH_BASE = 4
WEEK_YEAR_BASE = 52
MONTH_BASE = 12
QUARTER_BASE = 3
SEMESTER_BASE = 6


TIME_LABELS = {
    "minute": "Minute",
    "hour": "Hour",
    "day": "Day",
    "week": "Week",
    "month": "Month",
    "quarter": "Quarter",
    "semester": "Semester",
    "year": "Year"
}


TIME_LABEL_PLURALS = {
    "minute": "Minutes",
    "hour": "Hours",
    "day": "Days",
    "week": "Weeks",
    "month": "Months",
    "quarter": "Quarters",
    "semesters": "Semesters",
    "year": "Years"
}


def convert_datetime(delta, from_unit, to_unit):
    match to_unit:
        case 'minute':
            return convert_to_minute(delta, from_unit)
        case 'hour':
            return convert_to_hour(delta, from_unit)
        case 'day':
            return convert_to_day(delta, from_unit)
        case 'week':
            return convert_to_week(delta, from_unit)
        case 'month':
            return convert_to_month(delta, from_unit)
        case 'quarter':
            return convert_to_quarter(delta, from_unit)
        case 'semester':
            return convert_to_semester(delta, from_unit)
        case 'year':
            return convert_to_year(delta, from_unit)
        case _:
            return 0


def convert_to_second(delta, from_unit):
    match from_unit:
        case 'minute':
            return delta * SECOND_BASE
        case 'hour':
            return delta * MINUTE_BASE * SECOND_BASE
        case 'day':
            return delta * HOUR_BASE * MINUTE_BASE * SECOND_BASE
        case 'week':
            return delta * DAY_WEEK_BASE * HOUR_BASE * MINUTE_BASE * SECOND_BASE
        case 'month':
            return delta * DAY_MONTH_BASE * HOUR_BASE * MINUTE_BASE * SECOND_BASE
        case 'quarter':
            return delta * QUARTER_BASE * DAY_MONTH_BASE * HOUR_BASE * MINUTE_BASE * SECOND_BASE
        case 'semester':
            return delta * SEMESTER_BASE * DAY_MONTH_BASE * HOUR_BASE * MINUTE_BASE * SECOND_BASE
        case 'year':
            return delta * MONTH_BASE * DAY_MONTH_BASE * HOUR_BASE * MINUTE_BASE * SECOND_BASE
        case _:
            return 0


def convert_to_minute(delta, from_unit):
    match from_unit:
        case 'second':
            quot_val = delta / MINUTE_BASE
            mod_val = delta % MINUTE_BASE
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / MINUTE_BASE)
        case 'hour':
            return delta * MINUTE_BASE
        case 'day':
            return delta * MINUTE_BASE * HOUR_BASE
        case 'week':
            return delta * MINUTE_BASE * HOUR_BASE * DAY_WEEK_BASE
        case 'month':
            return delta * MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE
        case 'quarter':
            return delta * QUARTER_BASE * MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE
        case 'semester':
            return delta * SEMESTER_BASE * MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE
        case 'year':
            return delta * MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE * MONTH_BASE
        case _:
            return 0


def convert_to_hour(delta, from_unit):
    match from_unit:
        case 'second':
            base = (MINUTE_BASE * HOUR_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'minute':
            quot_val = delta / HOUR_BASE
            mod_val = delta % HOUR_BASE
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / HOUR_BASE)
        case 'day':
            return delta * HOUR_BASE
        case 'week':
            return delta * HOUR_BASE * DAY_WEEK_BASE
        case 'month':
            return delta * HOUR_BASE * DAY_MONTH_BASE
        case 'quarter':
            return delta * HOUR_BASE * DAY_MONTH_BASE * QUARTER_BASE
        case 'semester':
            return delta * HOUR_BASE * DAY_MONTH_BASE * SEMESTER_BASE
        case 'year':
            return delta * HOUR_BASE * DAY_MONTH_BASE * MONTH_BASE
        case _:
            return 0


def convert_to_day(delta, from_unit):
    match from_unit:
        case 'second':
            base = (SECOND_BASE * MINUTE_BASE * HOUR_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'minute':
            base = (MINUTE_BASE * HOUR_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'hour':
            quot_val = delta / HOUR_BASE
            mod_val = delta % HOUR_BASE
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / HOUR_BASE)
        case 'week':
            return delta * DAY_WEEK_BASE
        case 'month':
            return delta * DAY_MONTH_BASE
        case 'quarter':
            return delta * DAY_MONTH_BASE * QUARTER_BASE
        case 'semester':
            return delta * DAY_MONTH_BASE * SEMESTER_BASE
        case 'year':
            return delta * DAY_MONTH_BASE * MONTH_BASE
        case _:
            return 0


def convert_to_week(delta, from_unit):
    match from_unit:
        case 'second':
            base = (SECOND_BASE * MINUTE_BASE * HOUR_BASE * DAY_WEEK_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'minute':
            base = (MINUTE_BASE * HOUR_BASE * DAY_WEEK_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'hour':
            base = (HOUR_BASE * DAY_WEEK_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'day':
            quot_val = delta / DAY_WEEK_BASE
            mod_val = delta % DAY_WEEK_BASE
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / DAY_WEEK_BASE)
        case 'month':
            return delta * WEEK_MONTH_BASE
        case 'quarter':
            return delta * WEEK_MONTH_BASE * QUARTER_BASE
        case 'semester':
            return delta * WEEK_MONTH_BASE * SEMESTER_BASE
        case 'year':
            return delta * WEEK_YEAR_BASE
        case _:
            return 0


def convert_to_month(delta, from_unit):
    match from_unit:
        case 'second':
            base = (SECOND_BASE * MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'minute':
            base = (MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'hour':
            base = (HOUR_BASE * DAY_MONTH_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'day':
            quot_val = delta / DAY_MONTH_BASE
            mod_val = delta % DAY_MONTH_BASE
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / DAY_MONTH_BASE)
        case 'week':
            quot_val = delta / WEEK_MONTH_BASE
            mod_val = delta % WEEK_MONTH_BASE
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / WEEK_MONTH_BASE)
        case 'quarter':
            return delta * QUARTER_BASE
        case 'semester':
            return delta * SEMESTER_BASE
        case 'year':
            return delta * MONTH_BASE
        case _:
            return 0


def convert_to_quarter(delta, from_unit):
    match from_unit:
        case 'second':
            base = (SECOND_BASE * MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE * QUARTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'minute':
            base = (MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE * QUARTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'hour':
            base = (HOUR_BASE * DAY_MONTH_BASE * QUARTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'day':
            base = (DAY_MONTH_BASE * QUARTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'week':
            base = (WEEK_MONTH_BASE * QUARTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'semester':
            return delta * SEMESTER_BASE / QUARTER_BASE
        case 'year':
            return delta * MONTH_BASE / QUARTER_BASE
        case _:
            return 0


def convert_to_semester(delta, from_unit):
    match from_unit:
        case 'second':
            base = (SECOND_BASE * MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE * SEMESTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'minute':
            base = (MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE * SEMESTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'hour':
            base = (HOUR_BASE * DAY_MONTH_BASE * SEMESTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'day':
            base = (DAY_MONTH_BASE * SEMESTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'week':
            base = (WEEK_MONTH_BASE * SEMESTER_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'quarter':
            base = SEMESTER_BASE
            quot_val = delta * QUARTER_BASE / base
            mod_val = (delta * QUARTER_BASE) % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'year':
            return delta * MONTH_BASE / SEMESTER_BASE
        case _:
            return 0


def convert_to_year(delta, from_unit):
    match from_unit:
        case 'second':
            base = (SECOND_BASE * MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE * MONTH_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'minute':
            base = (MINUTE_BASE * HOUR_BASE * DAY_MONTH_BASE * MONTH_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'hour':
            base = (HOUR_BASE * DAY_MONTH_BASE * MONTH_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'day':
            base = (DAY_MONTH_BASE * MONTH_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'week':
            base = (WEEK_MONTH_BASE * MONTH_BASE)
            quot_val = delta / base
            mod_val = delta % base
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / base)
        case 'month':
            quot_val = delta / MONTH_BASE
            mod_val = delta % MONTH_BASE
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / MONTH_BASE)
        case 'quarter':
            quot_val = delta * QUARTER_BASE / MONTH_BASE
            mod_val = delta * QUARTER_BASE % MONTH_BASE
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / MONTH_BASE)
        case 'semester':
            quot_val = delta * SEMESTER_BASE / MONTH_BASE
            mod_val = delta * SEMESTER_BASE % MONTH_BASE
            if quot_val < 1:
                return quot_val
            else:
                if mod_val == 0:
                    return quot_val
                else:
                    return quot_val + (mod_val / MONTH_BASE)
        case _:
            return 0


def get_time_total(delta, unit='days'):
    match unit:
        case 'minute':
            return delta / timedelta(minutes=1)
        case 'hour':
            return delta / timedelta(hours=1)
        case 'week':
            return delta / timedelta(weeks=1)
        case 'month':
            return delta / timedelta(days=30)
        case 'quarter':
            return delta / timedelta(days=90)
        case 'semester':
            return delta / timedelta(days=180)
        case 'year':
            return delta / timedelta(days=365)
        case _:
            return delta.days


def get_timedelta_from_duration(duration, unit='day'):
    match unit:
        case 'minute':
            return timedelta(minutes=duration)
        case 'hour':
            return timedelta(hours=duration)
        case 'week':
            return timedelta(weeks=duration)
        case 'month':
            return timedelta(days=duration*30)
        case 'quarter':
            return timedelta(days=duration*90)
        case 'semester':
            return timedelta(days=duration*180)
        case 'year':
            return timedelta(days=duration*365)
        case _:
            return timedelta(days=duration)

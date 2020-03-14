odoo.ev_hr_timesheet = function (instance) {
    instance.ev_hr_timesheet = {};

    // func_import_shift_assign(instance);
    // func_shift_assign_sheet(instance);
    func_shift_assign_details(instance);
    // func_timesheet_sheet(instance);
    // func_time_sheet_line(instance);

    instance.web.form.custom_widgets.add('shift_assign_details', 'instance.ev_hr_timesheet.ShiftAssignDetails');
    // instance.web.form.custom_widgets.add('shift_assign_sheet', 'instance.ev_hr_timesheet.ShiftAssignSheet');
    // instance.web.form.custom_widgets.add('timesheet_sheet', 'instance.ev_hr_timesheet.TimesheetSheet');
    // instance.web.form.custom_widgets.add('time_sheet_line', 'instance.ev_hr_timesheet.TimeSheetLine');
    // instance.web.form.custom_widgets.add('import_shift_assign', 'instance.ev_hr_timesheet.ImportShiftAssign');
}
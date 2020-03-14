function func_shift_assign_details(instance) {
    var QWeb = instance.web.qweb;

    instance.ev_hr_timesheet.ShiftAssignDetails = instance.web.form.FormWidget.extend(instance.web.form.ReinitializeWidgetMixin, {
        events: {
            "click .oe_timesheet_weekly_account a": "go_to",
            "click #save": "click_button_save",
        },

        init: function () {
            this._super.apply(this, arguments);
            var self = this;
            this.set({
                sheets: [],
                period_id: false,
                update_data: [],
                department_id: false,
                period_id: false,
            });
            this.dates = []
            this.state = ''
            this.emp_shifts = []
            //this.update_data = []
            this.field_manager.on("field_changed:department_id", this, function () {
                this.set({"department_id": this.field_manager.get_field_value("department_id")});
            });
            this.field_manager.on("field_changed:period_id", this, function () {
                this.set({"period_id": this.field_manager.get_field_value("period_id")});
            });
            this.field_manager.on("field_changed:random_number", this, function () {
                this.set({"random_number": this.field_manager.get_field_value("random_number")});
            });
            this.field_manager.on("field_changed:state", this, function () {
                this.set({"state": this.field_manager.get_field_value("state")});
            });
            this.field_manager.on("field_changed:detail_ids", this, function () {
                this.set({"detail_ids": this.field_manager.get_field_value("detail_ids")});
            });
            //this.field_manager.on("field_changed:detail_ids", this, this.query_sheets);
            //this.res_o2m_drop = new instance.web.DropMisordered();
            this.render_drop = new instance.web.DropMisordered();
            //this.on("change:sheets", this, this.update_sheets);
        },
        click_button_save: function () {
            //console.log("ngadv set_shift_id")
            var shiftAssignDetail = new instance.web.Model("hr.shift.assign.detail");
            //console.log("update_data1: " + this.get("update_data"))
            //console.log("update_data2: " + this.update_data)
            shiftAssignDetail.call("set_shift_id", [this.get("update_data")])
                .then(function (result) {
                    //console.log("ngadv set_shift_id");
                });
        },
        initialize_field: function () {
            instance.web.form.ReinitializeWidgetMixin.initialize_field.call(this);
            var self = this;
            self.on("change:department_id", self, self.initialize_content);
            self.on("change:period_id", self, self.initialize_content);
            self.on("change:random_number", self, self.do_sync_data);
            self.on("change:detail_ids", self, self.initialize_content);
        },

        do_sync_data: function () {
            //console.log("ngadv set_shift_id")
            var shiftAssignDetail = new instance.web.Model("hr.shift.assign.detail");
            //console.log("update_data1: " + this.get("update_data"))
            //console.log("update_data2: " + this.update_data)
            shiftAssignDetail.call("set_shift_id", [this.get("update_data")])
                .then(function (result) {
                    //console.log("ngadv set_shift_id");
                });
            console.log('11111111111111111111111111111111111')
        },

        initialize_content: function () {
            if (!this.get("period_id") || !this.get("department_id")) {
                return;
            }
            var self = this;
            var emp_shifts;
            var dates;

            this.destroy_content();
            //console.log(self.$el.find('#shift_to_assign'))
            var shiftAssign = new instance.web.Model("hr.shift.assign");
            var shiftAssignDetail = new instance.web.Model("hr.shift.assign.detail");
            department_id = self.get("department_id")
            period_id = self.get("period_id")
            //state = self.get("state")

            shiftAssign.call("get_date_from_period", [period_id]).then(function (res_date) {
                if (res_date) {
                    var dates;
                    dates = [];
                    var start = instance.web.str_to_date(res_date.date_start);
                    var end = instance.web.str_to_date(res_date.date_stop);
                    while (start <= end) {
                        dates.push(start);
                        start = start.clone().addDays(1);
                    }
                    self.dates = dates;
                    shiftAssignDetail.call("get_shift_assign_detail", [department_id, period_id])
                        .then(function (result) {
                            self.emp_shifts = result;
                            self.display_data();
                            self.frezzeTable();
                        });
                }
                else {
                    return;
                }
            });
            //return this.render_drop.add(
            //    shiftAssign.call("get_date_from_period", [period_id]).then(function (res_date) {
            //        if (res_date) {
            //            dates = [];
            //            emp_shifts = [];
            //            var start = instance.web.str_to_date(res_date.date_start);
            //            var end = instance.web.str_to_date(res_date.date_stop);
            //            while (start <= end) {
            //                dates.push(start);
            //                start = start.clone().addDays(1);
            //            }
            //            return shiftAssignDetail.call("get_shift_assign_detail", [department_id, period_id])
            //                .then(function (result) {
            //                    emp_shifts = result;
            //                    self.frezzeTable();
            //                });
            //        }
            //        else {
            //            return;
            //        }
            //    })).then(function (result) {
            //        // we put all the gathered data in self, then we render
            //        self.dates = dates;
            //        self.emp_shifts = emp_shifts;
            //        self.display_data();
            //        self.frezzeTable();
            //    });
            //self.set({department_id: false, period_id: false})
        },
        destroy_content: function () {
            if (this.dfm) {
                this.dfm.destroy();
                this.dfm = undefined;
            }
        },
        display_data: function () {
            var self = this;
            console.log("state: " + self.get("state"))
            self.$el.html(QWeb.render("ev_hr_timesheet.ShiftAssignDetails", {
                shiftAssignDetail: self,
                state: self.get("state")
            }));
            if (!self.get('effective_readonly')) {
                var shifts_department = ['',];
                var shiftDepartment = new instance.web.Model("hr.employee.shift");
                shiftDepartment.call("get_shift_by_department", [department_id]).then(
                    function (results) {
                        //console.log("results: " + results)
                        _.each(results, function (result) {
                            shifts_department.push(result)
                        });
                    }
                );
                self.$('[class="shift_to_assign"]').autocomplete({
                    source: shifts_department
                });

                _.each(self.emp_shifts, function (emp_shift) {
                    _.each(emp_shift['data'], function (emp_data) {
                        self.get_box(emp_shift['employee_id'], emp_data['day']).change(function () {
                            var old_random_number_1 = self.field_manager.get_field_value("random_number_1");
                            console.log("old_random_number_1: " + old_random_number_1)
                            self.field_manager.set_values({'random_number_1': old_random_number_1 + 0.1})
                            var shiftAssignDetail = new instance.web.Model("hr.shift.assign.detail");
                            var detail_id = emp_shift['id'];
                            var employee_id = emp_shift['employee_id'];
                            var day = emp_data['day'];
                            var shift_name = self.get_box(employee_id, day).val().toUpperCase();
                            var old_shift_name = self.get_box(employee_id, day).attr("shift_name").toUpperCase();
                            //if (shift_name.length > 0) {
                            //
                            //}
                            if ($.inArray(shift_name, shifts_department) == -1) {
                                self.get_box(employee_id, day).css("background-color", "yellow");
                                self.get_box(employee_id, day).val(old_shift_name);
                            } else {
                                self.get_box(employee_id, day).css("background-color", "transparent");
                                self.get("update_data").push({
                                    'detail_id': detail_id,
                                    'employee_id': employee_id,
                                    'day': day,
                                    'shift_name': shift_name
                                });
                            }
                            console.log("detail_id: " + detail_id)
                            console.log("employee_id: " + employee_id)
                            console.log("day: " + day)
                            console.log("shift_name: " + shift_name)
                        });
                    });
                });
            }
        },

        get_box: function (emp_code, day) {
            return this.$('[emp-id="' + emp_code + '"][day="' + day + '"]');
        },

        sync: function () {
            this.setting = true;
            this.set({sheets: this.generate_o2m_value()});
            this.setting = false;
        },
        generate_o2m_value: function () {
            var self = this;
            var ops = [];
            //var ignored_fields = this.ignore_fields();
            _.each(self.emp_shifts, function (emp_shift) {
                _.each(emp_shift['data'], function (emp_data) {
                    var tmp = _.clone(emp_shift);
                    if ($('[emp-id="' + emp_shift['employee_id'] + '"][day="' + emp_data['day'] + '"]').val() !== null) {
                        _.each(emp_shift, function (v, k) {
                            if (v instanceof Array) {
                                tmp[k] = v[0];
                            }
                        });
                        // we remove emp as the reference to the _inherits field will no longer exists
                        //tmp = _.omit(tmp, ignored_fields);
                        ops.push(tmp);
                    }
                });
            });
            return ops;
        },
        frezzeTable: function () {
            $("#fixTable").tableHeadFixer({"left": 3});
            //$("#form_main\\:tblTimekeeping").find(".ui-datatable-tablewrapper").css("height", ($(window).height() - 280) + "px");
        },
    });

};

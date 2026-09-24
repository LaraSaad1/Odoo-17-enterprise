/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";

patch(AccountReportFilters.prototype, {
    async applyCustomPeriods(ev) {
        const key = "custom_periods_days";
        const value = ev.target.value.trim();
        const controller = this.controller;
        if (!value || value === controller.options[key]) {
            return;
        }

        // Try the stock helpers first, then fall back to a manual reload.
        if (typeof this.updateFilter === "function") {
            await this.updateFilter(key, value);
        } else if (typeof controller.updateOption === "function") {
            await controller.updateOption(key, value, true);
        } else {
            controller.options[key] = value;
            await controller.reload(key, controller.options);
        }
    },
});
/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { download } from "@web/core/network/download";
import { MoOverview } from "@mrp/components/mo_overview/mrp_mo_overview"; // <-- was "mo_overview"

patch(MoOverview.prototype, {
    async onExportXlsx() {
        await download({
            url: "/mrp/mo_overview/xlsx",
            data: {
                docids: this.activeId,
                replenishments: +this.state.showOptions.replenishments,
                availabilities: +this.state.showOptions.availabilities,
                receipts: +this.state.showOptions.receipts,
                unitCosts: +this.state.showOptions.unitCosts,
                moCosts: +this.state.showOptions.moCosts,
                realCosts: +this.state.showOptions.realCosts,
            },
        });
    },
});
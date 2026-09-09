# -*- coding: utf-8 -*-
from odoo import models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _build_wkhtmltopdf_args(
        self, paperformat_id, landscape, specific_paperformat_args=None, set_viewport_size=False,
    ):
        """Force UTF-8 decoding in wkhtmltopdf.

        Known Odoo/wkhtmltopdf issue: with wkhtmltopdf 0.12.6, non-ASCII
        characters (Arabic, accented Latin, etc.) get mis-decoded as
        Windows-1252/Latin-1 in the generated PDF, because Odoo doesn't pass
        an explicit --encoding flag and wkhtmltopdf falls back to a wrong
        default on some platforms (notably Windows).
        See: https://github.com/odoo/odoo/issues/80184
        """
        command_args = super()._build_wkhtmltopdf_args(
            paperformat_id,
            landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )
        if '--encoding' not in command_args:
            command_args += ['--encoding', 'utf-8']
        return command_args

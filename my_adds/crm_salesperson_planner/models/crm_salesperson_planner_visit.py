# Copyright 2021 Sygel - Valentin Vinagre
# Copyright 2021 Sygel - Manuel Regidor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CrmSalespersonPlannerVisit(models.Model):
    _name = "crm.salesperson.planner.visit"
    _description = "Salesperson Planner Visit"
    _order = "date desc,sequence"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Visit Number",
        required=True,
        default="/",
        copy=False,
    )

    partner_id = fields.Many2one(
            comodel_name="res.partner",
            string="Customer",
        )


    date = fields.Date(
        default=fields.Date.context_today,
        required=True,
    )
    region_ids = fields.Many2many(
    'res.country.state', 
    string='المنطقة',
    domain="[('country_id.code', '=', 'EG')]"
    )

    executed_visits_count = fields.Integer(
        string='عدد الزيارات المنفذة',
        compute='_compute_executed_visits_count',
        store=True,
    )
    sequence = fields.Integer(
        help="Used to order Visits in the different views",
        default=20,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="اسم المهندس",
        index=True,
        tracking=True,
        default=lambda self: self.env.user,
        domain=lambda self: [
            ("groups_id", "in", [self.env.ref("sales_team.group_sale_salesman").id])
        ],
    )
   
    new_customers_count = fields.Integer(
    string="عدد العملاء الجدد",
    compute='_compute_new_customers_count',
    store=True,
    )
    orders_count = fields.Integer(string="عدد الطلبيات")
    total_sales = fields.Float(string="إجمالي المبيعات")
    main_challenges = fields.Text(string="أهم التحديات")
    
    customer_line_ids = fields.One2many(
        comodel_name="crm.salesperson.planner.visit.customer.line",
        inverse_name="visit_id",
        string="Customer Visits",
    )
    description = fields.Html()
    state = fields.Selection(
        string="Status",
        required=True,
        copy=False,
        tracking=True,
        selection=[
            ("draft", "Draft"),
            ("confirm", "Validated"),
            ("done", "Visited"),
            ("cancel", "Cancelled"),
            ("incident", "Incident"),
        ],
        default="draft",
    )
 
    close_reason_image = fields.Image(max_width=1024, max_height=1024, attachment=True)
    close_reason_notes = fields.Text()
    visit_template_id = fields.Many2one(
        comodel_name="crm.salesperson.planner.visit.template", string="Visit Template"
    )
    calendar_event_id = fields.Many2one(
        comodel_name="calendar.event", string="Calendar Event"
    )
    visit_purpose_ids = fields.Many2many(
        'visit.purpose',
        string="هدف الزيارة"
    )

    _sql_constraints = [
        (
            "crm_salesperson_planner_visit_name",
            "UNIQUE (name)",
            "The visit number must be unique!",
        ),
    ]

    @api.depends("customer_line_ids")
    def _compute_executed_visits_count(self):
        for visit in self:
            visit.executed_visits_count = len(visit.customer_line_ids)

    @api.depends("customer_line_ids", "customer_line_ids.partner_id")
    def _compute_new_customers_count(self):
        for visit in self:
            visit.new_customers_count = len(visit.customer_line_ids.mapped("partner_id"))        

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "salesperson.planner.visit"
                )
        return super().create(vals_list)

    def action_draft(self):
        if self.state not in ["cancel", "incident", "done"]:
            raise ValidationError(
                _("The visit must be in cancelled, incident or visited state")
            )
        # if self.calendar_event_id:
        #     self.calendar_event_id.with_context(bypass_cancel_visit=True).unlink()
        self.write({"state": "draft"})

    def action_confirm(self):
        if self.filtered(lambda a: not a.state == "draft"):
            raise ValidationError(_("The visit must be in draft state"))
        self.write({"state": "confirm"})

    def action_done(self):
        if not self.state == "confirm":
            raise ValidationError(_("The visit must be in confirmed state"))
        self.write({"state": "done"})

    def action_cancel(self, image=None, notes=None):
        if self.state not in ["draft", "confirm"]:
            raise ValidationError(_("The visit must be in draft or validated state"))
        # if self.calendar_event_id:
        #     self.calendar_event_id.with_context(bypass_cancel_visit=True).unlink()
        self.write(
            {
                "state": "cancel",
               
                "close_reason_image": image,
                "close_reason_notes": notes,
            }
        )

    # def _prepare_calendar_event_vals(self):
    #     return {
    #         "name": self.name,
    #         "partner_ids": [(6, 0, [self.partner_id.id, self.user_id.partner_id.id])],
    #         "user_id": self.user_id.id,
    #         "start_date": self.date,
    #         "stop_date": self.date,
    #         "start": self.date,
    #         "stop": self.date,
    #         "allday": True,
    #         "res_model": self._name,
    #         "res_model_id": self.env.ref(
    #             "crm_salesperson_planner.model_crm_salesperson_planner_visit"
    #         ).id,
    #         "res_id": self.id,
    #     }

    # def create_calendar_event(self):
    #     events = self.env["calendar.event"]
    #     for item in self:
    #         event = self.env["calendar.event"].create(
    #             item._prepare_calendar_event_vals()
    #         )
    #         if event:
    #             event.activity_ids.unlink()
    #             item.calendar_event_id = event
    #         events += event
    #     return events

    def action_incident(self, image=None, notes=None):
        if self.state not in ["draft", "confirm"]:
            raise ValidationError(_("The visit must be in draft or validated state"))
        self.write(
            {
                "state": "incident",
                "close_reason_image": image,
                "close_reason_notes": notes,
            }
        )

    def unlink(self):
        if any(sel.state not in ["draft", "cancel"] for sel in self):
            raise ValidationError(_("Visits must be in cancelled state"))
        return super().unlink()

    def write(self, values):
        ret_val = super().write(values)
        # if (values.get("date") or values.get("user_id")) and not self.env.context.get(
        #     "bypass_update_event"
        # ):
        #     new_vals = {}
        #     for item in self.filtered(lambda a: a.calendar_event_id):
        #         if values.get("date"):
        #             new_vals["start"] = values.get("date")
        #             new_vals["stop"] = values.get("date")
        #         if values.get("user_id"):
        #             new_vals["user_id"] = values.get("user_id")
        #         item.calendar_event_id.write(new_vals)
        return ret_val


class VisitPurpose(models.Model):
    _name = 'visit.purpose'
    _description = 'Visit Purpose'

    name = fields.Char(string="Visit Purpose", required=True)


class CrmSalespersonPlannerVisitCustomerLine(models.Model):
    _name = "crm.salesperson.planner.visit.customer.line"
    _description = "Visit Customer Line"

    visit_id = fields.Many2one(
        comodel_name="crm.salesperson.planner.visit",
        string="Visit",
        required=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
        
    )
    partner_phone = fields.Char(string="Phone", related="partner_id.phone")
    partner_mobile = fields.Char(string="Mobile", related="partner_id.mobile")

    product_ids = fields.Many2many(
        comodel_name="product.template",
        relation="crm_salesperson_planner_visit_line_product_rel",
        string="Products",
        domain="[('sale_ok', '=', True)]",
    )
    product_performance = fields.Char(string="اداء منتجاتنا ورضا العميل")
    cultivated_area = fields.Float(string="المساحة المزروعة (فدان)")
    crop_type = fields.Char(string="نوع المحصول")
    growth_stage = fields.Selection([
    ('germination', 'انبات'),
    ('vegetative', 'نمو خضري'),
    ('flowering', 'تزهير'),
    ('fruiting', 'عقد'),
    ('harvest', 'حصاد')
    ], string="مرحلة النمو")

    crop_condition = fields.Selection([
    ('excellent', 'ممتاز'),
    ('good', 'جيد'),
    ('average', 'متوسط'),
    ('light', 'خفيف')
    ], string="حالة المحصول")
    observed_issues = fields.Char(string="المشاكل الظاهرة")
    technical_recommendations = fields.Char(string="التوصيات الفنية المقدمة")
    next_visit_date = fields.Date(string="موعد الزيارة القادمة")
    company_required_actions = fields.Text(string="إجراءات مطلوبة من الشركة")
    competitor_company = fields.Char(string="اسم الشركة المنافسة")
    competitor_product = fields.Char(string="المنتج المنافس")
    competitor_price = fields.Char(string="السعر")
    strengths_weaknesses = fields.Char(string="نقاط القوة و الضعف")
    executed_orders = fields.Char(string="الطلبات المنفذة")
    
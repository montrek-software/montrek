from django.urls import reverse
from company.repositories.company_repository import CompanyRepository
from baseclasses.dataclasses.view_classes import TabElement, ActionElement
from baseclasses.pages import MontrekPage


class CompanyOverviewPage(MontrekPage):
    page_title = "Companies"

    def get_tabs(self):
        action_new_company = ActionElement(
            icon="plus",
            link=reverse("company_create"),
            action_id="id_create_company",
            hover_text="Create company",
        )
        overview_tab = TabElement(
            name="Company List",
            link=reverse("company"),
            html_id="tab_company_list",
            active="active",
            actions=(action_new_company,),
        )
        action_upload_file = ActionElement(
            icon="upload",
            link=reverse("company_upload_file"),
            action_id="id_company_upload",
            hover_text="Upload company data from file",
        )
        file_upload_tab = TabElement(
            name="Uploads",
            link=reverse("company_view_uploads"),
            html_id="tab_uploads",
            actions=(action_upload_file,),
        )
        return (overview_tab, file_upload_tab)


class CompanyPage(MontrekPage):
    show_date_range_selector = True
    repository = CompanyRepository()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "pk" not in kwargs:
            raise ValueError("CompanyPage needs pk specified in url!")
        self.obj = CompanyRepository().std_queryset().get(pk=kwargs["pk"])
        self.page_title = self.obj.company_name

    def get_tabs(self):
        company_id = self.obj.pk
        action_back = ActionElement(
            icon="arrow-left",
            link=reverse("company"),
            action_id="back_to_overview",
            hover_text="Back to Overview",
        )
        action_delete_company = ActionElement(
            icon="trash",
            link=reverse("company_delete", kwargs={"pk": company_id}),
            action_id="delete_company",
            hover_text="Delete Company",
        )
        action_update_company = ActionElement(
            icon="pencil",
            link=reverse("company_update", kwargs={"pk": self.obj.id}),
            action_id="update_company",
            hover_text="Update Company",
        )
        details_tab = TabElement(
            name="Details",
            link=reverse("company_details", kwargs={"pk": self.obj.id}),
            html_id="tab_details",
            actions=(action_back, action_delete_company, action_update_company),
        )
        time_series_tab = TabElement(
            name="Time Series",
            link=reverse("company_ts_table", kwargs={"pk": self.obj.id}),
            html_id="tab_company_ts_table",
            actions=(action_back,),
        )
        history_tab = TabElement(
            name="History",
            link=reverse("company_history", kwargs={"pk": self.obj.id}),
            html_id="tab_history",
            actions=(action_back,),
        )

        return [details_tab, time_series_tab, history_tab]

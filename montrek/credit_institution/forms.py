from django import forms

from credit_institution.models import CreditInstitutionStaticSatellite


class CreditInstitutionCreateForm(forms.ModelForm):
    class Meta:
        model = CreditInstitutionStaticSatellite
        fields = [
            "credit_institution_name",
            "credit_institution_bic",
            "account_upload_method",
        ]

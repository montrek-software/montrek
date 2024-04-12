from baseclasses.forms import MontrekCreateForm


class MailingSendForm(MontrekCreateForm):
    class Meta:
        exclude = ("comment", "mail_state", "hub_entity_id")

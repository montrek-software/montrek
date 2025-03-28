from decouple import config
from baseclasses.dataclasses.link_model import LinkModel
from baseclasses.managers.montrek_manager import MontrekManager


class MontrekLinkManager(MontrekManager):
    def get_links(self) -> list[LinkModel]:
        raise NotImplementedError

    def to_html(self):
        html = "<table>"
        for link in self.get_links():
            target = "_self"
            if link.new_tab:
                target = "_blank"
            html += f'<tr style="background-color:transparent;"><td><a href="{link.href}" target="{target}">{link.title}</a></td></tr>'
        html += "</table>"
        return html


class DefaultLinkManager(MontrekLinkManager):
    def get_links(self) -> list[LinkModel]:
        links_config = config("LINKS", default="http://example.com,Example").split(" ")
        links = []
        for link in links_config:
            link_constituents = link.split(",")
            links.append(
                LinkModel(href=link_constituents[0], title=link_constituents[1])
            )
        return links

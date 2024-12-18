from reporting.managers.montrek_details_manager import MontrekDetailsManager
from reporting.dataclasses import table_elements as te
from reporting.managers.montrek_table_manager import MontrekTableManager
from showcase.repositories.sproduct_repositories import SProductRepository


class SProductTableManager(MontrekTableManager):
    repository_class = SProductRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.LinkTableElement(
                name="Details",
                url="sproduct_details",
                kwargs={"pk": "id"},
                icon="eye-open",
                hover_text="View Product Details",
            ),
            te.LinkTableElement(
                name="Edit",
                url="sproduct_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Product",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sproduct_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Product",
            ),
        ]


class SProductDetailsManager(MontrekDetailsManager):
    repository_class = SProductRepository

    @property
    def table_elements(self):
        return [
            te.StringTableElement(name="Product Name", attr="product_name"),
            te.DateTableElement(name="Inception Date", attr="inception_date"),
            te.LinkTableElement(
                name="Edit",
                url="sproduct_update",
                icon="edit",
                kwargs={"pk": "id"},
                hover_text="Update Product",
            ),
            te.LinkTableElement(
                name="Delete",
                url="sproduct_delete",
                icon="trash",
                kwargs={"pk": "id"},
                hover_text="Delete Product",
            ),
        ]

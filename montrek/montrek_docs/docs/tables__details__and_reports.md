Tables, Details, and Reports

## Definition

In Montrek, tables, details, and reports are essential components for displaying and managing data. Tables provide a structured way to present data, while details offer a more in-depth view of individual records. Reports, on the other hand, enable users to generate summaries and analysis of their data.

## Rendering

Montrek provides several ways to render tables, details, and reports. For tables, the `MontrekTableManager` class is responsible for generating the table structure and populating it with data. The `to_html` method can be used to render the table as HTML.

```python
from reporting.managers.montrek_table_manager import MontrekTableManager

table_manager = MontrekTableManager()
html_table = table_manager.to_html()
```

For details, the `MontrekDetailsManager` class is used to generate a detailed view of a single record. The `to_html` method can be used to render the details as HTML.

```python
from reporting.managers.montrek_details_manager import MontrekDetailsManager

details_manager = MontrekDetailsManager()
html_details = details_manager.to_html()
```

For reports, the `MontrekReportManager` class is responsible for generating reports based on user-defined criteria. The `generate_report` method can be used to render the report as HTML.

```python
from reporting.managers.montrek_report_manager import MontrekReportManager

report_manager = MontrekReportManager()
html_report = report_manager.generate_report()
```

## Connection to Models or Views

In Montrek, tables, details, and reports are often connected to models or views to retrieve and display data. The `MontrekTableManager` class, for example, can be used to generate a table based on a Django model.

```python
from django.db import models
from reporting.managers.montrek_table_manager import MontrekTableManager

class MyModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

table_manager = MontrekTableManager(model=MyModel)
html_table = table_manager.to_html()
```

Similarly, the `MontrekDetailsManager` class can be used to generate a detailed view of a single record based on a Django model.

```python
from django.db import models
from reporting.managers.montrek_details_manager import MontrekDetailsManager

class MyModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

details_manager = MontrekDetailsManager(model=MyModel)
html_details = details_manager.to_html()
```

Reports can also be generated based on data from Django models or views.

```python
from django.db import models
from reporting.managers.montrek_report_manager import MontrekReportManager

class MyModel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

report_manager = MontrekReportManager(model=MyModel)
html_report = report_manager.generate_report()
```

## Sum Row

A `MontrekTableManager` or `MontrekDataFrameTableManager` can show a row under the table with the sum of each numeric column. The sums cover all rows of the table, not only those of the current page.

```python
from reporting.dataclasses.summary_row_config import SummaryRowConfig

class HubCTableManager(MontrekTableManager):
    show_summary_row = True
    summary_row_config = SummaryRowConfig(
        exclude_attrs=("field_tsc3_int",),
        label_attr="field_tsc3_str",
    )
```

- Every `NumberTableElement` column is summed, except `PercentTableElement` and `ProgressBarTableElement` columns and those in `exclude_attrs`.
- The label reads "Sum", or "Summe" if `LANGUAGE_CODE` is German. It is shown in the column `label_attr`, by default the first column that is not summed.
- Columns of the queryset are summed in one SQL query. Columns whose table element computes its value in `get_value()` are summed in Python over all rows.
- A table with `is_large = True` cannot show a sum row; defining such a manager raises `ImproperlyConfigured`.
- The row is shown in the HTML, PDF and LaTeX table, in the Markdown table and in the Excel download, with the totals as numbers. CSV and JSON leave it out, as programs reading them would count it as a row.

## Markdown

`to_markdown()` renders a table or a details block as GitHub flavoured Markdown, e.g. for the body of an issue on a forge or as context for a language model.

```python
markdown = HubCTableManager(session_data).to_markdown()
markdown = HubCDetailsManager(session_data).to_markdown(base_url="")
```

- A table has the columns of its export manager, as the CSV and Excel downloads, and the rows of all pages. Numeric columns are aligned right, and a sum row is shown as in Excel.
- A details block is a table of labels and values. An element with `markdown_section=True` follows the table as a section of its own, so that the line breaks of a long text survive; `TextTableElement` does so by default. Empty sections are left out.
- Icon links (`LinkTableElement`) are left out, as in the other exports. Links of `LinkTextTableElement` and `LinkListTableElement` become Markdown links. They start with `base_url`, by default the host of the request (`session_data["host_url"]`), so that they work where the Markdown is read; pass `base_url=""` for relative links.
- List and details views offer the Markdown as a download next to CSV and Excel (`?gen_md=true`). A table too large for a direct download is mailed, as its CSV and Excel are.
- Each element renders its cell with `get_markdown(obj, base_url)`. HTML in a value is converted to Markdown (`HtmlMarkdownConverter`), plain text is kept as it is, so Markdown typed into a field renders. Override `format_markdown(value)` for a value that needs no row, `get_markdown()` for one that does.

A report renders as Markdown too (`MontrekReportManager.to_markdown()`, or `?gen_md=true` on a report view): its title, then its elements one below the other. Grids lose their columns, plots are named by their title, a `MarkdownReportingElement` is kept as it is. A report element of another app without `to_markdown()` is converted from its HTML (`ReportElementMarkdown`), which keeps its text.

## Summary

In summary, Montrek provides a range of tools and classes for generating tables, details, and reports. These components can be used to display and manage data in a structured and meaningful way. By connecting these components to Django models or views, developers can create powerful and data-driven applications.

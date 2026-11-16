from dataclasses import dataclass, field

from baseclasses.forms import LocalizedText


@dataclass(frozen=True)
class SummaryRowConfig:
    """How a table manager with ``show_summary_row`` sums its columns.

    Every numeric column is summed over all rows of the table, not only those
    of the page, except the columns in ``exclude_attrs`` (e.g. a year or a price
    per unit). ``label`` is shown in the column ``label_attr``, by default the
    first column that is not summed.
    """

    exclude_attrs: tuple[str, ...] = ()
    label_attr: str = ""
    label: LocalizedText = field(default=LocalizedText(en="Sum", de="Summe"))

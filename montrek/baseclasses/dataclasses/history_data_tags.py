from dataclasses import dataclass
import datetime


@dataclass
class HistoryDataTag:
    change_date: datetime.datetime
    user_emails: list[str]
    comments: list[str]

    def get_user_string(self) -> str:
        return ",".join([user_email for user_email in self.user_emails])

    def get_comment_string(self) -> str:
        return ",".join([comment for comment in self.comments])


class HistoryDataTagSet:
    def __init__(self):
        self._data = []

    def append(
        self,
        change_date: datetime.datetime,
        user_email: str | None,
        comment: str | None,
    ):
        user_email = user_email or ""
        comment = comment or ""
        if (index := self._date_index(change_date)) != -1:
            if user_email not in self._data[index].user_emails:
                self._data[index].user_emails.append(user_email)
            if comment not in self._data[index].comments:
                self._data[index].comments.append(comment)
        else:
            self._data.append(HistoryDataTag(change_date, [user_email], [comment]))

    def _date_index(self, change_date: datetime.datetime) -> int:
        for index, data in enumerate(self._data):
            if data.change_date == change_date:
                return index
        return -1

    def __getitem__(self, index: int) -> HistoryDataTag:
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)

from dataclasses import dataclass
import datetime


@dataclass
class HistoryDataTag:
    change_date: datetime.datetime
    user_ids: list[int]

    def get_user_string(self) -> str:
        return ",".join([str(user_id) for user_id in self.user_ids])


class HistoryDataTagSet:
    def __init__(self):
        self._data = []

    def append(self, change_date: datetime.datetime, user_id: int):
        if (index := self._date_index(change_date)) != -1:
            if user_id not in self._data[index].user_ids:
                self._data[index].user_ids.append(user_id)
        else:
            self._data.append(HistoryDataTag(change_date, [user_id]))

    def _date_index(self, change_date: datetime.datetime) -> int:
        for index, data in enumerate(self._data):
            if data.change_date == change_date:
                return index
        return -1

    def __getitem__(self, index: int) -> HistoryDataTag:
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)

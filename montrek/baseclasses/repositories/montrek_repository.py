
class MontrekRepository():
    def detail_queryset(self, **kwargs):
        raise NotImplementedError('MontrekRepository has no detail_queryset method!')

    def table_queryset(self, **kwargs):
        raise NotImplementedError('MontrekRepository has no table_queryset method!')

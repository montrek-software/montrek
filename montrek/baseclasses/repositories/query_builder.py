class QueryBuilder:
    def __init__(self, model, annotator):
        self.model = model
        self.annotator = annotator

    def build_queryset(self):
        return self.model.objects.annotate(**self.annotator.annotations)

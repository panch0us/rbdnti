from django import forms

class MultiFileUploadForm(forms.Form):
    news_id = forms.IntegerField(widget=forms.HiddenInput())
    # Убираем поле files полностью - будем обрабатывать напрямую в view
from django import forms


ALLOWED_STATUSES = (
    ("в продаже", "В продаже"),
    ("продан", "Продан"),
    ("забронирован", "Забронирован"),
)


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
        error_messages={
            "invalid": "Некорректный email.",
            "required": "Укажите email.",
        },
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Введите пароль"}),
        error_messages={"required": "Укажите пароль."},
    )


class RegisterForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
        error_messages={
            "invalid": "Некорректный email.",
            "required": "Укажите email.",
        },
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Минимум 6 символов"}),
        min_length=6,
        error_messages={
            "min_length": "Пароль: минимум 6 символов.",
            "required": "Укажите пароль.",
        },
    )


class ProfileUpdateForm(forms.Form):
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Новый пароль"}),
        min_length=6,
    )


class PropertyFilterForm(forms.Form):
    property_type_id = forms.ChoiceField(
        required=False,
        choices=(("", "Любой тип"),),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    status_filter = forms.ChoiceField(
        required=False,
        choices=(("", "Любой"),) + ALLOWED_STATUSES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    min_price = forms.DecimalField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )
    max_price = forms.DecimalField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )
    min_area = forms.FloatField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"})
    )
    max_area = forms.FloatField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"})
    )
    page = forms.IntegerField(
        required=False, min_value=1, initial=1, widget=forms.NumberInput(attrs={"class": "form-control"})
    )
    size = forms.ChoiceField(
        required=False,
        choices=(("10", "10"), ("20", "20"), ("50", "50")),
        initial="10",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class PropertyForm(forms.Form):
    property_type_id = forms.ChoiceField(
        choices=(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    total_area = forms.FloatField(widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}))
    finishing = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    wall_material = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    floor = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    floors_total = forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}))
    price = forms.DecimalField(widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    discount_price = forms.DecimalField(
        required=False, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )
    status = forms.ChoiceField(choices=ALLOWED_STATUSES, widget=forms.Select(attrs={"class": "form-select"}))
    address = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}))


class UploadPhotoForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={"class": "form-control"}))


class MultiFileInput(forms.FileInput):
    allow_multiple_selected = True


class UploadPhotosForm(forms.Form):
    files = forms.FileField(
        widget=MultiFileInput(attrs={"class": "form-control", "multiple": True}),
    )


class UploadDocumentForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={"class": "form-control"}))
    doc_type = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "схема"}))


ROLE_CHOICES = (
    ("user", "Пользователь"),
    ("manager", "Менеджер"),
    ("admin", "Администратор"),
)


class AssignRoleForm(forms.Form):
    user_id = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"}))
    role_name = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))


class DeleteUserForm(forms.Form):
    user_id = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": "form-control"}))


class SimplePropertyTypeForm(forms.Form):
    name = forms.CharField(
        max_length=256,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Например: квартира"}),
    )


CONTRACT_STATUSES = (
    ("создан", "Создан"),
    ("подписан", "Подписан"),
)


class ContractPatchForm(forms.Form):
    status = forms.ChoiceField(required=False, choices=(("", "(не менять)"),) + CONTRACT_STATUSES, widget=forms.Select(attrs={"class": "form-select"}))
    contract_date = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "YYYY-MM-DD"}))


class ContractFullForm(forms.Form):
    real_estate_object_id = forms.TypedChoiceField(
        coerce=int,
        choices=(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    user_id = forms.TypedChoiceField(
        coerce=int,
        choices=(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    manager_id = forms.TypedChoiceField(
        coerce=int,
        choices=(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    contract_date = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    status = forms.ChoiceField(choices=CONTRACT_STATUSES, widget=forms.Select(attrs={"class": "form-select"}))


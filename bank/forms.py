from django import forms

from .models import Account
from .utils import encrypt
from .validators import is_valid_pin


class AccountAdminForm(forms.ModelForm):
    new_pin = forms.CharField(
        label="Set new PIN",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="6 digits. Leave blank to keep the current PIN unchanged.",
    )
    confirm_new_pin = forms.CharField(
        label="Confirm new PIN",
        required=False,
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = Account
        fields = (
            "acc_no",
            "name",
            "mobile",
            "aadhar",
            "address",
            "dob",
            "gender",
            "occupation",
            "balance",
        )

    def clean(self):
        cleaned = super().clean()
        new = (cleaned.get("new_pin") or "").strip()
        conf = (cleaned.get("confirm_new_pin") or "").strip()
        if new or conf:
            if new != conf:
                raise forms.ValidationError("New PIN and confirmation do not match.")
            if not is_valid_pin(new):
                raise forms.ValidationError("PIN must be exactly 6 digits.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        new = (self.cleaned_data.get("new_pin") or "").strip()
        if new:
            obj.pin = encrypt(new)
        if commit:
            obj.save()
        return obj

import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_admin_login_page(client):
    url = reverse("admin:login")
    resp = client.get(url)
    assert resp.status_code in (200, 302)

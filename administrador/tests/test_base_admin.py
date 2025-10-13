import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
class TestBaseAdminView:
    def test_acceso_staff(self, client):
        #_user = User.objects.create_user(username="admin", password="1234", is_staff=True)
        client.login(username="admin", password="1234")
        url = reverse("administrador:base_admin")
        response = client.get(url)
        assert response.status_code == 200
        assert any("base_admin.html" in t.name for t in response.templates)

    def test_acceso_no_staff_redirige(self, client):
        #_user = User.objects.create_user(username="user", password="1234", is_staff=False)
        client.login(username="user", password="1234")
        url = reverse("administrador:base_admin")
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == "/"
